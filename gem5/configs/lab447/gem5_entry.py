import m5
from m5.objects import *
m5.util.addToPath("../")
from util.buildSystem import *
import json
import os

absolute_path = os.path.dirname(os.path.abspath(__file__))
filename = absolute_path + '/json/output_mesh.json'

print(f'config file: {filename}')

with open(filename) as f:
    data = json.load(f)

if(data['system']['type'] == 'Vanilla'):
    root = buildType1(data)
elif(data['system']['type'] == 'Mesh'):
    root = buildType2(data)

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause())) 