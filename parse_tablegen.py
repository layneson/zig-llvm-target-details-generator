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
import sys

class Feature:
    def __init__(self, id, def_name):
        self.def_name = def_name
        self.id = id
        
        self.llvm_name = None
        self.description = None
        self.dependencies = [0, 0, 0]

    def __str__(self):
        return f"{self.id}: {self.def_name}({self.pretty_name}) = '{self.description}'"


class Cpu:
    def __init__(self, llvm_name, dependencies):
        self.llvm_name = llvm_name
        self.dependencies = dependencies

    def __str__(self):
        return f"'{self.llvm_name}'"


def is_bit_set(deps, idx):
    bin = idx // 64
    offset = idx % 64

    return (deps[bin] & (1 << offset)) != 0


def gather_dependencies(deps, features, blacklist):
    # Given a list of features and a dep bitmap, gather a list of dep def_names,
    # in accordance with the blacklist.
    
    features_by_id = {feature.id: feature for feature in features}

    dep_def_names = []

    for feature in features:
        if is_bit_set(deps, feature.id):
            if feature.def_name in blacklist:
                # Explore its dependencies. Even though this is blacklisted, its deps might not be.
                blacklisted_deps = gather_dependencies(feature.dependencies, features, blacklist)
                for dep in blacklisted_deps:
                    if dep not in dep_def_names:
                        dep_def_names.append(dep)
            else:
                if feature.def_name not in dep_def_names:
                    dep_def_names.append(feature.def_name)

    return dep_def_names


def resolve_details(features, cpus, blacklist):
    # Basic idea: resolve the dependency bitmaps according to the blacklist. 

    target_details = {
        "features": [],
        "cpus": []
    }

    for feature in features:
        # Turn its dependency bitmap into a nice list.
        
        if feature.def_name in blacklist:
            continue
        
        dependency_def_names = gather_dependencies(feature.dependencies, features, blacklist)

        target_details["features"].append({
            "def_name": feature.def_name,
            "llvm_name": feature.llvm_name,
            "description": feature.description,
            "dependencies": dependency_def_names
        })

    for cpu in cpus:
        dependency_def_names = gather_dependencies(cpu.dependencies, features, blacklist)

        target_details["cpus"].append({
            "llvm_name": cpu.llvm_name,
            "dependencies": dependency_def_names
        })

    return target_details    


def parse_info_lines(feature_def_lines, feature_info_lines, cpu_info_lines):
    feature_def_re = re.compile(r"\s*(?P<def_name>\w+)\s*=\s*(?P<def_value>\d+).*")

    features = []
    features_by_def_name = {}

    for def_line in feature_def_lines:
        m = feature_def_re.match(def_line)
        if m is None:
            print("[!] Invalid feature def line (internal error)!", file=sys.stderr)
            sys.exit(1)

        def_name = m.group("def_name")
        def_value = int(m.group("def_value"))

        if def_name == "NumSubtargetFeatures":
            continue

        # The enum members are always 0-n, in-order.
        feature = Feature(def_value, def_name)
        features.append(feature)
        features_by_def_name[feature.def_name] = feature
    
    # "a35", "Cortex-A35 ARM processors", AArch64::ProcA35,    0x20800080800800ULL, 0x0ULL, 0x0ULL,    ,
    feature_info_re = re.compile(
        r'\s*"(?P<pretty_name>.*)",'
        r'\s*"(?P<description>.*)",'
        r"\s*.*::(?P<def_name>.*),"
        r"\s*(?P<b0>[0-9a-fA-FxX]+)ULL,"
        r"\s*(?P<b1>[0-9a-fA-FxX]+)ULL,"
        r"\s*(?P<b2>[0-9a-fA-FxX]+)ULL,"
        r".*")

    # Some features, for whatever reason, cannot be provided on the command line.
    # They do not have an entry in the feature info section.
    # So here, we collect the features that do show up here.
    real_features = []

    for info_line in feature_info_lines:
        # Removing braces will make these easier to parse.
        info_line = info_line.replace("{", "")
        info_line = info_line.replace("}", "")

        m = feature_info_re.match(info_line)
        if m is None:
            print("[!] Invalid feature info line (internal error)!", file=sys.stderr)
            sys.exit(1)

        def_name = m.group("def_name")

        feature = features_by_def_name[def_name]

        feature.llvm_name = m.group("pretty_name")
        feature.description = m.group("description")

        b0 = int(m.group("b0"), 16)
        b1 = int(m.group("b1"), 16)
        b2 = int(m.group("b2"), 16)

        feature.dependencies = [b0, b1, b2]

        real_features.append(feature)

    # "apple-latest", 0x0ULL, 0x0ULL, 0x10ULL, , &CycloneModel ,
    cpu_info_re = re.compile(
        r'\s*"(?P<pretty_name>.*)",'
        r"\s*(?P<b0>[0-9a-fA-FxX]+)ULL,"
        r"\s*(?P<b1>[0-9a-fA-FxX]+)ULL,"
        r"\s*(?P<b2>[0-9a-fA-FxX]+)ULL,"
        r".*")

    cpus = []

    for info_line in cpu_info_lines:
        info_line = info_line.replace("{", "")
        info_line = info_line.replace("}", "")
        
        m = cpu_info_re.match(info_line)
        if m is None:
            print("[!] Invalid cpu info line (internal error)!", file=sys.stderr)
            sys.exit(1)

        llvm_name = m.group("pretty_name")

        b0 = int(m.group("b0"), 16)
        b1 = int(m.group("b1"), 16)
        b2 = int(m.group("b2"), 16)

        cpus.append(Cpu(llvm_name, [b0, b1, b2]))

    return (real_features, cpus)


def parse_tablegen_file(tablegen_file, blacklist):
    # Scan through file, line by line.
    # Attack this in three sections:
    #   1. Feature definition.
    #   2. Feature dependency info.
    #   3. CPU definition and dependency info.

    find_enum_start_re = re.compile(r"\s*enum \{\s*")

    # Move past start of enum.
    while True:
        line = tablegen_file.readline()

        if find_enum_start_re.match(line) is not None:
            break
    
    find_enum_end_re = re.compile(r"\s*\};\s*")
    feature_def_lines = []

    # Find end of enum, while adding encountered lines to list.
    while True:
        line = tablegen_file.readline()

        if find_enum_end_re.match(line) is not None:
            break

        feature_def_lines.append(line)

    find_features_start_re = re.compile(r"\s*extern const llvm::SubtargetFeatureKV.*=.*")

    # Find the start of feature dep info.
    while True:
        line = tablegen_file.readline()

        if find_features_start_re.match(line) is not None:
            break

    feature_info_lines = []

    # Find the end of the feature dep info, while adding encountered lines to list.
    # End-of-enum re can be used here for the end of the feature array.
    while True:
        line = tablegen_file.readline()

        if find_enum_end_re.match(line) is not None:
            break

        feature_info_lines.append(line)

    find_cpus_start_re = re.compile(r"\s*extern const llvm::SubtargetSubTypeKV.*=.*")

    # Find the start of CPU info.
    while True:
        line = tablegen_file.readline()

        if find_cpus_start_re.match(line) is not None:
            break

    cpu_info_lines = []

    # Find the end of the cpu info, while adding encountered lines to list.
    # As above, end-of-enum re can be used here.
    while True:
        line = tablegen_file.readline()

        if find_enum_end_re.match(line) is not None:
            break

        cpu_info_lines.append(line)

    features, cpus = parse_info_lines(feature_def_lines, feature_info_lines, cpu_info_lines)

    return resolve_details(features, cpus, blacklist)
