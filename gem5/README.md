## NULL ISA build command
`cd gem5 && scons build/NULL_MESI_Two_Level/gem5.opt --default=NULL PROTOCOL=MESI_Two_Level -j$(nproc)`

## Run script command
`./gem5/build/NULL_MESI_Two_Level/gem5.opt -re --outdir=gem5_simout ./gem5/configs/lab447/gem5_entry.py`
with debug informations, add
`--debug-flags PE,DRAM`
e.g. `./gem5/build/NULL_MESI_Two_Level/gem5.opt -re --outdir=gem5_simout --debug-flags PE,DRAM ./gem5/configs/lab447/gem5_entry.py`

## Code Structure
```
gem5/
├── build                      -> binaries, link files
├── configs                    -> simulation configs (hardware architecture, simulation software...)
|   ├── lab447                 -> extend configs for DSE
|   |   ├── json               -> output hardware config for DSE
|   |   ├── util
|   |       └── buildSystem.py -> construct simulation system base on given hardware (architecture) and software (traffic pattern)
|   |   └── ...
|   └── gem5_entry.py          -> construct simluation system and run simulation
├── src                        -> gem5 source files (simulation objects, memory, cpu, etc.)
|   ├── lab447
|   |   ├── pe.cc              -> extend component source file
|   |   ├── pe.hh              -> extend component header file
|   |   ├── pe.py              -> extend component python binding file
|   |   ├── SConscript         -> building need file
|   |   └── traffic_pattern.hh -> dispatch traffic to PEs
|   ├── python
|   |   ├── components
|   |   |   ├── processors
|   |   |   |   └── lab447     -> python bind needed files
|   |   |   └── ...
|   |   └── ...
|   └── ...
└── ...
```
