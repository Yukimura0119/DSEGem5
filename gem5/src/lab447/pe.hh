#ifndef __LAB447_PE_HH__
#define __LAB447_PE_HH__

#include <cstdint>
#include <string>
#include <memory>
#include <tuple>
#include <unordered_map>
#include <queue>
#include <unordered_set>

#include "base/statistics.hh"
#include "enums/AddrMap.hh"
#include "mem/qport.hh"
#include "sim/clocked_object.hh"

#include "base/types.hh"
#include "mem/packet.hh"
#include "mem/request.hh"

#include "lab447/traffic_pattern.hh"

namespace gem5
{

class System;
struct PEParams;
class PE;
typedef PE *PEPtr;

class PE : public ClockedObject
{
  protected: // Params
    /**
     * The system used to determine which mode we are currently operating
     * in.
     */
    System *const system;

    /** The RequestorID used for generating requests */
    const RequestorID requestorId;

    /** The axis of this pe */
    uint32_t x, y;

    /** Blocksize and address increment */
    const Addr block_size;

    /** Cache line size in the simulated system */
    const Addr cache_line_size;

    /** For ITRI arch*/
    Addr global_mem_size;
    Addr local_mem_offset;

  public:
    PE(const PEParams &p);

    ~PE();

    Port &getPort(const std::string &if_name,
                  PortID idx=InvalidPortID) override;

    void init() override;

    std::string getCoordinate() { return std::to_string(x) + "," + std::to_string(y); };

    /** To parse traffic pattern json file and map to each pe */
    void parseTraffic(const std::string fpath);

    void start();

  private:

    typedef std::unordered_map<std::string, PEPtr> PEList;

    /** List of all instantiated PEs. */
    static PEList pe_list;

    /**
     * Generate a new request and associated packet
     *
     * @param addr Physical address to use
     * @param size Size of the request
     * @param cmd Memory command to send
     * @param flags Optional request flags
     */
    PacketPtr getPacket(Addr addr, unsigned size, const MemCmd& cmd,
                        Request::FlagsType flags = 0);
    /**
     * Receive a retry from the neighbouring port and attempt to
     * resend the waiting packet.
     */
    void recvReqRetry();

    void retryReq();

    /**
     * If a read response arrive, perform next opreation
    */
    bool recvTimingResp(PacketPtr pkt);

    void scheduleReq();

    Tick getComputeTime();

    /**
     * Check what current trafiic is, and then opearte corresponding actions
     * READ:    Send read request to memory hierachy
     * WRITE:   Send write request to memory hierachy
     * COMPUTE: Schedule compute event base on computational time
     */   
    void operateTraffic();

    /** Event for scheduling updates */
    EventFunctionWrapper operateNextEvent;
    EventFunctionWrapper scheduleReqEvent;

    /** Request port specialisation for the traffic generator */
    class PEPort : public RequestPort
    {
      public:

        PEPort(const std::string& name, PE& pe)
            : RequestPort(name, &pe), pe(pe)
        { }

      protected:

        void recvReqRetry() { pe.recvReqRetry(); }

        bool recvTimingResp(PacketPtr pkt)
        { return pe.recvTimingResp(pkt); }

        void recvTimingSnoopReq(PacketPtr pkt) { }

        void recvFunctionalSnoop(PacketPtr pkt) { }

        Tick recvAtomicSnoop(PacketPtr pkt) { return 0; }

      private:

        PE& pe;

    };

    /** The instance of request port used by the PE. */
    PEPort port;

    /** Packets waiting for being sent */
    std::queue<PacketPtr> waitingSend_read;
    std::queue<PacketPtr> waitingSend_write;
    
    Tick retryPktTick;

  protected: // Stats
    /** Reqs waiting for response **/
    std::unordered_map<RequestPtr, Tick> waitingResp_read;
    std::unordered_map<RequestPtr, Tick> waitingResp_write;

    struct StatGroup : public statistics::Group
    {
        StatGroup(statistics::Group *parent);

        /** Count the number of dropped requests. */
        statistics::Scalar numSuppressed;

        /** Count the number of generated packets. */
        statistics::Scalar numPackets;

        /** Count the number of retries. */
        statistics::Scalar numRetries;

        /** Count the time incurred from back-pressure. */
        statistics::Scalar retryTicks;

        /** Count the number of bytes read. */
        statistics::Scalar bytesRead;

        /** Count the number of bytes written. */
        statistics::Scalar bytesWritten;

        /** Total num of ticks read reqs took to complete  */
        statistics::Scalar totalReadLatency;

        /** Total num of ticks write reqs took to complete  */
        statistics::Scalar totalWriteLatency;

        /** Count the number reads. */
        statistics::Scalar totalReads;

        /** Count the number writes. */
        statistics::Scalar totalWrites;

        /** Avg num of ticks each read req took to complete  */
        statistics::Formula avgReadLatency;

        /** Avg num of ticks each write reqs took to complete  */
        statistics::Formula avgWriteLatency;

        /** Read bandwidth in bytes/s  */
        statistics::Formula readBW;

        /** Write bandwidth in bytes/s  */
        statistics::Formula writeBW;
    } stats;

  protected:
    std::vector<std::shared_ptr<Traffic>> traffic_list;
    uint32_t cur_traffic;

  private:
    typedef std::unordered_set<PEPtr> rdySyncList;
    static rdySyncList rdy_sync_list;
    static PEPtr broadcast_issuer;

    void waitSync();
    void sendBroadcast();
};

} // namespace gem5

#endif // __USER_LAB447_PE_HH__