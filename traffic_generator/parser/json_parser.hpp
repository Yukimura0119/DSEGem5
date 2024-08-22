#pragma once
#include "../workload_analysis/graph.hpp"
#include "../workload_analysis/strategy.hpp"
#include "json.hpp"
#include <fstream>
#include <vector>

using json = nlohmann::json;

class JsonParser
{
private:
    std::ifstream f = {};
    json m_config = {};
    std::string m_layout = "";
    std::string m_name = "";
    std::string m_mapping = "";
    std::unordered_map<std::string, int> m_hardwareInfo = {};
    Graph *m_model;
    Strategy *strategy;

    Operator getOpType(std::string type)
    {
        if (type == "Conv")
            return Operator::CONV;
        else if (type == "Gemm")
            return Operator::GEMM;
        else if (type == "Relu")
            return Operator::RELU;
        else if (type == "MaxPool")
            return Operator::MAXPOOL;
        else if (type == "BatchNormalization")
            return Operator::BATCHNORMAL;
        else if (type == "SoftMax")
            return Operator::SOFTMAX;
        else if (type == "Reshape")
            return Operator::RESHPAE;
        else if (type == "GlobalAveragePool")
            return Operator::AVGPOOL;
    }

    void preprocessing()
    {
        m_layout = m_config["Layout"];
        m_name = m_config["Name"];

        // mapping
        m_mapping = m_config["Mapping"];
        strategy->mappingStrategy = m_mapping;

        // split
        auto split = m_config["Split"];
        for (json::iterator it = split.begin(); it != split.end(); ++it)
        {
            auto splitSize = it.value();
            vector<int> shape;
            for (auto i : splitSize)
            {
                shape.push_back(i);
            }
            strategy->splitSize.push_back(shape);
        }

        // hardware info
        for (auto &[key, val] : m_config["HardwareInfo"].items())
        {
            m_hardwareInfo[key] = val;
        }

        int id = 0;
        for (auto layers : m_config["Model"])
        {
            // name
            string name = layers["name"];
            // id
            int id = layers["id"];
            // op_type
            Operator op_type = getOpType(layers["op_type"]);

            Node *node = new Node(id, name, op_type);

            // attribute
            std::map<std::string, pair<int, int>> tensor_addr;
            auto attributes = layers["attribute"];
            for (auto attr : attributes)
            {
                // for (json::iterator it = attr.begin(); it != attr.end(); ++it)
                // {
                //     std::cout << it.key() << " : " << it.value() << "\n";
                // }
                if (attr.find("address") == attr.end())
                {
                    auto name = attr["name"];
                    auto type = attr["type"];
                    vector<int> val;
                    if (name == "kernel_shape" || name == "pads" || name == "strides")
                    {
                        for (auto v : attr["ints"])
                            val.push_back(v);
                    }
                    // NodeAttribute *attribute = new NodeAttribute(name, type, val);
                    // node->attributes.push_back(attribute);
                }
                else
                {
                    uint64_t size, addr;
                    string key;
                    auto it = attr.begin();
                    for (int i = 0; i < attr.size(); i++, it++)
                    {
                        if (i == 0)
                            addr = *it;
                        else if (i == 1)
                            key = *it;
                        else
                            size = *it;
                    }
                    tensor_addr[key] = make_pair(addr, size);
                }
            }

            // input tensor----------------------------
            std::map<string, int> tensor_name;
            auto inputs = layers["input_tensor"];
            for (auto j : inputs)
            {
                auto type = j["type"];
                vector<int> shape;
                for (auto s : type["shape"])
                {
                    shape.push_back(s);
                }
                tensor_name[j["name"]] = 1;
                Tensor *tensor = new Tensor(j["name"], shape, type["elem_type"]);
                node->inputs.push_back(tensor);
            }

            // output tensor---------------------------
            auto output = layers["output_tensor"];
            auto type = output["type"];
            vector<int> shape;
            for (auto s : type["shape"])
            {
                shape.push_back(s);
            }
            tensor_name[output["name"]] = 2;
            Tensor *tensor = new Tensor(output["name"], shape, type["elem_type"]);
            node->outputs.push_back(tensor);

            // attribute
            // auto attributes = layers["attribute"];
            for (auto attr : attributes)
            {
                // for (json::iterator it = attr.begin(); it != attr.end(); ++it)
                // {
                //     std::cout << it.key() << " : " << it.value() << "\n";
                // }
                auto name = attr["name"];
                if (tensor_name.find(name) != tensor_name.end())
                {
                    if (tensor_name[name] == 1)
                    {
                        for (auto &i : node->inputs)
                        {
                            if (i->name == name)
                            {
                                i->address = attr["ints"][0];
                                i->original_size = attr["ints"][1];
                            }
                        }
                    }
                    else if (tensor_name[name] == 2)
                    {
                        for (auto &i : node->outputs)
                        {
                            if (i->name == name)
                            {
                                i->address = attr["ints"][0];
                                i->original_size = attr["ints"][1];
                            }
                        }
                    }
                }
                else
                {
                    auto type = attr["type"];
                    vector<int> val;
                    if (name == "kernel_shape" || name == "pads" || name == "strides")
                    {
                        for (auto v : attr["ints"])
                            val.push_back(v);
                    }
                    NodeAttribute *attribute = new NodeAttribute(name, type, val);
                    node->attributes.push_back(attribute);
                }
            }

            m_model->nodes.push_back(node);
        }
    }

public:
    JsonParser(std::string filename)
        : f(filename)
    {
        m_config = json::parse(f);
        m_model = new Graph();
        strategy = new Strategy();
        preprocessing();
    }

    std::string getTensorLayout()
    {
        return m_config["Layout"];
    }

    std::string getModelName()
    {
        return m_config["Name"];
    }

    std::string getMapping()
    {
        return m_config["Mapping"];
    }
    Graph *getModel()
    {
        return m_model;
    }
    Strategy *getStrategy()
    {
        return strategy;
    }
    unordered_map<std::string, int> getHardwareInfo()
    {
        return m_hardwareInfo;
    }
};
