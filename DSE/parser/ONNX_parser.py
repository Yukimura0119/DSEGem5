import json


class ONNXParser(object):
    def __init__(self, filename):
        with open(filename, "r") as f:
            self.onnx = json.load(f)
        self.model = []
        self.filename = filename

    def parse_design_space(self):
        for op in self.onnx:
            op_info = {}
            op_info["Type"] = op["op_type"]
            op_info[op["name"]] = {}
            op_info[op["name"]]["input"] = op["input_tensor"]
            op_info[op["name"]]["output"] = op["output_tensor"]
            self.model.append(op_info)
        return self.model

    def exportSWDesignPoint(self, split_tile, layer_id):
        # This function should include
        #   1. SW design point
        #   2. The format of Traffic generator supported
        model_name = self.filename.split("/")[-1].split(".")[0]
        result = {"Layout": "NCHW", "Name": model_name, "Model": [],
                  "Mapping": "", "Split": {}, "HardwareInfo": {"PE_Num": 0, "LocalMem": 0}}
        result["Model"].append(self.onnx[layer_id])
        result["Split"] = split_tile
        # TODO mapping strategy, HardwareInfo
        print(json.dumps(result, indent=4))

    def exportHWDesignPoint(self):
        # Same as exportSWDesignPoint
        pass


if __name__ == "__main__":
    x = ONNXParser("../../files/ONNX/resnet50.json")

    design_space = x.parse_design_space()
    with open('./tmp_files/resnet50_parsed.json', 'w') as f:
        json.dump(design_space, f, indent=4)
