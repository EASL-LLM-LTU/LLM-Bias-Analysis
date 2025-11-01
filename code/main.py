#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import argparse
import easl as easl

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EASL driver (generate HITs / update model)")

    parser.add_argument('--operation', dest="operation", choices=["generate", "update"], required=True,
                        help="generate HIT CSV or update model")
    parser.add_argument('--model', dest="model_path", required=True,
                        help="path to model CSV (e.g., gender_0.csv)")
    parser.add_argument('--item', dest="param_items", type=int, default=6,
                        help="items per HIT (default 6)")
    parser.add_argument('--match', dest="param_match", type=float, default=0.1,
                        help="gamma for match quality (default 0.1)")
    parser.add_argument('--hits', dest="param_hits", type=int, default=20,
                        help="number of HIT rows (default 20)")


    # embedding options
    parser.add_argument('--emb-col', dest="param_emb_col", type=str, default="embedding",
                        help="CSV column with embedding JSON (default 'embedding')")
    parser.add_argument('--emb-weight', dest="param_emb_weight", type=float, default=0.5,
                        help="weight for embedding similarity [0,1] (default 0.5)")
    parser.add_argument('--emb-eps', dest="param_emb_eps", type=float, default=0.05,
                        help="floor added to embedding factor (default 0.05)")
    parser.add_argument('--target', dest="param_target", type=int, default=0,
                        help="optional cumulative ratings target to display as X/Y (default 0 = no target)")

    args = parser.parse_args()
    params = {k: v for k, v in vars(args).items()}

    # get name and iteration from filename like gender_0.csv
    model_path = args.model_path
    model_dir = os.path.dirname(model_path)
    base = os.path.basename(model_path).split('.csv')[0]
    tokens = base.split('_')
    iterNum = int(tokens[-1])
    name = '_'.join(tokens[:-1]) if len(tokens) > 1 else base

    # pass stream name to EASL (used for filtering when updating)
    params["param_stream"] = name

    model = easl.EASL(params)

    if args.operation == "generate":
        model.loadItem(model_path)
        # output HIT file uses the SAME iteration as the input model, e.g., model _0 -> hit _0
        hit_path = os.path.join(model_dir, f"{name}_hit_{iterNum}.csv")
        nextItems = model.getNextK(args.param_hits, iterNum)
        model.generateHits(hit_path, nextItems)
        # Logging: how many seeds selected; corpus-wide embedding coverage
        num_seeds = len(nextItems)
        emb_col = args.param_emb_col
        total_items = len(model.items)
        items_with_emb = sum(
            1 for row in model.items.values()
            if row.get(emb_col) not in (None, "", "null")
        )
        frac_with_emb = (items_with_emb / total_items) if total_items > 0 else 0.0
        print(f"[Generate] {num_seeds} seeds selected for HITs.")
        print(f"[Generate] Embedding coverage: {items_with_emb}/{total_items} items ({frac_with_emb:.1%}).")

    if args.operation == "update":
        observe_path = os.path.join(model_dir, f"{name}_result_{iterNum}.csv")
        if not os.path.exists(observe_path):
            print(f"MTurk result file not found. Expected: {observe_path}")
            sys.exit(1)

        new_model_path = os.path.join(model_dir, f"{name}_{iterNum+1}.csv")
        model.loadItem(model_path)
        num_items = len(model.items)
        # Cumulative ratings = sum over items of (alpha + beta - 2); each new label adds ~1
        def _cum_labels(items_dict):
            total = 0.0
            for row in items_dict.values():
                try:
                    a = float(row.get("alpha", 0.0))
                    b = float(row.get("beta", 0.0))
                    total += max(0.0, (a + b - 2.0))
                except Exception:
                    continue
            return total

        cum_before = _cum_labels(model.items)
        items_with_any_before = sum(
            1 for row in model.items.values()
            if (float(row.get("alpha", 0.0)) + float(row.get("beta", 0.0))) > 2.0
        )

        model.observe(observe_path)   # filters by Answer.stream_choice if set
        model.saveItem(new_model_path)

        cum_after = _cum_labels(model.items)
        delta = cum_after - cum_before

        items_with_any_after = sum(
            1 for row in model.items.values()
            if (float(row.get("alpha", 0.0)) + float(row.get("beta", 0.0))) > 2.0
        )
        frac_with_any = (items_with_any_after / num_items) if num_items > 0 else 0.0

        # Optional progress to a target (e.g., 540/stream)
        target = int(getattr(args, "param_target", 0) or 0)
        if target > 0:
            print(f"[Update] +{int(round(delta))} ratings applied. Stream total = {int(round(cum_after))} / {target}")
        else:
            print(f"[Update] +{int(round(delta))} ratings applied. Stream total = {int(round(cum_after))}")

        print(f"[Update] Coverage: {items_with_any_after}/{num_items} items ({frac_with_any:.1%}) have ≥1 rating.")
        print(f"[Update] Updated model written to {new_model_path}")
