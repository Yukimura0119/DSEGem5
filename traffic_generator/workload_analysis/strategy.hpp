#ifndef _STRATEGY_HPP_
#define _STRATEGY_HPP_
#include "include.hpp"

struct Strategy{
    std::vector<std::vector<int>> splitSize; // e.g. {{1, 2, 2, 2}, {1, 2, 2, 2}}
    string mappingStrategy; // weight or output stationary
};

#endif