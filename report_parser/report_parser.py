import json
import re

def isFloat(s: str)->bool:
    pattern = r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$'
    return bool(re.match(pattern, s))

def parseReport(src_path: str, dest_path: str)->bool:
    lines = []
    with open(src_path) as f:
        lines = f.readlines()
    
    desired_items = ['finalTick',
                     'totalEnergy',
                     'demandAvgMissLatency',
                     'replacements',
                     'blockedCycles',
                     'ReadReq.hits.total',
                     'ReadReq.miss.total',
                     'numRetries',
                     'retryTicks',
                     'avgReadLatency',
                     'avgWriteLatency',
                     'readBW',
                     'writeBW'
                     ]
    desired_out = {'Stats': {}}

    for line in lines:
        for item in desired_items:
            if item in line:
                line = line.split()
                if not isFloat(line[1]):
                    continue
                if item not in desired_out['Stats']:
                    desired_out['Stats'][item] = float(line[1])
                else:
                    desired_out['Stats'][item] += float(line[1])

    jfile = json.dumps(desired_out)

    with open(dest_path, 'w') as jout:
        jout.write(jfile)

    return True
    