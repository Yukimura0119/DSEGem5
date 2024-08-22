from gem5.components.processors.lab447.pe_tile import PETile
from gem5.components.processors.linear_generator import *
from gem5.components.processors.random_generator import *
from gem5.components.cachehierarchies.lab447.lab447_private_l1_cache_hierarchy import Lab447PrivateL1CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_private_l1_private_l2_cache_hierarchy import Lab447PrivateL1PrivateL2CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_private_l1_shared_l2_cache_hierarchy import Lab447PrivateL1SharedL2CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_no_cache import Lab447NoCache
from gem5.components.memory import *
import m5
from m5.objects import *

m5.util.addToPath("../")


system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"

system.memory = SingleChannelHBM("8GiB")
system.mem_ranges = [AddrRange(start=0x0, size=system.memory.get_size())]
system.memory.set_memory_range(system.mem_ranges)

system.membus = SystemXBar()
system.membus.badaddr_responder = BadAddr()
system.membus.default = system.membus.badaddr_responder.pio


system.system_port = system.membus.cpu_side_ports


for cntr in system.memory.get_memory_controllers():
    cntr.port = system.membus.mem_side_ports

system.tile0 = PETile(
    num_cores=4,
    block_size=64, 
    global_mem_size=system.memory.get_size(),
    local_mem_offset=0x000000000
)
# system.tile0 = RandomGenerator(
#     duration="10000us",
#     rate="40GB/s",
#     num_cores=4,
#     max_addr=system.memory.get_size(),
#     # data_limit=10000 * 64
# )

# system.cache0 = Lab447NoCache()
system.cache0 = Lab447PrivateL1CacheHierarchy(l1d_size="32KiB", l1i_size="32KiB")
system.cache0.incorporate_tile(system.membus, system.tile0)

system.tile1 = PETile(
    num_cores=4,
    block_size=64, 
    global_mem_size=system.memory.get_size(),
    local_mem_offset=0x000000000
)

# system.tile1 = RandomGenerator(
#     duration="10000us",
#     rate="40GB/s",
#     num_cores=4,
#     max_addr=system.memory.get_size(),
#     # data_limit=10000 * 64
# )

# system.cache1 = Lab447NoCache()
system.cache1 = Lab447PrivateL1CacheHierarchy(l1d_size="32KiB", l1i_size="32KiB")
system.cache1.incorporate_tile(system.membus, system.tile1)

root = Root(full_system=False, system=system)
m5.instantiate()

system.tile0._parseTraffic(fpath = '../files/Traffic_Pattern/fake-traffic.json')
system.tile1._parseTraffic(fpath = '../files/Traffic_Pattern/fake-traffic.json')

system.tile0.start_traffic()
system.tile1.start_traffic()

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause())) 