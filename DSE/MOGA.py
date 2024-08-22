from algo_prototype import Algo
from GA import SW_GA, HW_GA, NpEncoder
from parser.ONNX_parser import ONNXParser
from parser.HW_parser import HWParser
from design_space import SWSpace, HWSpace
from downstream_API import TrafficGeneratorAPI, Gem5SimulatorAPI, GetReportAPI
from deap import base
from deap import creator
from deap import tools
from abc import abstractmethod
import json
import numpy as np
import random
import os
import timeit
import matplotlib.pyplot as plt


def co_sw_dse(sw_file, hw_file, cost_model, dataflow, pe=4, local_mem=32):
    if hw_file != "":
        hw = HWParser(hw_file, cost_model)
        pe, local_mem = hw.getPE()
    pe = pe
    local_mem = local_mem
    for gen in [1]:
        start = timeit.default_timer()
        sw = ONNXParser(sw_file)
        sw_design_space = SWSpace(sw.parse_design_space())
        x = SW_MOGA(sw_design_space, cost_model, sw_file,
                    dataflow, pe, local_mem)
        num_generations = gen
        sol_per_pop = 1
        i = 0
        latency = 0
        energy = 0
        mapping = []
        while i < len(sw_design_space.src_space):
            sw_design_space.setNextLayer()
            flag = x.setup()
            if flag == False:
                i += 1
                continue
            final_population = x.run(i, num_generations=num_generations,sol_per_pop=sol_per_pop)
            pareto_fronts = tools.sortNondominated(
                final_population, len(final_population))

            layer_pareto_fronts = []
            output_json = []
            for j, front in enumerate(pareto_fronts, 1):
                for individual in front:
                    layer_pareto_fronts.append(
                        list(individual.fitness.values))
                    output_json.append(
                        {"Mapping": individual, "Latency": individual.fitness.values[0], "Energy": individual.fitness.values[1]})
            with open(f"lipper_expe/expe1/SW_Co-design_{i}", "w") as fo:
                json.dump(output_json, fo, indent=4)
            # Choose the first of pareto set
            for j in range(1):
                if output_json[j]["Latency"] >= 1e18:
                    latency += 1e18
                else:
                    latency += output_json[j]["Latency"]
                if output_json[j]["Energy"] >= 1e18:
                    energy += 1e18
                else:
                    energy += output_json[j]["Energy"]
                mapping.append(output_json[j]["Mapping"])
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
    return latency, energy, mapping


class HW_MOGA(HW_GA):
    def __init__(self, hw_design_space, cost_model, arch_type, dataflow, isCodesign, sw_file):
        super().__init__(hw_design_space, cost_model, arch_type)
        self.toolbox = base.Toolbox()
        self.isCodesign = isCodesign
        self.dataflow = dataflow
        self.sw_file = sw_file
        self.best_mapping = {
            "Mapping": None, "Latency": 9223372036854775807, "Energy": 9223372036854775807}

    def fitness(self, individual):
        penalty = 9223372036854775807
        if self.cost_model == "maestro":
            pass
        elif self.cost_model == "gem5":
            decoded_design_point = self.decode(individual)
            with open("files/DSE_HW/DSE_hw.json", "w") as fo:
                json.dump(decoded_design_point, fo, indent=4, cls=NpEncoder)
            total_latency = 0
            total_energy = 0
            if self.isCodesign:
                latency, energy, mapping = co_sw_dse(self.sw_file,
                                                     "files/DSE_HW/DSE_hw.json", self.cost_model, self.dataflow)
                self.best_mapping["Latency"] = latency
                self.best_mapping["Mapping"] = mapping
                self.best_mapping["Energy"] = energy
            else:
                for file in os.listdir("files/DSE/fixed_sw"):
                    with open(f"files/DSE/fixed_sw/{file}", "r") as fo:
                        tmp = json.load(fo)
                        tmp["HardwareInfo"]["PE_Num"] = self.pe_num
                        tmp["HardwareInfo"]["LocalMem"] = self.local_mem
                    with open(f"files/DSE/fixed_sw/{file}", "w") as fo:
                        json.dump(tmp, fo, indent=4, cls=NpEncoder)
                tg_ret_code, error_msg = TrafficGeneratorAPI(
                    f"files/DSE/fixed_sw/{file}")
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
            total_energy += energy
        return int(total_latency), int(total_energy)

    def init_individual(self, icls, encoded_space):
        return icls(random.choice(subarray) for subarray in encoded_space)

    def custom_mutate(self, individual, indpb):
        for i in range(len(individual)):
            if random.random() < indpb:
                individual[i] = random.choice(self.gene_space[i])
        return individual,

    def plotPareto(self, pareto_set, i):

        x_values = [np.log10(
            solution[0]) for solution in pareto_set if solution[0] < 1e16 and solution[1] < 1e16]
        y_values = [np.log10(
            solution[1]) for solution in pareto_set if solution[0] < 1e16 and solution[1] < 1e16]

        plt.scatter(x_values, y_values)

        plt.xlabel('Latency')
        plt.ylabel('Energy')

        plt.savefig(f'./lipper_expe/expe1/png/pareto_front_{i}.png')

    def setup(self):
        creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0))
        creator.create("Individual", list, fitness=creator.FitnessMulti)
        if self.cost_model == "gem5":
            self.gene_space = self.encode(self.design_space.getDesignPoint())

        self.toolbox.register("individual", self.init_individual,
                              creator.Individual, self.gene_space)
        self.toolbox.register("population", tools.initRepeat,
                              list, self.toolbox.individual)

        self.toolbox.register("evaluate", self.fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self.custom_mutate,
                              indpb=0.2)
        self.toolbox.register("select", tools.selNSGA2)

    def run(self, i, num_generations, num_parents_mating, sol_per_pop):
        pop = self.toolbox.population(n=sol_per_pop)
        CXPB, MUTPB, NGEN = 0.3, 0.1, num_generations
        fitnesses = list(map(self.toolbox.evaluate, pop))
        for g in range(NGEN):
            print(
                f"===========================HW MOGA generation {g} =========================")
            offspring = self.toolbox.select(pop, len(pop))
            offspring = list(map(self.toolbox.clone, offspring))
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            pop[:] = offspring
        return pop


class SW_MOGA(SW_GA):
    def __init__(self, sw_design_space, cost_model, filename, dataflow, pe, local_mem):
        super().__init__(sw_design_space, cost_model, filename, dataflow, pe, local_mem)
        self.toolbox = base.Toolbox()

    def fitness(self, individual):
        penalty = 9223372036854775807
        if self.cost_model == "maestro":
            self.wrapper.genMappingFile(self.layer_name, self.layer_type.upper(), self.pe,
                                        individual, self.design_space.getLayerDim(), self.dataflow)
            self.wrapper.run()
            latency, energy = self.wrapper.parseCSV()
            if latency == 0:
                latency = penalty
                energy = penalty
            return latency, energy

        elif self.cost_model == "gem5":
            split_tile = self.genSplit(individual)
            if not self.trafficGeneratorCstr(split_tile):
                return penalty, penalty
            output_file_name = self.exportSWDesignPoint(split_tile)
            # call traffic generator
            tg_ret_code, error_msg = TrafficGeneratorAPI(output_file_name)
            if tg_ret_code:
                print(error_msg)
                return penalty, penalty
            # call gem5 simulator
            g5_ret_code, error_msg = Gem5SimulatorAPI()
            if g5_ret_code:
                print(error_msg)
                return penalty, penalty
            # call get report
            latency, energy, error_msg = GetReportAPI()
            if latency == 1:
                print(error_msg)
                return penalty, penalty
            print("Latency:", latency)
            print("Energy:", energy)
            return int(latency), int(energy)

    def init_individual(self, icls, encoded_space):
        return icls(random.choice(subarray) for subarray in encoded_space)

    def custom_mutate(self, individual, indpb):
        for i in range(len(individual)):
            if random.random() < indpb:
                individual[i] = random.choice(self.gene_space[i])
        return individual,

    def plotPareto(self, pareto_set, i):

        x_values = [np.log10(
            solution[0]) for solution in pareto_set if solution[0] < 1e16 and solution[1] < 1e16]
        y_values = [np.log10(
            solution[1]) for solution in pareto_set if solution[0] < 1e16 and solution[1] < 1e16]

        plt.scatter(x_values, y_values)

        plt.xlabel('Latency')
        plt.ylabel('Energy')
        plt.title('Pareto Front')

        plt.savefig(f'./lipper_expe/expe1/png/pareto_front_{i}.png')

    def setup(self):
        creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0))
        creator.create("Individual", list, fitness=creator.FitnessMulti)
        self.layer_type, self.layer_name, design_point = self.design_space.getDesignPoint()
        if self.cost_model == "maestro":
            if self.layer_type != "Conv":
                self.design_space.setNextLayer()
                return False

        if self.layer_type not in ["Conv", "BatchNormalization", "Relu", "GlobalAveragePool", "MaxPool"]:
            self.design_space.setNextLayer()
            return False

        self.gene_space = self.encode(design_point)
        self.toolbox.register("individual", self.init_individual,
                              creator.Individual, self.gene_space)
        self.toolbox.register("population", tools.initRepeat,
                              list, self.toolbox.individual)

        self.toolbox.register("evaluate", self.fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self.custom_mutate,
                              indpb=0.2)
        self.toolbox.register("select", tools.selNSGA2)
        return True

    def run(self, i, num_generations, sol_per_pop):
        print(self.layer_name)
        pop = self.toolbox.population(n=sol_per_pop)
        CXPB, MUTPB, NGEN = 0.5, 0.2, num_generations
        fitnesses = list(map(self.toolbox.evaluate, pop))
        for g in range(NGEN):
            print(
                f"============================SW MOGA generation {g} ==========================")
            offspring = self.toolbox.select(pop, len(pop))
            offspring = list(map(self.toolbox.clone, offspring))
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            pop[:] = offspring
        return pop
