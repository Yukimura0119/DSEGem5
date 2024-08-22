import os
import timeit
import json
#from DSE.DSE_engine import DSE_main
'''
1. DSE engine
    input :
        files/ONNX/mobilenetv2.json
        files/HW_config/expe1.json
    output : files/DSE/DSE_mobilenetv2.json
    Workflow :
        python3 DSE/DSE_engine.py -m files/ONNX/mobilenetv2.json -a files/HW_config/expe1.json
2. Traffic generator
    input : files/DSE/DSE_mobilenetv2.json
    output : files/Traffic_Pattern/traffic_pattern.json
    Workflow :
        traffic_generator/traffic_generator files/DSE/DSE_mobilenetv2.json
3. gem5 simulator
    input : files/Traffic_Pattern/traffic_pattern.json
    output : files/Report/report.json
    Workflow :
        gem5/build/X86/gem5.opt gem5/configs/user_defined/pe-gen.py
'''
def DSE(model, architecture):
    DSE_main(model, architecture)
    assert os.path.exists("files/DSE/DSE_" + model), "DSE generate DSE_" + model + " file error"
    print("-----------DSE pass!-----------")
def TrafficGenerator(dse_model):
    exit_code = os.system("traffic_generator/top " + dse_model)
    assert exit_code == 0, "Traffic generator failed"
    assert os.path.exists("files/Traffic_Pattern/traffic_pattern.json"), "Traffic generator generate traffic pattern error"
    print("Traffic generator pass!")
    print("-----------Traffic generator pass!-----------")
def Gem5Simulator():
    exit_code = os.system("./gem5/build/NULL_MESI_Two_Level/gem5.opt -re --outdir=rrrrr ./gem5/configs/lab447/gem5_entry.py")
    assert exit_code == 0, "gem5 simulator failed"
    assert os.path.exists("rrrrr/stats.txt"), "gem5 generate report error"
    print("-----------gem5 pass!-----------")
def DSE_GetReport():
    exit_code = os.system("python3 report_parser/main.py")
    assert exit_code == 0, "get report failed"
    assert os.path.exists("files/Report/report.json"), "Not find report.json"
    print("-----------report pass!-----------")
    with open("files/Report/report.json") as f:
        report = json.load(f)
    print(report)
if __name__ == "__main__":
    # DSE Engine
    #model = "files/ONNX/mobilenetv2.json"
    #architecture = "files/HW_config/expe1.json"
    #DSE_main(model, architecture)
    # Traffic generator
    start = timeit.default_timer()
    #dse_model = "files/DSE/DSE_resnet50_mem.json"
    #TrafficGenerator(dse_model)
    # gem5
    Gem5Simulator()
    DSE_GetReport()
    end = timeit.default_timer()
    print(end - start)