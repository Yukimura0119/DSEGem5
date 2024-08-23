#!/bin/bash

python3 DSE/main.py \
    --sw onnx_parser/json/fuse/vgg16_fuse.json \
    --arch files/HW_config/gem5_search_vanilla.json \
    --cost_model gem5 \
    --output dse_out \
    --dataflow shi \
    --metrics both \
    --optimize CO