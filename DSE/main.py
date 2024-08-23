import argparse
import os
import timeit
import json
import numpy as np
from GA import HW_GA, SW_GA
from MOGA import SW_MOGA, HW_MOGA
from MOBO import MOBO
from deap import tools
from parser.HW_parser import HWParser
from parser.ONNX_parser import ONNXParser
from design_space import SWSpace, HWSpace
from arg_valid import *

import numpy as np
from pathlib import Path
import pdb


def convert(data):
    if isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {key: convert(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert(item) for item in data]
    else:
        return data

def exportJsonResult(solution, i, hw_algo, sw_algo):
    print(solution)
    
    for list_item in solution:
        if isinstance(list_item, dict):
            for key, val in list_item.items():
                list_item[key] = convert(val)   
    
    fpath = Path(args.output) / f"{args.cost_model}_result" / f"{hw_algo}_{sw_algo}_{args.optimize}_{args.metrics}_{args.dataflow}_result_{i}.json"
    
    if not os.path.exists(f"{args.output}/{args.cost_model}_result"):
        os.makedirs(f"{args.output}/{args.cost_model}_result")

    with open(fpath, "w") as fo:
        json.dump(solution, fo, indent=4)
    return fpath


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def bo_dse(sw_file, hw_file, output, cost_model, dataflow, num_gen):
    start = timeit.default_timer()
    if "vanilla" in hw_file:
        arch_type = "vanilla"
    elif "mesh" in hw_file:
        arch_type = "mesh"
    hw = HWParser(hw_file, cost_model)
    hw_design_space = HWSpace(hw.parse_design_space())
    x = MOBO(hw_design_space, cost_model, arch_type, dataflow, sw_file, num_gen)
    x.run()

def hw_dse(sw_file, hw_file, cost_model, output, dataflow, isCodesign=False, num_generation=1):
    start = timeit.default_timer()
    if "vanilla" in hw_file:
        arch_type = "vanilla"
    elif "mesh" in hw_file:
        arch_type = "mesh"
    hw = HWParser(hw_file, cost_model)
    hw_design_space = HWSpace(hw.parse_design_space())
    output_json = []
    for gen in [num_generation]:
        start = timeit.default_timer()
        num_generations = gen
        sol_per_pop = 10
        if args.metrics == "latency" or args.metrics == "power":
            x = HW_GA(hw_design_space, cost_model, arch_type)
            x.run(gen, num_parents_mating=2, sol_per_pop=10)
            exportJsonResult(x.solution_set, "GA", "fixed")
            end = timeit.default_timer()
            print("HW DSE Time:", end - start)
        elif args.metrics == "both":
            x = HW_MOGA(hw_design_space, cost_model, arch_type,
                        dataflow, isCodesign, sw_file)
            x.setup()
            final_population = x.run(1, num_generations=num_generations, num_parents_mating=10, sol_per_pop=sol_per_pop)
            pareto_fronts = tools.sortNondominated(
                final_population, len(final_population))
            for j, front in enumerate(pareto_fronts, 1):
                for individual in front:
                    output_json.append(
                        {"HW_Config": individual, "Latency": individual.fitness.values[0], "Power": individual.fitness.values[1]})
            filename = exportJsonResult(output_json, 1, "MOGA", "MOGA")
            print(x.best_mapping)
            end = timeit.default_timer()
            print("HW DSE Time:", end - start)


def sw_dse(sw_file, hw_file, cost_model, output, dataflow, num_generation=10):
    if cost_model == "gem5":
        os.system(f"cp {hw_file} ./files/DSE_HW/DSE_hw.json")
    elif cost_model == "maestro":
        with open(hw_file) as fo:
            hw_json = json.load(fo)
            hw_design_point = hw_json["system"]
        with open("./DSE/maestro/data/hw/accelerator_1.m", "w") as fo:
            fo.write(f'num_pes: {hw_design_point["num_pes"]}\n')
            fo.write(f'l1_size_cstr: {hw_design_point["l1_size_cstr"]}\n')
            fo.write(f'l2_size_cstr: {hw_design_point["l2_size_cstr"]}\n')
            fo.write(f'noc_bw_cstr: {hw_design_point["noc_bw_cstr"]}\n')
            fo.write(
                f'offchip_bw_cstr: {hw_design_point["offchip_bw_cstr"]}\n')
    hw = HWParser(hw_file, cost_model)
    pe, local_mem = hw.getPE()
    sw_result_list = []
    for gen in [num_generation]:
        start = timeit.default_timer()
        if args.metrics == "latency" or args.metrics == "power":
            sw = ONNXParser(sw_file)
            sw_design_space = SWSpace(sw.parse_design_space())
            x = SW_GA(sw_design_space, cost_model,
                      sw_file, dataflow, pe, local_mem)
            i = 0
            while i < len(sw_design_space.src_space):
                num_generations = gen
                sol_per_pop = 10
                flag = x.run(i, num_generations=num_generations, num_parents_mating=2, sol_per_pop=sol_per_pop)
                if not flag:
                    i += 1
                    continue
                fuse_num = sw.onnx[i]["fuse"]
                i += fuse_num
                x.design_space.layer = i
                if fuse_num == 0:
                    i += 1
                    x.design_space.layer += 1
                break
            end = timeit.default_timer()
            print(f"Generation {gen} : {end - start}")
            filename = exportJsonResult(x.solution_set, i, "fixed", "GA")
        elif args.metrics == "both":
            sw = ONNXParser(sw_file)
            sw_design_space = SWSpace(sw.parse_design_space())
            x = SW_MOGA(sw_design_space, cost_model, sw_file,
                        args.dataflow, pe, local_mem)
            num_generations = gen
            sol_per_pop = 10
            i = 0
            all_pareto_fronts = {}
            while i < len(sw_design_space.src_space):
                flag = x.setup()
                if flag == False:
                    i += 1
                    continue
                final_population = x.run(1, num_generations=num_generations, sol_per_pop=sol_per_pop)
                print(final_population)
                pareto_fronts = tools.sortNondominated(
                    final_population, len(final_population))
                layer_pareto_fronts = []
                output_json = []
                for j, front in enumerate(pareto_fronts, 1):
                    for individual in front:
                        layer_pareto_fronts.append(
                            list(individual.fitness.values))
                        output_json.append(
                            {"Mapping": individual, "Latency": individual.fitness.values[0], "Power": individual.fitness.values[1]})
                filename = exportJsonResult(output_json, i, "fixed", "MOGA")
                # x.plotPareto(layer_pareto_fronts, i)
                print(output_json)
                fuse_num = sw.onnx[i]["fuse"]
                i += fuse_num
                x.design_space.layer = i
                if fuse_num == 0:
                    i += 1
                    x.design_space.layer += 1
                print(layer_pareto_fronts)
                i += 1
                sw_design_space.layer = i
                break
            end = timeit.default_timer()
            print(end - start)
        sw_result_list.append(filename)
    return sw_result_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sw', type=valid_file,
                        required=True, help="Given an ONNX model")
    parser.add_argument('--arch', type=valid_file,
                        required=True, help="Given HW config")
    parser.add_argument('--optimize', type=valid_optimize,
                        default="SW", help="SW / HW / CO")
    parser.add_argument('--hw_algo', type=valid_hw_algo,
                        default="GA", help="BO / GA")
    parser.add_argument('--sw_algo', type=valid_sw_algo,
                        default="GA", help="GA")
    parser.add_argument('--cost_model', type=valid_cost_model,
                        default="gem5", help="maestro / gem5")
    parser.add_argument('--metrics',  type=valid_metrics,
                        default='latency', help="latency / power / both")
    parser.add_argument('--output', help="output file path")
    parser.add_argument('--dataflow', default="random",
                        type=valid_dataflow, help="nvdla / shi / random")
    args = parser.parse_args()
    if (args.optimize == 'SW'):
        sw_dse(sw_file=args.sw, hw_file=args.arch, cost_model=args.cost_model,
               output=args.output, dataflow=args.dataflow, num_generation=10)
    elif (args.optimize == 'HW'):
        hw_dse(sw_file=args.sw, hw_file=args.arch, cost_model=args.cost_model,
               output=args.output, dataflow=args.dataflow, isCodesign=False, num_generation=10)
    elif (args.optimize == 'CO'):
        if args.hw_algo == "BO":
            bo_dse(sw_file=args.sw, hw_file=args.arch, cost_model=args.cost_model,
                   output=args.output, dataflow=args.dataflow, num_gen=10)
        else:
            hw_dse(sw_file=args.sw, hw_file=args.arch, cost_model=args.cost_model,
                   output=args.output, dataflow=args.dataflow, isCodesign=True, num_gen=10)
