from algo_prototype import Algo
from parser.ONNX_parser import ONNXParser
from parser.HW_parser import HWParser
from design_space import SWSpace, HWSpace
from downstream_API import TrafficGeneratorAPI, Gem5SimulatorAPI, GetReportAPI
from abc import abstractmethod
import pygad
import timeit
import json
import copy
import numpy as np
import os
import re

class GA(Algo):
    def __init__(self, design_space, cost_model):
        super().__init__(design_space, cost_model)
        # self.design_space = design_space

    @abstractmethod
    def fitness(self):
        pass

    @abstractmethod
    def encode(self):
        pass


class HW_GA(GA):
    def __init__(self, hw_design_space, cost_model, arch_type):
        super().__init__(hw_design_space, cost_model)
        self.sw_dse = None
        self.arch_type = arch_type
        self.solution_set = []
        self.best_sw_solution_set = None

    def calculateSWSol(self, solution_set):
        latency = 0
        for i in solution_set:
            latency += i['latency']
        return latency


    def fitness(self, ga, solution, idx):
        penalty = 9223372036854775807
        if self.cost_model == "maestro":
            self.wrapper.genHWConfig(solution)
            self.best_sw_solution_set = self.sw_dse()
            fitness_val = self.calculateSWSol(self.best_sw_solution_set)
            print(fitness_val)
            return -fitness_val
        elif self.cost_model == "gem5":
            decoded_design_point = self.decode(solution)
            with open("files/DSE_HW/DSE_hw.json", "w") as fo:
                json.dump(decoded_design_point, fo, indent=4,cls=NpEncoder)
            total_latency = 0
            for file in os.listdir("files/DSE/fixed_sw"):
                with open(f"files/DSE/fixed_sw/{file}", "r") as fo:
                    tmp = json.load(fo)
                    tmp["HardwareInfo"]["PE_Num"] = self.pe_num
                    tmp["HardwareInfo"]["LocalMem"] = self.local_mem
                with open(f"files/DSE/fixed_sw/{file}", "w") as fo:
                    json.dump(tmp, fo, indent=4, cls=NpEncoder)
                tg_ret_code, error_msg = TrafficGeneratorAPI(f"files/DSE/fixed_sw/{file}")
                if tg_ret_code:
                    print(error_msg)
                    return penalty
                # call gem5 simulator
                g5_ret_code, error_msg = Gem5SimulatorAPI()
                if g5_ret_code:
                    print(error_msg)
                    return penalty
                # call get report
                latency, energy, error_msg = GetReportAPI()
                if latency == 1:
                    print(error_msg)
                    return penalty
                print("Latency:", latency)
                print("Energy:", energy)
                total_latency += latency
                break
            return int(total_latency)
   

    def encode(self, design_point):
        encoded_design_point = []
        for out_key in design_point:
            for key, val in design_point[out_key].items():
                tmp = []
                if isinstance(val, dict):
                    low = int(val['low'])
                    high = int(val['high'])
                    step = int(val['step'])
                    for i in range(low, high+1, step):
                        tmp.append(i)
                elif isinstance(val, list):
                    tmp = [i for i in range(len(val))]
                if len(tmp) != 0:
                    encoded_design_point.append(tmp)

        return encoded_design_point

    def decode(self, solution):
        decoded_design_point = copy.deepcopy(self.design_space.src_space)
        if self.arch_type == "vanilla":
            ddr_type = self.design_space.src_space["memory"]["dramInterface"]
            l1_size = self.design_space.src_space["tile"]["l1Size"]
            decoded_design_point["system"]["clockRate"] = str(solution[0]) + decoded_design_point["system"]["clockRate"]["suffix"]
            decoded_design_point["system"]["numTiles"] = 1
            decoded_design_point["memory"]["dramInterface"] = ddr_type[solution[1]]
            # decoded_design_point["memory"]["size"] = str(solution[2]) + decoded_design_point["memory"]["size"]["suffix"]
            decoded_design_point["memory"]["size"] = "4GiB"
            decoded_design_point["noc"]["width"] = solution[3]
            # decoded_design_point["tile"]["pePerTile"] = solution[4]
            decoded_design_point["tile"]["pePerTile"] = 16
            decoded_design_point["tile"]["l1Size"] = l1_size[solution[5]]
            self.local_mem = int(re.search('(\d+)', l1_size[solution[5]]).group(1))
            # self.pe_num = solution[4]
            self.pe_num = 16
        return decoded_design_point

    def run(self, num_generations, num_parents_mating, sol_per_pop):
        if self.cost_model == "gem5":
            gene_space = self.encode(self.design_space.getDesignPoint())
        elif self.cost_model == "maestro":
            pass
        # self.sw_dse = sw_dse
        self.ga_instance = pygad.GA(num_generations=num_generations,
                                    num_parents_mating=num_parents_mating,
                                    sol_per_pop=sol_per_pop,
                                    num_genes=len(gene_space),
                                    fitness_func=self.fitness,
                                    gene_type=int,
                                    mutation_num_genes=1,
                                    gene_space=gene_space,
                                    parent_selection_type="sss",
                                    crossover_type="single_point",
                                    mutation_type="random"
                                    )
        self.ga_instance.run()
        solution, solution_fitness, solution_idx = self.ga_instance.best_solution(
            self.ga_instance.last_generation_fitness)
        print("HW_Parameters of the best solution : {solution}".format(
            solution=solution))
        print("HW_Fitness value of the best solution = {solution_fitness}".format(
            solution_fitness=solution_fitness))
        print("HW_Index of the best solution : {solution_idx}".format(
            solution_idx=solution_idx))
        self.solution_set.append(
            {"solution": solution, "latency": -solution_fitness, "sw_solution_set": self.best_sw_solution_set})

    def genDesignPoint(self):
        pass


class SW_GA(GA):
    def __init__(self, sw_design_space, cost_model, filename, dataflow, pe, local_mem):
        super().__init__(sw_design_space, cost_model)
        self.layer_name = ""
        self.layer_type = ""
        self.pe = pe
        self.local_mem = local_mem
        self.last_fitness = 0
        self.solution_set = []
        self.dataflow = dataflow
        self.model_name = filename.split("/")[-1].split(".")[0]
        with open(filename, "r") as f:
            self.onnx = json.load(f)

    def genSplit(self, solution):
        split_tile = {"input_tile": []}
        dim = self.design_space.getLayerDim()
        # split_tile["input_tile"] = [
        #     int(i/j) for i, j in zip(dim["input"], solution[:4])]
        split_tile["input_tile"] = solution[:4]
        if self.layer_type == "Conv":
            weight_sol = [solution[4], solution[1], solution[5], solution[6]]
            split_tile["weight_tile"] = weight_sol
            # split_tile["weight_tile"] = [
            #     int(i/j) for i, j in zip(dim["weight"], weight_sol)]
        return split_tile

    def exportSWDesignPoint(self, split_tile):
        if self.cost_model == "gem5":
            result = {"Layout": "NCHW", "Name": self.model_name, "Model": [],
                      "Mapping": "", "Split": {}, "HardwareInfo": {"PE_Num": 0, "LocalMem": 0}}
            fuse_num = self.onnx[self.design_space.layer]["fuse"]
            for i in range(fuse_num):
                result["Model"].append(self.onnx[self.design_space.layer+i])
            if fuse_num == 0:
                result["Model"].append(self.onnx[self.design_space.layer])
            result["Split"] = split_tile

            # TODO Mapping, HardwareInfo
            result["HardwareInfo"]["PE_Num"] = self.pe 
            result["HardwareInfo"]["LocalMem"] = self.local_mem
            if self.dataflow == "nvdla":
                result["Mapping"] = "weight"
            elif self.dataflow == "shi":
                result["Mapping"] = "output"
            else:
                result["Mapping"] = "weight"
            ###
            dse_json_file_name = f"files/DSE/DSE_{self.model_name}_{self.design_space.layer}.json"
            with open(dse_json_file_name, "w") as fo:
                json.dump(result, fo, indent=4, cls=NpEncoder)
            return dse_json_file_name

    def trafficGeneratorCstr(self, split_tile):
        x = [split_tile["input_tile"]]
        if self.layer_type == 'Conv':
            x.append(split_tile["weight_tile"])
        # print(np.sum([np.prod(i) for i in x])*4/1024 / 256)
        if np.prod([np.prod(i) for i in x]) < 100000:
            return True
        return False

    def fitness(self, ga, solution, idx):
        penalty = 9223372036854775807
        
        if self.cost_model == "maestro":
            self.wrapper.genMappingFile(self.layer_name, self.layer_type.upper(), self.pe,
                                        solution, self.design_space.getLayerDim(), self.dataflow)
            self.wrapper.run()
            latency, energy = self.wrapper.parseCSV()
            if latency == 0:
                latency = penalty
                energy = penalty
            return latency

        elif self.cost_model == "gem5":
            split_tile = self.genSplit(solution)
            if not self.trafficGeneratorCstr(split_tile):
                return penalty
        
            output_file_name = self.exportSWDesignPoint(
                split_tile)
            # call traffic generator

            tg_ret_code, error_msg = TrafficGeneratorAPI(output_file_name)
            if tg_ret_code:
                print(error_msg)
                return penalty
            # call gem5 simulator
            g5_ret_code, error_msg = Gem5SimulatorAPI()
            if g5_ret_code:
                print(error_msg)
                exit(0)
                return penalty
            # call get report
            latency, energy, error_msg = GetReportAPI()
            if latency == 1:
                print(error_msg)
                return penalty
            print("Latency:", latency)
            return int(latency)

    def encode(self, design_point):
        encoded_design_point = []
        if self.layer_type == "Conv":
            encoded_design_point.extend(design_point["input"][:5])
            encoded_design_point.extend(design_point["input"][6:])
            if self.dataflow == "nvdla":
                for i in range(len(encoded_design_point)):
                    if i != 1 and i != 4:
                        encoded_design_point[i] = [1]

            elif self.dataflow =="shi":
                for i in range(len(encoded_design_point)):
                    if i != 2 and i != 3:
                        encoded_design_point[i] = [1]
        else:
            encoded_design_point.extend(design_point["input"][:5])
            if self.dataflow == "nvdla":
                for i in range(len(encoded_design_point)):
                    if i != 1:
                        encoded_design_point[i] = [1]

            elif self.dataflow =="shi":
                for i in range(len(encoded_design_point)):
                    if i != 2 and i != 3:
                        encoded_design_point[i] = [1]
        return encoded_design_point

    def gen_kcp(self, solution):
        solution["input_tile"][0] = 1
        solution["input_tile"][1] = solution["input_tile"][1]
        solution["input_tile"][2] = 1
        solution["input_tile"][3] = 1
        if len(solution) != 1:
            solution["weight_tile"][0] = solution["weight_tile"][0]
            solution["weight_tile"][1] = 1
            solution["weight_tile"][2] = 1
            solution["weight_tile"][3] = 1

        return solution

    def gen_xyp(self, solution):
        solution["input_tile"][0] = 1
        solution["input_tile"][1] = 1
        solution["input_tile"][2] = solution["input_tile"][2]
        solution["input_tile"][3] = solution["input_tile"][3]
        if len(solution) != 1:
            solution["weight_tile"][0] = 1
            solution["weight_tile"][1] = 1
            solution["weight_tile"][2] = 1
            solution["weight_tile"][3] = 1

        return solution

    def run(self, i, num_generations, num_parents_mating, sol_per_pop):
        self.layer_type, self.layer_name, design_point = self.design_space.getDesignPoint()
        print(i, self.layer_name)
        if self.cost_model == "maestro":
            if self.layer_type != "Conv":
                self.design_space.setNextLayer()
                return False
        # Currently, only support the following operator
        if self.layer_type not in ["Conv", "BatchNormalization", "Relu", "GlobalAveragePool", "MaxPool"]:
            self.design_space.setNextLayer()
            return False
        gene_space = self.encode(design_point)
        self.ga_instance = pygad.GA(num_generations=num_generations,
                                    num_parents_mating=num_parents_mating,
                                    sol_per_pop=sol_per_pop,
                                    num_genes=len(gene_space),
                                    fitness_func=self.fitness,
                                    gene_type=int,
                                    mutation_num_genes=1,
                                    gene_space=gene_space,
                                    parent_selection_type="sss",
                                    crossover_type="single_point",
                                    mutation_type=None
                                    )

        self.ga_instance.run()
        solution, solution_fitness, solution_idx = self.ga_instance.best_solution(
            self.ga_instance.last_generation_fitness)
        self.solution_set.append(
            {"solution": solution, "latency": -solution_fitness})
        return True
        # self.ga_instance.plot_fitness()

        # Saving the GA instance.
        # The filename to which the instance is saved. The name is without extension.
        # filename = f'GA_result/{num_generations}_{i}'
        # self.ga_instance.save(filename=filename)

        # Print Log
        # print("SW_Parameters of the best solution : {solution}".format(
        # solution=solution))
        # print("SW_Fitness value of the best solution = {solution_fitness}".format(
        # solution_fitness=solution_fitness))
        # print("SW_Index of the best solution : {solution_idx}".format(
        # solution_idx=solution_idx))



class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)
