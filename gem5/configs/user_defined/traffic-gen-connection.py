from gem5.components.processors.linear_generator import *
from gem5.components.cachehierarchies.lab447.lab447_private_l1_cache_hierarchy import Lab447PrivateL1CacheHierarchy
from gem5.components.memory import *
import m5
from m5.objects import *


m5.util.addToPath("../")


system                           = System()
system.clk_domain                = SrcClockDomain()
system.clk_domain.clock          = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode                   = "timing"

system.global_mem = SingleChannelDDR3_1600("1GiB")
system.mem_ranges = [AddrRange(start=0x00000000, size=system.global_mem.get_size())]
system.global_mem.set_memory_range(system.mem_ranges)

system.global_membus = SystemXBar()
system.global_membus.badaddr_responder = BadAddr()
system.global_membus.default = system.global_membus.badaddr_responder.pio

system.tile0_local_mem = SingleChannelDDR3_1600("1GiB")
system.tile0_local_mem.set_memory_range([AddrRange(start=0x40000000, size=system.tile0_local_mem.get_size())])

system.tile0_local_membus = SystemXBar()
system.tile0_local_membus.badaddr_responder = BadAddr()
system.tile0_local_membus.default = system.tile0_local_membus.badaddr_responder.pio

system.system_port = system.global_membus.cpu_side_ports


for cntr in system.global_mem.get_memory_controllers():
    cntr.port = system.global_membus.mem_side_ports

for cntr in system.tile0_local_mem.get_memory_controllers():
    cntr.port = system.tile0_local_membus.mem_side_ports

system.tile0_local_membus.mem_side_ports = system.global_membus.cpu_side_ports

system.tile0 = LinearGenerator(
    duration="250us",
    rate="40GB/s",
    num_cores=1,
    max_addr=system.global_mem.get_size(),
    # data_limit=10000 * 64
)

system.cache = Lab447PrivateL1CacheHierarchy(l1d_size="64kB", l1i_size="64kB")
system.cache.incorporate_tile(system.tile0_local_membus, system.tile0)

root = Root(full_system=False, system=system)
m5.instantiate()
system.tile0.start_traffic()

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause())) 