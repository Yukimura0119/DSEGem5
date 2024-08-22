from m5.params import *
from m5.objects import *

from m5.objects import GarnetNetwork, GarnetExtLink, GarnetIntLink, \
                        GarnetRouter, GarnetNetworkInterface


class GTRocket(GarnetNetwork):

    def __init__(self, ruby_system):
        super().__init__()
        self.ruby_system = ruby_system

    # Makes a generic mesh
    def connectControllers(self, controllers, pePerTile, ncol, l2PerTile, linkWidth):
        nodes = controllers

        chiplet_link_latency = 16
        chiplet_link_width = linkWidth
        interp_link_latency = 1
        interp_link_width = linkWidth
        router_latency = 1

        cpu_nodes = []
        l2_nodes = []
        mc_nodes = []
        dma_nodes = []

        for node in nodes:
            if node.type == 'L1Cache_Controller':
                cpu_nodes.append(node)
            elif node.type == 'L2Cache_Controller':
                l2_nodes.append(node)
            elif node.type == 'Directory_Controller':
                mc_nodes.append(node)
            elif node.type == 'DMA_Controller':
                dma_nodes.append(node)

        # Compute the configuration:
        num_cpus_per_chiplet = pePerTile
        num_cpu_chiplets = int(len(cpu_nodes) / num_cpus_per_chiplet)
        num_l2_mc_dma_chiplets = len(l2_nodes) + len(mc_nodes) + len(dma_nodes)

        # Mesh rows and columns
        num_columns = ncol
        num_rows = int(num_cpus_per_chiplet / num_columns)
        
        assert(num_cpus_per_chiplet % num_columns == 0), 'pe_per_tile should be divided exactly by num_cols'
        assert(num_columns >= l2PerTile), 'l2_per_tile should be less than num_cols'
        assert((num_rows*num_columns*num_cpu_chiplets) == int(len(cpu_nodes)))

        num_routers = len(cpu_nodes) + len(l2_nodes) \
                        + len(mc_nodes) + len(dma_nodes) \
                        + num_cpu_chiplets  + 1
                        
        # num_cpu_chiplets -> for L2Xbar in each chiplet
        # 1 -> for MemoryXbar
        
        # Create the routers in the mesh
        self.routers = [GarnetRouter(router_id=i, latency=router_latency, width=chiplet_link_width) \
            for i in range(num_routers)]

        # link counter to set unique link ids
        link_count = 0

        # start from router 0
        router_id = 0

        # Connect each CPU to a unique router
        ext_links = []
        for (i, n) in enumerate(cpu_nodes):
            self.routers[router_id].width = chiplet_link_width # nominal flit size
            ext_links.append(GarnetExtLink(link_id=link_count, ext_node=n,
                                    int_node=self.routers[router_id],
                                    latency = chiplet_link_latency,
                                    width = chiplet_link_width
                                    ))
            print_connection("CPU", n.version, "Router", router_id, link_count,\
                              chiplet_link_latency, chiplet_link_width)
            link_count += 1
            router_id += 1

        
        # Connect each L2 to a router
        l2c_router_start_id = router_id
        for (i, n) in enumerate(l2_nodes):
            self.routers[router_id].width = chiplet_link_width # nominal flit size
            ext_links.append(GarnetExtLink(link_id=link_count, ext_node=n,
                                    int_node=self.routers[router_id],
                                    latency = chiplet_link_latency,
                                    width = chiplet_link_width
                                    ))
            print_connection("L2", n.version, "Router", router_id, link_count,\
                              chiplet_link_latency, chiplet_link_width)
            link_count += 1
            router_id += 1
       
        # Connect the MC nodes to routers
        mcc_router_start_id = router_id
        for (i, n) in enumerate(mc_nodes):
            self.routers[router_id].width = chiplet_link_width # nominal flit size
            ext_links.append(GarnetExtLink(link_id=link_count, ext_node=n,
                                    int_node=self.routers[router_id],
                                    latency = chiplet_link_latency,
                                    width = chiplet_link_width,
                                    ))
            print_connection("MC", n.version, "Router", router_id, link_count,\
                              chiplet_link_latency, chiplet_link_width)
            link_count += 1
            router_id += 1
   
        # Connect the DMA nodes to routers
        dmac_router_start_id = router_id
        for (i, n) in enumerate(dma_nodes):
            self.routers[router_id].width = chiplet_link_width # nominal flit size
            ext_links.append(GarnetExtLink(link_id=link_count, ext_node=n,
                                    int_node=self.routers[router_id],
                                    latency = chiplet_link_latency,
                                    width = chiplet_link_width
                                    ))
            print_connection("DMA", n.version, "Router", router_id, link_count,\
                              chiplet_link_latency, chiplet_link_width)
            link_count += 1
            router_id += 1

        self.ext_links = ext_links
         ## All routers except L2Xbar and MemoryXbar have been connected
        assert(router_id == num_routers - (1 + num_cpu_chiplets))

        l2xbar_id = router_id # L2Xbar start id
        for i in range(num_cpu_chiplets):
            self.routers[l2xbar_id+i].latency=2 # Assume 2-cycle high-radix l2xbar
      
        
        router_id += num_cpu_chiplets
        memxbar_id = router_id # MemoryXbar start id
        self.routers[memxbar_id].latency=4 # Assume 4-cycle high-radix memoryxbar
     

        self.netifs = [GarnetNetworkInterface(id=i) \
                    for (i,n) in enumerate(self.ext_links)]

        # Create the mesh links.
        int_links = []

        test_num_cpus = 0
        for cc in range(num_cpu_chiplets):
            for row in range(num_rows):
                for col in range(num_columns):
                    test_num_cpus += 1
                    if (col + 1 < num_columns):
                        # East output to West input links (weight = 1)
                        east_out = (cc*num_cpus_per_chiplet) + col + (row * num_columns)
                        west_in = (cc*num_cpus_per_chiplet) + (col + 1) + (row * num_columns)
                        int_links.append(GarnetIntLink(link_id=link_count,
                                                src_node=self.routers[east_out],
                                                dst_node=self.routers[west_in],
                                                # ONLY FOR INFORMATION, JUST A STRING
                                                src_outport="East",
                                                dst_inport="West",
                                                latency = chiplet_link_latency,
                                                width = chiplet_link_width,
                                                weight=1
                                                ))
                        print_connection("Router", get_router_id(self.routers[east_out]),
                                         "Router", get_router_id(self.routers[west_in]),
                                          link_count,
                                          chiplet_link_latency, chiplet_link_width)
                        link_count += 1

                        # West output to East input links (weight = 1)
                        east_in = (cc*num_cpus_per_chiplet) + col + (row * num_columns)
                        west_out = (cc*num_cpus_per_chiplet) +  (col + 1) + (row * num_columns)
                        int_links.append(GarnetIntLink(link_id=link_count,
                                                src_node=self.routers[west_out],
                                                dst_node=self.routers[east_in],
                                                src_outport="West",
                                                dst_inport="East",
                                                latency = chiplet_link_latency,
                                                width = chiplet_link_width,
                                                weight=1
                                                ))
                        print_connection("Router", get_router_id(self.routers[west_out]),
                                         "Router", get_router_id(self.routers[east_in]),
                                          link_count,
                                          chiplet_link_latency, chiplet_link_width)
                        link_count += 1
    
            for col in range(num_columns):
                for row in range(num_rows):
                    if (row + 1 < num_rows):
                        # North output to South input links (weight = 2)
                        north_out = (cc*num_cpus_per_chiplet) + col + (row * num_columns)
                        south_in = (cc*num_cpus_per_chiplet) + col + ((row+1) * num_columns)
                        int_links.append(GarnetIntLink(link_id=link_count,
                                                src_node=self.routers[north_out],
                                                dst_node=self.routers[south_in],
                                                src_outport="North",
                                                dst_inport="South",
                                                latency = chiplet_link_latency,
                                                width = chiplet_link_width,
                                                weight=2
                                                ))
                        print_connection("Router", get_router_id(self.routers[north_out]),
                                         "Router", get_router_id(self.routers[south_in]),
                                          link_count,
                                          chiplet_link_latency, chiplet_link_width)
                        link_count += 1

                        # South output to North input links (weight = 2)
                        north_in = (cc*num_cpus_per_chiplet) + col + (row * num_columns)
                        south_out = (cc*num_cpus_per_chiplet) + col + ((row+1) * num_columns)
                        int_links.append(GarnetIntLink(link_id=link_count,
                                                src_node=self.routers[south_out],
                                                dst_node=self.routers[north_in],
                                                src_outport="South",
                                                dst_inport="North",
                                                latency = chiplet_link_latency,
                                                width = chiplet_link_width,
                                                weight=2
                                                ))
                        print_connection("Router", get_router_id(self.routers[south_out]),
                                         "Router", get_router_id(self.routers[north_in]),
                                          link_count,
                                          chiplet_link_latency, chiplet_link_width)
                        link_count += 1
                        
    
        ## Added all CPU chiplet links
        assert(test_num_cpus == len(cpu_nodes))

        # First connect all CPU chiplets to their own l2xbar and connect all l2xbar to their own l2cache
        cc_router_id = 0
        l2xbar_cnt = 0
        l2cache_cnt = 0
        for cc in range(num_cpu_chiplets):
            # in each tile, connect first few l1cache to their own l2xar
            for ll in range(l2PerTile):
                # CPU Chiplet to l2xbar
                int_links.append(GarnetIntLink(link_id=link_count,
                                        src_node=self.routers[cc_router_id+ll],
                                        dst_node=self.routers[l2xbar_id+l2xbar_cnt],
                                        latency = interp_link_latency,
                                        width = interp_link_width,
                                        weight=1
                                        ))
                print_connection("Router", get_router_id(self.routers[cc_router_id+ll]),
                             "Router", get_router_id(self.routers[l2xbar_id+l2xbar_cnt]),
                             link_count,
                             interp_link_latency, interp_link_width)
                link_count += 1
    
                # l2xbar to CPU chiplet
                int_links.append(GarnetIntLink(link_id=link_count,
                                        src_node=self.routers[l2xbar_id+l2xbar_cnt],
                                        dst_node=self.routers[cc_router_id+ll],
                                        latency = interp_link_latency,
                                        width = interp_link_width,
                                        weight=1
                                        ))
                print_connection("Router", get_router_id(self.routers[l2xbar_id+l2xbar_cnt]),
                             "Router", get_router_id(self.routers[cc_router_id+ll]),
                             link_count,
                             interp_link_latency, interp_link_width)
                link_count += 1
                
                # l2cache to l2xbar
                int_links.append(GarnetIntLink(link_id=link_count,
                                        src_node=self.routers[l2c_router_start_id+l2cache_cnt],
                                        dst_node=self.routers[l2xbar_id+l2xbar_cnt],
                                        latency = interp_link_latency,
                                        width = interp_link_width,
                                        weight=1
                                        ))
                print_connection("Router", get_router_id(self.routers[l2c_router_start_id+l2cache_cnt]),
                             "Router", get_router_id(self.routers[l2xbar_id+l2xbar_cnt]),
                             link_count,
                             interp_link_latency, interp_link_width)
                link_count += 1
                
                # l2xbar to l2cache 
                int_links.append(GarnetIntLink(link_id=link_count,
                                        src_node=self.routers[l2xbar_id+l2xbar_cnt],
                                        dst_node=self.routers[l2c_router_start_id+l2cache_cnt],
                                        latency = interp_link_latency,
                                        width = interp_link_width,
                                        weight=1
                                        ))
                print_connection("Router", get_router_id(self.routers[l2xbar_id+l2xbar_cnt]),
                             "Router", get_router_id(self.routers[l2c_router_start_id+l2cache_cnt]),
                             link_count,
                             interp_link_latency, interp_link_width)
                link_count += 1
                l2cache_cnt += 1
                
            l2xbar_cnt += 1
            cc_router_id += num_cpus_per_chiplet
        
        # Next, connect all l2cache and memory to xbar
        # Router id of first L2 chiplet should be same as num_cpus
        assert(l2c_router_start_id == len(cpu_nodes))
        ncc_router_id = l2c_router_start_id
    
        # connect l2 and memory to Xbar
        for ncc in range(num_l2_mc_dma_chiplets):
            int_links.append(GarnetIntLink(link_id=link_count,
                                    src_node=self.routers[ncc_router_id],
                                    dst_node=self.routers[memxbar_id],
                                    latency = interp_link_latency,
                                    width = interp_link_width,
                                    weight=1
                                    ))
            print_connection("Router", get_router_id(self.routers[ncc_router_id]),
                             "Router", get_router_id(self.routers[memxbar_id]),
                             link_count,
                             interp_link_latency, interp_link_width)
            link_count += 1

            # Xbar to chiplet
            int_links.append(GarnetIntLink(link_id=link_count,
                                    src_node=self.routers[memxbar_id],
                                    dst_node=self.routers[ncc_router_id],
                                    latency = interp_link_latency,
                                    width = interp_link_width,
                                    weight=1
                                    ))
            print_connection("Router", get_router_id(self.routers[memxbar_id]),
                             "Router", get_router_id(self.routers[ncc_router_id]),
                             link_count,
                             interp_link_latency, interp_link_width)
            link_count += 1

            ncc_router_id += 1
     
        # At the end ncc_router_id should be same as last chiplet, namely xbar
        assert(ncc_router_id == l2xbar_id)

        self.int_links = int_links

def get_router_id(node) :
    # return str(node).split('.')[4].split('routers')[1]
    pass

def print_connection(src_type, src_id, dst_type, dst_id, link_id, lat, bw):
    # print(str(src_type) + "-" + str(src_id) + " connected to " + \
    #       str(dst_type) + "-" + str(dst_id) + " via Link-" + str(link_id) + \
    #      " with latency=" + str(lat) + " (cycles)" \
    #      " and bandwidth=" + str(bw) + " (bits)")
    pass