cmake_minimum_required(VERSION 3.7)
project(graphology_py)

set(CMAKE_CXX_STANDARD 11)

set(SOURCE_FILES main.cpp)
add_executable(graphology_py ${SOURCE_FILES})