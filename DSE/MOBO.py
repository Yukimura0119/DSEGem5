from algo_prototype import Algo
from MOGA import co_sw_dse
import timeit
from ax.service.ax_client import AxClient
from ax.utils.notebook.plotting import render, init_notebook_plotting
from ax.service.utils.instantiation import ObjectiveProperties
import torch
from ax.plot.pareto_utils import compute_posterior_pareto_frontier
from ax.plot.pareto_frontier import plot_pareto_frontier

import numpy as np
import json
import re
import matplotlib.pyplot as plt


class MOBO(Algo):
    def __init__(self, hw_design_space, cost_model, arch_type, dataflow, sw_file):
        super().__init__(hw_design_space, cost_model)
        self.ax_client = AxClient(verbose_logging=False)
        self.arch_type = arch_type
        self.dataflow = dataflow
        self.sw_file = sw_file

    def evaluate(self, parameters):
        print("HW Para:", parameters)
        parameters['tile.pePerTile'] = 4
        issuffix = re.search(r"\D", parameters['tile.l1Size'])
        latency, energy, mapping = co_sw_dse(sw_file=self.sw_file, hw_file="", cost_model=self.cost_model, dataflow=self.dataflow,
                                             pe=parameters['tile.pePerTile'], local_mem=int(parameters['tile.l1Size'][:issuffix.start()]))

        return {"Latency": latency, "Energy": energy}

    def parameterSpace(self, design_point):
        para = []
        for out_key in design_point:
            for key, val in design_point[out_key].items():
                if isinstance(val, dict):
                    tmp = {"name": out_key + "." + key}
                    tmp["type"] = "range"
                    tmp["bounds"] = [int(val["low"]), int(val["high"])]
                    tmp["value_type"] = "int"
                elif isinstance(val, list):
                    tmp = {"name": out_key + "." + key}
                    tmp["type"] = "choice"
                    tmp["values"] = val
                    tmp["value_type"] = "str"
                else:
                    continue
                para.append(tmp)
        return para

    def run(self):
        design_point = self.design_space.getDesignPoint()
        parameters = self.parameterSpace(design_point)
        self.ax_client.create_experiment(
            name="HW_DSE",
            parameters=parameters,
            objectives={
                "Latency": ObjectiveProperties(minimize=True),
                "Energy": ObjectiveProperties(minimize=True)
            },
            overwrite_existing_experiment=True,
        )

        for i in range(10):
            parameters, trial_index = self.ax_client.get_next_trial()
            self.ax_client.complete_trial(
                trial_index=trial_index, raw_data=self.evaluate(parameters))
        result = self.ax_client.get_pareto_optimal_parameters()
        for key, val in result.items():
            print(key, val)
        data = self.ax_client.experiment.fetch_data()
        # objectives = self.ax_client.experiment.optimization_config.objective.objectives
        objectives = self.ax_client.experiment.optimization_config.objective.objectives
        frontier = compute_posterior_pareto_frontier(
            experiment=self.ax_client.experiment,
            data=self.ax_client.experiment.fetch_data(),
            primary_objective=objectives[1].metric,
            secondary_objective=objectives[0].metric,
            absolute_metrics=["Latency", "Energy"],
            num_points=20,
        )
        render(plot_pareto_frontier(frontier, CI_level=0.90), "test.png")


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)
