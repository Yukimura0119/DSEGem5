import json
 

model = 'resnet50'
# model = 'mobilenetv2'
# model = 'resnet101'
# model = 'vgg16'

file = f'../json/{model}.json'

# Opening JSON file
with open(file) as json_file:
    data = json.load(json_file)
    # print(type(data))
    # print(len(data))

    for i in range(len(data)):
        data[i]['fuse'] = 0 
        
    final = json.dumps(data,  indent=3)
    with open(f"../json/no_fuse/{model}_no_fuse.json", "w") as outfile:
        outfile.write(final)
