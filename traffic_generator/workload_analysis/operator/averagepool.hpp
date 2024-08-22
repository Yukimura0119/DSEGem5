#ifndef _AVERAGEPOOL_HPP_
#define _AVERAGEPOOL_HPP_

#include "../include.hpp"
#include "./workload.hpp"

class AvgPool : public Workload
{
public:
    AvgPool()
    {
        // std::cout << "AvgPool constructor\n";
    }

    virtual ~AvgPool()
    {
        // std::cout << "AvgPool destructor\n";
    }

    void split();
};

void AvgPool::split()
{
    // input tensor
    split_node->inputs[0]->shape[1] /= strategy.splitSize[0][1];

    // output tensor
    split_node->outputs[0]->shape[1] /= strategy.splitSize[0][1];
}

#endif