#!/bin/python
# -*- coding: utf-8 -*-

import os, sys
import argparse
import easl as easl  # brings in the EASL class (selection + model updates)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    # The script can either:
    # - generate new HITs (batches of items to annotate), or
    # - update the model with results from annotators
    arg_parser.add_argument(
        '--operation', dest="operation", choices=["generate", "update"], required=True,
        default=None, help="choose whether to generate HITs or update the model"
    )

    # Path to the current model file (e.g. project_0.csv, project_1.csv, …)
    arg_parser.add_argument(
        '--model', dest="model_path", required=False,
        default=None, help="path to the model CSV"
    )

    # Number of items shown together in one HIT (default: 5)
    arg_parser.add_argument(
        '--item', dest="param_items", type=int, required=False,
        default=5, help="items per HIT (default 5)"
    )

    # Gamma controls how similar/different partner items are when paired
    arg_parser.add_argument(
        '--match', dest="param_match", type=float, required=False,
        default=0.1, help="gamma parameter for partner selection (default 0.1)"
    )

    # How many HITs to generate in this round
    arg_parser.add_argument(
        '--hits', dest="param_hits", type=int, required=False,
        default=20, help="number of HITs to generate (recommend: total_items / items_per_hit)"
    )

    args = arg_parser.parse_args()

    # Package parsed arguments into a dict (EASL expects params in this form)
    params = {k: v for k, v in vars(args).items()}

    # Create the EASL model object with the given runtime parameters
    model = easl.EASL(params)

    # Quick sanity checks
    if args.operation is None:
        print("Please specify an operation: generate or update")
        exit(1)

    if args.model_path is None:
        print("Please provide a model_path")
        exit(1)

    # Figure out where we are in the iteration process
    model_path = args.model_path
    model_dir = '/'.join(model_path.split('/')[:-1])          # folder containing the model CSV
    model_name = "_".join(model_path.split('/')[-1].split('_')[:-1])  # base name without _t
    iterNum = int(model_path.split('/')[-1].split('.')[0].split('_')[-1])  # parse iteration number

    # --- OPERATION 1: GENERATE HITs ---
    if args.operation == "generate":
        model.loadItem(model_path)  

        # Save HITs as: project_hit_{t+1}.csv
        hit_path = model_dir + '/' + model_name + '_hit_' + str(iterNum + 1) + ".csv"

        # For round 0 → random groups; later → high-variance seeds + partners by match quality
        nextItems = model.getNextK(args.param_hits, iterNum)

        # Write the HIT CSV with N items per row (id1,sent1,...,idN,sentN,...)
        model.generateHits(hit_path, nextItems)

    # --- OPERATION 2: UPDATE MODEL ---
    if args.operation == "update":
        # Look for the MTurk results file from this round
        observe_path = model_dir + '/' + model_name + '_result_' + str(iterNum + 1) + ".csv"
        if not os.path.exists(observe_path):
            print(f"MTurk result file not found. Expected: {observe_path}")
            exit(1)

        # Next model file will be: project_{t+1}.csv
        new_model_path = model_dir + '/' + model_name + '_' + str(iterNum + 1) + ".csv"

        # Load the current model, apply new annotations, and save the updated state
        model.loadItem(model_path)
        model.observe(observe_path)
        model.saveItem(new_model_path)
