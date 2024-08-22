from ..abstract_cache_hierarchy import AbstractCacheHierarchy
from ..classic.abstract_classic_cache_hierarchy import AbstractClassicCacheHierarchy
from ..classic.caches.l1dcache import L1DCache
from ..classic.caches.l1icache import L1ICache
from ..classic.caches.mmu_cache import MMUCache
from ....isas import ISA

from m5.objects import Cache, BaseXBar, SystemXBar, BadAddr, Port

from ....utils.override import *

class Lab447PrivateL1CacheHierarchy(AbstractClassicCacheHierarchy):
    """
    A cache setup where each core has a private L1 data and instruction Cache.
    """
    
    def __init__(
        self,
        l1d_size: str,
        l1i_size: str,
    ) -> None:
        """
        :param l1d_size: The size of the L1 Data Cache (e.g., "32kB").

        :param  l1i_size: The size of the L1 Instruction Cache (e.g., "32kB").

        :param membus: The memory bus. This parameter is optional parameter and
        will default to a 64 bit width SystemXBar is not specified.
        """

        AbstractClassicCacheHierarchy.__init__(self=self)
        self._l1d_size = l1d_size
        self._l1i_size = l1i_size

    def incorporate_tile(self, sys_membus, pe) -> None:
        self.l1icaches = [
            L1ICache(size=self._l1i_size)
            for i in range(pe.get_num_cores())
        ]

        self.l1dcaches = [
            L1DCache(size=self._l1d_size)
            for i in range(pe.get_num_cores())
        ]
        # ITLB Page walk caches
        self.iptw_caches = [
            MMUCache(size="8KiB")
            for _ in range(pe.get_num_cores())
        ]
        # DTLB Page walk caches
        self.dptw_caches = [
            MMUCache(size="8KiB")
            for _ in range(pe.get_num_cores())
        ]
        
        for i, cpu in enumerate(pe.get_cores()):

            cpu.connect_icache(self.l1icaches[i].cpu_side)
            cpu.connect_dcache(self.l1dcaches[i].cpu_side)

            self.l1icaches[i].mem_side = sys_membus.cpu_side_ports
            self.l1dcaches[i].mem_side = sys_membus.cpu_side_ports

            self.iptw_caches[i].mem_side = sys_membus.cpu_side_ports
            self.dptw_caches[i].mem_side = sys_membus.cpu_side_ports

            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )
            cpu.connect_interrupt()