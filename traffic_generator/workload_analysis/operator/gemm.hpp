#ifndef _GEMM_HPP_
#define _GEMM_HPP_

#include "../include.hpp"
#include "./workload.hpp"

class GEMM: public Workload{
    GEMM()
    {
        std::cout << "\nGEMM constructor-------------------\n";
    }

    ~GEMM()
    {
        std::cout << "\nGEMM destructor-------------------\n";
    }

    void split();
};

void GEMM::split()
{
    // split k

    // split n
}

#endif
