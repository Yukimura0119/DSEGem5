import onnx
import json
from onnx import shape_inference
# model = onnx.load('./models/resnet50-v1-7.onnx')

# def modify_input():
#     model = onnx.load("../models/resnet50-v1-7.onnx")
#     input = model.graph.input
#     input[0].type.tensor_type.shape.dim[0].dim_value = 1
#     return model

def inference(path):
    # path = "../models/resnet50-v1-7.onnx"
    # new_path = "../models/resnet50-v1-7.onnx"
    model = onnx.load(path)
    input = model.graph.input
    input[0].type.tensor_type.shape.dim[0].dim_value = 1
    model = onnx.shape_inference.infer_shapes(model)
    onnx.save(onnx.shape_inference.infer_shapes(model), path)
    return model

def modify_input(input):
    input[0].type.tensor_type.shape.dim[0].dim_value = 1

def build_list_nodes(nodes):
    # list of dictionary
    all_nodes = []
    
    # id table
    id_table = {}
    id_table2 = {}
    node_cnt = 0

    # parse each op
    for op in nodes:
        node = {}
        node['name'] = op.name
        node['id'] = node_cnt
        id_table[op.name] = node_cnt
        id_table2[node_cnt] = op.name
        node_cnt = node_cnt + 1
        node['op_type'] = op.op_type
        node['attribute'] = []
        node['childs'] = []
        node['input_tensor'] = []
        node['output_tensor'] = []

        all_nodes.append(node)

    # deal with consumer
    for i, op in enumerate(nodes):
        parent = []
        for prod in op.input:
            # exclude input and weight of first layer
            if(id_table.get(prod) != None):
                parent.append(id_table[prod])
        all_nodes[i]['parents'] = parent

        child = []
        if parent:
            for par in parent:
                all_nodes[par]['childs'].append(i)
        
    return all_nodes


# parse a tensor to dictionary tensor
def parse_tensor(tensor):
    tensor_dict = dict()
    tensor_type = {}

    tensor_dict['name'] = tensor.name
    tensor_type['elem_type'] = tensor.type.tensor_type.elem_type

    dim = []
    len_dim = len(tensor.type.tensor_type.shape.dim)
    for j in range(len_dim):
        dim.append(tensor.type.tensor_type.shape.dim[j].dim_value)
    
    tensor_type['shape'] = dim
    tensor_dict['type'] = tensor_type
    
    return tensor_dict

# parse one or multiple tensors to list of dictionary
def parse_tensors(tensors):
    tensor_list = []

    for i in range(len(tensors)):
        tensor = {}
        tensor_type = {}

        tensor['name'] = tensors[i].name
        tensor_type['elem_type'] = tensors[i].type.tensor_type.elem_type

        dim = []
        len_dim = len(tensors[i].type.tensor_type.shape.dim)
        for j in range(len_dim):
            dim.append(tensors[i].type.tensor_type.shape.dim[j].dim_value)

        tensor_type['shape'] = dim
        tensor['type'] = tensor_type
        tensor_list.append(tensor)
    
    return tensor_list


# parse output tensor
def parse_output_tensor(all_nodes, model):
    # get all output tensors
    output_tensors = model.graph.value_info
    len_output = len(output_tensors)

    # parse all output tensor exclude the last output
    for i in range(len_output):
        output_tensor = parse_tensor(output_tensors[i])
        all_nodes[i]['output_tensor'] = output_tensor

    # parse last output tensor
    last_output_tensor = model.graph.output[0]
    tensor_dict = parse_tensor(last_output_tensor)
    all_nodes[-1]['output_tensor'] = tensor_dict


# parse input tensor from previous output tensor
def parse_input_tensor(all_nodes):
    for n in all_nodes:
        if n['parents']:
            for par in n['parents']:
                n['input_tensor'].append(all_nodes[par]['output_tensor'])


def parse_attribute(all_nodes, onnx_nodes):
    len_node = len(all_nodes)
    for k in range(len_node):    
        
        # Conv
        if all_nodes[k]['op_type'] == 'Conv':
            list_attr = []
            for i in range(5):
                attr_dict = {}
                attr_item = onnx_nodes[k].attribute[i]
                
                # name
                attr_dict['name'] = attr_item.name

                if(i == 1):
                    attr_dict['i'] = attr_item.i
                else:
                    # ints
                    ints = []
                    for j in range(len(attr_item.ints)):
                        ints.append(attr_item.ints[j])
                    attr_dict['ints'] = ints
                # type
                attr_dict['type'] = attr_item.type
                list_attr.append(attr_dict)
            all_nodes[k]['attribute'] = list_attr
            
        # batchnorm
        elif all_nodes[k]['op_type'] == 'BatchNormalization':
            list_attr = []
            for i in range(3):
                attr_dict = {}
                attr_item = onnx_nodes[k].attribute[i]
                
                # name
                attr_dict['name'] = attr_item.name
                # f
                attr_dict['f'] = attr_item.f
                # type
                attr_dict['type'] = attr_item.type
                list_attr.append(attr_dict)
            all_nodes[k]['attribute'] = list_attr
            
        # maxpool
        elif all_nodes[k]['op_type'] == 'MaxPool':
            # maxpool
            list_attr = []
            for i in range(3):
                attr_dict = {}
                attr_item = onnx_nodes[k].attribute[i]
                
                # name
                attr_dict['name'] = attr_item.name
                # ints
                ints = []
                for j in range(len(attr_item.ints)):
                    ints.append(attr_item.ints[j])
                attr_dict['ints'] = ints
                # type
                attr_dict['type'] = attr_item.type
                list_attr.append(attr_dict)
            all_nodes[k]['attribute'] = list_attr
            
        # gemm
        elif all_nodes[k]['op_type'] == 'Gemm':
            list_attr = []
            for i in range(4):
                attr_dict = {}
                attr_item = onnx_nodes[k].attribute[i]
                
                # name
                attr_dict['name'] = attr_item.name
                # f/i
                if i == 0 or i == 1:
                    attr_dict['f'] = attr_item.f
                else:
                    attr_dict['i'] = attr_item.i
                # type
                attr_dict['type'] = attr_item.type
                list_attr.append(attr_dict)
            all_nodes[k]['attribute'] = list_attr
        else:
            all_nodes[k]['attribute'] = []


def print_nodes(all_nodes, i):
    final = json.dumps(all_nodes[i], indent=3)
    print(final)

def parse_to_json(all_nodes):
    final = json.dumps(all_nodes, indent=2)
    with open("../json/resnet50.json", "w") as outfile:
        outfile.write(final)

def main():
    # inference
    # path = "../models/resnet50-v1-7_inference.onnx"
    # model = inference(path)

    # memory onnx

    nodes = model.graph.node

    # build list of nodes
    all_nodes = build_list_nodes(nodes)

    # parse attribute
    parse_attribute(all_nodes, nodes)
    
    # parse output tensor
    parse_output_tensor(all_nodes, model)

    # parse input tensor from previous output tensor
    parse_input_tensor(all_nodes)

    # first input tesnsor(data)
    input_all = model.graph.input
    tensor_list = parse_tensors(input_all[0:1])
    all_nodes[0]['input_tensor'].append(tensor_list[0])
    all_nodes[0]

    # record tensors of conv2d & batchnorm
    conv_inputs = []
    batchnorm_inputs = []

    for i in input_all:
        if 'conv' in i.name:
            conv_inputs.append(i)
        elif 'batchnorm' in i.name:
            batchnorm_inputs.append(i)


    # insert input tensor into batchnorm op
    cnt = 0
    for i in all_nodes:
        if i['op_type'] == 'BatchNormalization':
            tensor_list = parse_tensors(batchnorm_inputs[cnt:cnt+4])
            i['input_tensor'] += tensor_list
            cnt += 4
    
    # insert conv tensor(weight, bias)
    cnt = 0
    for i in all_nodes:
        if i['op_type'] == 'Conv':
            if 'weight' in conv_inputs[cnt+1].name:
                tensor_list = parse_tensors(conv_inputs[cnt:cnt+1])
                i['input_tensor'] += tensor_list
                cnt += 1
            else:
                tensor_list = parse_tensors(conv_inputs[cnt:cnt+2])
                i['input_tensor'] += tensor_list
                cnt += 2
            
    # gemm operator
    gemm_tensors = input_all[-2:]
    tensor_list = parse_tensors(gemm_tensors)
    all_nodes[-1]['input_tensor'].append(tensor_list)
    all_nodes[-1]

    # parse_to_json
    parse_to_json(all_nodes)

    # test print
#     print_nodes(all_nodes, 0)


if __name__ == '__main__':
    main()