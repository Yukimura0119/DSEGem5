from allocation_policies import first_fit, best_fit

def getBlkIdx(mem_table: list, tensor_size: int, mem_max: int, allocation_policy: str)->int:
    policy_list = {
        'firstFit': first_fit.getBlkIdx,
        'bestFit': best_fit.getBlkIdx
    }

    if allocation_policy not in policy_list.keys():
        raise NotImplementedError('Allocation policy: {allocation_policy} is not implemented')
    
    return policy_list[allocation_policy](mem_table, tensor_size, mem_max)