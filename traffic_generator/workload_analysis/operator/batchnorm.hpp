#ifndef _BATCHNORM_HPP_
#define _BATCHNORM_HPP_

#include "./workload.hpp"

class Batchnorm : public Workload
{
public:
    Batchnorm()
    {
        // std::cout << "Batchnorm constructor\n";
    }

    virtual ~Batchnorm()
    {
        // std::cout << "Batchnorm destructor\n";
    }

    virtual void split();
};

void Batchnorm::split()
{
    // input tensor
    for (int j = 0; j < 4; j++)
    {
        split_node->inputs[0]->shape[j] /= strategy.splitSize[0][j];
        split_node->outputs[0]->shape[j] /= strategy.splitSize[0][j];
    }
    // scale, B, mean, var
    for (int i = 1; i <= 4; i++)
    {
        split_node->inputs[i]->shape[0] /= strategy.splitSize[0][0];
    }

    // output node
    // for (int i = 0; i < split_node->outputs.size(); i++)
    // {
    //     split_node->outputs[i] = split_node->inputs[0];
    // }
}

#endif