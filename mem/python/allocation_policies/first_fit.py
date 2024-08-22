def getBlkIdx(mem_table: list, tensor_size: int, mem_max: int)->int:
    if tensor_size > mem_max:
        return -1

    for idx, blk in enumerate(mem_table):
        if blk['valid'] == 0:
            continue
        if blk['size'] >= tensor_size:
            return idx
        
    return -1