import os
import argparse
import onnx

import utils
from mem_table import MemTable


def main(args)->None:
    # add activations informations to model graph
    input_shape = [int(dim) for dim in args.input_shape.split(',')]

    if args.layout != 'nchw':
        input_shape[1], input_shape[2], input_shape[3] = input_shape[2], input_shape[3], input_shape[1]

    inferred_model = utils.inferShapes(args.model_path, input_shape, False)
    inferred_model_mem = utils.placeTensor(args.model_path, inferred_model, args.dtype, args.mem_size, True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model_path', type=str, default='models/resnet50-v1-7.onnx', help='onnx model path, default="models/resnet50-v1-7.onnx"')
    parser.add_argument('-l', '--layout', type=str, choices=['nchw', 'nhwc'], default='nchw', help='choose one from ["nchw", "hwcn"]')
    parser.add_argument('-i', '--input_shape', type=str, default='1,3,224,224', help='model input shape, followed layout ex: 1,3,224,224')
    parser.add_argument('-d', '--dtype', type=str, default='float32', choices=['int8', 'int32', 'float32', 'float64'], help='dtype of model weights choose one from ["int8", "int32", "float32", "float64"]')
    parser.add_argument('-s', '--mem_size', type=str, default='4GB', help='DRAM size')

    args = parser.parse_args()

    main(args)