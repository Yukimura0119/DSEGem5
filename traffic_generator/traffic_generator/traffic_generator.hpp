#ifndef _TRAFFIC_GENERATOR_HPP_
#define _TRAFFIC_GENERATOR_HPP_

#include "./traffic.hpp"
#include "../workload_analysis/include.hpp"
#include "../workload_analysis/operator/workload.hpp"
#include "../workload_analysis/pe.hpp"
#include "../workload_analysis/graph.hpp"

class TrafficGenerator
{
public:
    std::vector<Traffic> trafficList;
    std::string operatorType;
    int numSubgraph;
    long long inputSubgraphSize;
    long long outputSubgraphSize;
    Node split_node;
    Node base_node;
    int numPE;
    int round;
    int remainder;
    long long latency;
    Strategy strategy;

    TrafficGenerator(int numPE, int numSubgraph, Node &split_node, Node &base_node)
        : numPE(numPE), numSubgraph(numSubgraph), split_node(split_node), base_node(base_node)
    {
        // cout << "traffic generator constructor\n";
        this->round = std::ceil(double(numSubgraph) / numPE);
        this->remainder = numSubgraph % numPE;
    }
    ~TrafficGenerator()
    {
        // cout << "traffic generator destructor\n";
    }

    // read strategy
    void init_strategy(Strategy strategy)
    {
        this->strategy = strategy;
    }

    // general function
    void unicast_read(int num_subgraph, uint64_t size, uint64_t &addr);
    void unicast_write(int num_subgraph, uint64_t size, uint64_t &addr);
    void compute(int num_subgraph);
    void broadcast_read(uint64_t size, uint64_t &addr);

    // opeartor function
    void generate_traffic_element_wise();
    void generate_traffic_conv_weight_stationary();
    void generate_traffic_conv_output_stationary();
    void generate_traffic_batchnorm();

    // optimized
    void generate_traffic_conv_weight_reduction();
    void generate_traffic_conv_output_reduction();
    void generate_traffic_batchnorm_reduction();

    // fused
    void generate_traffic_conv_batchnorm_weight();
    void generate_traffic_conv_batchnorm_output();
};

void TrafficGenerator::unicast_read(int num_subgraph, uint64_t size, uint64_t &addr)
{
    for (int i = 0; i < num_subgraph; i++)
    {
        Traffic traffic = Traffic(
            RequestType::READ,
            std::make_pair(0, i),
            std::make_pair(1, 0),
            addr,
            size,
            TrafficType::UNICAST,
            TrafficType::UNICAST);

        trafficList.push_back(traffic);
        addr += size;
    }
}

void TrafficGenerator::unicast_write(int num_subgraph, uint64_t size, uint64_t &addr)
{
    for (int i = 0; i < num_subgraph; i++)
    {
        Traffic traffic = Traffic(
            RequestType::WRITE,
            std::make_pair(0, i),
            std::make_pair(1, 0),
            addr,
            size,
            TrafficType::UNICAST,
            TrafficType::UNICAST);

        trafficList.push_back(traffic);
        addr += size;
    }
}

void TrafficGenerator::broadcast_read(uint64_t size, uint64_t &addr)
{
    // broadcast
    Traffic traffic = Traffic(
        RequestType::READ,
        std::make_pair(0, 0),
        std::make_pair(1, 0),
        addr,
        size,
        TrafficType::UNICAST,
        TrafficType::BROADCAST);

    trafficList.push_back(traffic);
    addr += size;

    // SYNC
    for (int i = 1; i < numPE; i++)
    {
        Traffic traffic = Traffic(
            RequestType::SYNC,
            std::make_pair(0, i),
            std::make_pair(1, 0),
            0,
            0,
            TrafficType::UNICAST,
            TrafficType::UNICAST);

        trafficList.push_back(traffic);
    }
}

void TrafficGenerator::compute(int num_subgraph)
{
    for (int i = 0; i < num_subgraph; i++)
    {
        Traffic traffic = Traffic(
            RequestType::COMPUTE,
            std::make_pair(0, i),
            std::make_pair(1, 0),
            addr,
            0,
            TrafficType::UNICAST,
            TrafficType::UNICAST);

        trafficList.push_back(traffic);
    }
}

// ---------------------------------------------------------------------------
// Element wise op -----------------------------------------------------------
void TrafficGenerator::generate_traffic_element_wise()
{
    cout << "traffic generator element wise\n";

    // size
    long long input_subgraph_size;
    long long output_subgraph_size = split_node.outputs[0]->size;

    // address
    long long input_address;
    long long output_address;

    for (int i = 0; i < round; i++)
    {
        // unit read input
        for (int j = 0; j < split_node.inputs.size(); j++)
        {
            input_subgraph_size = split_node.inputs[j]->size;
            // input_address = split_node.inputs[j]->address;
            unicast_read(numPE, input_subgraph_size, split_node.inputs[j]->address);
        }
        // compute
        compute(numPE);

        // unit write
        // output_address = split_node.outputs[0]->address;
        unicast_write(numPE, output_subgraph_size, split_node.outputs[0]->address);
    }
    if (remainder)
    {
        // unit read input
        for (int j = 0; j < split_node.inputs.size(); j++)
        {
            input_subgraph_size = split_node.inputs[j]->size;
            unicast_read(numPE, input_subgraph_size, split_node.inputs[j]->address);
        }
        // compute
        compute(remainder);
        // unit write
        unicast_write(remainder, output_subgraph_size, split_node.outputs[0]->address);
    }
}

// Conv2d  Weight stationary
void TrafficGenerator::generate_traffic_conv_weight_stationary()
{
    int weight_round = strategy.splitSize[1][0] / numPE; // K/PE
    int c = strategy.splitSize[0][1];                    // channel
    int hw = strategy.splitSize[0][2] * strategy.splitSize[0][3];

    for (int i = 0; i < weight_round; i++)
    {
        // bias
        if (split_node.inputs.size() > 2)
        {
            unicast_read(numPE, split_node.inputs[2]->size, split_node.inputs[2]->address);
        }

        for (int j = 0; j < c; j++)
        {
            // read weight
            unicast_read(numPE, split_node.inputs[1]->size, split_node.inputs[1]->address);

            for (int k = 0; k < hw; k++)
            {
                // read input tensor
                broadcast_read(split_node.inputs[0]->size, split_node.inputs[0]->address);
                // broadcast_read(input_size, addr);

                // compute
                compute(numPE);

                // write partial sum
                // unicast_write(numPE, output_size, addr);
                unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
            }
        }
    }
}

// output stationary
void TrafficGenerator::generate_traffic_conv_output_stationary()
{
    int c = strategy.splitSize[0][1];
    int knum = strategy.splitSize[1][0];
    int hw_mult = strategy.splitSize[0][2] * strategy.splitSize[0][3];
    int input_round = hw_mult / numPE;
    int input_remainder = hw_mult % numPE;

    for (int i = 0; i < c; i++)
    {
        for (int j = 0; j < input_round; j++)
        {
            // read input
            unicast_read(numPE, split_node.inputs[0]->size, split_node.inputs[0]->address);

            for (int k = 0; k < knum; k++)
            {
                // read weight
                broadcast_read(split_node.inputs[1]->size, split_node.inputs[1]->address);

                // bias
                if (split_node.inputs.size() > 2)
                    unicast_read(numPE, split_node.inputs[2]->size, split_node.inputs[2]->address);

                // compute
                compute(numPE);
            }
        }
        // remainder
        if (input_remainder)
        {
            // read input
            unicast_read(input_remainder, split_node.inputs[0]->size, split_node.inputs[0]->address);
            // bias
            if (split_node.inputs.size() > 2)
            {
                unicast_read(input_remainder, split_node.inputs[2]->size, split_node.inputs[2]->address);
            }

            for (int k = 0; k < knum; k++)
            {
                // read weight
                broadcast_read(split_node.inputs[1]->size, split_node.inputs[1]->address);

                // bias
                if (split_node.inputs.size() > 2)
                    unicast_read(numPE, split_node.inputs[2]->size, split_node.inputs[2]->address);

                // compute
                compute(input_remainder);
            }
        }
    }

    // write
    unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
}

// ---------------------------------------------------------------------------
// Batchnorm op --------------------------------------------------------------
void TrafficGenerator::generate_traffic_batchnorm()
{
    cout << "traffic generator batchnorm\n";

    // size
    long long input_subgraph_size;
    long long output_subgraph_size = split_node.outputs[0]->size;

    // address
    long long input_address;
    long long output_address;

    int c = strategy.splitSize[0][1];
    int hw = strategy.splitSize[0][2] * strategy.splitSize[0][3];
    int input_round = hw / numPE;
    int input_remainder = hw % numPE;

    // split c dim only
    if (strategy.splitSize[0][1] > 1 && strategy.splitSize[0][2] == 1 && strategy.splitSize[0][3] == 1)
    {
        int c_round = c / numPE;
        int c_remainder = c % numPE;

        for (int i = 0; i < c_round; i++)
        {
            // read input
            unicast_read(numPE, split_node.inputs[0]->size, split_node.inputs[0]->address);
            // scale, B, mean, var,
            for (int j = 1; j < split_node.inputs.size(); j++)
            {
                unicast_read(numPE, split_node.inputs[j]->size, split_node.inputs[j]->address);
            }
            // compute
            compute(numPE);
            // write
            unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
        }
        if (c_remainder)
        {
            // read input
            unicast_read(c_remainder, split_node.inputs[0]->size, split_node.inputs[0]->address);
            // scale, B, mean, var,
            for (int j = 1; j < split_node.inputs.size(); j++)
            {
                broadcast_read(split_node.inputs[j]->size, split_node.inputs[j]->address);
            }
            // compute
            compute(c_remainder);
            // write
            unicast_write(c_remainder, split_node.outputs[0]->size, split_node.outputs[0]->address);
        }
    }
    // split c, h, w
    else if (strategy.splitSize[0][1] > 1 && strategy.splitSize[0][2] != 1 && strategy.splitSize[0][3] != 1)
    {
        cout << "split c\n";

        for (int i = 0; i < c; i++)
        {
            // scale, B, mean, var,
            for (int j = 1; j < split_node.inputs.size(); j++)
            {
                broadcast_read(split_node.inputs[j]->size, split_node.inputs[j]->address);
            }

            for (int j = 0; j < input_round; j++)
            {
                // read input
                unicast_read(numPE, split_node.inputs[0]->size, split_node.inputs[0]->address);
                // compute
                compute(numPE);
                // write
                unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
            }
            if (input_remainder)
            {
                // read input
                unicast_read(input_remainder, split_node.inputs[0]->size, split_node.inputs[0]->address);
                // compute
                compute(input_remainder);
                // write
                unicast_write(input_remainder, split_node.outputs[0]->size, split_node.outputs[0]->address);
            }
        }
    }
    // if not splitting c dim, split h & w dim
    else if (strategy.splitSize[0][1] == 1)
    {
        cout << "not split c, split h & w\n";

        // scale, B, mean, var,
        for (int j = 1; j < split_node.inputs.size(); j++)
        {
            broadcast_read(split_node.inputs[j]->size, split_node.inputs[j]->address);
        }

        for (int i = 0; i < round; i++)
        {
            // unit read input
            input_subgraph_size = split_node.inputs[0]->size;
            unicast_read(numPE, input_subgraph_size, split_node.inputs[0]->address);
            // compute
            compute(numPE);
            // unit write
            unicast_write(numPE, output_subgraph_size, split_node.outputs[0]->address);
        }
        if (remainder)
        {
            // unit read input
            unicast_read(numPE, input_subgraph_size, split_node.inputs[0]->address);
            // compute
            compute(remainder);
            // unit write
            unicast_write(remainder, output_subgraph_size, split_node.outputs[0]->address);
        }
    }
}

// --------------------------------------------------------------
// Traffic Reduction(Reuse)
void TrafficGenerator::generate_traffic_conv_weight_reduction()
{
    long long input_size = split_node.inputs[0]->size;
    long long weight_size = split_node.inputs[1]->size;
    long long output_size = split_node.outputs[0]->size;
    long long bias_size = 1;
    if (split_node.inputs.size() > 2)
        bias_size = split_node.inputs[2]->size;

    int weight_round = strategy.splitSize[1][0] / numPE; // K/PE
    int c = strategy.splitSize[0][1];                    // channel
    int hw = strategy.splitSize[0][2] * strategy.splitSize[0][3];

    // bias
    if (split_node.inputs.size() > 2)
    {
        broadcast_read(split_node.inputs[2]->size, split_node.inputs[2]->address);
    }

    for (int i = 0; i < weight_round; i++)
    {
        for (int j = 0; j < c; j++)
        {
            // read weight
            unicast_read(numPE, split_node.inputs[1]->size, split_node.inputs[1]->address);
            // unicast_read(numPE, weight_size, addr);

            for (int k = 0; k < hw; k++)
            {
                // read input tensor
                broadcast_read(split_node.inputs[0]->size, split_node.inputs[0]->address);
                // broadcast_read(input_size, addr);

                // compute
                compute(numPE);

                // write partial sum
                // unicast_write(numPE, output_size, addr);
                unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
            }
        }
    }
}

void TrafficGenerator::generate_traffic_conv_output_reduction()
{
    cout << "traffic generator conv output reduction\n";
    long long input_size = split_node.inputs[0]->size;
    long long weight_size = split_node.inputs[1]->size;
    long long output_size = split_node.outputs[0]->size;
    long long bias_size = 1;
    if (split_node.inputs.size() > 2)
        bias_size = split_node.inputs[2]->size;

    int c = strategy.splitSize[0][1];
    int knum = strategy.splitSize[1][0];
    int hw_mult = strategy.splitSize[0][2] * strategy.splitSize[0][3];
    int input_round = hw_mult / numPE;
    int input_remainder = hw_mult % numPE;

    // bias
    if (split_node.inputs.size() > 2)
    {
        broadcast_read(split_node.origianl_input_size[2], split_node.inputs[2]->address);
    }

    for (int i = 0; i < c; i++)
    {
        for (int j = 0; j < input_round; j++)
        {
            // read input
            unicast_read(numPE, split_node.inputs[0]->size, split_node.inputs[0]->address);

            for (int k = 0; k < knum; k++)
            {
                // read weight
                broadcast_read(split_node.inputs[1]->size, split_node.inputs[1]->address);

                // compute
                compute(numPE);
            }
        }
        // remainder
        if (input_remainder)
        {
            // read input
            unicast_read(input_remainder, split_node.inputs[0]->size, split_node.inputs[0]->address);
            // bias
            if (split_node.inputs.size() > 2)
                unicast_read(input_remainder, split_node.inputs[2]->size, split_node.inputs[2]->address);

            for (int k = 0; k < knum; k++)
            {
                // read weight
                broadcast_read(split_node.inputs[1]->size, split_node.inputs[1]->address);

                // compute
                compute(input_remainder);
            }
        }
    }

    // write
    unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
}

void TrafficGenerator::generate_traffic_batchnorm_reduction()
{
    cout << "traffic generator batchnorm reduction\n";
    // size
    long long input_subgraph_size;
    long long output_subgraph_size = split_node.outputs[0]->size;

    int c = strategy.splitSize[0][1];
    int hw = strategy.splitSize[0][2] * strategy.splitSize[0][3];
    int input_round = hw / numPE;
    int input_remainder = hw % numPE;

    int num_subgraph = strategy.splitSize[0][1] * strategy.splitSize[0][2] * strategy.splitSize[0][3];
    int round = num_subgraph / numPE;
    int remainder = num_subgraph % numPE;

    // cout << round << endl;
    // cout << remainder << endl;

    // scale, B, mean, var,
    for (int j = 1; j < split_node.origianl_input_size.size(); j++)
    {
        broadcast_read(split_node.origianl_input_size[j], split_node.inputs[j]->address);
    }

    for (int i = 0; i < round; i++)
    {
        // read input
        unicast_read(numPE, split_node.inputs[0]->size, split_node.inputs[0]->address);
        // compute
        compute(numPE);
        // write
        unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
    }
    if (remainder)
    {
        // read input
        unicast_read(remainder, split_node.inputs[0]->size, split_node.inputs[0]->address);
        // compute
        compute(remainder);
        // write
        unicast_write(remainder, split_node.outputs[0]->size, split_node.outputs[0]->address);
    }
}

void TrafficGenerator::generate_traffic_conv_batchnorm_weight()
{
    cout << "generate traffic conv & batchnorm weight\n";

    int weight_round = strategy.splitSize[1][0] / numPE; // K/PE
    int c = strategy.splitSize[0][1];                    // channel
    int hw = strategy.splitSize[0][2] * strategy.splitSize[0][3];

    for (int i = 0; i < weight_round; i++)
    {
        // bias
        if (split_node.inputs.size() == 7)
        {
            unicast_read(numPE, split_node.inputs[2]->size, split_node.inputs[2]->address);
        }

        // batchnorm weight
        int n = split_node.inputs.size();
        // cout << "n = " << n << endl;
        for (int j = 0; j < 4; j++)
        {
            unicast_read(numPE, split_node.inputs[n - 1 - j]->size, split_node.inputs[n - 1 - j]->address);
            // cout << "traffic pattern = " << trafficList.size() << endl;
        }

        for (int j = 0; j < c; j++)
        {
            // read weight
            unicast_read(numPE, split_node.inputs[1]->size, split_node.inputs[1]->address);
            // cout << "traffic pattern = " << trafficList.size() << endl;
            for (int k = 0; k < hw; k++)
            {
                // read input tensor
                broadcast_read(split_node.inputs[0]->size, split_node.inputs[0]->address);
                // cout << "traffic pattern = " << trafficList.size() << endl;
                // compute
                compute(numPE);
                // cout << "traffic pattern = " << trafficList.size() << endl;
                // write partial sum
                unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
                // cout << "traffic pattern = " << trafficList.size() << endl;
            }
        }
    }
}

void TrafficGenerator::generate_traffic_conv_batchnorm_output()
{
    cout << "generate traffic conv & batchnorm weight\n";

    int c = strategy.splitSize[0][1];
    int knum = strategy.splitSize[1][0];
    int hw_mult = strategy.splitSize[0][2] * strategy.splitSize[0][3];
    int input_round = hw_mult / numPE;
    int input_remainder = hw_mult % numPE;

    for (int i = 0; i < c; i++)
    {
        for (int j = 0; j < input_round; j++)
        {
            // read input
            unicast_read(numPE, split_node.inputs[0]->size, split_node.inputs[0]->address);
            // cout << "traffic pattern = " << trafficList.size() << endl;

            for (int k = 0; k < knum; k++)
            {
                // read weight
                broadcast_read(split_node.inputs[1]->size, split_node.inputs[1]->address);
                // cout << "traffic pattern = " << trafficList.size() << endl;

                // bias
                if (split_node.inputs.size() == 7)
                {
                    unicast_read(numPE, split_node.inputs[2]->size, split_node.inputs[2]->address);
                    // cout << "traffic pattern = " << trafficList.size() << endl;
                }

                // batchnorm weight
                int n = split_node.inputs.size();
                // cout << "n = " << n << endl;
                for (int j = 0; j < 4; j++)
                {
                    unicast_read(numPE, split_node.inputs[n - 1 - j]->size, split_node.inputs[n - 1 - j]->address);
                    // cout << "traffic pattern = " << trafficList.size() << endl;
                }

                // compute
                compute(numPE);
                // cout << "traffic pattern = " << trafficList.size() << endl;
            }
        }
        // remainder
        if (input_remainder)
        {
            // read input
            unicast_read(input_remainder, split_node.inputs[0]->size, split_node.inputs[0]->address);
            // bias
            if (split_node.inputs.size() == 7)
            {
                unicast_read(numPE, split_node.inputs[2]->size, split_node.inputs[2]->address);
                // cout << "traffic pattern = " << trafficList.size() << endl;
            }

            for (int k = 0; k < knum; k++)
            {
                // read weight
                broadcast_read(split_node.inputs[1]->size, split_node.inputs[1]->address);

                // bias
                if (split_node.inputs.size() > 2)
                {
                    unicast_read(numPE, split_node.inputs[2]->size, split_node.inputs[2]->address);
                }

                // batchnorm weight
                int n = split_node.inputs.size();
                for (int j = 0; j < 4; j++)
                {
                    unicast_read(numPE, split_node.inputs[n - 1 - j]->size, split_node.inputs[n - 1 - j]->address);
                }

                // compute
                compute(input_remainder);
            }
        }
    }

    // write
    unicast_write(numPE, split_node.outputs[0]->size, split_node.outputs[0]->address);
    // cout << "traffic pattern = " << trafficList.size() << endl;
}

#endif