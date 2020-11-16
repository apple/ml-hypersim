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
parser.add_argument("--out_vrscene_file", required=True)
parser.add_argument("--set_nodes_invisible_if_not_in_mesh", action="store_true")
parser.add_argument("--set_lights_invisible", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.in_vrscene_file)
assert os.path.exists(args.in_mesh_metadata_objects_file)



print("[HYPERSIM: MODIFY_VRSCENE_SET_UNIQUE_RENDER_ENTITY_IDS] Begin...")



output_dir = os.path.dirname(args.out_vrscene_file)

if output_dir == "":
    output_dir = "."

if not os.path.exists(output_dir): os.makedirs(output_dir)



renderer = vray.VRayRenderer()
def log_msg(renderer, message, level, instant):
    print(str(instant) + " " + str(level) + " " + message)
renderer.setOnLogMessage(log_msg)
renderer.load(args.in_vrscene_file)
time.sleep(0.5)



# rename_axis() sets the name of the current index
# reset_index() demotes the existing index to a column and creates a new unnamed index
# set_index() sets the current index 
df_objects = pd.read_csv(args.in_mesh_metadata_objects_file).rename_axis("object_id").reset_index().set_index("object_name")



render_entity_id = 1

nodes = renderer.classes.Node.getInstances()
for n in nodes:
    n.objectID = render_entity_id
    render_entity_id = render_entity_id + 1
    if args.set_nodes_invisible_if_not_in_mesh:
        object_name = str(n).split("@")[0]
        if object_name not in df_objects.index:
            n.visible = False

light_rectangles = renderer.classes.LightRectangle.getInstances()
for l in light_rectangles:
    l.objectID       = render_entity_id
    render_entity_id = render_entity_id + 1
    if args.set_lights_invisible:
        l.invisible = True

light_meshes = renderer.classes.LightMesh.getInstances()
for l in light_rectangles:
    l.objectID       = render_entity_id
    render_entity_id = render_entity_id + 1
    if args.set_lights_invisible:
        l.invisible = True

lights_domes = renderer.classes.LightDome.getInstances()
for l in lights_domes:
    l.objectID       = render_entity_id
    render_entity_id = render_entity_id + 1
    if args.set_lights_invisible:
        l.invisible = True



renderer.export(args.out_vrscene_file)
print("[HYPERSIM: MODIFY_VRSCENE_SET_UNIQUE_RENDER_ENTITY_IDS] Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: MODIFY_VRSCENE_SET_UNIQUE_RENDER_ENTITY_IDS] Finished.")
