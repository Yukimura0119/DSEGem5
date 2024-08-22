import m5
from m5.objects import *
from gem5.components.processors.lab447.pe_tile import PETile
from gem5.components.cachehierarchies.lab447.lab447_private_l1_cache_hierarchy import Lab447PrivateL1CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_private_l1_private_l2_cache_hierarchy import Lab447PrivateL1PrivateL2CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_private_l1_shared_l2_cache_hierarchy import Lab447PrivateL1SharedL2CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_no_cache import Lab447NoCache
from gem5.components.memory import *

m5.util.addToPath("../")

# initialize system
system                           = System()
system.clk_domain                = SrcClockDomain()
system.clk_domain.clock          = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode                  = "timing"

# initialize global memory
system.global_mem = SingleChannelDDR3_1600("8GiB")
system.mem_ranges = [AddrRange(start=0x0, size=system.global_mem.get_size())]
system.global_mem.set_memory_range(system.mem_ranges)

# initialize global memory bus
system.global_membus                   = SystemXBar()
system.global_membus.badaddr_responder = BadAddr()
system.global_membus.default           = system.global_membus.badaddr_responder.pio

# connect global memory controller to global memory bus 
system.system_port = system.global_membus.cpu_side_ports
for cntr in system.global_mem.get_memory_controllers():
    cntr.port = system.global_membus.mem_side_ports

# initial petiles (connect to cache each)
num_tiles = 8

petiles =  []
caches = []

for tile_idx in range(num_tiles):
    petiles.append(PETile(num_cores=1, 
                           block_size=64, 
                           global_mem_size=system.global_mem.get_size(),
                           local_mem_offset=0x000000000))

    caches.append(Lab447PrivateL1CacheHierarchy(l1d_size="64kB", l1i_size="64kB"))
    caches[tile_idx].incorporate_tile(system.global_membus, petiles[tile_idx])

system.petiles = petiles
system.caches  = caches

root = Root(full_system=False, system=system)
m5.instantiate()

system.petiles[0]._parseTraffic(fpath='../files/Traffic_Pattern/fake-traffic.json')
for petile in system.petiles:
    petile.start_traffic()

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause())) 