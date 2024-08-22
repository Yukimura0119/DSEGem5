from gem5.components.processors.linear_generator import *
from gem5.components.processors.random_generator import *
from gem5.components.processors.lab447.pe_tile import PETile
from gem5.components.cachehierarchies.lab447.lab447_private_l1_cache_hierarchy import Lab447PrivateL1CacheHierarchy
from gem5.components.memory import *
import m5
from m5.objects import *


m5.util.addToPath("../")


system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"

system.memory = SingleChannelDDR3_1600("1GiB")
system.mem_ranges = [AddrRange(start=0x00000000, size=system.memory.get_size())]
system.memory.set_memory_range(system.mem_ranges)

system.membus = SystemXBar()
system.membus.badaddr_responder = BadAddr()
system.membus.default = system.membus.badaddr_responder.pio

system.system_port = system.membus.cpu_side_ports


for cntr in system.memory.get_memory_controllers():
    cntr.port = system.membus.mem_side_ports


# system.pe = LinearGenerator(
#     duration="10000us",
#     rate="40GB/s",
#     num_cores=4,
#     max_addr=system.memory.get_size(),
#     # data_limit=10000 * 64
# )
system.pe = RandomGenerator(
    duration="10000us",
    rate="40GB/s",
    num_cores=4,
    max_addr=system.memory.get_size(),
    # data_limit=10000 * 64
)

# system.pe = PETile(
#     num_cores=4,    
# )



system.cache = Lab447PrivateL1CacheHierarchy(l1d_size="64kB", l1i_size="64kB")
system.cache.incorporate_tile(system.membus, system.pe)

root = Root(full_system=False, system=system)
m5.instantiate()
# system.pe._parseTraffic(fpath = "traffic_pattern.json")
system.pe.start_traffic()

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause())) 