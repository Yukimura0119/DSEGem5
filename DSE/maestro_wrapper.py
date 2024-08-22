import os
import pandas as pd
import numpy as np


class MAESTROWrapper:
    def __init__(self):
        self.directives = []
        self.mapping_file = "test"
        self.csv_line = 0

    def _dummy_gen_design_point(self, directives):
        return *directives,

    def _dummy_gen_dim(self, dimension, name):
        res = []
        for i in dimension["input"]:
            res.append(i)
        for i in range(len(dimension["weight"])):
            if i != 1:
                res.append(dimension["weight"][i])
        return res

    def genHWConfig(self, hw_design_point):
        # hw_design_poin = {"num_pes": 100, "l1_size_cstr": 50,
        # "l2_size_cstr": 1000, "noc_bw_cstr": 70, "offchip_bw_cstr": 40}
        with open("./DSE/maestro/data/hw/accelerator_1.m", "w") as fo:
            fo.write(f'num_pes: {hw_design_point[0]}\n')
            fo.write(f'l1_size_cstr: {hw_design_point[1]}\n')
            fo.write(f'l2_size_cstr: {hw_design_point[2]}\n')
            fo.write(f'noc_bw_cstr: {hw_design_point[2]}\n')
            fo.write(f'offchip_bw_cstr: {hw_design_point[4]}\n')

    def genMappingFile(self, layer_name, layer_type, pe, directives, dimension, dataflow="shi"):
        dim = self._dummy_gen_dim(dimension, layer_name)
        #dim = dimension
        with open("./DSE/{}.m".format(self.mapping_file), "w") as fo:
            if dataflow == "shi":
                fo.write("Network {} {{\n".format("SHI"))
                fo.write("Layer {} {{\n".format(layer_name))
                fo.write("Type: {}\n".format(layer_type))
                fo.write("Dimensions {{ N: {:.0f}, C: {:.0f}, X: {:.0f}, Y: {:.0f}, K: {:.0f}, R: {:.0f}, S: {:.0f} }}\n".format(*dim))
                fo.write("Dataflow {\n")

                # Write dataflow
                n, c, x, y, k, r, s = self._dummy_gen_design_point(directives)
                fo.write("TemporalMap({} ,{}:) K;\n".format(k, k))
                fo.write("SpatialMap({}, 1) Y;\n".format(y, y))
                fo.write("TemporalMap({}, 1) X;\n".format(x,x))
                fo.write("TemporalMap(1, 1) C;\n")
                fo.write("TemporalMap({}, {}) R;\n".format(dim[-1], dim[-1]))
                fo.write("TemporalMap({}, {}) S;\n".format(dim[-1], dim[-1]))
                fo.write("Cluster({}, P);\n".format(pe))
                fo.write("SpatialMap({}, 1) X;\n".format(x))

                fo.write("}\n")
                fo.write("}\n")
                fo.write("}")
            elif dataflow == "nvdla":
                fo.write("Network {} {{\n".format("NVDLA"))
                fo.write("Layer {} {{\n".format(layer_name))
                fo.write("Type: {}\n".format(layer_type))
                fo.write("Dimensions {{ N: {:.0f}, C: {:.0f}, X: {:.0f}, Y: {:.0f}, K: {:.0f}, R: {:.0f}, S: {:.0f} }}\n".format(*dim))
                fo.write("Dataflow {\n")

                # Write dataflow
                n, c, x, y, k, r, s = self._dummy_gen_design_point(directives)
                fo.write("SpatialMap({} ,{}) K;\n".format(k, k))
                fo.write("TemporalMap({}, {}) C;\n".format(c, c))
                fo.write("TemporalMap({} ,{}) R;\n".format(dim[-1], dim[-1]))
                fo.write("TemporalMap({}, {}) S;\n".format(dim[-1], dim[-1]))
                fo.write("TemporalMap({}, {}) Y;\n".format(y, y))
                fo.write("TemporalMap({}, {}) X;\n".format(x, x))
                fo.write("Cluster({}, P);\n".format(pe))
                fo.write("SpatialMap({}, {}) C;\n".format(c, c))

                fo.write("}\n")
                fo.write("}\n")
                fo.write("}")

    def run(self):
        param_list = [
            "--print_res=false",
            "--print_res_csv_file=true",
            "--print_log_file=false",
            "--Mapping_file=./DSE/{}.m".format(self.mapping_file),
            "--HW_file=./DSE/maestro/data/hw/accelerator_1.m",
            "--msg_print_lv=0",
        ]
        # print("./DSE/maestro/maestro {} {} {} {} {}".format(*param_list))
        exit_code = os.system("./DSE/maestro/maestro {} {} {} {} {} >/dev/null".format(*param_list))

        if exit_code != 0:
            print("Maestro error")

    def parseCSV(self):
        if "{}.csv".format(self.mapping_file) in os.listdir():
            df = pd.read_csv("{}.csv".format(self.mapping_file))
            layer_name = df[" Layer Number"]
            runtime = np.array(df[" Runtime (Cycles)"])[-1]
            power = np.array(df[" Power"])[-1]
            if len(df) == self.csv_line:
                print("Invalid runtime error")
                return 0, 0
            if len(df) > 100:
                self.csv_line = 0
                self.deleteCSV()
            self.csv_line += 1
            return runtime, power
        else:
            print("CSV File not found")

    def deleteCSV(self):
        os.system("rm {}.csv".format(self.mapping_file))
