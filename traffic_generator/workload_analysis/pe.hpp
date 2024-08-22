#ifndef _PE_H_
#define _PE_H_

#include "include.hpp"

class PEGrid
{
public:
    int peNum;
    long long peMemory; // each pe remain memory (bytes)
    std::vector<long long> peMemArr;

    PEGrid(int peNum, long long memory)
        : peNum(peNum), peMemory(memory)
    {
        peMemArr.resize(peNum);
        std::fill(peMemArr.begin(), peMemArr.end(), memory);
    }

    bool isRunnable(long long subgraphMem);
    std::pair<int, int> numRound(int numSubgraph);
};

bool PEGrid::isRunnable(long long subgraphMem)
{   
    std::cout << "subgraphMem = " << subgraphMem << " bytes" << std::endl;
    std::cout << "peMemory = " << peMemory << " bytes" << std::endl;

    return true;

    if (subgraphMem <= peMemory)
        return true;
    else
        return false;
}

std::pair<int, int> PEGrid::numRound(int numSubgraph)
{
    // return number of round & remainder of subgraph
    return {std::ceil((double)numSubgraph / peNum), numSubgraph % peNum};
}

#endif