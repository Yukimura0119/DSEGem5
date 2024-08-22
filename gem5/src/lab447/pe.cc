#include "params/PE.hh"
#include "lab447/pe.hh"

#include "base/intmath.hh"
#include "base/trace.hh"
#include "debug/Checkpoint.hh"
#include "debug/PE.hh"
#include "enums/AddrMap.hh"
#include "sim/sim_exit.hh"
#include "sim/stats.hh"
#include "sim/system.hh"
#include "sim/sim_exit.hh"

#include "base/logging.hh"

#include "nlohmann/json.hpp"

#include <iostream>
#include <algorithm>
#include <string>
#include <fstream>
#include <cstdlib>

#include <filesystem>
namespace fs = std::filesystem;

using json = nlohmann::json;

namespace gem5
{

/**
 * static list of all PEGens, used for initialization etc.
*/
PE::PEList PE::pe_list;
PE::rdySyncList PE::rdy_sync_list;
PEPtr PE::broadcast_issuer = nullptr;

PE::PE(const PEParams &p)
    : ClockedObject(p),
      system(p.system),
      requestorId(system->getRequestorId(this)),
      block_size(p.block_size), cache_line_size(system->cacheLineSize()),
      operateNextEvent([this]{ operateTraffic(); }, name()),
      scheduleReqEvent([this]{ scheduleReq(); }, name()),
      port(name() + ".port", *this),
      retryPktTick(0),
      stats(this),
      cur_traffic(0),
      global_mem_size(p.global_mem_size), local_mem_offset(p.local_mem_offset)
{
    DPRINTF(PE, "%s: name: %s, requestorId id: %d, block size: %lu, cache line size: %lu\n",
                __func__, name(), requestorId, block_size, cache_line_size);
    DPRINTF(PE, "%s: port: %s, current traffic: %u, global memory size: %lu, local memory offset %lu\n",
                 __func__, port.name(), cur_traffic, global_mem_size, local_mem_offset);

    x = (pe_list.size()) / p.grid_width;
    y = (pe_list.size()) % p.grid_width;

    DPRINTF(PE, "%s: x: %u, y: %u\n", __func__, x, y);

    pe_list.insert(std::make_pair(getCoordinate(), this));
}

PE::~PE()
{
    DPRINTF(PE, "%s\n", __func__);
}

Port &
PE::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "port")
        return port;
    else
        return ClockedObject::getPort(if_name, idx);

}

void
PE::init()
{
    ClockedObject::init();

    if (!port.isConnected())
        fatal("The port of %s is not connected!\n", name());
}

PacketPtr
PE::getPacket(Addr addr, unsigned size, const MemCmd& cmd,
              Request::FlagsType flags)
{
    // Create new request
    RequestPtr req = std::make_shared<Request>(addr, size, flags,
                                               requestorId);
    // Dummy PC to have PC-based prefetchers latch on; get entropy into higher
    // bits
    req->setPC(((Addr)requestorId) << 2);

    // Embed it in a packet
    PacketPtr pkt = new Packet(req, cmd);

    uint8_t* pkt_data = new uint8_t[req->getSize()];
    pkt->dataDynamic(pkt_data);

    if (cmd.isWrite()) {
        std::fill_n(pkt_data, req->getSize(), (uint8_t)requestorId);
    }

    return pkt;
}

void
PE::recvReqRetry()
{
    DPRINTF(PE, "%s: Received retry\n", __func__);
    stats.numRetries++;
    retryReq();
}

void
PE::retryReq()
{
    assert(!waitingSend_read.empty() || !waitingSend_write.empty());

    DPRINTF(PE, "%s: Remain %u read packet(s) and %u write packet(s) waiting for retry\n", 
                __func__, waitingSend_read.size(), waitingSend_write.size());

    schedule(scheduleReqEvent, curTick() + 1);
}

bool
PE::recvTimingResp(PacketPtr pkt)
{
    std::unordered_map<RequestPtr, Tick> &waitingResp = pkt->isRead() ? waitingResp_read : waitingResp_write;

    DPRINTF(PE, "%s: Receive response at tick %ld, pkt: addr=0x%x, size=%lu, type=%c\n", 
                __func__, curTick(), pkt->getAddr(), pkt->getSize(), pkt->isRead() ? 'r' : 'w');

    auto iter = waitingResp.find(pkt->req);

    panic_if(iter == waitingResp.end(), "%s: "
                "Received unexpected response [%s reqPtr=%x]\n",
                __func__, pkt->print(), pkt->req);

    assert(iter->second <= curTick());

    if (pkt->isWrite()) {
        ++stats.totalWrites;
        stats.bytesWritten += pkt->req->getSize();
        stats.totalWriteLatency += curTick() - iter->second;

        waitingResp.erase(iter);
    } else {
        ++stats.totalReads;
        stats.bytesRead += pkt->req->getSize();
        stats.totalReadLatency += curTick() - iter->second;

        waitingResp.erase(iter);

        if(waitingSend_read.empty() && waitingResp.empty() &&
           !rdy_sync_list.count(this)) {
            DPRINTF(PE, "%s: Got last read response, schedule operateNextEvent at next tick\n", __func__);
            schedule(operateNextEvent, curTick() + 1);
        } else {
            DPRINTF(PE, "%s: Got read response\n", __func__);
            if (!waitingSend_read.empty())
                DPRINTF(PE, "%s: Remain read packets to send\n", __func__);
            if (!waitingResp.empty())
                DPRINTF(PE, "%s: Remain read packets to receive\n", __func__);
            if (broadcast_issuer) {
                if (rdy_sync_list.size() == pe_list.size())
                    DPRINTF(PE, "%s: Brodcast issuer is sending pkts\n", __func__);
                else if (!rdy_sync_list.empty()) {
                    DPRINTF(PE, "%s: Brodcast issuer is waiting other receiver(s) operating sync\n", __func__);
                    DPRINTF(PE, "%s: Waiting for: \n", __func__);
                    for (const auto& iter : pe_list)
                        if (!rdy_sync_list.count(iter.second))
                            DPRINTF(PE, "%s: %s\n", __func__, iter.second->name());
                 } else {
                    DPRINTF(PE, "%s: No such condition = =\n", __func__);
                }
            }
            if (!broadcast_issuer) {
                if (!rdy_sync_list.empty()) {
                    DPRINTF(PE, "%s: Waiting for broadcast issuer\n", __func__);
                    DPRINTF(PE, "%s: Current sync list: \n", __func__);
                    for (const auto& rdy_pe : rdy_sync_list)
                        DPRINTF(PE, "%s: %s\n", __func__, rdy_pe->name());
                }
                else {
                    DPRINTF(PE, "%s: No broacast is issued\n", __func__);
                }
            }
        }
    }

    delete pkt;
    if ((waitingResp_read.empty() && waitingSend_read.empty()) &&
        (waitingResp_write.empty() && waitingSend_write.empty()) &&
        ((!broadcast_issuer && rdy_sync_list.empty())) &&
        (cur_traffic >= traffic_list.size())) {

        DPRINTF(PE, "%s: PE: %s, All responses arrived\n", __func__, name());
        pe_list.erase(getCoordinate());
        if(pe_list.empty()) {
            exitSimLoop(name() + " has encountered the exit state and will "
                        "terminate the simulation.\n");
        }
    }

    DPRINTF(PE, "%s: Remain %u read packet(s) and %u write packet(s) to send\n", 
                __func__, waitingSend_read.size(), waitingSend_write.size());
    DPRINTF(PE, "%s: Remain %u read packet(s) and %u write packet(s) to receive\n", 
                __func__, waitingResp_read.size(), waitingResp_write.size());

    return true;
}

PE::StatGroup::StatGroup(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(numSuppressed, statistics::units::Count::get(),
               "Number of suppressed packets to non-memory space"),
      ADD_STAT(numPackets, statistics::units::Count::get(),
               "Number of packets generated"),
      ADD_STAT(numRetries, statistics::units::Count::get(), "Number of retries"),
      ADD_STAT(retryTicks, statistics::units::Tick::get(),
               "Time spent waiting due to back-pressure"),
      ADD_STAT(bytesRead, statistics::units::Byte::get(), "Number of bytes read"),
      ADD_STAT(bytesWritten, statistics::units::Byte::get(),
               "Number of bytes written"),
      ADD_STAT(totalReadLatency, statistics::units::Tick::get(),
               "Total latency of read requests"),
      ADD_STAT(totalWriteLatency, statistics::units::Tick::get(),
               "Total latency of write requests"),
      ADD_STAT(totalReads, statistics::units::Count::get(), "Total num of reads"),
      ADD_STAT(totalWrites, statistics::units::Count::get(), "Total num of writes"),
      ADD_STAT(avgReadLatency, statistics::units::Rate<
                    statistics::units::Tick, statistics::units::Count>::get(),
               "Avg latency of read requests", totalReadLatency / totalReads),
      ADD_STAT(avgWriteLatency, statistics::units::Rate<
                    statistics::units::Tick, statistics::units::Count>::get(),
               "Avg latency of write requests",
               totalWriteLatency / totalWrites),
      ADD_STAT(readBW, statistics::units::Rate<
                    statistics::units::Byte, statistics::units::Second>::get(),
               "Read bandwidth", bytesRead / simSeconds),
      ADD_STAT(writeBW, statistics::units::Rate<
                    statistics::units::Byte, statistics::units::Second>::get(),
               "Write bandwidth", bytesWritten / simSeconds)
{
}

void
PE::scheduleReq()
{
    std::queue<PacketPtr> &waitingSend = waitingSend_write.empty() ? waitingSend_read : waitingSend_write;

    assert(!waitingSend.empty());

    PacketPtr pkt = waitingSend.front();

    std::unordered_map<RequestPtr, Tick> &waitingResp = pkt->isRead() ? waitingResp_read : waitingResp_write;

    if (pkt && system->isMemAddr(pkt->getAddr())) {
        stats.numPackets++;

        if (port.sendTimingReq(pkt)) {
            DPRINTF(PE, "%s: Succeed to send pkt: %c to addr 0x%x, size %d\n",
                        __func__, pkt->isRead() ? 'r' : 'w', pkt->getAddr(), pkt->getSize());

            waitingSend.pop();
            if (pkt->req->isBroadcast()) {
                for (const auto& iter : pe_list)
                    iter.second->waitingResp_read[pkt->req] = curTick();
            }else
                waitingResp[pkt->req] = curTick();

            if (retryPktTick) {
                stats.retryTicks += curTick() - retryPktTick;
                retryPktTick = 0;
            }

            if (waitingSend.empty()) {
                if (waitingResp_read.empty()) {
                    // All write requests are sent, opearte next traffic
                    DPRINTF(PE, "%s all write packets are sent, schedule operateNextEvent\n", __func__);
                    schedule(operateNextEvent, curTick() + 1);
                } else if (broadcast_issuer && (broadcast_issuer == this)) {
                    broadcast_issuer = nullptr;
                    rdy_sync_list.clear();
                    DPRINTF(PE, "%s all broadcast packets are sent\n", __func__);
                } else {
                    // Read requests have to wait for all read response arrived  
                    if (!broadcast_issuer)
                        DPRINTF(PE, "%s all packets are sent, no broadcast issuer\n", __func__);
                    else
                        DPRINTF(PE, "%s all packets are sent, broadcast issuer is not this\n", __func__);
                }
            } else
                schedule(scheduleReqEvent, curTick() + 1);
        } else {
            // Port is busy, no need to schedule event, receiver will call retry()
            DPRINTF(PE, "%s: Failed to send pkt: %c to addr 0x%x, size %d\n",
                        __func__, pkt->isRead() ? 'r' : 'w', pkt->getAddr(), pkt->getSize());
            retryPktTick = curTick();
        }
    } else if (pkt) {
        // Invalid memory address
        DPRINTF(PE, "%s: Suppressed packet %s 0x%x\n",
                    __func__, pkt->cmdString(), pkt->getAddr());

        ++stats.numSuppressed;
        if (!(static_cast<int>(stats.numSuppressed.value()) % 10000))
            warn("%s suppressed %d packets with non-memory addresses\n",
                    name(), stats.numSuppressed.value());

        delete pkt;
        pkt = nullptr;

        if (waitingSend.empty()) {
            if (waitingResp_read.empty()) {
                schedule(operateNextEvent, curTick() + 1);
                DPRINTF(PE, "%s all write packets are sent, schedule operateNextEvent\n", __func__);
            } if (broadcast_issuer && (broadcast_issuer == this)) {
                broadcast_issuer = nullptr;
                rdy_sync_list.clear();
                DPRINTF(PE, "%s all broadcast packets are sent\n", __func__);
            } else {
                // Read requests have to wait for all read response arrived  
                if (!broadcast_issuer)
                    DPRINTF(PE, "%s all packets are sent, no broadcast issuer\n", __func__);
                else
                    DPRINTF(PE, "%s all packets are sent, broadcast issuer is not this\n", __func__);
            }       
             
        } else
            schedule(scheduleReqEvent, curTick() + 1);
    }

    DPRINTF(PE, "%s: Remain %u read packet(s) and %u write packet(s) to sent\n", 
                __func__, waitingSend_read.size(), waitingSend_write.size());
}

void 
PE::parseTraffic(const std::string fpath)
{
    std::ifstream f(fpath.c_str());
    Addr addr;

    panic_if (!f.good(), "Json file `%s` not found\n", fpath.c_str());
    
    json data = json::parse(f);

    for(const auto& traffic : data) {            
        auto iter = pe_list.find(std::string(traffic["src"]));
        panic_if (iter == pe_list.end(), "%s: Can't find pe(%s)\n", __func__, std::string(traffic["src"]));

        addr = traffic["addr"].get<Addr>();
        // For ITRI local memory arch 
        addr = addr >= global_mem_size ? addr + local_mem_offset : addr;

        iter->second->traffic_list.emplace_back(std::make_shared<Traffic>(TrafficRequestType(traffic["type"].get<int>()), 
                                                                          std::make_pair(traffic["src"].get<std::string>()[0] - '0', traffic["src"].get<std::string>()[2] - '0'),
                                                                          std::make_pair(traffic["dest"].get<std::string>()[0] - '0', traffic["dest"].get<std::string>()[2] - '0'),
                                                                          addr,
                                                                          traffic["size"].get<uint64_t>(),
                                                                          TrafficType(traffic["request"].get<int>()),
                                                                          TrafficType(traffic["response"].get<int>())));
    }

    for (const auto& it : pe_list) {
        DPRINTF(PE, "PE::parseTraffic(): src(%s), total %u traffic:\n", it.first, it.second->traffic_list.size());
        for (const auto& traffic : it.second->traffic_list) {
            DPRINTF(PE, "  %s", traffic->toString());
        }
    }
}

Tick
PE::getComputeTime()
{
    // TODO  construct lookup table and return compute time according to table
    return 100;
}

void
PE::operateTraffic()
{
    if(cur_traffic >= traffic_list.size() ) {
        /* All traffic has been operated, doing nothing */
        DPRINTF(PE, "%s: %s, all traffic have been opearted\n", __func__, name());

        if ((waitingResp_read.empty() && waitingSend_read.empty()) &&
            (waitingResp_write.empty() && waitingSend_write.empty()) &&
            ((!broadcast_issuer && rdy_sync_list.empty()))) {
            pe_list.erase(getCoordinate());
            if (pe_list.empty()) {
                exitSimLoop(name() + " has encountered the exit state and will "
                            "terminate the simulation.\n");
            }
        }
    } else {
        bool isRead    = traffic_list[cur_traffic]->type == TrafficRequestType::READ;
        bool isCompute = traffic_list[cur_traffic]->type == TrafficRequestType::COMPUTE;
        bool isSync    = traffic_list[cur_traffic]->type == TrafficRequestType::SYNC;

        if (isCompute) {
            DPRINTF(PE, "%s: Compute for %ld ticks, schedule operateNextEvent\n", __func__, getComputeTime());
            schedule(operateNextEvent, curTick() + getComputeTime());
        } else if (isSync) {
            DPRINTF(PE, "%s: Sync\n", __func__);
            rdy_sync_list.insert(this);
            if (rdy_sync_list.size() == pe_list.size()) {
                assert(broadcast_issuer);
                broadcast_issuer->sendBroadcast();
            } else {
                DPRINTF(PE, "%s: Current sync list: \n", __func__);
                for (const auto& rdy_pe : rdy_sync_list)
                    DPRINTF(PE, "%s: %s\n", __func__, rdy_pe->name());
            }
        } else {
            DPRINTF(PE, "%s: issue %c traffic\n", __func__, isRead ? 'r' : 'w');
            Addr base_addr = traffic_list[cur_traffic]->addr;
            unsigned size  = traffic_list[cur_traffic]->size <= cache_line_size ? cache_line_size : traffic_list[cur_traffic]->size;
            MemCmd cmd     = isRead ? MemCmd::ReadReq : MemCmd::WriteReq;
            bool broadcast = traffic_list[cur_traffic]->response == TrafficType::BROADCAST;
            PacketPtr pkt;
            std::queue<PacketPtr> &waitingSend = isRead ? waitingSend_read : waitingSend_write;

            if (base_addr % cache_line_size) {
                size += base_addr % cache_line_size;
                base_addr -= base_addr % cache_line_size; 
            }

            for (int i=0; i<(size/cache_line_size); i++) {
                Addr addr     = base_addr + i * cache_line_size;
                pkt           = getPacket(addr, cache_line_size, cmd);
                if (broadcast)
                    pkt->req->setBroadcast();
                waitingSend.push(pkt);       
            }
            DPRINTF(PE, "%s: Got %u packet(s) of size %u from trafiic: %s\n", 
                        __func__, size/cache_line_size, cache_line_size, traffic_list[cur_traffic]->toString());

            if (broadcast) {
                waitSync();
            } else
                schedule(scheduleReqEvent, curTick() + 1);
        }

        cur_traffic++;
    }
}

void
PE::waitSync()
{
    broadcast_issuer = this;

    rdy_sync_list.insert(this);

    if (rdy_sync_list.size() == pe_list.size())
        sendBroadcast();
    else {
        DPRINTF(PE, "%s: Current sync list: \n", __func__);
        for (const auto& rdy_pe : rdy_sync_list)
            DPRINTF(PE, "%s: %s\n", __func__, rdy_pe->name());
    }
}

void
PE::sendBroadcast()
{
    DPRINTF(PE, "%s: start send broadcast requests\n", __func__);
    schedule(scheduleReqEvent, curTick() + 1);
}

void
PE::start()
{
    schedule(operateNextEvent, curTick() + 1);
}

} // namespace gem5