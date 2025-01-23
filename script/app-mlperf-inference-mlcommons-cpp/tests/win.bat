rem TBD: current not compiling - need to check ...

mlcr "install llvm prebuilt" --version=16.0.4
mlcr "install llvm prebuilt" --version=17.0.6

mlcr "get lib onnxruntime lang-cpp _cpu" --version=1.11.1
mlcr "get lib onnxruntime lang-cpp _cpu" --version=1.13.1
mlcr "get lib onnxruntime lang-cpp _cpu" --version=1.15.1
