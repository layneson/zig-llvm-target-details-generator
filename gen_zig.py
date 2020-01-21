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

import re

zig_ident_re = re.compile("[a-zA-Z_][a-zA-Z0-9_]*")
int_re = re.compile("[iu][0-9]+")

def convert_name(name):
    name = name.replace("-", "_")
    name = name.replace(".", "_")

    if int_re.match(name) is not None:
        name = '_' + name

    if zig_ident_re.match(name) is None:
        name = '@"' + name + '"'

    return name


def generate_zig_code(out_file, arch_name, target_details):
    out_file.write('const std = @import("../std.zig");\n')
    out_file.write("const Cpu = std.Target.Cpu;\n")
    out_file.write("\n")
    out_file.write("pub const Feature = enum {\n")
    
    features = target_details["features"]
    features.sort(key=lambda f: f["llvm_name"])

    features_by_def_name = {feature["def_name"]: feature for feature in features}

    cpus = target_details["cpus"]
    cpus.sort(key=lambda c: c["llvm_name"])

    for feature in features:
        tag_name = convert_name(feature["llvm_name"])

        out_file.write(f"    {tag_name},\n")

    out_file.write("};\n")
    out_file.write("\n")

    out_file.write("pub usingnamespace Cpu.Feature.feature_set_fns(Feature);\n")
    out_file.write("\n")

    out_file.write("pub const all_features = blk: {\n")
    out_file.write("    const len = @typeInfo(Feature).Enum.fields.len;\n")
    out_file.write("    std.debug.assert(len <= @typeInfo(Cpu.Feature.Set).Int.bits);\n")
    out_file.write("    var result: [len]Cpu.Feature = undefined;\n");

    for feature in features:
        llvm_name = feature["llvm_name"]
        tag_name = convert_name(llvm_name)
        description = feature["description"]
        deps = feature["dependencies"]

        out_file.write(f"    result[@enumToInt(Feature.{tag_name})] = .{{\n")
        out_file.write(f"        .index = @enumToInt(Feature.{tag_name}),\n")
        out_file.write(f"        .name = @tagName(Feature.{tag_name}),\n")
        out_file.write(f'        .llvm_name = "{llvm_name}",\n')
        out_file.write(f'        .description = "{description}",\n')

        if len(deps) > 0: 
            out_file.write("        .dependencies = featureSet(&[_]Feature{\n")

            for dep in deps:
                dep_feature = features_by_def_name[dep]
                dep_tag_name = convert_name(dep_feature["llvm_name"])

                indent = " " * 12
                out_file.write(f"{indent}.{dep_tag_name},\n")

            out_file.write("        }),\n")
        else:
            out_file.write("        .dependencies = 0,\n")

        out_file.write("    };\n")

    out_file.write("    break :blk result;\n")
    out_file.write("};\n")
    out_file.write("\n")

    out_file.write("pub const cpu = struct {\n")

    for cpu in cpus:
        llvm_name = cpu["llvm_name"]
        name = convert_name(llvm_name)
        deps = cpu["dependencies"]

        out_file.write(f"    pub const {name} = Cpu{{\n")
        out_file.write(f'        .name = "{name}",\n')
        out_file.write(f'        .llvm_name = "{llvm_name}",\n')

        if len(deps) > 0: 
            out_file.write("        .features = featureSet(&[_]Feature{\n")

            for dep in deps:
                dep_feature = features_by_def_name[dep]
                dep_tag_name = convert_name(dep_feature["llvm_name"])

                indent = " " * 12
                out_file.write(f"{indent}.{dep_tag_name},\n")

            out_file.write("        }),\n")
        else:
            out_file.write("        .features = 0,\n")

        out_file.write("    };\n")

    out_file.write("};\n")
    out_file.write("\n")

    out_file.write(f"/// All {arch_name} CPUs, sorted alphabetically by name.\n")
    out_file.write( 
        "/// TODO: Replace this with usage of `std.meta.declList`. It does work, but stage1\n"
        "/// compiler has inefficient memory and CPU usage, affecting build times.\n")
    out_file.write("pub const all_cpus = &[_]*const Cpu{\n")

    for cpu in cpus:
        name = convert_name(cpu["llvm_name"])

        out_file.write(f"    &cpu.{name},\n")

    out_file.write("};\n")
