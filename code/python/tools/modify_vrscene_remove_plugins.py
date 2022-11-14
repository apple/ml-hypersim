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
parser.add_argument("--remove_plugins", nargs="+")
args = parser.parse_args()

assert os.path.exists(args.in_file)



print("[HYPERSIM: MODIFY_VRSCENE_REMOVE_PLUGINS] Begin...")



output_dir = os.path.dirname(args.out_file)
if output_dir == "":
    output_dir = "."

if not os.path.exists(output_dir): os.makedirs(output_dir)



with open(args.in_file, "r") as in_file:
    in_lines  = in_file.readlines()



# remove all plugins from the remove list and store their names
tmp_lines = []
remove_plugin_names = []
remove = False

for in_line in in_lines:
    
    in_line_tokens = in_line.split()

    for remove_plugin in args.remove_plugins:
        if len(in_line_tokens) == 3 and in_line_tokens[0] == remove_plugin and in_line_tokens[2] == "{":
            print("[HYPERSIM: MODIFY_VRSCENE_REMOVE_PLUGINS] REMOVING PLUGIN: " + in_line)
            remove = True
            remove_plugin_names.append(in_line_tokens[1])
            break

    if not remove:
        tmp_lines.append(in_line)

    # turn off removing if the current line starts with a closing bracket
    if len(in_line_tokens) == 1 and in_line_tokens[0] == "}":
        remove = False



print("[HYPERSIM: MODIFY_VRSCENE_REMOVE_PLUGINS] REMOVING REFERENCES TO REMOVED PLUGINS: " + str(remove_plugin_names))

# remove all references to removed plugins
in_lines = tmp_lines
tmp_lines = []

for in_line in in_lines:

    # turn on removing if the current line starts with anything from the remove list
    in_line_tokens = in_line.replace("=", " ").replace("(", " ").replace(")", " ").split()

    if len(in_line_tokens) >= 1:
        if in_line_tokens[0] == "ListIntHex" or in_line_tokens[0] == "ListVectorHex":
            tmp_lines.append(in_line)
            continue

    if len(in_line_tokens) >= 2:
        if in_line_tokens[1] == "ListIntHex" or in_line_tokens[1] == "ListVectorHex":
            tmp_lines.append(in_line)
            continue

    for remove_plugin_name in remove_plugin_names:
        if remove_plugin_name in in_line:
            print("[HYPERSIM: MODIFY_VRSCENE_REMOVE_PLUGINS] REMOVING PLUGIN NAME " + remove_plugin_name + " FROM LINE: " + in_line)
            in_line = in_line.replace(remove_plugin_name + ", ", "")
            in_line = in_line.replace(remove_plugin_name + ",", "")
            in_line = in_line.replace(remove_plugin_name, "")

    tmp_lines.append(in_line)



# write lines to file
out_lines = tmp_lines
with open(args.out_file, "w") as out_file:
    for out_line in out_lines:
        out_file.write(out_line)



print("[HYPERSIM: MODIFY_VRSCENE_REMOVE_PLUGINS] Finished.")
