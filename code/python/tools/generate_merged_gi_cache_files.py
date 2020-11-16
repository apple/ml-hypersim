#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import glob
import inspect
import os
import shlex
import subprocess
import sys

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--in_light_cache_files", required=True)
parser.add_argument("--in_irradiance_map_files", required=True)
parser.add_argument("--out_light_cache_file", required=True)
parser.add_argument("--out_irradiance_map_file", required=True)
args = parser.parse_args()



print("[HYPERSIM: GENERATE_MERGED_GI_CACHE_FILES] Begin...")



input_light_cache_dir = os.path.dirname(args.in_light_cache_files)
if input_light_cache_dir == "":
    input_light_cache_dir = "."

input_irradiance_map_dir = os.path.dirname(args.in_irradiance_map_files)
if input_irradiance_map_dir == "":
    input_irradiance_map_dir = "."

output_light_cache_dir = os.path.dirname(args.out_light_cache_file)
if output_light_cache_dir == "":
    output_light_cache_dir = "."

output_irradiance_map_dir = os.path.dirname(args.out_irradiance_map_file)
if output_irradiance_map_dir == "":
    output_irradiance_map_dir = "."

assert os.path.exists(input_light_cache_dir)
assert os.path.exists(input_irradiance_map_dir)

if not os.path.exists(output_light_cache_dir): os.makedirs(output_light_cache_dir)
if not os.path.exists(output_irradiance_map_dir): os.makedirs(output_irradiance_map_dir)



in_light_cache_files    = sort(glob.glob(args.in_light_cache_files))
in_irradiance_map_files = sort(glob.glob(args.in_irradiance_map_files))

if sys.platform == "win32":
    in_light_cache_files    = [f.replace("\\", "\\\\") for f in in_light_cache_files]
    in_irradiance_map_files = [f.replace("\\", "\\\\") for f in in_irradiance_map_files]
    out_light_cache_file    = args.out_light_cache_file.replace("\\", "\\\\")
    out_irradiance_map_file = args.out_irradiance_map_file.replace("\\", "\\\\")
else:
    in_light_cache_files    = in_light_cache_files
    in_irradiance_map_files = in_irradiance_map_files
    out_light_cache_file    = args.out_light_cache_file
    out_irradiance_map_file = args.out_irradiance_map_file

light_cache_merge_args    = " -incremental -load " + " -load ".join(in_light_cache_files)    + " -save " + out_light_cache_file    + " -nodisplay"
irradiance_map_merge_args = " -incremental -load " + " -load ".join(in_irradiance_map_files) + " -save " + out_irradiance_map_file + " -nodisplay"

if len(in_light_cache_files) > 0:
    cmd = _system_config.imapviewer_bin + light_cache_merge_args
    print("")
    print(cmd)
    print("")
    if sys.platform == "win32":
        retval = subprocess.run(shlex.split(cmd)) # do not use os.system because it can't handle very long command-line arguments on Windows
        retval.check_returncode()
    else:
        retval = os.system(cmd)
        assert retval == 0
else:
    print("[HYPERSIM: GENERATE_MERGED_GI_CACHE_FILES] No light cache input files found, nothing to merge...")

if len(in_irradiance_map_files) > 0:
    cmd = _system_config.imapviewer_bin + irradiance_map_merge_args
    print("")
    print(cmd)
    print("")
    if sys.platform == "win32":
        retval = subprocess.run(shlex.split(cmd)) # do not use os.system because it can't handle very long command-line arguments on Windows
        retval.check_returncode()
    else:
        retval = os.system(cmd)
        assert retval == 0
else:
    print("[HYPERSIM: GENERATE_MERGED_GI_CACHE_FILES] No irradiance map input files found, nothing to merge...")



print("[HYPERSIM: GENERATE_MERGED_GI_CACHE_FILES] Finished.")
