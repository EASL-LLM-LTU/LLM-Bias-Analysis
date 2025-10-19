#!/bin/python
# -*- coding: utf-8 -*-

import os,sys
import csv
import random
import numpy as np

# Seeds the RNGs so item selection and HIT assembly are repeatable.
np.random.seed(12345) 
random.seed(12345)

class EASL:
    """
    Efficient Annotation for Scalar Labels
    """

    def __init__(self, params):
        # Holds runtime settings (items per HIT, gamma for match quality, number of HITs, etc.).
        self.params = params
        # Stores all items from the model CSV, keyed by item id.
        self.items = {}
        # Keeps the header from the model CSV (e.g., id, sent, alpha, beta, mode, var, ...).
        self.headerModel = []
        # Will be the header for the HIT CSV, i.e., model headers repeated for slots 1..N.
        self.headerHits = []
        print("model parameters")
        print(self.params)

    def loadItem(self, filePath):
        # Loads the current model CSV as a stream of dict rows.
        csvReader = csv.DictReader(open(filePath, 'r'))
        self.headerModel = csvReader.fieldnames
        # Builds the HIT header by appending a slot index (1..N) to each model header.
        for _h in self.headerModel:
            for _i in range(1, self.params["param_items"]+1):
                self.headerHits.append(_h + str(_i))

        # Caches each row by its "id" for quick lookups during selection and updates.
        for row in csvReader:
            self.items[row["id"]] = row

    def saveItem(self, newModelPath):
        # Writes the updated model CSV using the original model headers.
        csvWriter = csv.DictWriter(open(newModelPath, 'w', newline=''), fieldnames=self.headerModel)
        csvWriter.writeheader()
        for row in self.items.values():
            csvWriter.writerow(row)

    def generateHits(self, filePath, hitItems):
        # Writes the HIT CSV with columns like id1,sent1,...,idN,sentN,...
        csvWriter = csv.DictWriter(open(filePath, 'w', newline=''), fieldnames=self.headerHits)
        csvWriter.writeheader()

        # hitItems maps a seed item id to an array of partner ids.
        for itemID, compareIDs in hitItems.items():
            # Combines the seed and its partners, then shuffles their order within the HIT.
            ids = [itemID] + list(compareIDs)
            random.shuffle(ids)
            rowDict = {}

            # For each slot in the HIT, copies all model fields with the slot suffix.
            for i, id_i in enumerate(ids):
                for headerItem in self.headerModel:
                    rowDict[headerItem + str(i+1)] = self.items[id_i][headerItem]
            csvWriter.writerow(rowDict)

    def getNextK(self, k, iterNum):
        # Selects items for k HIT rows and returns {seed_id: [partner_ids]}.
        kItems = {}

        if iterNum == 0:
            # On the first pass, it ensures every item is shown once by random grouping.
            idList = []
            for itemID, row in self.items.items():
                idList.append(itemID)
            random.shuffle(idList)

            # Pads the list so its length is divisible by N (items per HIT).
            residual = self.params["param_items"] - (len(idList) % self.params["param_items"])
            idList = idList + idList[:residual]
            assert len(idList) % self.params["param_items"] == 0
            # Note: if length is already divisible by N, this adds one extra full group (harmless overhead).

            # Splits into chunks of N; treats the first as the seed, the rest as partners.
            for sublist in zip(*[iter(idList)] * self.params["param_items"]):
                kItems[sublist[0]] = np.array(sublist[1:])

        else:
            # For later rounds, it prioritises uncertainty and then pairs by similarity.

            # 1) Picks k seeds with the highest variance (i.e., most uncertain).
            varList = []    # Each entry is (itemID, variance).
            indexSet = set([])

            for itemID, row in self.items.items():
                varList.append((row["id"], float(row["var"])))
                indexSet.add(itemID)

            # Sorts by variance (desc), then by id for stability, and takes the top k.
            varList = sorted(varList, key=lambda x:(-x[1], x[0]))
            kItemList = varList[:k]

            # Ensures a seed cannot be sampled as its own partner.
            for _k in kItemList:
                indexSet.remove(_k[0])

            # 2) For each seed, samples N-1 partners with probability proportional to match quality.
            for _k in kItemList:
                _j = _k[0]  # seed item id
                candidateID = []
                candidateProb = []
                sumProb = 0.
                # Pulls the seed’s current mode and variance.
                m_j = float(self.items[_j]["mode"])
                var_j = float(self.items[_j]["var"])
                param_gamma = float(self.params["param_match"])

                # Computes a match quality score against each remaining candidate.
                for _i in indexSet:
                    m_i = float(self.items[_i]["mode"])
                    var_i = float(self.items[_i]["var"])
                    # c^2 blends gamma and both items' variances.
                    csq = 2. * param_gamma**2 + var_j + var_i
                    # Higher when modes are similar; gamma controls how tight the neighborhood is.
                    matchQuality = np.sqrt(2.0 * param_gamma**2 / csq) * np.exp( -((m_j - m_i)**2) / (2.0 * csq))
                    sumProb += matchQuality
                    candidateID.append(_i)
                    candidateProb.append(matchQuality)

                # Turns raw scores into a probability distribution.
                candidateProb = [p/sumProb for p in candidateProb]
                # Samples distinct partners without replacement according to those probabilities.
                selectedIDs = np.random.choice(candidateID, self.params["param_items"]-1, p=candidateProb, replace=False)
                kItems[_j] = selectedIDs

            # (Authors left some useful debug prints here, commented out.)

        return kItems

    def alpha_from_beta(self, b, m):
        # Given beta and mode, computes the corresponding alpha for a Beta distribution.
        if m==1.0 or m==0.0 or b<=1:
            print("undefined")
            exit(1)
        return m/(1.-m)*b - (2.0*m-1.)/(1.-m)

    def beta_from_alpha(self, a, m):
        # Given alpha and mode, computes the corresponding beta.
        if m==1.0 or m==0.0 or a<=1:
            print("undefined")
            exit(1)
        return (1.-m)*a/m - (1.-2.*m)/m

    def alpha_beta_from_mode_sum(self, m, S):
        # Given a desired mode and total mass S (alpha+beta), returns (alpha, beta).
        alpha = m * (S - 2.) + 1.
        beta = S - (S - 2.) * m - 1.
        assert alpha + beta == S
        return alpha, beta

    def mode(self, alpha, beta):
        # Computes the Beta mode; falls back to 0.5 for Beta(1,1), which has no defined mode.
        alpha, beta = float(alpha), float(beta)
        if alpha == 1. and beta == 1.:
            return 0.5
        else:
            assert alpha + beta > 2.0
            if alpha < 1.0 and beta < 1.0:
                print("Error: alpha={}, beta={}".format(str(alpha), str(beta)))
                exit(1)
            return (alpha - 1.0) / (alpha + beta - 2.0)

    def mean(self, alpha, beta):
        # Returns the mean of a Beta(alpha, beta).
        alpha, beta = float(alpha), float(beta)
        return alpha / (alpha + beta)

    def variance(self, alpha, beta):
        # Returns the variance of a Beta(alpha, beta).
        alpha, beta = float(alpha), float(beta)
        return (alpha * beta) / ((np.power(alpha + beta, 2.0)) * (alpha + beta + 1))

    def observe(self, observe_path):
        # Applies the annotation results to update alpha/beta, then refreshes mode and variance.
        csvReader = csv.DictReader(open(observe_path, 'r'))
        for row in csvReader:
            # Walks each slot 1..N in the HIT row.
            for _i in range(1, self.params["param_items"]+1):
                # Item id as echoed back by the platform.
                id_i = row["Input.id{}".format(_i)]
                # Converts the 0..100 slider score to 0..1.
                s_i = float(row["Answer.range{}".format(_i)])/100.
                # Updates the Beta counts with this score.
                self.items[id_i]["alpha"] = float(self.items[id_i]["alpha"]) + s_i
                self.items[id_i]["beta"] = float(self.items[id_i]["beta"]) + (1. - s_i)
                # Recomputes the item’s mode and variance after the update.
                self.items[id_i]["mode"] = self.mode(self.items[id_i]["alpha"], self.items[id_i]["beta"])
                self.items[id_i]["var"] = self.variance(self.items[id_i]["alpha"], self.items[id_i]["beta"])
