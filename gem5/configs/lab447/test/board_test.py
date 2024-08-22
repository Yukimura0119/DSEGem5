from gem5.components.boards.test_board import TestBoard
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.linear_generator import *
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import PrivateL1SharedL2CacheHierarchy

import m5
from m5.objects import Root


memory = SingleChannelDDR3_1600("1GiB")
cache_hierarchy = NoCache()
# cache_hierarchy = PrivateL1SharedL2CacheHierarchy(l1d_size="64kB", l1i_size="64kB", l2_size="128kB")

generator = LinearGenerator(
    duration="250us",
    rate="40GB/s",
    num_cores=1,
    max_addr=memory.get_size(),
    data_limit=64 * 100 * 3 
)

# Add them to the Test board.
board = TestBoard(
    clk_freq="3GHz",
    generator=generator,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

root = Root(full_system=False, system=board)
board._pre_instantiate()
m5.instantiate()

# Start the traffic generator.
generator.start_traffic()
exit_event = m5.simulate()