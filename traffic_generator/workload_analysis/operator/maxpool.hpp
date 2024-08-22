#ifndef _MAXPOOL_HPP_
#define _MAXPOOL_HPP_

#include "../include.hpp"
#include "../graph.hpp"
#include "../strategy.hpp"
#include "./workload.hpp"

class MaxPool : public Workload
{
public:
    MaxPool()
    {
        // cout << "Max Pool Workload\n";
    }

    void split();
};

void MaxPool::split()
{
    // cout << "Maxpool split\n";
    // channel
    split_node->inputs[0]->shape[1] /= strategy.splitSize[0][1];
    split_node->outputs[0]->shape[1] /= strategy.splitSize[0][1];

    // output height, width
    split_node->outputs[0]->shape[2] /= strategy.splitSize[0][2];
    split_node->outputs[0]->shape[3] /= strategy.splitSize[0][3];

    // input height, width
    // int *values = static_cast<int *>(split_node->attributes[0]->values);
    auto kernel = split_node->attributes[0]->data[0];
    cout << kernel << "\n";

    // values = static_cast<int *>(split_node->attributes[1]->values);
    auto pad = split_node->attributes[1]->data[0];
    cout << pad << "\n";

    // values = static_cast<int *>(split_node->attributes[2]->values);
    auto stride = split_node->attributes[2]->data[0];
    cout << stride << "\n";

    auto output_h = split_node->outputs[0]->shape[2];

    split_node->inputs[0]->shape[2] = (output_h - 1) * stride + kernel;
    split_node->inputs[0]->shape[3] = (output_h - 1) * stride + kernel;
}

#endif