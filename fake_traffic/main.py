import json
import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument('-n', "--num_traffic", type=int, default=100, help="number of fake traffic to generate")

args = parser.parse_args()

traffic = []

for i in range(args.num_traffic):
    traffic.append({"type": random.randint(0,2),
                    "src": "0,"+str(random.randint(0,3)),
                    "dest": "0,1",
                    "addr": random.randint(0, 4294967296),
                    "size": random.randint(1, 8192),
                    "request": 0,
                    "response": 0})


j = json.dumps(traffic, indent=4)

with open("files/Traffic_Pattern/fake-traffic.json", "w") as f:
    f.write(j)