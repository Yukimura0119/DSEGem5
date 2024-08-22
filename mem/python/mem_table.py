from allocation_policies import policy

class MemTable:
    def __init__(self, size: int, policy_name: str = 'bestFit'):
        self.table       = [{'valid': 1, 'addr': 0, 'size': size, 'tensor_name': ''}]
        self.policy_name = policy_name
        self.size        = size

    def __len__(self):
        return len(self.table)

    def getSize(self):
        return self.size

    def allocate(self, tensor_name: str, tensor_size: int)->tuple([int, int]):
        blk_idx = policy.getBlkIdx(self.table, tensor_size, self.size, self.policy_name)
        if blk_idx == -1:
            print(f'MemTable::allocate, Out of memory: {tensor_name}: {tensor_size/1024}KB')
            # TODO: alloc tensor to different block
            return tensor_size, -1
        else:
            addr = self.table[blk_idx]['addr']
            if tensor_size == self.table[blk_idx]['size']:
                self.table[blk_idx]['valid'] = 0
                self.table[blk_idx]['tensor_name'] = tensor_name
            else:
                new_blk = {'valid': 0, 'addr': self.table[blk_idx]['addr'], 'size': tensor_size, 'tensor_name': tensor_name}
                self.table[blk_idx]['addr'] += tensor_size
                self.table[blk_idx]['size'] -= tensor_size
                self.table.insert(blk_idx, new_blk)
            
            return 0, addr
        
    def deallocate(self, tensor_name: str)->bool:
        # memory only contains one block
        if len(self.table) == 1:
            if self.table[0]['tensor_name'] != tensor_name:
                print(f'allocation::deallocate, can not find allocated tensor: {tensor_name} deallocate failed')
                return False
            else:
                self.table[idx]['valid'] = 1
                self.table[idx]['tensor'] = ""
            return True

        # memory contains more than one block
        for idx, blk in enumerate(self.table):
            if blk['tensor_name'] == tensor_name:
                # set target block free
                self.table[idx]['valid'] = 1
                self.table[idx]['tensor'] = ""
            
                # target block is the first block of memory table, only check next block
                if (idx == 0):
                    if (self.table[idx+1]['valid'] == 1):                    
                        self.table[idx]['size'] +=  self.table[idx+1]['size']
                        self.table.remove(self.table[idx+1])
                # target block is the last block of memory table, only check previos block
                elif idx == (len(self.table) - 1):
                    if (self.table[idx-1]['valid'] == 1):
                        self.table[idx]['addr'] =   self.table[idx-1]['addr']
                        self.table[idx]['size'] +=  self.table[idx-1]['size']
                        self.table.remove(self.table[idx-1])
                # target block is in the middle of memory table, check both next and previos blocks
                else:
                    if (self.table[idx+1]['valid'] == 1):
                        self.table[idx]['size'] +=  self.table[idx+1]['size']
                        self.table.remove(self.table[idx+1])
                    if (self.table[idx-1]['valid'] == 1):
                        self.table[idx]['addr'] =   self.table[idx-1]['addr']
                        self.table[idx]['size'] +=  self.table[idx-1]['size']
                        self.table.remove(self.table[idx-1])

                return True
            
        print(f'MemTable::deallocate, can not find allocated tensor: {tensor_name} deallocate failed')
        return False
    
    def printTable(self)->None:
        for idx, blk in enumerate(self.table):
            print(f'table[{idx}]: valid: {blk["valid"]}, addr: {blk["addr"]}, size: {blk["size"]}, tensor_name: {blk["tensor_name"]}')