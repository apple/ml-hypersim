#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import inspect
import os
import pandas as pd

import path_utils
path_utils.add_path_to_sys_path("../lib", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import approx_mvbb_utils

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", required=True)
parser.add_argument("--bounding_box_type", required=True)
args = parser.parse_args()

assert os.path.exists(args.scene_dir)
assert args.bounding_box_type == "axis_aligned" or args.bounding_box_type == "object_aligned_2d" or args.bounding_box_type == "object_aligned_3d"



print("[HYPERSIM: SCENE_GENERATE_BOUNDING_BOXES] Begin...")



mesh_vertices_hdf5_file                     = os.path.join(args.scene_dir, "_detail", "mesh", "mesh_vertices.hdf5")
mesh_faces_vi_hdf5_file                     = os.path.join(args.scene_dir, "_detail", "mesh", "mesh_faces_vi.hdf5")
mesh_faces_oi_hdf5_file                     = os.path.join(args.scene_dir, "_detail", "mesh", "mesh_faces_oi.hdf5")
mesh_objects_sii_hdf5_file                  = os.path.join(args.scene_dir, "_detail", "mesh", "mesh_objects_sii.hdf5")
mesh_objects_si_hdf5_file                   = os.path.join(args.scene_dir, "_detail", "mesh", "mesh_objects_si.hdf5")
metadata_semantic_instance_colors_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_colors.hdf5")
metadata_semantic_colors_hdf5_file          = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_colors.hdf5")

if args.bounding_box_type == "axis_aligned":
    metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_axis_aligned_positions.hdf5")
    metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_axis_aligned_orientations.hdf5")
    metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_axis_aligned_extents.hdf5")
if args.bounding_box_type == "object_aligned_2d":
    metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_2d_positions.hdf5")
    metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_2d_orientations.hdf5")
    metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_2d_extents.hdf5")
if args.bounding_box_type == "object_aligned_3d":
    metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_3d_positions.hdf5")
    metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_3d_orientations.hdf5")
    metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_3d_extents.hdf5")



with h5py.File(mesh_vertices_hdf5_file,                     "r") as f: mesh_vertices                     = f["dataset"][:]
with h5py.File(mesh_faces_vi_hdf5_file,                     "r") as f: mesh_faces_vi                     = f["dataset"][:]
with h5py.File(mesh_faces_oi_hdf5_file,                     "r") as f: mesh_faces_oi                     = f["dataset"][:]
with h5py.File(mesh_objects_sii_hdf5_file,                  "r") as f: mesh_objects_sii                  = matrix(f["dataset"][:]).A1
with h5py.File(mesh_objects_si_hdf5_file,                   "r") as f: mesh_objects_si                   = matrix(f["dataset"][:]).A1
with h5py.File(metadata_semantic_instance_colors_hdf5_file, "r") as f: metadata_semantic_instance_colors = f["dataset"][:]
with h5py.File(metadata_semantic_colors_hdf5_file,          "r") as f: metadata_semantic_colors          = f["dataset"][:]



num_instances = metadata_semantic_instance_colors.shape[0]

bounding_box_positions    = np.inf*ones((num_instances,3))
bounding_box_orientations = np.inf*ones((num_instances,3,3))
bounding_box_extents      = np.inf*ones((num_instances,3))

for sii in unique(mesh_objects_sii):
    if sii == -1:
        continue

    color_sii = metadata_semantic_instance_colors[sii]
    fi_sii    = where(in1d(mesh_faces_oi, where(mesh_objects_sii == sii)[0]))[0]

    assert fi_sii.shape[0] > 0

    mesh_faces_vi_sii  = mesh_faces_vi[fi_sii]
    mesh_vertices_sii_ = mesh_vertices[mesh_faces_vi_sii.ravel()]

    if args.bounding_box_type == "axis_aligned":    

        print("[HYPERSIM: SCENE_GENERATE_BOUNDING_BOXES] Generating axis-aligned bounding box for semantic instance ID " + str(sii) + "...")

        mesh_vertices_sii_min    = np.min(mesh_vertices_sii_, axis=0)
        mesh_vertices_sii_max    = np.max(mesh_vertices_sii_, axis=0)
        mesh_vertices_sii_extent = mesh_vertices_sii_max - mesh_vertices_sii_min
        mesh_vertices_sii_center = mesh_vertices_sii_min + mesh_vertices_sii_extent/2.0

        bounding_box_center_world = matrix(mesh_vertices_sii_center).A
        bounding_box_extent_world = matrix(mesh_vertices_sii_extent).A
        R_world_from_obj          = matrix(identity(3))

    if args.bounding_box_type == "object_aligned_2d":

        print("[HYPERSIM: SCENE_GENERATE_BOUNDING_BOXES] Generating object-and-gravity-aligned bounding box for semantic instance ID " + str(sii) + "...")

        mesh_vertices_sii_min    = np.min(mesh_vertices_sii_, axis=0)
        mesh_vertices_sii_max    = np.max(mesh_vertices_sii_, axis=0)
        mesh_vertices_sii_extent = mesh_vertices_sii_max - mesh_vertices_sii_min
        mesh_vertices_sii_center = mesh_vertices_sii_min + mesh_vertices_sii_extent/2.0

        bounding_box_center_world = matrix(mesh_vertices_sii_center).A
        bounding_box_extent_world = matrix(mesh_vertices_sii_extent).A
        R_world_from_obj          = matrix(identity(3))

        tmp_dir = os.path.join(args.scene_dir, "_tmp")

        bounding_box_center_world_2d, bounding_box_extent_world_2d, bounding_box_orientation_2d = \
            approx_mvbb_utils.generate_oriented_bounding_box_2d(mesh_vertices_sii_[:,0:2],
                                                                tmp_dir=tmp_dir)

        bounding_box_center_world[0,0:2] = bounding_box_center_world_2d
        bounding_box_extent_world[0,0:2] = bounding_box_extent_world_2d
        R_world_from_obj[0:2,0:2]        = bounding_box_orientation_2d

    if args.bounding_box_type == "object_aligned_3d":

        print("[HYPERSIM: SCENE_GENERATE_BOUNDING_BOXES] Generating object-aligned bounding box for semantic instance ID " + str(sii) + "...")

        tmp_dir = os.path.join(args.scene_dir, "_tmp")

        # use default parameters, see https://github.com/gabyx/ApproxMVBB
        bounding_box_center_world, bounding_box_extent_world, R_world_from_obj = \
            approx_mvbb_utils.generate_oriented_bounding_box_3d(mesh_vertices_sii_,
                                                                n_epsilon=0.001,
                                                                n_point_samples=500,
                                                                n_grid_size=5,
                                                                n_diam_opt_loops=0,
                                                                n_grid_search_opt_loops=5,
                                                                tmp_dir=tmp_dir)

    bounding_box_positions[sii]    = bounding_box_center_world
    bounding_box_orientations[sii] = R_world_from_obj
    bounding_box_extents[sii]      = bounding_box_extent_world



with h5py.File(metadata_semantic_instance_bounding_box_positions_hdf5_file,    "w") as f: f.create_dataset("dataset", data=bounding_box_positions)
with h5py.File(metadata_semantic_instance_bounding_box_orientations_hdf5_file, "w") as f: f.create_dataset("dataset", data=bounding_box_orientations)
with h5py.File(metadata_semantic_instance_bounding_box_extents_hdf5_file,      "w") as f: f.create_dataset("dataset", data=bounding_box_extents)



print("[HYPERSIM: SCENE_GENERATE_BOUNDING_BOXES] Finished.")
