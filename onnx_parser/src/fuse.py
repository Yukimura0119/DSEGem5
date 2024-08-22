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

        if data[i]['op_type'] == 'Conv':
            # print(i)
            if (i+1) < len(data) and (i+2) < len(data):
                if data[i+1]['op_type'] == 'BatchNormalization' and data[i+2]['op_type'] == 'Relu':
                    data[i]['fuse'] = 3 # conv, batchnorm, relu 
                    print(i, ' fuse 3 op')
                elif data[i+1]['op_type'] == 'BatchNormalization':
                    data[i]['fuse'] = 2
                    print(i, ' fuse 2 op')
                elif data[i+1]['op_type'] == 'Relu':
                    data[i]['fuse'] = 2
                    print(i, ' fuse 2 op')

        
    final = json.dumps(data,  indent=3)
    with open(f"../json/fuse/{model}_fuse.json", "w") as outfile:
        outfile.write(final)



