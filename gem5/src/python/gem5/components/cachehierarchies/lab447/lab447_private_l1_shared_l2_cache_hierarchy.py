from ..abstract_cache_hierarchy import AbstractCacheHierarchy
from ..classic.abstract_classic_cache_hierarchy import AbstractClassicCacheHierarchy
from ..abstract_two_level_cache_hierarchy import AbstractTwoLevelCacheHierarchy
from ..classic.caches.l1dcache import L1DCache
from ..classic.caches.l1icache import L1ICache
from ..classic.caches.l2cache import L2Cache
from ..classic.caches.mmu_cache import MMUCache
from ....isas import ISA
from m5.objects import Cache, L2XBar, BaseXBar, SystemXBar, BadAddr, Port

from ....utils.override import *


class Lab447PrivateL1SharedL2CacheHierarchy(
    AbstractClassicCacheHierarchy, AbstractTwoLevelCacheHierarchy
):
    """
    A cache setup where each core has a private L1 Data and Instruction Cache,
    and a L2 cache is shared with all cores. The shared L2 cache is mostly
    inclusive with respect to the split I/D L1 and MMU caches.
    """

    def __init__(
        self,
        l1d_size: str,
        l1i_size: str,
        l2_size: str,
        l1d_assoc: int = 8,
        l1i_assoc: int = 8,
        l2_assoc: int = 16,
    ) -> None:
        """
        :param l1d_size: The size of the L1 Data Cache (e.g., "32kB").
        :param  l1i_size: The size of the L1 Instruction Cache (e.g., "32kB").
        :param l2_size: The size of the L2 Cache (e.g., "256kB").
        :param l1d_assoc: The associativity of the L1 Data Cache.
        :param l1i_assoc: The associativity of the L1 Instruction Cache.
        :param l2_assoc: The associativity of the L2 Cache.
        :param membus: The memory bus. This parameter is optional parameter and
        will default to a 64 bit width SystemXBar is not specified.
        """

        AbstractClassicCacheHierarchy.__init__(self=self)
        AbstractTwoLevelCacheHierarchy.__init__(
            self,
            l1i_size=l1i_size,
            l1i_assoc=l1i_assoc,
            l1d_size=l1d_size,
            l1d_assoc=l1d_assoc,
            l2_size=l2_size,
            l2_assoc=l2_assoc,
        )

    def incorporate_tile(self, sys_membus, pe) -> None:

        self.l1icaches = [
            L1ICache(
                size=self._l1i_size,
                assoc=self._l1i_assoc,
                writeback_clean=False,
            )
            for i in range(pe.get_num_cores())
        ]
        self.l1dcaches = [
            L1DCache(size=self._l1d_size, assoc=self._l1d_assoc)
            for i in range(pe.get_num_cores())
        ]
        self.l2bus = L2XBar()
        self.l2cache = L2Cache(size=self._l2_size, assoc=self._l2_assoc)
        # ITLB Page walk caches
        self.iptw_caches = [
            MMUCache(size="8KiB", writeback_clean=False)
            for _ in range(pe.get_num_cores())
        ]
        # DTLB Page walk caches
        self.dptw_caches = [
            MMUCache(size="8KiB", writeback_clean=False)
            for _ in range(pe.get_num_cores())
        ]


        for i, cpu in enumerate(pe.get_cores()):

            cpu.connect_icache(self.l1icaches[i].cpu_side)
            cpu.connect_dcache(self.l1dcaches[i].cpu_side)

            self.l1icaches[i].mem_side = self.l2bus.cpu_side_ports
            self.l1dcaches[i].mem_side = self.l2bus.cpu_side_ports
            self.iptw_caches[i].mem_side = self.l2bus.cpu_side_ports
            self.dptw_caches[i].mem_side = self.l2bus.cpu_side_ports

            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )

            cpu.connect_interrupt()

        self.l2bus.mem_side_ports = self.l2cache.cpu_side
        sys_membus.cpu_side_ports = self.l2cache.mem_side