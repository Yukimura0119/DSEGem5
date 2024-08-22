from mem_table import MemTable

def test_alloc_1blk_full():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 8192)
    assert(len(mem_table) == 1)

def test_alloc_1blk():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)

def test_alloc_2blk_full():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.allocate('test2 blk', 4096)
    assert(len(mem_table) == 2)

def test_alloc_2blk_full():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.allocate('test2 blk', 2048)
    assert(len(mem_table) == 3)

def test_dealloc_merge_next():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.deallocate('test1 blk')    
    assert(len(mem_table) == 1)

def test_dealloc_not_merge():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.allocate('test2 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.deallocate('test1 blk')
    assert(len(mem_table) == 2)

def test_dealloc_merge_prev():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.allocate('test2 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.deallocate('test1 blk')
    assert(len(mem_table) == 2)
    mem_table.deallocate('test2 blk')    
    assert(len(mem_table) == 1)

def test_dealloc_not_merge2():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.allocate('test2 blk', 2048)
    assert(len(mem_table) == 3)
    mem_table.allocate('test3 blk', 2048)
    assert(len(mem_table) == 3)
    mem_table.deallocate('test1 blk')
    assert(len(mem_table) == 3)
    mem_table.deallocate('test3 blk')
    assert(len(mem_table) == 3)

def test_dealloc_merge_both():
    mem_table = MemTable(8192)

    mem_table.allocate('test1 blk', 4096)
    assert(len(mem_table) == 2)
    mem_table.allocate('test2 blk', 2048)
    assert(len(mem_table) == 3)
    mem_table.allocate('test3 blk', 2048)
    assert(len(mem_table) == 3)
    mem_table.deallocate('test1 blk')
    assert(len(mem_table) == 3)
    mem_table.deallocate('test3 blk')
    assert(len(mem_table) == 3)
    mem_table.deallocate('test2 blk')    
    assert(len(mem_table) == 1)