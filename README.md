# Zig LLVM Target Details Generator
This project transforms information about LLVM-supported target features and CPUs into representative code for the Zig standard library.

## Prereqs
- Python 3
- LLVM v9 source code
- `llvm-tblgen` executable

## Usage
Run `python3 gen.py <path-to-llvm-src-dir>`. Use `-h` to see a list of optional arguments.

There is a basic blacklist file that is included in this repo. Add `-blacklist blacklist.txt` to the above command to use it.
The `blacklist.txt` file contains any "features" whose definition names do not start with `Feature`. This generally includes
feature families, processor families, sub-architectures, etc.

## Progress
- [x] Parse LLVM tablegen output.
- [x] Resolve feature dependencies with blacklist support.
- [x] Generate JSON files describing all details for each target arch.
- [x] Generate Zig code describing all details for each target arch.
