def getBlkIdx(mem_table: list, tensor_size: int, mem_max: int)->int:
    if tensor_size > mem_max:
        return -1

    best_size = mem_max + 1
    best_idx  = -1 

    for idx, blk in enumerate(mem_table):
        if blk['valid'] == 0:
            continue
        if blk['size'] >= tensor_size and blk['size'] < best_size:
            best_idx  = idx
            best_size = blk['size']
        
    return best_idx