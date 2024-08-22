import onnx
import json
from onnx import shape_inference

# do model inference
path = "../models/mobilenetv2-7.onnx"
new_path = "../models/mobilenetv2-7.onnx"
model = onnx.load(path)
model = onnx.shape_inference.infer_shapes(model)
onnx.save(onnx.shape_inference.infer_shapes(model), new_path)

# parse all nodes
nodes = model.graph.node

# id table
id_table = {}
node_cnt = 0

# all nodes
all_nodes = []

# parse each op
for op in nodes:
    node = {}
    node['name'] = op.name
    node['id'] = node_cnt
    id_table[op.name] = node_cnt
    node_cnt = node_cnt + 1
    node['op_type'] = op.op_type
    
    # record all attribute of one op
    attr_list = []
    for attr in op.attribute:
        attr_list.append(attr)
    node['attribute'] = attr_list
    
    all_nodes.append(node)

# deal with consumer
for i, op in enumerate(nodes):
    producer = []
    for prod in op.input:
        # exclude input and weight of first layer
        if(id_table.get(prod) != None):
            producer.append(id_table[prod])
    all_nodes[i]['producer'] = producer
    
    
    