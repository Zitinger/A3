cmake_minimum_required(VERSION 3.25)
project(A3)

set(CMAKE_CXX_STANDARD 20)

add_executable(A3 main.cpp
        RandomStreamGen.cpp
        RandomStreamGen.h
        HashFuncGen.cpp
        HashFuncGen.h
        HyperLogLog.cpp
        HyperLogLog.h)
