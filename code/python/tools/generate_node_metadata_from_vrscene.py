#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import pandas as pd
import time
import vray

parser = argparse.ArgumentParser()
parser.add_argument("--in_vrscene_file", required=True)
parser.add_argument("--in_mesh_metadata_objects_file", required=True)
parser.add_argument("--out_metadata_nodes_file", required=True)
parser.add_argument("--out_metadata_node_strings_file", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_vrscene_file)
assert os.path.exists(args.in_mesh_metadata_objects_file)



print("[HYPERSIM: GENERATE_NODE_METADATA_FROM_VRSCENE] Begin...")



output_metadata_nodes_dir        = os.path.dirname(args.out_metadata_nodes_file)
output_metadata_node_strings_dir = os.path.dirname(args.out_metadata_node_strings_file)

if output_metadata_nodes_dir == "":
    output_metadata_nodes_dir = "."
if output_metadata_node_strings_dir == "":
    output_metadata_node_strings_dir = "."

if not os.path.exists(output_metadata_nodes_dir): os.makedirs(output_metadata_nodes_dir)
if not os.path.exists(output_metadata_node_strings_dir): os.makedirs(output_metadata_node_strings_dir)



renderer = vray.VRayRenderer()
def log_msg(renderer, message, level, instant):
    print(str(instant) + " " + str(level) + " " + message)
renderer.setOnLogMessage(log_msg)
renderer.load(args.in_vrscene_file)
time.sleep(0.5)



print("[HYPERSIM: GENERATE_NODE_METADATA_FROM_VRSCENE] Extracting human-readable strings from all nodes...")



# note that we traverse in depth-first order because it makes it easier to detect cycles,
# see https://stackoverflow.com/questions/2869647/why-dfs-and-not-bfs-for-finding-cycle-in-graphs
def get_strings_for_plugin(plugin):

    nodes_to_visit          = []
    path_prefixes           = []
    nodes_to_visit_added_by = []
    traversal_stack         = []

    strings = []
    paths   = []

    nodes_to_visit.append(plugin)
    path_prefixes.append("<root>")
    nodes_to_visit_added_by.append(None)

    while len(nodes_to_visit) > 0:

        node        = nodes_to_visit.pop(0)
        path_prefix = path_prefixes.pop(0)
        added_by    = nodes_to_visit_added_by.pop(0)

        if len(traversal_stack) != 0:
            while traversal_stack[-1] != added_by:
                traversal_stack.pop()

        if isinstance(node, str):
            strings.append(node)
            paths.append(path_prefix)

        if isinstance(node, vray.Plugin) and not isinstance(node, vray.PluginRef):

            strings.append(str(node))
            paths.append(path_prefix)

            node_key = str(node)
            traversal_stack.append(node_key)

            tmp_nodes_to_visit          = []
            tmp_path_prefixes           = []
            tmp_nodes_to_visit_added_by = []

            for param_name in sort(list(node.getMeta().keys())):

                param      = node.__getitem__(param_name)
                param_meta = node.getMeta()[param_name]

                if isinstance(param, str):
                    tmp_nodes_to_visit.append(param)
                    tmp_path_prefixes.append(path_prefix + "." + param_name)
                    tmp_nodes_to_visit_added_by.append(node_key)

                if isinstance(param, vray.Plugin) and not isinstance(param, vray.PluginRef):
                    param_key = str(param)
                    if param_key not in traversal_stack:
                        tmp_nodes_to_visit.append(param)
                        tmp_path_prefixes.append(path_prefix + "." + param_name)
                        tmp_nodes_to_visit_added_by.append(node_key)

                if isinstance(param, vray.List) and param_meta["type"] == "List<String>":
                    for i in range(len(param)):
                        pi_ = param[i]
                        tmp_nodes_to_visit.append(pi_)
                        tmp_path_prefixes.append(path_prefix + "." + param_name + "[" + str(i) + "]")
                        tmp_nodes_to_visit_added_by.append(node_key)

                if isinstance(param, vray.List) and param_meta["type"] == "List<Plugin>":
                    for i in range(len(param)):
                        pi_       = param[i]
                        param_key = str(pi_)
                        if not isinstance(pi_, vray.PluginRef) and param_key not in traversal_stack:
                            tmp_nodes_to_visit.append(pi_)
                            tmp_path_prefixes.append(path_prefix + "." + param_name + "[" + str(i) + "]")
                            tmp_nodes_to_visit_added_by.append(node_key)

            nodes_to_visit          = tmp_nodes_to_visit          + nodes_to_visit
            path_prefixes           = tmp_path_prefixes           + path_prefixes
            nodes_to_visit_added_by = tmp_nodes_to_visit_added_by + nodes_to_visit_added_by

    assert len(nodes_to_visit) == 0
    assert len(path_prefixes) == 0
    assert len(nodes_to_visit_added_by) == 0

    return paths, strings



# rename_axis() sets the name of the current index
# reset_index() demotes the existing index to a column and creates a new unnamed index
# set_index() sets the current index 
df_objects = pd.read_csv(args.in_mesh_metadata_objects_file).rename_axis("object_id").reset_index().set_index("object_name")

nodes = renderer.classes.Node.getInstances()

df_nodes        = pd.DataFrame(columns=["node_id", "node_name", "object_id", "object_name"])
df_node_strings = pd.DataFrame(columns=["node_id", "path", "string"])

for n in nodes:

    node_id = int(n.objectID)

    print("node_id = %05d (%s)" % (node_id,n))
    
    object_name = str(n).split("@")[0]
    if object_name in df_objects.index:
        object_id     = df_objects.loc[object_name]["object_id"]
        df_nodes_curr = pd.DataFrame(columns=["node_id", "node_name", "object_id", "object_name"], data={"node_id":[node_id], "node_name":[str(n)], "object_id":[object_id], "object_name":[object_name]})
    else:
        df_nodes_curr = pd.DataFrame(columns=["node_id", "node_name", "object_id", "object_name"], data={"node_id":[node_id], "node_name":[str(n)], "object_id":[-1],        "object_name":["_NULL_OBJECT"]})
    df_nodes = df_nodes.append(df_nodes_curr, ignore_index=True)

    n_paths, n_strings   = get_strings_for_plugin(n)
    df_node_strings_curr = pd.DataFrame(columns=["node_id", "path", "string"], data={"node_id":node_id, "path":n_paths, "string":n_strings})
    df_node_strings      = df_node_strings.append(df_node_strings_curr, ignore_index=True)

df_nodes.to_csv(args.out_metadata_nodes_file, index=False)
df_node_strings.to_csv(args.out_metadata_node_strings_file, index=False)

print("[HYPERSIM: GENERATE_NODE_METADATA_FROM_VRSCENE] Finished generating node metadata.")

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: GENERATE_NODE_METADATA_FROM_VRSCENE] Finished.")
