from ..classic.abstract_classic_cache_hierarchy import AbstractClassicCacheHierarchy
from ..abstract_cache_hierarchy import AbstractCacheHierarchy
from ...boards.abstract_board import AbstractBoard
from ....isas import ISA

from m5.objects import Bridge, BaseXBar, SystemXBar, BadAddr, Port

from ....utils.override import *


class Lab447NoCache(AbstractClassicCacheHierarchy):
    """
    No cache hierarchy. The CPUs are connected straight to the memory bus.

    By default a SystemXBar of width 64bit is used, though this can be
    configured via the constructor.

    NOTE: At present this does not work with FS. The following error is
    received:

    ```
    ...
    build/X86/mem/snoop_filter.cc:277: panic: panic condition
    (sf_item.requested & req_mask).none() occurred: SF value
    0000000000000000000000000000000000000000000000000000000000000000 ...
    missing the original request
    Memory Usage: 3554472 KBytes
    Program aborted at tick 1668400099164
    --- BEGIN LIBC BACKTRACE ---
    ...
    ```
    """

    def __init__(
        self
    ) -> None:
        """
        :param membus: The memory bus for this setup. This parameter is
        optional and will default toa 64 bit width SystemXBar is not specified.

        :type membus: BaseXBar
        """
        super().__init__()

    def incorporate_tile(self, sys_membus, pe) -> None:
        for core in pe.get_cores():

            core.connect_icache(sys_membus.cpu_side_ports)
            core.connect_dcache(sys_membus.cpu_side_ports)
            core.connect_walker_ports(
                sys_membus.cpu_side_ports, sys_membus.cpu_side_ports
            )
            core.connect_interrupt()