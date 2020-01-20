"""
Copyright (c) 2020 Layne Gustafson.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import argparse
import sys
import os
import subprocess
import tempfile

from parse_tablegen import parse_tablegen_file

# Suffix to use for tablegen output files.
TABLEGEN_FILE_SUFFIX = "_tablegen.cpp"

# Represents an LLVM Target.
class Target:
    def __init__(self, llvm_target_name, llvm_td_name, zig_target_name):
        self.target_dir = llvm_target_name
        self.td_name = llvm_td_name
        self.output_name = zig_target_name

        self.tablegen_file_name = zig_target_name + TABLEGEN_FILE_SUFFIX


# Defines what targets are processed.
# This includes all LLVM targets supported by Zig that define features/CPUs.
TARGETS = [
    Target("AArch64", "AArch64.td", "aarch64"),
    Target("AMDGPU", "AMDGPU.td", "amdgpu"),
    Target("ARM", "ARM.td", "arm"),
    Target("AVR", "AVR.td", "avr"),
    Target("BPF", "BPF.td", "bpf"),
    Target("Hexagon", "Hexagon.td", "hexagon"),
    # Target("Lanai", "Lanai.td", "lanai"), # Excluded since it does not define any features.
    Target("Mips", "Mips.td", "mips"),
    Target("MSP430", "MSP430.td", "msp430"),
    Target("NVPTX", "NVPTX.td", "nvptx"),
    Target("PowerPC", "PPC.td", "powerpc"),
    Target("RISCV", "RISCV.td", "riscv"),
    Target("Sparc", "Sparc.td", "sparc"),
    Target("SystemZ", "SystemZ.td", "systemz"),
    Target("WebAssembly", "WebAssembly.td", "wasm"),
    Target("X86", "X86.td", "x86"),
    # Target("XCore", "XCore.td", "xcore"), # Excluded since it does not define any features.
]


def main():
    arg_parser = argparse.ArgumentParser(
        description="Generate Zig standard library representation of LLVM target feature/CPU information.", 
        allow_abbrev=False)

    arg_parser.add_argument(
        "llvm_source_dir", 
        help="path to LLVM top-level source directory")

    arg_parser.add_argument(
        "-tblgen-exe", 
        nargs="?", 
        default="llvm-tblgen-9", 
        help="(default: llvm-tblgen-9) override tablegen executable path")
    arg_parser.add_argument(
        "-output-dir", 
        nargs="?", 
        default="out", 
        help="(default: out) override output directory")
    arg_parser.add_argument(
        "-work-dir", 
        nargs="?", 
        default=None, 
        help="(default: <temporary dir>) override directory where intermediate results are stored")
    arg_parser.add_argument(
        "-cache-tablegen",
        action="store_true",
        help="(default: false) cache tablegen results, or use cached results if they exist. Can only be used in combination with -work-dir")

    args = arg_parser.parse_args()

    llvm_source_root = args.llvm_source_dir
    llvm_target_dir = os.path.join(llvm_source_root, "lib/Target")

    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    tblgen_path = args.tblgen_exe

    if not os.path.isdir(output_dir):
        print("[!] Output dir must exist!", file=sys.stderr)
        sys.exit(1)

    working_dir = args.work_dir or tempfile.mkdtemp(prefix="zig_gen_llvm_target_details")
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)

    # Only enable caching if a work dir is specified and caching is requested.
    tablegen_cache_enabled = args.work_dir is not None and args.cache_tablegen

    for target in TARGETS:
        print("= {}".format(target.output_name))

        tablegen_file_path = os.path.join(working_dir, target.tablegen_file_name)

        if not tablegen_cache_enabled or not os.path.isfile(tablegen_file_path):
            with open(tablegen_file_path, "w") as tablegen_out:
                target_dir = os.path.join(llvm_target_dir, target.target_dir)

                print("  > Running tablegen...")
                subprocess.run(
                    [tblgen_path, target.td_name, "-I", "../../../include", "--gen-subtarget"],
                    cwd=target_dir,
                    stdout=tablegen_out
                ).check_returncode()

        with open(tablegen_file_path, "r") as tablegen_in:
            print("  > Parsing tablegen...")
            target_details = parse_tablegen_file(tablegen_in)
            print(target_details)
        

if __name__ == "__main__":
    main()
