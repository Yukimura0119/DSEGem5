import m5
import argparse
import importlib
from m5.objects import Root
from gem5.components.boards.test_board import TestBoard
from gem5.components.processors.lab447.pe_tile import PETile
from gem5.components.processors.linear_generator import LinearGenerator
from gem5.components.processors.random_generator import RandomGenerator
from gem5.components.memory import *
from gem5.components.cachehierarchies.ruby\
    .lab447_mesi_two_level_cache_hierarchy import Lab447MESITwoLevelCacheHierarchy

 
l2_per_tile=2
num_cols=2
num_tiles=1
pe_per_tile=4
link_width=128


cache_hierarchy = Lab447MESITwoLevelCacheHierarchy(
    l1i_size="32KiB",
    l1i_assoc=8,
    l1d_size="32KiB",
    l1d_assoc=8,
    l2_size="256KiB",
    l2_assoc=4,
    l2_per_tile=l2_per_tile,
    num_cols=num_cols,
    num_tiles=num_tiles,
    pe_per_tile=pe_per_tile,
    link_width=link_width
)

memory = SingleChannelDDR3_1600("8GiB")

# generator = RandomGenerator(
#             duration="250us",
#             rate="40GB/s",
#             num_cores=pe_per_tile * num_tiles,
#             max_addr=memory.get_size(),
#             # data_limit=64
# )

generator = PETile (num_cores=pe_per_tile * num_tiles, 
                    block_size=64, 
                    global_mem_size=memory.get_size(),
                    local_mem_offset=0x000000000
)

motherboard = TestBoard(
    clk_freq="3GHz",
    generator=generator,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)
root = Root(full_system=False, system=motherboard)
motherboard._pre_instantiate()
m5.instantiate()

generator._parseTraffic(fpath = '../files/Traffic_Pattern/traffic_pattern-test.json') 
generator.start_traffic()

print("Beginning simulation!")
exit_event = m5.simulate()
print(
    "Exiting @ tick {} because {}.".format(m5.curTick(), exit_event.getCause())
)