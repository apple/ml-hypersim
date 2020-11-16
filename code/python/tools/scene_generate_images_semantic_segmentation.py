#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import glob
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", required=True)
parser.add_argument("--camera_name", required=True)
parser.add_argument("--segmentation_type", required=True)
args = parser.parse_args()

assert os.path.exists(args.scene_dir)
assert args.segmentation_type == "semantic_instance" or args.segmentation_type == "semantic"



print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION] Begin...")



detail_dir = os.path.join(args.scene_dir, "_detail")
images_dir = os.path.join(args.scene_dir, "images")

in_scene_fileroot                    = "scene"
in_render_entity_id_hdf5_dir         = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_geometry_hdf5")
in_render_entity_id_hdf5_files       = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_geometry_hdf5", "frame.*.render_entity_id.hdf5")
in_metadata_nodes_file               = os.path.join(detail_dir, "metadata_nodes.csv")
out_hdf5_dir                         = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_geometry_hdf5")
out_preview_dir                      = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_geometry_preview")
out_segmentation_name                = args.segmentation_type

if args.segmentation_type == "semantic_instance":
    in_mesh_objects_segmentation_file    = os.path.join(detail_dir, "mesh", "mesh_objects_sii.hdf5")
    in_metadata_segmentation_colors_file = os.path.join(detail_dir, "mesh", "metadata_semantic_instance_colors.hdf5")
if args.segmentation_type == "semantic":
    in_mesh_objects_segmentation_file    = os.path.join(detail_dir, "mesh", "mesh_objects_si.hdf5")
    in_metadata_segmentation_colors_file = os.path.join(detail_dir, "mesh", "metadata_semantic_colors.hdf5")



with h5py.File(in_mesh_objects_segmentation_file, "r") as f: mesh_object_ids_to_segmentation_indices = matrix(f["dataset"][:,0]).A1.astype(int32)
mesh_object_id_max  = mesh_object_ids_to_segmentation_indices.shape[0]-1

with h5py.File(in_metadata_segmentation_colors_file, "r") as f: segmentation_ids_to_segmentation_colors = f["dataset"][:]
segmentation_id_max = segmentation_ids_to_segmentation_colors.shape[0]-1

df_nodes    = pd.read_csv(in_metadata_nodes_file)
node_ids_   = df_nodes["node_id"].to_numpy()
node_ids    = r_[-1,node_ids_]
node_id_max = node_ids_.shape[0]

# Nodes are assigned render_entity_ids from 1 to N in modify_vrscene_set_unique_render_entity_ids.py,
# then node metadata is subsequently generated for all nodes in generate_node_metadata_from_vrscene.py,
# so we expect the node ids we see here to be 1 to N.
assert all(node_ids_ == arange(1,node_id_max+1)) 

node_ids_to_mesh_object_ids_ = df_nodes["object_id"].to_numpy()
node_ids_to_mesh_object_ids  = r_[-1,node_ids_to_mesh_object_ids_]



in_filenames = [ os.path.basename(f) for f in sort(glob.glob(in_render_entity_id_hdf5_files)) ]

for in_filename in in_filenames:

    in_file_root = in_filename.replace(".render_entity_id.hdf5", "")

    in_render_entity_id_hdf5_file = os.path.join(in_render_entity_id_hdf5_dir, in_filename)
    out_hdf5_file                 = os.path.join(out_hdf5_dir, in_file_root + "." + out_segmentation_name + ".hdf5")
    out_png_file                  = os.path.join(out_preview_dir, in_file_root + "." + out_segmentation_name + ".png")

    try:
        with h5py.File(in_render_entity_id_hdf5_file, "r") as f: render_entity_id_img = f["dataset"][:].astype(int32)
    except:
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION] WARNING: COULD NOT LOAD RENDER ENTITY ID IMAGE: " + in_render_entity_id_hdf5_file + "...")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION]")
        continue

    mesh_object_id_img     = ones_like(render_entity_id_img)*-1
    segmentation_id_img    = ones_like(render_entity_id_img)*-1
    segmentation_color_img = zeros((render_entity_id_img.shape[0], render_entity_id_img.shape[1], 3), dtype=uint8)

    # nodes are assigned render_entity_ids 1 to N, and all lights are set to invisible, so we should never encounter a render_entity_id greater than node_id_max
    assert all(logical_or(render_entity_id_img == -1, logical_and(render_entity_id_img >= 1, render_entity_id_img <= node_id_max)))
    mesh_object_id_img[render_entity_id_img != -1] = node_ids_to_mesh_object_ids[render_entity_id_img[render_entity_id_img != -1]]

    assert all(logical_or(mesh_object_id_img == -1, logical_and(mesh_object_id_img >= 0, mesh_object_id_img <= mesh_object_id_max)))
    segmentation_id_img[mesh_object_id_img != -1] = mesh_object_ids_to_segmentation_indices[mesh_object_id_img[mesh_object_id_img != -1]]

    assert all(logical_or(segmentation_id_img == -1, logical_and(segmentation_id_img >= 1, segmentation_id_img <= segmentation_id_max)))
    segmentation_color_img[segmentation_id_img != -1] = segmentation_ids_to_segmentation_colors[segmentation_id_img[segmentation_id_img != -1]]

    print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION] Saving output files for the input file: " + in_render_entity_id_hdf5_file + "...")

    with h5py.File(out_hdf5_file, "w") as f: f.create_dataset("dataset", data=segmentation_id_img.astype(int16), compression="gzip", compression_opts=9)

    imsave(out_png_file, segmentation_color_img)



print("[HYPERSIM: SCENE_GENERATE_IMAGES_SEMANTIC_SEGMENTATION] Finished.")
