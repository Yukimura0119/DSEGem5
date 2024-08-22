#ifndef _UTIL_HPP_
#define _UTIL_HPP_

#include "./graph.hpp"
#include "./strategy.hpp"
#include "./include.hpp"

int get_num_subgraph(Strategy& strategy)
{
    int num_subgraph = 1;

    if(strategy.splitSize.size() == 2)
    {
        num_subgraph *= strategy.splitSize[0][2];
        num_subgraph *= strategy.splitSize[0][3];
        for(auto& i:strategy.splitSize[1])
            num_subgraph *= i;
    }
    else
    {
        for(auto& i:strategy.splitSize[0])
            num_subgraph *= i;
    }
    return num_subgraph;
}

#endif