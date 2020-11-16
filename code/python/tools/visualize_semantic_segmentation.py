#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import mayavi.mlab
import os



parser = argparse.ArgumentParser()
parser.add_argument("--mesh_dir", required=True)
parser.add_argument("--segmentation_type")
parser.add_argument("--mesh_opacity", type=float)
parser.add_argument("--show_bounding_boxes", action="store_true")
parser.add_argument("--bounding_box_type")
args = parser.parse_args()

assert os.path.exists(args.mesh_dir)

if args.segmentation_type is not None:
    assert args.segmentation_type == "semantic_instance" or args.segmentation_type == "semantic"

if args.show_bounding_boxes:
    assert args.bounding_box_type == "axis_aligned" or args.bounding_box_type == "object_aligned_2d" or args.bounding_box_type == "object_aligned_3d"



print("[HYPERSIM: VISUALIZE_SEMANTIC_SEGMENTATION] Begin...")



if args.mesh_opacity is not None:
    mesh_opacity = args.mesh_opacity
else:
    mesh_opacity = 0.25

if args.segmentation_type is not None:
    segmentation_type = args.segmentation_type
else:
    segmentation_type = "semantic_instance"

mesh_vertices_hdf5_file                     = os.path.join(args.mesh_dir, "mesh_vertices.hdf5")
mesh_faces_vi_hdf5_file                     = os.path.join(args.mesh_dir, "mesh_faces_vi.hdf5")
mesh_faces_oi_hdf5_file                     = os.path.join(args.mesh_dir, "mesh_faces_oi.hdf5")
mesh_objects_sii_hdf5_file                  = os.path.join(args.mesh_dir, "mesh_objects_sii.hdf5")
mesh_objects_si_hdf5_file                   = os.path.join(args.mesh_dir, "mesh_objects_si.hdf5")
metadata_semantic_instance_colors_hdf5_file = os.path.join(args.mesh_dir, "metadata_semantic_instance_colors.hdf5")
metadata_semantic_colors_hdf5_file          = os.path.join(args.mesh_dir, "metadata_semantic_colors.hdf5")

with h5py.File(mesh_vertices_hdf5_file,                     "r") as f: mesh_vertices                     = f["dataset"][:]
with h5py.File(mesh_faces_vi_hdf5_file,                     "r") as f: mesh_faces_vi                     = f["dataset"][:]
with h5py.File(mesh_faces_oi_hdf5_file,                     "r") as f: mesh_faces_oi                     = f["dataset"][:]
with h5py.File(mesh_objects_sii_hdf5_file,                  "r") as f: mesh_objects_sii                  = matrix(f["dataset"][:]).A1
with h5py.File(mesh_objects_si_hdf5_file,                   "r") as f: mesh_objects_si                   = matrix(f["dataset"][:]).A1
with h5py.File(metadata_semantic_instance_colors_hdf5_file, "r") as f: metadata_semantic_instance_colors = f["dataset"][:]
with h5py.File(metadata_semantic_colors_hdf5_file,          "r") as f: metadata_semantic_colors          = f["dataset"][:]



c_mesh = (0.75,0.75,0.75)
mayavi.mlab.triangular_mesh(mesh_vertices[:,0], mesh_vertices[:,1], mesh_vertices[:,2], mesh_faces_vi, representation="surface", color=c_mesh, opacity=mesh_opacity)

if segmentation_type == "semantic_instance":

    for sii in unique(mesh_objects_sii):
        if sii == -1:
            continue

        color_sii = metadata_semantic_instance_colors[sii]
        fi_sii    = where(in1d(mesh_faces_oi, where(mesh_objects_sii == sii)[0]))[0]

        assert fi_sii.shape[0] > 0

        mesh_faces_vi_sii  = mesh_faces_vi[fi_sii]
        mesh_vertices_sii_ = mesh_vertices[mesh_faces_vi_sii.ravel()]
        mesh_faces_vi_sii_ = arange(mesh_vertices_sii_.shape[0]).reshape(-1,3)

        c_sii = tuple(color_sii / 255.0)
        mayavi.mlab.triangular_mesh(mesh_vertices_sii_[:,0], mesh_vertices_sii_[:,1], mesh_vertices_sii_[:,2], mesh_faces_vi_sii_, representation="surface", color=c_sii, opacity=mesh_opacity)

if segmentation_type == "semantic":
    
    for si in unique(mesh_objects_si):
        if si == -1:
            continue

        color_si = metadata_semantic_colors[si]
        fi_si    = where(in1d(mesh_faces_oi, where(mesh_objects_si == si)[0]))[0]

        assert fi_si.shape[0] > 0

        mesh_faces_vi_si = mesh_faces_vi[fi_si]
        mesh_vertices_si_ = mesh_vertices[mesh_faces_vi_si.ravel()]
        mesh_faces_vi_si_ = arange(mesh_vertices_si_.shape[0]).reshape(-1,3)

        c_si = tuple(color_si / 255.0)
        mayavi.mlab.triangular_mesh(mesh_vertices_si_[:,0], mesh_vertices_si_[:,1], mesh_vertices_si_[:,2], mesh_faces_vi_si_, representation="surface", color=c_si, opacity=mesh_opacity)



if args.show_bounding_boxes:

    if args.bounding_box_type == "axis_aligned":
        metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_axis_aligned_positions.hdf5")
        metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_axis_aligned_orientations.hdf5")
        metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_axis_aligned_extents.hdf5")
    if args.bounding_box_type == "object_aligned_2d":
        metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_2d_positions.hdf5")
        metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_2d_orientations.hdf5")
        metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_2d_extents.hdf5")
    if args.bounding_box_type == "object_aligned_3d":
        metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_3d_positions.hdf5")
        metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_3d_orientations.hdf5")
        metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_3d_extents.hdf5")

    with h5py.File(metadata_semantic_instance_bounding_box_positions_hdf5_file,    "r") as f: bounding_box_positions    = f["dataset"][:]
    with h5py.File(metadata_semantic_instance_bounding_box_orientations_hdf5_file, "r") as f: bounding_box_orientations = f["dataset"][:]
    with h5py.File(metadata_semantic_instance_bounding_box_extents_hdf5_file,      "r") as f: bounding_box_extents      = f["dataset"][:]

    for sii in unique(mesh_objects_sii):
        if sii == -1:
            continue

        color_sii = metadata_semantic_instance_colors[sii]

        bounding_box_center_world = matrix(bounding_box_positions[sii]).A
        bounding_box_extent_world = matrix(bounding_box_extents[sii]).A
        R_world_from_obj          = matrix(bounding_box_orientations[sii])
        t_world_from_obj          = matrix(bounding_box_positions[sii]).T

        c_bounding_box_x_axis = (1.0,0.0,0.0)
        c_bounding_box_y_axis = (0.0,1.0,0.0)
        c_bounding_box_z_axis = (0.0,0.0,1.0)

        bounding_box_x_axis_obj = matrix([1.0,0.0,0.0]).T
        bounding_box_y_axis_obj = matrix([0.0,1.0,0.0]).T
        bounding_box_z_axis_obj = matrix([0.0,0.0,1.0]).T

        bounding_box_x_axis_world = (R_world_from_obj*bounding_box_x_axis_obj).T.A
        bounding_box_y_axis_world = (R_world_from_obj*bounding_box_y_axis_obj).T.A
        bounding_box_z_axis_world = (R_world_from_obj*bounding_box_z_axis_obj).T.A

        s_scale_factor = 2.5

        mayavi.mlab.quiver3d(bounding_box_center_world[0:1,0], bounding_box_center_world[0:1,1], bounding_box_center_world[0:1,2],
                             bounding_box_x_axis_world[0:1,0], bounding_box_x_axis_world[0:1,1], bounding_box_x_axis_world[0:1,2],
                             mode="arrow", scale_factor=s_scale_factor, color=c_bounding_box_x_axis)

        mayavi.mlab.quiver3d(bounding_box_center_world[0:1,0], bounding_box_center_world[0:1,1], bounding_box_center_world[0:1,2],
                             bounding_box_y_axis_world[0:1,0], bounding_box_y_axis_world[0:1,1], bounding_box_y_axis_world[0:1,2],
                             mode="arrow", scale_factor=s_scale_factor, color=c_bounding_box_y_axis)

        mayavi.mlab.quiver3d(bounding_box_center_world[0:1,0], bounding_box_center_world[0:1,1], bounding_box_center_world[0:1,2],
                             bounding_box_z_axis_world[0:1,0], bounding_box_z_axis_world[0:1,1], bounding_box_z_axis_world[0:1,2],
                             mode="arrow", scale_factor=s_scale_factor, color=c_bounding_box_z_axis)

        c_sii = tuple(color_sii / 255.0)

        bounding_box_corner_000_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,0.0,0.0]).T - 0.5)
        bounding_box_corner_100_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,0.0,0.0]).T - 0.5)
        bounding_box_corner_010_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,1.0,0.0]).T - 0.5)
        bounding_box_corner_110_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,1.0,0.0]).T - 0.5)
        bounding_box_corner_001_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,0.0,1.0]).T - 0.5)
        bounding_box_corner_101_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,0.0,1.0]).T - 0.5)
        bounding_box_corner_011_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,1.0,1.0]).T - 0.5)
        bounding_box_corner_111_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,1.0,1.0]).T - 0.5)

        bounding_box_corner_000_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_000_obj).T.A
        bounding_box_corner_100_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_100_obj).T.A
        bounding_box_corner_010_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_010_obj).T.A
        bounding_box_corner_110_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_110_obj).T.A
        bounding_box_corner_001_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_001_obj).T.A
        bounding_box_corner_101_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_101_obj).T.A
        bounding_box_corner_011_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_011_obj).T.A
        bounding_box_corner_111_world = (t_world_from_obj + R_world_from_obj*bounding_box_corner_111_obj).T.A

        s_tube_radius = 0.1

        # x=0
        bounding_box_line_000_010_world = r_[bounding_box_corner_000_world, bounding_box_corner_010_world]
        bounding_box_line_010_011_world = r_[bounding_box_corner_010_world, bounding_box_corner_011_world]
        bounding_box_line_011_001_world = r_[bounding_box_corner_011_world, bounding_box_corner_001_world]
        bounding_box_line_001_000_world = r_[bounding_box_corner_001_world, bounding_box_corner_000_world]

        mayavi.mlab.plot3d(bounding_box_line_000_010_world[:,0], bounding_box_line_000_010_world[:,1], bounding_box_line_000_010_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_010_011_world[:,0], bounding_box_line_010_011_world[:,1], bounding_box_line_010_011_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_011_001_world[:,0], bounding_box_line_011_001_world[:,1], bounding_box_line_011_001_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_001_000_world[:,0], bounding_box_line_001_000_world[:,1], bounding_box_line_001_000_world[:,2], tube_radius=s_tube_radius, color=c_sii)

        # x=1
        bounding_box_line_100_110_world = r_[bounding_box_corner_100_world, bounding_box_corner_110_world]
        bounding_box_line_110_111_world = r_[bounding_box_corner_110_world, bounding_box_corner_111_world]
        bounding_box_line_111_101_world = r_[bounding_box_corner_111_world, bounding_box_corner_101_world]
        bounding_box_line_101_100_world = r_[bounding_box_corner_101_world, bounding_box_corner_100_world]

        mayavi.mlab.plot3d(bounding_box_line_100_110_world[:,0], bounding_box_line_100_110_world[:,1], bounding_box_line_100_110_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_110_111_world[:,0], bounding_box_line_110_111_world[:,1], bounding_box_line_110_111_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_111_101_world[:,0], bounding_box_line_111_101_world[:,1], bounding_box_line_111_101_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_101_100_world[:,0], bounding_box_line_101_100_world[:,1], bounding_box_line_101_100_world[:,2], tube_radius=s_tube_radius, color=c_sii)

        # y=0
        bounding_box_line_000_100_world = r_[bounding_box_corner_000_world, bounding_box_corner_100_world]
        bounding_box_line_100_101_world = r_[bounding_box_corner_100_world, bounding_box_corner_101_world]
        bounding_box_line_101_001_world = r_[bounding_box_corner_101_world, bounding_box_corner_001_world]
        bounding_box_line_001_000_world = r_[bounding_box_corner_001_world, bounding_box_corner_000_world]

        mayavi.mlab.plot3d(bounding_box_line_000_100_world[:,0], bounding_box_line_000_100_world[:,1], bounding_box_line_000_100_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_100_101_world[:,0], bounding_box_line_100_101_world[:,1], bounding_box_line_100_101_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_101_001_world[:,0], bounding_box_line_101_001_world[:,1], bounding_box_line_101_001_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_001_000_world[:,0], bounding_box_line_001_000_world[:,1], bounding_box_line_001_000_world[:,2], tube_radius=s_tube_radius, color=c_sii)

        # y=1
        bounding_box_line_010_110_world = r_[bounding_box_corner_010_world, bounding_box_corner_110_world]
        bounding_box_line_110_111_world = r_[bounding_box_corner_110_world, bounding_box_corner_111_world]
        bounding_box_line_111_011_world = r_[bounding_box_corner_111_world, bounding_box_corner_011_world]
        bounding_box_line_011_010_world = r_[bounding_box_corner_011_world, bounding_box_corner_010_world]

        mayavi.mlab.plot3d(bounding_box_line_010_110_world[:,0], bounding_box_line_010_110_world[:,1], bounding_box_line_010_110_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_110_111_world[:,0], bounding_box_line_110_111_world[:,1], bounding_box_line_110_111_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_111_011_world[:,0], bounding_box_line_111_011_world[:,1], bounding_box_line_111_011_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_011_010_world[:,0], bounding_box_line_011_010_world[:,1], bounding_box_line_011_010_world[:,2], tube_radius=s_tube_radius, color=c_sii)

        # z=0
        bounding_box_line_000_100_world = r_[bounding_box_corner_000_world, bounding_box_corner_100_world]
        bounding_box_line_100_110_world = r_[bounding_box_corner_100_world, bounding_box_corner_110_world]
        bounding_box_line_110_010_world = r_[bounding_box_corner_110_world, bounding_box_corner_010_world]
        bounding_box_line_010_000_world = r_[bounding_box_corner_010_world, bounding_box_corner_000_world]

        mayavi.mlab.plot3d(bounding_box_line_000_100_world[:,0], bounding_box_line_000_100_world[:,1], bounding_box_line_000_100_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_100_110_world[:,0], bounding_box_line_100_110_world[:,1], bounding_box_line_100_110_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_110_010_world[:,0], bounding_box_line_110_010_world[:,1], bounding_box_line_110_010_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_010_000_world[:,0], bounding_box_line_010_000_world[:,1], bounding_box_line_010_000_world[:,2], tube_radius=s_tube_radius, color=c_sii)

        # z=1
        bounding_box_line_001_101_world = r_[bounding_box_corner_001_world, bounding_box_corner_101_world]
        bounding_box_line_101_111_world = r_[bounding_box_corner_101_world, bounding_box_corner_111_world]
        bounding_box_line_111_011_world = r_[bounding_box_corner_111_world, bounding_box_corner_011_world]
        bounding_box_line_011_001_world = r_[bounding_box_corner_011_world, bounding_box_corner_001_world]

        mayavi.mlab.plot3d(bounding_box_line_001_101_world[:,0], bounding_box_line_001_101_world[:,1], bounding_box_line_001_101_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_101_111_world[:,0], bounding_box_line_101_111_world[:,1], bounding_box_line_101_111_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_111_011_world[:,0], bounding_box_line_111_011_world[:,1], bounding_box_line_111_011_world[:,2], tube_radius=s_tube_radius, color=c_sii)
        mayavi.mlab.plot3d(bounding_box_line_011_001_world[:,0], bounding_box_line_011_001_world[:,1], bounding_box_line_011_001_world[:,2], tube_radius=s_tube_radius, color=c_sii)

mayavi.mlab.show()



print("[HYPERSIM: VISUALIZE_SEMANTIC_SEGMENTATION] Finished.")
