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

# Represents an LLVM Target.
class Target:
    def __init__(self, llvm_target_name, llvm_td_name, zig_target_name):
        self.target_dir = llvm_target_name
        self.td_name = llvm_td_name
        self.output_name = zig_target_name


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

TABLEGEN_FILE_SUFFIX = "_tablegen.cpp"


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

    args = arg_parser.parse_args()

    llvm_source_root = args.llvm_source_dir
    llvm_target_dir = os.path.join(llvm_source_root, "lib/Target")

    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    tblgen_path = args.tblgen_exe
    print(tblgen_path)

    if not os.path.isdir(output_dir):
        print("[!] Output dir must exist!", file=sys.stderr)
        sys.exit(1)

    # First, run LLVM tablegen for all chosen targets.
    for target in TARGETS:
        print("= {}".format(target.output_name))

        with open(os.path.join(output_dir, target.output_name + TABLEGEN_FILE_SUFFIX), "w") as tablegen_out:
            target_dir = os.path.join(llvm_target_dir, target.target_dir)

            print("  > Running tablegen...")
            subprocess.run(
                [tblgen_path, target.td_name, "-I", "../../../include", "--gen-subtarget"],
                cwd=target_dir,
                stdout=tablegen_out
            ).check_returncode()
        

if __name__ == "__main__":
    main()
