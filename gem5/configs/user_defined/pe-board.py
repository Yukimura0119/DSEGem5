from gem5.components.boards.test_board import TestBoard
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import PrivateL1CacheHierarchy
from gem5.components.cachehierarchies.classic.no_cache import NoCache

from gem5.components.processors.lab447.pe_tile import PETile

import m5
from m5.objects import Root

# Setup the components.
memory = SingleChannelDDR3_1600("8GiB")
generator = PETile(
    num_cores = 4,
    grid_width = 4
)

# cache_hierarchy = NoCache()
cache_hierarchy = PrivateL1CacheHierarchy(l1d_size="256kB", l1i_size="256kB")

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

generator._parseTraffic(fpath = "../files/Traffic_Pattern/traffic_pattern.json")

# Start the traffic generator.
generator.start_traffic()
print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause())) 