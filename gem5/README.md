## NULL ISA build command
`cd gem5 && scons build/NULL_MESI_Two_Level/gem5.opt --default=NULL PROTOCOL=MESI_Two_Level -j$(nproc)`

## Run script command
`./gem5/build/NULL_MESI_Two_Level/gem5.opt -re --outdir=gem5_simout ./gem5/configs/lab447/gem5_entry.py`
with debug informations, add
`--debug-flags PE, DRAM`
