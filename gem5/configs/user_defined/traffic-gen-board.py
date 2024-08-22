from gem5.components.boards.test_board import TestBoard
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.linear_generator import LinearGenerator
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import PrivateL1CacheHierarchy

import m5
from m5.objects import Root

# Setup the components.
memory = SingleChannelDDR3_1600("1GiB")
generator = LinearGenerator(
    duration="250us",
    rate="40GB/s",
    num_cores=4,
    max_addr=memory.get_size(),
    data_limit=128
)
# cache_hierarchy = NoCache()
cache_hierarchy = PrivateL1CacheHierarchy('32kB', '32kB')

# Add them to the Test board.
board = TestBoard(
    clk_freq="3GHz",
    generator=generator,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Setup the root and instantiate the simulation.
# This is boilerplate code, to be removed in future releaes of gem5.
root = Root(full_system=False, system=board)
board._pre_instantiate()
m5.instantiate()

# Start the traffic generator.
generator.start_traffic()
exit_event = m5.simulate()
