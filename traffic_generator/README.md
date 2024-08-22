# Traffic Generator

```
traffic_generator/
├── Makefile               -> makefile
├── parser/                -> parse model json to cpp 
├── top.cpp                -> main function
├── traffic_generator/     -> generate traffic patterns
└── workload_analysis/     -> do model splitting & workload analysis
```

## Build

```sh
cd traffic_generator && make
```

## Run
```sh
./traffic_generator/top files/DSE/XXX.json
```

## Weight Aggregation
Use Weight Aggregation
```cpp
#define TRAFFIC_OPTIMIZE 1
```
Not Use Weight Aggregation
```cpp
// #define TRAFFIC_OPTIMIZE 1
```

## Debug
See the debug message
```cpp
#define DEBUG 1
```
Not see the debug message
```cpp
// #define DEBUG 1
```


