#ifndef _CONV_BATCHNROM_RELU_HPP_
#define _CONV_BATCHNROM_RELU_HPP_

#include "../include.hpp"
#include "../graph.hpp
#include "./workload.hpp"

class ConvBatchnormRelu : public Workload
{
public:
    int numSubgraph = 1;

    Conv()
    {
        // std::cout << "\nConv2d constructor-------------------\n";
    }

    virtual ~Conv()
    {
        // std::cout << "Conv2d destructor----------------------\n";
    }
    void split();
    // long long computeSize();
};

void Conv::split()
{
    // x' = (x + 2 * padding - r)/ stride + 1
    // y' = (y + 2 * padding - s)/ stride + 1
    // x = (x' - 1) * stride + r - 2 * padding
    // y = (y' - 1) * stride + s - 2 * padding

    // output
    // c
    split_node->outputs[0]->shape[1] /= strategy.splitSize[1][0];
    // h
    split_node->outputs[0]->shape[2] /= strategy.splitSize[0][2];
    // w
    split_node->outputs[0]->shape[3] /= strategy.splitSize[0][3];


    // input tensor
    // c
    split_node->inputs[0]->shape[1] /= strategy.splitSize[0][1];
    // x, y
    auto pad = split_node->attributes[3]->data[0];
    // cout << pad << endl;
    auto stride = split_node->attributes[4]->data[0];
    // cout << stride << endl;

    auto r = split_node->inputs[1]->shape[2];
    auto s = split_node->inputs[1]->shape[3];

    // original size
    split_node->inputs[0]->shape[2] /= strategy.splitSize[0][2];
    split_node->inputs[0]->shape[3] /= strategy.splitSize[0][3];

    // update size with padding
    // split x
    if(strategy.splitSize[0][2] > 1)
    {
        split_node->inputs[0]->shape[2] = (split_node->outputs[0]->shape[2] - 1) * stride + r - pad;
    }
    // split y
    if(strategy.splitSize[0][3] > 1)
    {
        split_node->inputs[0]->shape[3] = (split_node->outputs[0]->shape[3] - 1) * stride + s - pad;
    }

    // split_node->inputs[0]->shape[2] = (split_node->outputs[0]->shape[2] - 1) * stride + r - pad;
    // split_node->inputs[0]->shape[3] = (split_node->outputs[0]->shape[3] - 1) * stride + s - pad;

    // weight tensor
    for (int i = 0; i < 4; i++)
    {
        split_node->inputs[1]->shape[i] /= strategy.splitSize[1][i];
    }
    // bias
    if (split_node->inputs.size() > 2)
    {
        split_node->inputs[2]->shape[0] /= strategy.splitSize[1][0];
    }
}

#endif