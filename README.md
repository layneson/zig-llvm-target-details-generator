# Zig LLVM Target Details Generator
This repo contains scripts that can be used to transform information about LLVM-supported target features and CPUs into representative code for the Zig standard library.

## Prereqs
LLVM v9 source is required, as well as the LLVM v9 `llvm-tblgen` executable.

## Run
Run `python3 gen.py <path-to-llvm-src-dir>`. Use `-h` for other optional arguments.
