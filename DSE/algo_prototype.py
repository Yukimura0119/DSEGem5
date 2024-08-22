from maestro_wrapper import MAESTROWrapper
from design_space import *
from abc import ABC, abstractclassmethod


class Algo(ABC):
    def __init__(self, design_space, cost_model):
        self.wrapper = MAESTROWrapper()
        self.design_space = design_space
        self.cost_model = cost_model

    def run(self, layer_id, m_type, tiling):
        self.wrapper.genMappingFile(layer_id, m_type, tiling)
        self.wrapper.run()

    def evaluate(self):
        self.wrapper.genMappingFile(1, "CONV")
        self.wrapper.run()
