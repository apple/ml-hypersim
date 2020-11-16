#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_file", required=True)
parser.add_argument("--replace_old_path", required=True)
parser.add_argument("--replace_new_path", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_file)



print("[HYPERSIM: MODIFY_VRSCENE_REPLACE_PATHS] Begin...")



output_dir = os.path.dirname(args.out_file)
if output_dir == "":
    output_dir = "."

if not os.path.exists(output_dir): os.makedirs(output_dir)



replace_startswith_list = [ "file", "ies_file", "auto_save_file", "#include" ]

with open(args.in_file, "r") as in_file:

    in_lines  = in_file.readlines()
    out_lines = []

    for in_line in in_lines:

        in_line_strip = in_line.strip()
        replace = False
        for replace_startswith_str in replace_startswith_list:
            if in_line_strip.startswith(replace_startswith_str):
                replace = True
                break

        if replace:
            out_lines.append(in_line.replace(args.replace_old_path, args.replace_new_path))
        else:
            out_lines.append(in_line)

with open(args.out_file, "w") as out_file:
    for out_line in out_lines:
        out_file.write(out_line)



print("[HYPERSIM: MODIFY_VRSCENE_REPLACE_PATHS] Finished.")
