#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import json
import random
import numpy as np

# fixed seeds so HIT sampling is repeatable
np.random.seed(12345)
random.seed(12345)


# preferred column order (extras are kept after these)
STANDARD_COLS = ["output_id", "output", "prompt_id", "prompt", "alpha", "beta", "mode", "var", "embedding"]

class EASL:
    """Minimal EASL core: load model, pick HITs, and fold in scores."""

    def __init__(self, params):
        self.params = params
        self.items = {}        # output_id -> row dict
        self.headerModel = []  # ordered model headers
        self.headerHits = []   # model headers repeated per slot (id1, id2, ...)
        self.emb_cache = {}

    def get_embedding(self, text):
        """Placeholder for embedding generation from text."""
        # This can be replaced with real embedding logic
        return []

    def loadItem(self, filePath):
        # read model CSV, normalise header order, cache rows by output_id
        with open(filePath, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            ordered = [c for c in STANDARD_COLS if c in fieldnames]
            extras = [c for c in fieldnames if c not in ordered]
            self.headerModel = ordered + extras

            # build per-slot HIT header
            self.headerHits = []
            for h in self.headerModel:
                for i in range(1, self.params["param_items"] + 1):
                    self.headerHits.append(f"{h}{i}")

            # cache items
            for row in reader:
                # If embedding is missing or empty, generate and store it
                emb_col = self.params.get("param_emb_col", "embedding")
                if not row.get(emb_col):
                    embedding_vec = self.get_embedding(row.get("output", ""))
                    row[emb_col] = json.dumps(embedding_vec)
                oid = row["output_id"]
                self.items[oid] = row
                # parse and cache embedding
                try:
                    emb_vec = np.array(json.loads(row[emb_col]), dtype=float)
                except Exception:
                    emb_vec = None
                self.emb_cache[oid] = emb_vec

    def saveItem(self, newModelPath):
        # write updated model with normalised header order
        with open(newModelPath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self.headerModel)
            writer.writeheader()
            for row in self.items.values():
                writer.writerow(row)

    def generateHits(self, filePath, hitItems):
        # write HIT CSV: each row = N items side-by-side
        with open(filePath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.headerHits)
            writer.writeheader()
            for seed_id, partners in hitItems.items():
                ids = [seed_id] + list(partners)
                random.shuffle(ids)  # shuffle within the HIT to avoid position bias
                rowDict = {}
                for slot, oid in enumerate(ids, start=1):
                    for h in self.headerModel:
                        rowDict[f"{h}{slot}"] = self.items[oid][h]
                writer.writerow(rowDict)

    # ---------- helpers ----------

    def _parse_vec(self, row):
        """Return embedding vector (np.array) from the configured column, or None."""
        col = self.params.get("param_emb_col", "embedding")
        oid = row.get("output_id")
        if oid in self.emb_cache:
            return self.emb_cache[oid]
        s = row.get(col)
        if not s:
            return None
        try:
            v = np.array(json.loads(s), dtype=float)
            self.emb_cache[oid] = v
            return v
        except Exception:
            return None

    @staticmethod
    def _cos_sim(a, b):
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0.0 or nb == 0.0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def mode_beta(self, alpha, beta):
        alpha, beta = float(alpha), float(beta)
        if alpha == 1.0 and beta == 1.0:
            return 0.5
        if alpha + beta <= 2.0:
            return alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
        return (alpha - 1.0) / (alpha + beta - 2.0)

    def var_beta(self, alpha, beta):
        alpha, beta = float(alpha), float(beta)
        denom = (alpha + beta) ** 2 * (alpha + beta + 1.0)
        return (alpha * beta) / denom if denom > 0 else 0.0

    # ---------- selection ----------

    def getNextK(self, k, iterNum):
        """Return a dict: seed_id -> array of (N-1) partner ids."""
        kItems = {}
        N = self.params["param_items"]

        # iteration 0: random groups to cover the pool once
        if iterNum == 0:
            idList = list(self.items.keys())
            random.shuffle(idList)
            rem = len(idList) % N
            if rem != 0:
                idList += idList[:(N - rem)]
            it = iter(idList)
            for chunk in zip(*[it] * N):
                seed, partners = chunk[0], np.array(chunk[1:])
                kItems[seed] = partners
            return kItems

        # later: seeds = top-k variance; partners sampled by (scalar × embedding) match
        varList = sorted(
            [(oid, float(row["var"])) for oid, row in self.items.items()],
            key=lambda x: (-x[1], x[0])
        )
        seeds = varList[:k]
        pool = set(self.items.keys())
        for oid, _ in seeds:
            pool.discard(oid)

        gamma = float(self.params["param_match"])
        lam = float(self.params.get("param_emb_weight", 0.5))   # [0,1]
        emb_eps = float(self.params.get("param_emb_eps", 0.05))

        for oid, _ in seeds:
            m_j = float(self.items[oid]["mode"])
            v_j = float(self.items[oid]["var"])
            emb_j = self.emb_cache.get(oid)

            cand_ids, cand_scores = [], []
            total = 0.0

            for cid in pool:
                m_i = float(self.items[cid]["mode"])
                v_i = float(self.items[cid]["var"])

                # scalar match quality
                c2 = 2.0 * (gamma ** 2) + v_j + v_i
                q_scalar = np.sqrt((2.0 * (gamma ** 2)) / c2) * np.exp(-((m_j - m_i) ** 2) / (2.0 * c2))

                # embedding factor (0..1); neutral 0.5 if missing
                emb_i = self.emb_cache.get(cid)
                if emb_j is not None and emb_i is not None:
                    cos01 = 0.5 * (self._cos_sim(emb_j, emb_i) + 1.0)
                else:
                    cos01 = 0.5

                # blend scalar + embeddings with a small floor
                factor_emb = emb_eps + (1.0 - emb_eps) * ((1.0 - lam) + lam * cos01)
                q = q_scalar * factor_emb

                cand_ids.append(cid)
                cand_scores.append(q)
                total += q

            probs = [s / total for s in cand_scores] if total > 0 else [1.0 / len(cand_ids)] * len(cand_ids)
            partners = np.random.choice(cand_ids, N - 1, p=probs, replace=False)
            kItems[oid] = partners

        return kItems

    # ---------- MTurk parsing helpers ----------

    def _get_rating_from_row(self, row, i):
        """
        Return the raw rating string for slot i from an MTurk row, trying several
        common field name variants (e.g., Answer.range{i}, Answer.Answer.gender_range{i}).
        """
        candidates = [
            f"Answer.range{i}",
            f"Answer.Answer.range{i}",
            f"Answer.gender_range{i}",
            f"Answer.Answer.gender_range{i}",
            f"range{i}",
        ]
        for key in candidates:
            if key in row and row[key] not in (None, ""):
                return row[key]
        # Fallback: search any Answer* key that ends with the slot index
        # e.g., "Answer.something_range3" -> i == 3
        suffix = str(i)
        for k, v in row.items():
            if k.startswith("Answer") and k.endswith(suffix) and v not in (None, ""):
                return v
        return None

    def _open_result_reader(self, path):
        """
        Try multiple encodings so MTurk exports (UTF-16, UTF-8-BOM, etc.) don't crash parsing.
        Returns: (file_handle, csv.DictReader)
        Caller is responsible for closing file_handle.
        """
        encodings = ["utf-8-sig", "utf-16", "utf-8", "latin-1"]
        last_err = None
        for enc in encodings:
            try:
                f = open(path, 'r', newline='', encoding=enc)
                # Try creating the reader; will raise if header can't be decoded
                reader = csv.DictReader(f)
                # Force read of fieldnames to validate decode
                _ = reader.fieldnames
                return f, reader
            except Exception as e:
                last_err = e
                try:
                    f.close()
                except Exception:
                    pass
                continue
        raise UnicodeError(f"Could not decode results file with tried encodings {encodings}: {last_err}")

    # ---------- updates ----------

    def observe(self, observe_path):
        """Apply scores from result CSV and update alpha/beta/mode/var."""
        f, reader = self._open_result_reader(observe_path)
        try:
            N = self.params["param_items"]
            stream_expected = self.params.get("param_stream")

            for row in reader:
                # only update rows that match this stream 
                stream_choice = row.get("Answer.stream_choice")
                if stream_expected and stream_choice and (stream_choice != stream_expected and
                                                          not stream_choice.startswith(stream_expected[0])):
                    continue

                for i in range(1, N + 1):
                    oid = row.get(f"Input.output_id{i}")
                    if not oid or oid not in self.items:
                        continue
                    s = self._get_rating_from_row(row, i)
                    if s is None or s == "":
                        continue
                    # Convert 1–5 ratings to 0–1 scale, then clamp.
                    s = (float(s) - 1.0) / 4.0
                    # s = float(s) / 100.0
                    if s < 0.0: s = 0.0
                    if s > 1.0: s = 1.0

                    a = float(self.items[oid]["alpha"]) + s
                    b = float(self.items[oid]["beta"])  + (1.0 - s)

                    self.items[oid]["alpha"] = a
                    self.items[oid]["beta"]  = b
                    self.items[oid]["mode"]  = self.mode_beta(a, b)
                    self.items[oid]["var"]   = self.var_beta(a, b)
        finally:
            try:
                f.close()
            except Exception:
                pass
