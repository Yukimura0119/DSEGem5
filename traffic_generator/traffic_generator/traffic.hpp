#ifndef _TRAFFIC_HPP_
#define _TRAFFIC_HPP_

// #include "./include.hpp"

uint64_t addr;

enum class RequestType
{
    READ,   // Fetch data from downstream
    WRITE,  // Write back data to downstream
    COMPUTE, // PE computation, not the traffic
    SYNC    // for broadcast
};

enum class TrafficType
{
    UNICAST,
    MULTICAST,
    BROADCAST
};

struct Traffic
{
public:
    RequestType type;
    std::pair<int, int> src;  // <0, 0>
    std::pair<int, int> dest; // <1, 1>
    uint64_t addr;            
    uint64_t size;
    // std::string elements;      // {[i, j] : 0<= i <= 9 and 0 <= j <= 19}
    TrafficType request;  // Traffic type of request to NoC
    TrafficType response; // Traffic type of response from NoC

    Traffic(RequestType requestType, std::pair<int, int> src, std::pair<int, int> dest, uint64_t addr, uint64_t size, TrafficType request, TrafficType response)
        : type(requestType), addr(addr), src(src), dest(dest), size(size), request(request), response(response)
    {
    }
};

#endif