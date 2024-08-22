import json
import re


class HWParser(object):
    def __init__(self, filename, cost_model):
        self.design_space = {}
        self.cost_model = cost_model
        with open(filename, "r") as f:
            self.hw_config = json.load(f)

    # First version. For the whole system overview
    # Parse for the workload analysis
    # def parse_workload_info(self):
        # self.hw_para = {"PE_Num": 0, "LocalMem": 0}
        # for subSystem in self.hw_config["subSystem"]:
            # self.hw_para["PE_Num"] = len(subSystem["components"][0]["info"])
            # self.hw_para["LocalMem"] = 128
        # return self.hw_para

    # First version. For the whole system overview
    # Using $ as the notation for the parser, it will be re-filled into json after the DSE is done
    # We also need to keep track of the path of the json
    # def json_filter(self, obj, design_space, prefix):
        # if isinstance(obj, dict):
        # for key in obj.keys():
        # obj[key] = self.json_filter(obj[key], design_space, prefix + "." + key)
        # elif isinstance(obj, list):
        # for i in range(len(obj)):
        # obj[i] = self.json_filter(obj[i], design_space, prefix + "." + str(i))
        # elif isinstance(obj, str) and obj.startswith('$'):
        # limit = {"low": "", "high": "", "suffix": ""}
        # para_range = obj[1:].split(",")
        # suffix = re.search(r"\D", para_range[2])
        # if suffix:
        # limit["low"] = para_range[0]
        # limit["high"] = para_range[1]
        # limit["step"] = para_range[2][:suffix.start()]
        # limit["suffix"] = para_range[2][suffix.start():]
        # else:
        # limit["low"] = para_range[0]
        # limit["high"] = para_range[1]
        # design_space[prefix] = limit
        # prefix = ""
        # return obj

    # Second version
    def json_filter(self):
        design_space = {}
        for key, val in self.hw_config.items():
            design_space[key] = {}
            for inner_key, inner_val in val.items():
                # Numerical
                if inner_val != None and inner_val[0] == "$":
                    para = inner_val[1:].split(", ")
                    issuffix = re.search(r"\D", para[2])
                    suffix = ""
                    step = 0
                    if issuffix:
                        step = para[2][:issuffix.start()]
                        suffix = para[2][issuffix.start():]
                    else:
                        step = para[2]

                    design_space[key][inner_key] = {
                        "low": para[0], "high": para[1], "step": step, "suffix": suffix}
                # Categorical
                elif inner_val != None and inner_val[0] == "*":
                    design_space[key][inner_key] = inner_val[1:].split(", ")
                else:
                    design_space[key][inner_key] = inner_val
        return design_space

    def parse_design_space(self):
        self.design_space = self.json_filter()
        return self.design_space

    def getPE(self):
        if self.cost_model == "gem5":
            local_mem = self.hw_config["tile"]["l1Size"]
            issuffix = re.search(r"\D", local_mem)
            local_mem = local_mem[:issuffix.start()]
            return self.hw_config["system"]["numTiles"]*self.hw_config["tile"]["pePerTile"], int(local_mem)
        elif self.cost_model == "maestro":
            return self.hw_config["system"]["num_pes"], self.hw_config["system"]["l1_size_cstr"]

if __name__ == "__main__":
    # print(HWParser("expe1.json").parse())
    x = HWParser(
        "files/HW_config/gem5_search_vanilla.json", "gem5")
    design_space = x.parse_design_space()
    print(json.dumps(design_space, indent=4))
