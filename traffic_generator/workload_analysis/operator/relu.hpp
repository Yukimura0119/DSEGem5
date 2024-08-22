#ifndef _RELU_HPP_
#define _RELU_HPP_

#include "./workload.hpp"

class Relu : public Workload
{
public:
    Relu()
    {
        // std::cout << "Relu constructor\n";
    }

    virtual ~Relu()
    {
        // std::cout << "Relu destructor\n";
    }
};

#endif