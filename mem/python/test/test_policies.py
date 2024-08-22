from allocation_policies import policy

def test_first_fit_0_fit():
    mem_table = [{'valid': 1, 'addr': 0, 'size': 8192, 'tensor_name': ''}]

    blk_idx = policy.getBlkIdx(mem_table, 32, 8192, 'firstFit')
    assert(blk_idx == 0)

def test_first_fit_1_fit():
    mem_table = [{'valid': 1, 'addr': 0, 'size': 31, 'tensor_name': ''}, {'valid': 1, 'addr': 0, 'size': 8192, 'tensor_name': ''}]

    blk_idx = policy.getBlkIdx(mem_table, 32, 8192, 'firstFit')
    assert(blk_idx == 1)


def test_first_fit_skip_invalid():
    mem_table = [{'valid': 0, 'addr': 0, 'size': 32, 'tensor_name': ''}, {'valid': 1, 'addr': 0, 'size': 8192, 'tensor_name': ''}]

    blk_idx = policy.getBlkIdx(mem_table, 32, 8192, 'firstFit')
    assert(blk_idx == 1)
