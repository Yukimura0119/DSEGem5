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


class Lab447PrivateL1PrivateL2CacheHierarchy(
    AbstractClassicCacheHierarchy, AbstractTwoLevelCacheHierarchy
):
    """
    A cache setup where each core has a private L1 Data and Instruction Cache,
    and a private L2 cache.
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

        :type l1d_size: str

        :param  l1i_size: The size of the L1 Instruction Cache (e.g., "32kB").

        :type l1i_size: str

        :param l2_size: The size of the L2 Cache (e.g., "256kB").

        :type l2_size: str

        :param membus: The memory bus. This parameter is optional parameter and
        will default to a 64 bit width SystemXBar is not specified.

        :type membus: BaseXBar
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
            L1ICache(size=self._l1i_size)
            for i in range(pe.get_num_cores())
        ]
        self.l1dcaches = [
            L1DCache(size=self._l1d_size)
            for i in range(pe.get_num_cores())
        ]
        self.l2buses = [
            L2XBar() for i in range(pe.get_num_cores())
        ]
        self.l2caches = [
            L2Cache(size=self._l2_size)
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

            self.l1icaches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.l1dcaches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.iptw_caches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.dptw_caches[i].mem_side = self.l2buses[i].cpu_side_ports

            self.l2buses[i].mem_side_ports = self.l2caches[i].cpu_side

            sys_membus.cpu_side_ports = self.l2caches[i].mem_side

            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )
            
            cpu.connect_interrupt()
