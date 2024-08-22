import json
import os
import timeit

def TrafficGeneratorAPI(dse_model):
    try:
        start = timeit.default_timer()
        exit_code = os.system(f"traffic_generator/top {dse_model}>/dev/null && wc -l files/Traffic_Pattern/traffic_pattern.json")
        assert exit_code == 0, "Traffic generator failed"
        # assert os.path.exists("files/Traffic_Pattern/traffic_pattern.json"), "Traffic generator generate traffic pattern error"
        print("-----------Traffic generator pass!-----------")
        end = timeit.default_timer()
        print(f"TG : {end-start}")
        return 0, ""
    except:
        return 1, "traffic generator error"

def Gem5SimulatorAPI():
    try:
        start = timeit.default_timer()
        exit_code = os.system("./gem5/build/NULL_MESI_Two_Level/gem5.opt -re --outdir=gem5_simout ./gem5/configs/lab447/gem5_entry.py")
        assert exit_code == 0, "gem5 simulator failed"
        # assert os.path.exists("gem5/m5out/stats.txt"), "gem5 generate report error"
        assert os.path.exists("gem5_simout/stats.txt"), "gem5 generate report error"
        print("-----------gem5 pass!-----------")
        end = timeit.default_timer()
        print(f"G5 : {end-start}")
        return 0, ""
    except:
        return 1, "Gem5 simulate error"
    
def GetReportAPI():
    try:
        exit_code = os.system("python3 report_parser/main.py")
        assert exit_code == 0, "get report failed"
        assert os.path.exists("files/Report/report.json"), "Not find report.json"
        print("-----------report pass!-----------")
        with open("files/Report/report.json") as f:
            report = json.load(f)
        return report["Stats"]["finalTick"], report["Stats"]["totalEnergy"], ""
    except:
        return 1, "Get report error"

