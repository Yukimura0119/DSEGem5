import m5
from m5.objects import *
from gem5.components.processors.lab447.pe_tile import PETile
from gem5.components.cachehierarchies.lab447.lab447_private_l1_cache_hierarchy import Lab447PrivateL1CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_private_l1_private_l2_cache_hierarchy import Lab447PrivateL1PrivateL2CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_private_l1_shared_l2_cache_hierarchy import Lab447PrivateL1SharedL2CacheHierarchy
from gem5.components.cachehierarchies.lab447.lab447_no_cache import Lab447NoCache
from gem5.components.memory import *
from gem5.components.boards.test_board import TestBoard
from gem5.components.cachehierarchies.ruby\
    .lab447_mesi_two_level_cache_hierarchy import Lab447MESITwoLevelCacheHierarchy
m5.util.addToPath("../")

def buildType1(data) -> Root:
    # initial system
    system = System()
    system.clk_domain = SrcClockDomain()
    system.clk_domain.voltage_domain = VoltageDomain()
    system.mem_mode = "timing"
    system.clk_domain.clock = data['system']['clockRate']

    # number of tiles
    numTiles = data['system']['numTiles']

    # memory
    memoryInfo = data['memory']
    system.memory = globals()[memoryInfo['dramInterface']](memoryInfo['size'])
    system.mem_ranges = [AddrRange(start=0x0, size=system.memory.get_size())]
    system.memory.set_memory_range(system.mem_ranges)

    # membus
    system.membus = SystemXBar()
    system.membus.width = data['noc']['width']
    system.membus.badaddr_responder = BadAddr()
    system.membus.default = system.membus.badaddr_responder.pio

    # connection between membus and memory
    system.system_port = system.membus.cpu_side_ports
    for cntr in system.memory.get_memory_controllers():
        cntr.port = system.membus.mem_side_ports
    
    # number of PEs per tile
    pePerTile = data['tile']['pePerTile']
    
    # tile configuration
    pe = []
    cache = []
    tileInfo = data['tile']
    for i in range(numTiles):
        pe.append(PETile(num_cores=pePerTile, 
                        block_size=64, 
                        global_mem_size=system.memory.get_size(),
                        local_mem_offset=0x000000000,
                        grid_width=pePerTile))
        if(tileInfo['l2Size'] == None):
            cache.append(globals()[tileInfo['cache']](tileInfo['l1Size'], tileInfo['l1Size']))
        else:
            cache.append(globals()[tileInfo['cache']](tileInfo['l1Size'], \
                tileInfo['l1Size'], tileInfo['l2Size'], tileInfo['l1Assoc'],  \
                tileInfo['l1Assoc'], tileInfo['l2Assoc']))
        cache[i].incorporate_tile(system.membus, pe[i])    
    system.pe = pe
    system.cache = cache
    
    # build up system
    root = Root(full_system=False, system=system)
    m5.instantiate()
    
    # set up PE within each tile
    system.pe[0]._parseTraffic(fpath = '/workspace/files/Traffic_Pattern/traffic_pattern.json') 
    for i in range(numTiles):
        system.pe[0].start_traffic()
    
    return root

def buildType2(data) -> Root:
    
    # ruby cache system
    cache_hierarchy = Lab447MESITwoLevelCacheHierarchy(
    l1i_size=data['tile']['l1Size'],
    l1i_assoc=data['tile']['l1Assoc'],
    l1d_size=data['tile']['l1Size'],
    l1d_assoc=data['tile']['l1Assoc'],
    l2_size=data['tile']['l2Size'],
    l2_assoc=data['tile']['l2Assoc'],
    l2_per_tile=data['tile']['l2PerTile'],
    num_cols=data['tile']['numCols'],
    num_tiles=data['system']['numTiles'],
    pe_per_tile=data['tile']['pePerTile'],
    link_width=data['noc']['width'] * 8
    )
    
    # memory
    memoryInfo = data['memory']
    memory = globals()[memoryInfo['dramInterface']](memoryInfo['size'])
    
    # PE
    generator = PETile (num_cores=data['tile']['pePerTile'] * data['system']['numTiles'], 
                        block_size=64, 
                        global_mem_size=memory.get_size(),
                        local_mem_offset=0x000000000,
                        grid_width=data['tile']['pePerTile']
    )
    
    # binding components with board
    motherboard = TestBoard(
    clk_freq=data['system']['clockRate'],
    generator=generator,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    )
    
    # build up system
    root = Root(full_system=False, system=motherboard)
    motherboard._pre_instantiate()
    m5.instantiate()
    
    # set up PE within each tile
    generator._parseTraffic(fpath = '/workspace/files/Traffic_Pattern/traffic_pattern.json') 
    generator.start_traffic()
    
    return root