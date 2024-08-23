import onnx
import json

def onnx2json(onnx_path: str, json_path: str):
    model = onnx.load(onnx_path)
    graph = model.graph

    nodes_list = []

    for node in graph.node:
        node_dict = {
            "name": node.name,
            "id": len(nodes_list),
            "op_type": node.op_type,
            "attribute": [],
            "childs": [],
            "input_tensor": [],
            "output_tensor": {},
            "parents": []
        }

        for inp in node.input:
            input_tensor = {
                "name": inp,
                "type": {
                    "elem_type": 1,
                    "shape": [] 
                }
            }
            node_dict["input_tensor"].append(input_tensor)

        if node.output:
            node_dict["output_tensor"] = {
                "name": node.output[0],
                "type": {
                    "elem_type": 1,
                    "shape": [] 
                }
            }

        for attr in node.attribute:
            attr_dict = {
                "name": attr.name,
                "type": attr.type,
            }
            if attr.type == onnx.AttributeProto.INTS:
                attr_dict["ints"] = list(attr.ints)
            elif attr.type == onnx.AttributeProto.INT:
                attr_dict["ints"] = [attr.i]
            elif attr.type == onnx.AttributeProto.FLOAT:
                attr_dict["ints"] = [attr.f]
            elif attr.type == onnx.AttributeProto.STRING:
                attr_dict["ints"] = [attr.s.decode('utf-8')]
            elif attr.type == onnx.AttributeProto.TENSOR:
                attr_dict["ints"] = [str(attr.t)]
            node_dict["attribute"].append(attr_dict)

        nodes_list.append(node_dict)

    # 將列表轉換為 JSON 並保存
    with open(json_path, 'w') as json_file:
        json.dump(nodes_list, json_file, indent=2)
    
    
def main(args):
    onnx2json(args.input_path, args.output_path)
    
    
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_path', type=str, help='input onnx file path')
    parser.add_argument('-o', '--output_path', type=str, help='output json file path')
    
    args = parser.parse_args()
    
    main(args)