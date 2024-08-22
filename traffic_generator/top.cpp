#ifndef _TOP_CPP_
#define _TOP_CPP_

#include "parser/json_parser.hpp"
#include <iostream>

#include "workload_analysis/graph.hpp"
#include "workload_analysis/pe.hpp"
#include "workload_analysis/include.hpp"
#include "workload_analysis/operator/conv.hpp"
#include "workload_analysis/operator/batchnorm.hpp"
#include "workload_analysis/operator/relu.hpp"
#include "workload_analysis/operator/averagepool.hpp"
#include "workload_analysis/operator/workload.hpp"
#include "workload_analysis/operator/maxpool.hpp"
#include "workload_analysis/operator/conv_batchnorm.hpp"

#include "traffic_generator/traffic.hpp"
#include "traffic_generator/traffic_generator.hpp"

#include "workload_analysis/util.hpp"

// #define TRAFFIC_OPTIMIZE 1
// #define DEBUG 1

using namespace std;

int main(int argc, char *argv[])
{
    // JsonParser j = JsonParser("../files/DSE/DSE_resnet50_maxpool.json");
    JsonParser j = JsonParser(argv[1]);
    Graph *x = j.getModel();
    Strategy *strategy = j.getStrategy();

#ifdef DEBUG
    cout << "test operator----------------------------------\n";
    for (auto i : x->nodes)
    {
        cout << i->id << endl;
        cout << i->name << endl;

        // attribute
        for (auto j : i->attributes)
        {
            cout << j->name << " ";
            if (j->data.size() > 0)
            {
                for (auto k : j->data)
                {
                    cout << k << " ";
                }
            }
            cout << "\n";
        }
        // inputs tensor
        for (auto in : i->inputs)
        {
            cout << in->name << ": ";
            for (auto s : in->shape)
            {
                cout << s << " ";
            }
            cout << "\n Address:" << in->address << " Size:" << in->original_size << endl;
            cout << endl;
        }
        // outputs tensor
        for (auto in : i->outputs)
        {
            cout << in->name << ": ";
            for (auto s : in->shape)
            {
                cout << s << " ";
            }
            cout << "\n Address:" << in->address << " Size:" << in->original_size << endl;
            cout << endl;
        }
    }

    cout << "test strategy--------------------------------\n";
    for (auto &i : strategy->splitSize)
    {
        for (auto &j : i)
        {
            cout << j << " ";
        }
        cout << "\n";
    }
    cout << strategy->mappingStrategy << "\n";

#endif
    cout << "test hardware config ---------------------------\n";
    auto hardware = j.getHardwareInfo();
    auto PE_Num = hardware["PE_Num"];
    auto LocalMem = hardware["LocalMem"] * 1000;
    cout << "PE = " << hardware["PE_Num"] << "\n";
    cout << "LocalMem = " << hardware["LocalMem"] << "\n";

    // init pe class ------------------------------------------------------
    PEGrid *peGrid = new PEGrid(PE_Num, LocalMem);

    // traffic generator---------------------------------------------------
    TrafficGenerator *trafficGenerator;

    // --------------------------------------------------------------------
    // multiple operators
    if (x->nodes.size() > 1)
    {
        // conv + batchnorm + relu
        if (x->nodes.size() == 3)
        {
            cout << "analysis conv & batchnorm & relu\n";

            // change input nodes, insert batchnorm nodes
            for (int i = 1; i < x->nodes[1]->inputs.size(); i++)
            {
                x->nodes[0]->inputs.push_back(x->nodes[1]->inputs[i]);
            }
            // change output nodes
            x->nodes[0]->outputs.clear();
            auto relu_output = x->nodes[1]->outputs[0];
            x->nodes[0]->outputs.push_back(relu_output);
        }
        else if (x->nodes.size() == 2)
        {
            // conv + batchnorm ------------------------------------------
            if (x->nodes[1]->op == Operator::BATCHNORMAL)
            {
                cout << "analysis conv & batchnorm\n";

                // change input nodes, insert batchnorm nodes
                for (int i = 1; i < x->nodes[1]->inputs.size(); i++)
                {
                    x->nodes[0]->inputs.push_back(x->nodes[1]->inputs[i]);
                }
                // change output nodes
                x->nodes[0]->outputs.clear();
                auto relu_output = x->nodes[1]->outputs[0];
                x->nodes[0]->outputs.push_back(relu_output);
            }
            // conv + relu ------------------------------------------------
            else if (x->nodes[1]->op == Operator::RELU)
            {
                cout << "analysis conv & relu\n";
                auto relu_output = x->nodes[1]->outputs[0];
                x->nodes[0]->outputs.clear();
                x->nodes[0]->outputs.push_back(relu_output);
            }
        }
    }

    // node
    Node *node = x->nodes[0];
    Node baseNode = *(x->nodes[0]);
    Node splitNode(baseNode); // copy of node

    Node *split_node = &splitNode;

    if (node->op == Operator::CONV && node->inputs.size() <= 3)
    {
        cout << "-------------CONV op\n";

        // workload analysis
        Conv *workload = new Conv();
        workload->init(node, split_node, *strategy);
        workload->compute_original_size();
        workload->split();
        long long memory_requirement = workload->computeSize();
#ifdef DEBUG
        workload->print();
#endif
        int num_subgraph = get_num_subgraph(*strategy);
        cout << "num_subgraph = " << num_subgraph << endl;

        if (peGrid->isRunnable(memory_requirement))
        {
            std::cout << "runnable\n";

            if (strategy->mappingStrategy == "weight")
            {
                // generate traffic pattern file
                trafficGenerator = new TrafficGenerator(PE_Num, num_subgraph, *split_node, baseNode);
                trafficGenerator->init_strategy(*strategy);
#ifdef TRAFFIC_OPTIMIZE
                cout << "weight traffic reduction\n";
                trafficGenerator->generate_traffic_conv_weight_reduction();
#else
                trafficGenerator->generate_traffic_conv_weight_stationary();
#endif
            }
            else if (strategy->mappingStrategy == "output")
            {
                // generate traffic pattern file
                trafficGenerator = new TrafficGenerator(PE_Num, num_subgraph, *split_node, baseNode);
                trafficGenerator->init_strategy(*strategy);

#ifdef TRAFFIC_OPTIMIZE
                cout << "output traffic reduction\n";
                trafficGenerator->generate_traffic_conv_output_reduction();
#else
                cout << "output traffic no reduction\n";
                trafficGenerator->generate_traffic_conv_output_stationary();
#endif
            }
        }
        else
        {
            std::cout << "not runnable\n";
        }
        delete workload;
    }

    // Conv + batchnorm, Conv + batchnorm + relu
    else if (node->op == Operator::CONV && node->inputs.size() > 3)
    {
        cout << "-------------CONV fuse --------------\n";

        // workload
        ConvBatchnorm *workload = new ConvBatchnorm();
        workload->init(node, split_node, *strategy);
        workload->compute_original_size();
        workload->split();
        long long memory_requirement = workload->computeSize();
#ifdef DEBUG
        workload->print();
#endif

        if (peGrid->isRunnable(memory_requirement))
        {
            std::cout << "runnable\n";

            if (strategy->mappingStrategy == "weight")
            {
                // generate traffic pattern file
                trafficGenerator = new TrafficGenerator(PE_Num, 1, *split_node, baseNode);
                trafficGenerator->init_strategy(*strategy);
                trafficGenerator->generate_traffic_conv_batchnorm_weight();
                // trafficGenerator->generate_traffic_conv_weight_stationary();

                // #ifdef TRAFFIC_OPTIMIZE
                //                 trafficGenerator->generate_traffic_conv_weight_reduction();
                // #else
                //                 trafficGenerator->generate_traffic_conv_weight_stationary();
                // #endif

                cout << trafficGenerator->trafficList.size() << endl;
            }
            else if (strategy->mappingStrategy == "output")
            {
                // generate traffic pattern file
                trafficGenerator = new TrafficGenerator(PE_Num, 1, *split_node, baseNode);
                trafficGenerator->init_strategy(*strategy);

                trafficGenerator->generate_traffic_conv_batchnorm_output();

                // #ifdef TRAFFIC_OPTIMIZE
                //                 trafficGenerator->generate_traffic_conv_output_reduction();
                // #else
                //                 trafficGenerator->generate_traffic_conv_output_stationary();
                // #endif
                // trafficGenerator->generate_traffic_conv_output_reduction();
            }
        }

        delete workload;
    }
    else if (node->op == Operator::BATCHNORMAL)
    {
        cout << "BATCHNORMAL op\n";
        // Node *split_node = node;

        // workload analysis
        Batchnorm *workload = new Batchnorm();
        workload->init(node, split_node, *strategy);
        workload->compute_original_size();
        workload->split();
        long long memory_requirement = workload->computeSize();
#ifdef DEBUG
        workload->print();
#endif

        int num_subgraph = get_num_subgraph(*strategy);
        cout << "num_subgraph = " << num_subgraph << endl;

        if (peGrid->isRunnable(memory_requirement))
        {
            std::cout << "runnable\n";
            // number of round
            auto numRound = peGrid->numRound(num_subgraph);
            int round = numRound.first;
            int remainder = numRound.second;

            std::cout << "round = " << round << std::endl;
            std::cout << "remainder = " << remainder << std::endl;

            // generate traffic pattern file
            trafficGenerator = new TrafficGenerator(PE_Num, num_subgraph, *split_node, baseNode);
            trafficGenerator->init_strategy(*strategy);

#ifdef TRAFFIC_OPTIMIZE
            trafficGenerator->generate_traffic_batchnorm_reduction();
#else
            trafficGenerator->generate_traffic_batchnorm();
#endif

            // trafficGenerator->generate_traffic_batchnorm();
            // trafficGenerator->generate_traffic_batchnorm_reduction();
        }
        else
        {
            std::cout << "not runnable\n";
        }
        delete workload;
    }

    else if (node->op == Operator::RELU)
    {
        cout << "RELU op\n";

        // workload analysis
        Relu *workload = new Relu();
        workload->init(node, split_node, *strategy);
        workload->split();
        long long memory_requirement = workload->computeSize();
#ifdef DEBUG
        workload->print();
#endif

        int num_subgraph = get_num_subgraph(*strategy);
        cout << "num_subgraph = " << num_subgraph << endl;

        if (peGrid->isRunnable(memory_requirement))
        {
            std::cout << "runnable\n";
            // number of round
            auto numRound = peGrid->numRound(num_subgraph);
            int round = numRound.first;
            int remainder = numRound.second;

            std::cout << "round = " << round << std::endl;
            std::cout << "remainder = " << remainder << std::endl;

            // generate traffic pattern file
            trafficGenerator = new TrafficGenerator(PE_Num, num_subgraph, *split_node, baseNode);
            trafficGenerator->generate_traffic_element_wise();
        }
        else
        {
            std::cout << "not runnable\n";
        }
        delete workload;
    }
    else if (node->op == Operator::MAXPOOL)
    {
        cout << "MAXPOOL op\n";
        // workload analysis
        MaxPool *workload = new MaxPool();
        workload->init(node, split_node, *strategy);
        workload->split();
        long long memory_requirement = workload->computeSize();
#ifdef DEBUG
        workload->print();
#endif

        int num_subgraph = get_num_subgraph(*strategy);
        cout << "num_subgraph = " << num_subgraph << endl;

        if (peGrid->isRunnable(memory_requirement))
        {
            std::cout << "runnable\n";
            // number of round
            auto numRound = peGrid->numRound(num_subgraph);
            int round = numRound.first;
            int remainder = numRound.second;

            std::cout << "round = " << round << std::endl;
            std::cout << "remainder = " << remainder << std::endl;

            // generate traffic pattern file
            trafficGenerator = new TrafficGenerator(PE_Num, num_subgraph, *split_node, baseNode);
            trafficGenerator->generate_traffic_element_wise();
        }
        else
        {
            std::cout << "not runnable\n";
        }

        delete workload;
    }

    else if (node->op == Operator::AVGPOOL)
    {
        cout << "AVGPOOL op\n";

        // workload analysis
        AvgPool *workload = new AvgPool();
        workload->init(node, split_node, *strategy);
        workload->split();
        long long memory_requirement = workload->computeSize();
#ifdef DEBUG
        workload->print();
#endif
        int num_subgraph = get_num_subgraph(*strategy);
        cout << "num_subgraph = " << num_subgraph << endl;

        if (peGrid->isRunnable(memory_requirement))
        {
            std::cout << "runnable\n";
            // number of round
            auto numRound = peGrid->numRound(num_subgraph);
            int round = numRound.first;
            int remainder = numRound.second;

            std::cout << "round = " << round << std::endl;
            std::cout << "remainder = " << remainder << std::endl;

            // generate traffic pattern file
            trafficGenerator = new TrafficGenerator(PE_Num, num_subgraph, *split_node, baseNode);
            trafficGenerator->generate_traffic_element_wise();
        }
        else
        {
            std::cout << "not runnable\n";
        }

        delete workload;
    }
    else
    {
        cout << "Do not support Operator\n";
        return 1;
    }

    cout << "traffic list = " << trafficGenerator->trafficList.size() << endl;

    // --------------------------------------------------------------------------
    // json file ----------------------------------------------------------------
    json jsonArray = json::array();
    for (auto &i : trafficGenerator->trafficList)
    {
        // debug broadcast read
        if ((int)i.type == 1 && (int)i.request == 0 && (int)i.response == 2)
        {
            cout << "---------------------------\n";
            cout << "broadcast write !!!\n";
            for (auto &j : strategy->splitSize)
            {
                for (auto &k : j)
                {
                    cout << k << " ";
                }
                cout << "\n";
            }
            cout << strategy->mappingStrategy << "\n";
        }
        // debug broadcast read

        json obj = json({});
        obj["type"] = (int)i.type;
        obj["src"] = to_string(i.src.first) + "," + to_string(i.src.second);
        obj["dest"] = to_string(i.dest.first) + "," + to_string(i.dest.second);
        obj["addr"] = i.addr;
        obj["size"] = i.size;
        obj["request"] = (int)i.request;
        obj["response"] = (int)i.response;

        jsonArray.push_back(obj);
    }
    // cout<<jsonArray.dump();

    std::ofstream o("../files/Traffic_Pattern/traffic_pattern.json");
    o << std::setw(4) << jsonArray << std::endl;

    // free memory ------------------------------------------
    delete x;
    delete strategy;
    delete node;
    // delete split_node;
    delete trafficGenerator;
    delete peGrid;
}

#endif
