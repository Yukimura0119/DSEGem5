#ifndef _GRAPH_H_
#define _GRAPH_H_
#include "./include.hpp"

enum class DataType
{
    INT8,
    FP8,
    BF16,
    FP16,
    INT32,
    FP32,
    INT64,
    FP64
};

class Tensor
{
public:
    uint32_t id;
    std::string name;

    std::vector<int> shape; // N, C, H, W
    DataType data_type;
    // void *data; // to be discussed

    long long size; // how many bits
    uint64_t address; // base addresss
    uint64_t original_size;

    // std::vector<Node *> producers;
    // std::vector<Node *> consumers;
    Tensor()
    {
    }
    Tensor(string name, std::vector<int> shape, DataType datatype)
        : name(name), shape(shape), data_type(datatype)
    {
        // size = 1;
    }
};

class NodeAttribute
{
public:
    std::string name;
    DataType data_type;
    uint32_t length;
    void *values; // to be discussed
    vector<int> data;
    NodeAttribute()
    {
    }
    NodeAttribute(string name, DataType data_type, vector<int> data)
        : name(name), data_type(data_type), data(data)
    {
    }
};

enum class Operator
{
    CONV,
    GEMM,
    RELU,
    MAXPOOL,
    BATCHNORMAL,
    SOFTMAX,
    RESHPAE,
    AVGPOOL
};

// op
class Node
{
public:
    uint32_t id;
    std::string name;
    Operator op;

    std::vector<Tensor *> inputs;
    std::vector<Tensor *> outputs;
    std::vector<NodeAttribute *> attributes;

    std::vector<Node *> parents;
    std::vector<Node *> childs;

    long long size;
    vector<long long> origianl_input_size;

    Node()
    {
    }
    Node(uint32_t id, std::string name, Operator op)
        : id(id), name(name), op(op)
    {
    }
};

class Graph
{
public:
    std::string name;
    std::vector<Tensor *> tensors;
    std::vector<Node *> nodes;

    std::vector<Tensor *> inputs;
    std::vector<Tensor *> outputs;
};

#endif
