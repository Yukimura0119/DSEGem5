import typing

kernel = {"Conv": {},
          "BatchNormalization": {},
          "Relu": {},
          "Add": {},
          "GlobalAveragePool": {},
          }

kernel["Conv"] = {
    "N": 1,
    "C": 32,
    "H": 32,
    "W": 32,
    "Stride": 2,
    "Padding": 3
}

kernel["Relu"] = {
    "N": 1,
    "C": 32,
    "H": 32,
    "W": 32
}

kernel["BatchNormalization"] = {
    "N": 1,
    "C": 32,
    "H": 32,
    "W": 32
}

kernel["Add"] = {
    "N": 1,
    "C": 64,
    "H": 32,
    "W": 32
}

kernel["GlobalAveragePool"] = {
    "N": 1,
    "C": 64,
    "H": 32,
    "W": 32,
    "R": 7,
    "S": 7
}
kernel["Reshape"] = {
    "N": 1,
    "C": 64,
    "H": 32,
    "W": 32
}

kernel["MaxPool"] = {
    "N": 1,
    "C": 64,
    "H": 32,
    "W": 32,
    "R": 7,
    "S": 7
}

kernel["Flatten"] = {
    "N": 1,
    "C": 64,
    "H": 32,
    "W": 32
}

kernel["Gemm"] = {
    "N": 1,
    "C": 64,
    "H": 32,
    "W": 32
}
