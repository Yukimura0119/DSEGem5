#ifndef __USER_DEFINED_TRAFFIC_PATTERNS_HH__
#define __USER_DEFINED_TRAFFIC_PATTERNS_HH__

#include <string>
#include <sstream>

enum class TrafficRequestType {
    READ    = 0,      // Fetch data from downstream
    WRITE   = 1,      // Write back data to downstream
    COMPUTE = 2,      // PE computation, not the traffic
    SYNC    = 3
};

enum class TrafficType {
    UNICAST   = 0,
    MULTICAST = 1,  
    BROADCAST = 2
};

struct Traffic{
    TrafficRequestType type;
    std::pair<int, int> src;     // <0, 0>
    std::pair<int, int> dest;    // <1, 1>
    uint64_t addr;    
    uint64_t size;
    TrafficType request;         // Traffic type of request to NoC
    TrafficType response;        // Traffic type of response from NoC

    Traffic()
    { }

    Traffic(TrafficRequestType _type,
            std::pair<int, int> _src,
            std::pair<int, int> _dest,
            uint64_t _addr, uint64_t _size,
            TrafficType _request, TrafficType _response)
          : type(_type), src(_src), dest(_dest),
            addr(_addr), size(_size),
            request(_request), response(_response)
    { }

    std::string toString() const
    {
        std::string str = "";

        str += "type: ";
        switch (type) {
            case (TrafficRequestType::READ):    str += "read\t"; break;
            case (TrafficRequestType::WRITE):   str += "write\t"; break;
            case (TrafficRequestType::COMPUTE): str += "compute\t"; break;
            case (TrafficRequestType::SYNC):    str += "sync\t"; break;
        }

        str += ",src(" + std::to_string(src.first) + "," + std::to_string(src.second) + ")";
        
        str += ",\tdest(" + std::to_string(dest.first) + "," + std::to_string(dest.second) + ")";
        
        std::ostringstream ss;
        ss << "0x" << std::hex << addr;
        str += ",\taddr: " + ss.str();

        str += ",\tsize: " + std::to_string(size);

        str += ",\treuest: ";
        switch (request) {
            case (TrafficType::UNICAST):   str += "uni-cast"; break;
            case (TrafficType::MULTICAST): str += "multi-cast"; break;
            case (TrafficType::BROADCAST): str += "broad-cast"; break;
        }

        str += ",\tresponse: ";
        switch (response) {
            case (TrafficType::UNICAST):   str += "uni-cast"; break;
            case (TrafficType::MULTICAST): str += "multi-cast"; break;
            case (TrafficType::BROADCAST): str += "broad-cast"; break;
        }

        str += '\n';

        return str;
    }
};

#endif