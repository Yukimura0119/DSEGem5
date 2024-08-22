from parser.HW_parser import HWParser
from parser.ONNX_parser import ONNXParser
from abc import ABC, abstractmethod
from kernel_function import *
import json
import numpy as np
import pandas as pd


class DesignSpace(ABC):
    def __init__(self, src_space):
        self.src_space = src_space
        self.design_space = []

    def dumpJson(self):
        print(json.dumps(self.src_space, indent=4))

    @abstractmethod
    def getDesignPoint(self):
        pass


class HWSpace(DesignSpace):
    def __init__(self, src_space):
        super().__init__(src_space)

    def getDesignPoint(self):
        return self.src_space


class SWSpace(DesignSpace):
    def __init__(self, src_space):
        super().__init__(src_space)
        self.layer = 0

    # Using DP to get the factor of value, _get_all_combinations(n, V) n : level of factor, V : value
    def _get_all_combinations(self, n, V):
        dp = [[[] for j in range(V+1)] for i in range(n+1)]

        for v in range(1, V+1):
            dp[1][v].append([v])

        for i in range(2, n+1):
            for v in range(1, V+1):
                for pv in range(1, v+1):
                    if v % pv == 0:
                        for prev in dp[i-1][v//pv]:
                            dp[i][v].append(prev + [pv])
        return dp[n][V], len(dp[n][V])

    def _kernel_matching(self, arr, layer_type, idx):
        valid = []
        mapping = {0: "N", 1: "C", 2: "H", 3: "W"}
        cstr = {}
        cstr[mapping[idx]] = kernel[layer_type][mapping[idx]]
        for i in arr:
            #if i[0] <= cstr[mapping[idx]]:
            valid.append(i[1])
        return valid

    def getLayerDim(self):
        dim = {"input" : []}
        op_type = ""
        for key, val in self.src_space[self.layer].items():
            if key == 'Type':
                op_type = val
            else:
                dim["input"] = val["input"][0]["type"]["shape"]
                if op_type == 'Conv':
                    dim["weight"] = val["input"][1]["type"]["shape"]
        # return self.src_space[self.layer]
        return dim

    def getLayerName(self):
        for key in self.src_space[self.layer]:
            if key != "Type":
                return key

    def getLayerType(self):
        for key, val in self.src_space[self.layer].items():
            if key == "Type":
                return val

    def setNextLayer(self):
        self.layer += 1
    # e.g. layer 1 conv, [1, 3, 224, 224], [64, 3, 7, 7]
    #                    input : [[1], [1,3], [32, 28, 16, 14, 8, 7, 4, 2, 1], [32, 28, 16, 14, 8, 7, 4, 2, 1]]
    #                    weight : [[32, 16, 8, 4, 2, 1], [3, 1], [7, 1], [7,1]]
    #   Result:
    #   ('Conv', 'resnetv17_conv0_fwd',
    #   {'input': [[1], [1, 3], [7, 8, 14, 16, 28, 32, 56, 112, 224], [7, 8, 14, 16, 28, 32, 56, 112, 224]],
    #    'kernel': [[64], [1, 3], [1, 7], [1, 7]]})

    def getDesignPoint(self):
        layer_type = ""
        layer_name = ""
        dim = {"input": []}
        for info in self.src_space[self.layer]:
            if info == "Type":
                layer_type = self.src_space[self.layer][info]
                if layer_type not in ["Conv", "BatchNormalization", "Relu", "GlobalAveragePool", "MaxPool"]:
                    return layer_type, "", None 
            else:
                layer_name = info
                for key, val in self.src_space[self.layer][info].items():
                    if key != "output":
                        pruned = []
                        for data in val:
                            if "bias" in data["name"]:
                                continue
                            dim_size = data["type"]["shape"]
                            for i, num in enumerate(dim_size):
                                factor, _ = self._get_all_combinations(2, num)
                                pruned = self._kernel_matching(
                                    factor, layer_type, i)
                                dim["input"].append(pruned)
        return layer_type, layer_name, dim

    # Need to be modified
    def spaceComplexity(self):
        layer = 0
        original_complex = 1
        factor = 0
        kernel_factor = 0
        for op in self.src_space:
            layer += 1
            op_data = []
            for info in op:
                if info != "Type":
                    op_data.extend(op[info]["input"])
                    if "kernel" in op[info].keys():
                        op_data.extend(op[info]["kernel"])
            factor_pro = 1
            original_pro = 1
            kernel_pro = 1
            for i in range(len(op_data)):
                factors, dimension_count = self._get_all_combinations(
                    2, op_data[i])
                exceed_count = 0
                mapping = {0: "N", 1: "C", 2: "H", 3: "W"}
                cstr = {}
                for j in range(4):
                    cstr[mapping[j]] = kernel[op["Type"]][mapping[j]]
                if len(op_data) == 4:  # only input
                    for j in factors:
                        if j[1] > cstr[mapping[i]]:
                            exceed_count += 1
                elif len(op_data) == 8:  # input and weight
                    for j in factors:
                        if j[1] > cstr[mapping[i % 4]]:
                            exceed_count += 1
                factor_pro *= dimension_count
                original_pro *= op_data[i]
                kernel_pro *= (dimension_count - exceed_count)
            factor += factor_pro
            original_complex += original_pro
            kernel_factor += kernel_pro
        print(layer)
        print("Without pruned : {}\nFactor : {}\nFactor+kernel : {}".format(
            original_complex, factor, kernel_factor))


if __name__ == "__main__":
    # x = HWParser("../files/HW_config/expe2.json")
    x = HWParser("./accelerator_1.json")
    hw_space = HWSpace(x.parse_design_space())
    hw_space.dumpJson()
    y = ONNXParser("../files/ONNX/resnet50.json")
    sw_space = SWSpace(y.parse_design_space())
    print(sw_space.getDesignPoint())
