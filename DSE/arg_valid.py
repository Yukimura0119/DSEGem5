import os
import argparse


def valid_file(param):
    if not os.path.isfile(param):
        raise argparse.ArgumentTypeError(f'The file "{param}" does not exist.')
    return param


def valid_optimize(param):
    if param not in ["SW", "HW", "CO"]:
        raise argparse.ArgumentTypeError("Invalid optimize")
    return param


def valid_hw_algo(param):
    if param not in ["BO", "GA"]:
        raise argparse.ArgumentTypeError("HW algo only BO or GA")
    return param


def valid_sw_algo(param):
    if param not in ["GA"]:
        raise argparse.ArgumentTypeError("SW algo only GA")
    return param


def valid_cost_model(param):
    if param not in ["maestro", "gem5"]:
        raise argparse.ArgumentTypeError("Cost model only maestro or gem5")
    return param


def valid_metrics(param):
    if param not in ["latency", "energy", "both"]:
        raise argparse.ArgumentTypeError(
            "Metrics only latency, energy, or both")
    return param
def valid_dataflow(param):
    if param not in ["nvdla", "shi", "random"]:
        raise argparse.ArgumentTypeError(
            "Metrics only latency, energy, or both")
    return param
