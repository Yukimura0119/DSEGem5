from algo_prototype import Algo
from design_space import SWSpace
from parser.ONNX_parser import ONNXParser
import timeit
from ax.service.ax_client import AxClient, ObjectiveProperties
import numpy as np
import json

class BO(Algo):
    def __init__(self, hw_design_space={}, sw_design_space={}):
        super().__init__(sw_design_space=sw_design_space)
        self.layer_name = ""
        self.layer_type = ""
        self.ax_client = AxClient(verbose_logging=False)
        self.solution_set = []

    def _convertAX2MAESTRO(self, parameters):
        x = np.array([parameters.get(i) for i in sorted(parameters.keys())])
        return x

    def evaluate(self, parameters):
        parameters = self._convertAX2MAESTRO(parameters)
        self.wrapper.genMappingFile(self.layer_name, self.layer_type.upper(),
                                    parameters, sw_design_space.getLayerDim())
        self.wrapper.run()
        latency = self.wrapper.parseCSV()
        return {"Latency": (latency, 0.0)}

    def parameterSpace(self, design_point):
        parameters = []
        del design_point["input"][5]

        for idx, val in enumerate(design_point["input"]):
            para = {"name": f"x{idx}", "type": "choice", "values": val}
            parameters.append(para)
        return parameters

    def run(self, i):
        print(i, self.layer_name)
        self.layer_type, self.layer_name, design_point = sw_design_space.getDesignPoint()
        if self.layer_type != "Conv":
            sw_design_space.setNextLayer()
            return
        parameters = self.parameterSpace(design_point)
        self.ax_client.create_experiment(
            name="BO_in_MAESTRO",
            parameters=parameters,
            objectives={"Latency": ObjectiveProperties(minimize=True)},
            overwrite_existing_experiment=True
        )
        for i in range(10):
            parameters, trial_index = self.ax_client.get_next_trial()
            self.ax_client.complete_trial(
                trial_index=trial_index, raw_data=self.evaluate(parameters))
        best_parameters, values = self.ax_client.get_best_parameters()
        print(best_parameters)
        print(values)
        self.solution_set.append(
            {"solution": self._convertAX2MAESTRO(best_parameters), "latency": values[0]["Latency"]})
        sw_design_space.setNextLayer()


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


def calculate(solution_set):
    sol = 0
    for i in solution_set:
        sol += i["latency"]
    return sol


if __name__ == "__main__":
    result = {}
    t = {}
    sol = {}
    start = timeit.default_timer()
    sw = ONNXParser("../files/ONNX/resnet50.json")
    sw_design_space = SWSpace(sw.parse_design_space())
    x = BO(sw_design_space=sw_design_space)
    for i in range(len(sw_design_space.src_space)):
        x.run(i)
    end = timeit.default_timer()
    print("Time:", end - start)
    # with open(f"./BO_result/sol.json", "w") as fo:
    # json.dump(x.solution_set, fo, indent=4, cls=NpEncoder)
    sol = calculate(x.solution_set)
    print(sol)
