import os

import onnx
from onnxruntime.tools import onnx_model_utils

from mem_table import MemTable

def inferShapes(model_path: str, input_shape: list, save_model: bool = True)->onnx.ModelProto:
    dir_path, _ = os.path.splitext(model_path)
    model_name  = os.path.basename(dir_path)
    submodel_dir_path = os.path.join(os.getcwd(), 'out')

    model = onnx.load(model_path)
    onnx.checker.check_model(model)
    onnx_model_utils.make_input_shape_fixed(model.graph, model.graph.input[0].name, input_shape)
    inferred_model = onnx.shape_inference.infer_shapes(model)
    onnx.checker.check_model(inferred_model)

    dest_dir = os.path.join(submodel_dir_path, model_name)

    if save_model:
        os.makedirs(dest_dir, exist_ok=True)
        onnx.save(inferred_model, os.path.join(dest_dir, model_name + "_inffered.onnx"))

    return inferred_model

def dtype2byte(dtype: str)->int:
    if dtype == 'int8':
        return 1
    elif dtype == 'int32' or dtype == 'float32':
        return 4
    elif dtype == 'float64':
        return 8
    else:
        raise RuntimeError('Unknown dtype')

def sizeStr2Int(size_str: str)->int:
    if 'GB' in size_str:
        return int(size_str.split('GB')[0]) *  int(2**30)
    elif 'MB' in size_str:
        return int(size_str.split('MB')[0]) *  int(2**20)
    elif 'KB' in size_str:
        return int(size_str.split('KB')[0]) *  int(2**10)
    elif 'B' in size_str:
        return int(size_str.split('B')[0])


def placeTensor(model_path: str, inferred_model: onnx.ModelProto, dtype: str, mem_size: str, save_model: bool = True)->onnx.ModelProto:
    dir_path, _ = os.path.splitext(model_path)
    model_name  = os.path.basename(dir_path)
    submodel_dir_path = os.path.join(os.getcwd(), 'out')

    # add memory address and size to model graph
    mem_table = MemTable(size=sizeStr2Int(mem_size))

    # insert weight size, addr
    tensor_mem_info = {}
    for input in inferred_model.graph.input:
        tensor_size = 1
        for dim in input.type.tensor_type.shape.dim:
            tensor_size *= dim.dim_value
        tensor_size *= dtype2byte(dtype)
        remain_size, addr = mem_table.allocate(input.name, tensor_size)
        if addr == -1:
            raise RuntimeError(f'Insufficient memory capacity while allocating input and weights, try {tensor_size}, remain {mem_table.table[-1]["size"]}')
        elif remain_size != 0:
            pass
        else:
            tensor_mem_info[input.name] = {'addr': addr, 'size': tensor_size}

    # insert activation size, addr
    for activation in inferred_model.graph.value_info:
        tensor_size = 1
        for dim in activation.type.tensor_type.shape.dim:
            tensor_size *= dim.dim_value
        tensor_size *= dtype2byte(dtype) # float
        remain_size, addr = mem_table.allocate(activation.name, tensor_size)

        if addr == -1:
            raise RuntimeError(f'Insufficient memory capacity while allocating activation, try {tensor_size}, remain {mem_table.table[-1]["size"]}')
        elif remain_size != 0:
            pass
        else:
            tensor_mem_info[activation.name] = {'addr': addr, 'size': tensor_size}
    # insert output size, addr
    for output in inferred_model.graph.output:
        tensor_size = 1
        for dim in output.type.tensor_type.shape.dim:
            tensor_size *= dim.dim_value
        tensor_size *= dtype2byte(dtype) # float
        remain_size, addr = mem_table.allocate(output.name, tensor_size)

        if addr == -1:
            raise RuntimeError(f'Insufficient memory capacity while allocating activation, try {tensor_size}, remain {mem_table.table[-1]["size"]}')
        elif remain_size != 0:
            pass
        else:
            tensor_mem_info[output.name] = {'addr': addr, 'size': tensor_size}
    
    for node in inferred_model.graph.node:
        for input in node.input:
            if input not in tensor_mem_info.keys():
                raise RuntimeError(f'input tensor not found: {input}')
            addr_size = onnx.helper.make_attribute(f'{input}', [tensor_mem_info[input]['addr'], tensor_mem_info[input]['size']])
            node.attribute.insert(0, addr_size)

        
        for output in node.output:
            if output not in tensor_mem_info.keys():
                raise RuntimeError(f'output tensor not found: {output}')
            addr_size = onnx.helper.make_attribute(f'{output}', [tensor_mem_info[output]['addr'], tensor_mem_info[output]['size']])
            node.attribute.insert(0, addr_size)

    dest_dir = os.path.join(submodel_dir_path, model_name)

    if save_model:
        os.makedirs(dest_dir, exist_ok=True)
        onnx.save(inferred_model, os.path.join(dest_dir, model_name + "_mem.onnx"))

    return inferred_model