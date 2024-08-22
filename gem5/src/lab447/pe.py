from m5.params import *
from m5.proxy import *
from m5.SimObject import *
from m5.objects.ClockedObject import ClockedObject

class PE(ClockedObject):
    type = 'PE'
    cxx_header = "lab447/pe.hh"
    cxx_class = "gem5::PE"

    # System used to determine the mode of the memory system
    system           = Param.System(Parent.any, "System this generator is part of")

    # Port used for sending requests and receiving responses
    port             = RequestPort("This port sends requests and receives responses")

    block_size       = Param.UInt64(64, "Block size of memory")

    global_mem_size  = Param.UInt64(0x40000000, "Size of global memory")

    local_mem_offset = Param.UInt64(0x00000000, "Offset of local memory")

    grid_width       = Param.UInt64(4, "Grid width of system")

    # These additional parameters allow TrafficGen to be used with scripts
    # that expect a BaseCPU
    cpu_id = Param.Int(-1, "CPU identifier")
    socket_id = Param.Unsigned(0, "Physical Socket identifier")
    numThreads = Param.Unsigned(1, "number of HW thread contexts")

    @cxxMethod
    def start(self):
        pass

    @cxxMethod
    def parseTraffic(self, fpath):
        pass

    @classmethod
    def memory_mode(cls):
        return "timing"

    @classmethod
    def require_caches(cls):
        return False

    def createThreads(self):
        pass

    def createInterruptController(self):
        pass

    def connectCachedPorts(self, in_ports):
        if hasattr(self, "_cached_ports") and (len(self._cached_ports) > 0):
            for p in self._cached_ports:
                exec("self.%s = in_ports" % p)
        else:
            self.port = in_ports

    def connectAllPorts(self, cached_in, uncached_in, uncached_out):
        self.connectCachedPorts(cached_in)

    def connectBus(self, bus):
        self.connectAllPorts(
            bus.cpu_side_ports, bus.cpu_side_ports, bus.mem_side_ports
        )

    def addPrivateSplitL1Caches(self, ic, dc, iwc=None, dwc=None):
        self.dcache = dc
        self.port = dc.cpu_side
        self._cached_ports = ["dcache.mem_side"]
        self._uncached_ports = []
