#ifndef _Workload_HPP_
#define _Workload_HPP_

#include "../include.hpp"
#include "../graph.hpp"
#include "../strategy.hpp"

// split node to smaller node
class Workload
{
public:
    Strategy strategy;
    Node *node;
    Node *split_node;
    int numSubgraph;
    vector<long long> inputSize;
    vector<long long> outputSize;

    Workload()
    {
    }
    void init(Node *node, Node *split_node, Strategy strategy);
    virtual void split();
    virtual long long computeSize(); // compute input/output subgraph size
    virtual void compute_original_size();
    virtual void print();
};

void Workload::init(Node *node, Node *split_node, Strategy strategy)
{
    this->node = node;
    this->split_node = split_node;
    this->strategy = strategy;
}

void Workload::split()
{
    // input/kernel tensor
    for (int i = 0; i < strategy.splitSize.size(); i++)
    {
        for (int j = 0; j < 4; j++)
        {
            split_node->inputs[i]->shape[j] /= strategy.splitSize[i][j];
            // split_node->inputs[i]->size *= split_node->inputs[i]->shape[j];
            // split_node->inputs[i]->num_subgraph *= strategy.splitSize[i][j];
        }
    }

    // output node
    for (int i = 0; i < split_node->outputs.size(); i++)
    {
        split_node->outputs[i] = split_node->inputs[0];
    }
}

long long Workload::computeSize()
{
    long long memory_usage = 0;

    // input tensor
    for (auto &i : split_node->inputs)
    {
        long long size = 1;
        for (auto &j : i->shape)
        {
            size *= j;
        }
        // if (i->data_type == DataType::FP32)
        //     size *= 4;
        size *= 4;
        i->size = size;

        memory_usage += size; 
    }
    // split_node->size += size;

    // output tensor
    for (auto &i : split_node->outputs)
    {
        long long size = 1;
        for (auto &j : i->shape)
        {
            size *= j;
        }
        // if (i->data_type == DataType::FP32)
        //     size *= 4;
        size *= 4;
        i->size = size;

        memory_usage += size; 
    }
    // split_node->size += size;
    // cout << split_node->size << "\n";

    // base_node ----------------------------------------
    // input tensor
    // for (auto &i : node->inputs)
    // {
    //     long long size = 1;
    //     for (auto &j : i->shape)
    //     {
    //         size *= j;
    //     }
    //     // if (i->data_type == DataType::FP32)
    //     //     size *= 4;
    //     size *= 32;
    //     i->size = size;
    // }
    // // split_node->size += size;

    // // output tensor
    // for (auto &i : node->outputs)
    // {
    //     long long size = 1;
    //     for (auto &j : i->shape)
    //     {
    //         size *= j;
    //     }
    //     // if (i->data_type == DataType::FP32)
    //     //     size *= 4;
    //     size *= 32;
    //     i->size = size;
    // }

    // memory_usage *= 4;
    cout << "memory usage = " << memory_usage << " bytes \n";
    return memory_usage;
}

void Workload::compute_original_size()
{
    // base_node ----------------------------------------
    // input tensor
    cout << "compute original\n";
    for (auto &i : node->inputs)
    {
        long long size = 1;
        for (auto &j : i->shape)
        {
            size *= j;
        }
        // if (i->data_type == DataType::FP32)
        //     size *= 4;
        // size *= 32;
        i->size = size;
        split_node->origianl_input_size.push_back(size);
    }
}

void Workload::print()
{
    for (auto i : split_node->inputs)
    {
        for (auto shape : i->shape)
        {
            cout << shape << " ";
        }
        cout << i->size;
        cout << "\n";
    }

    for (auto i : split_node->outputs)
    {
        for (auto shape : i->shape)
        {
            cout << shape << " ";
        }
        cout << i->size;
        cout << "\n";
    }
}

#endif