#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import inspect
import mayavi.mlab
import os

import path_utils
path_utils.add_path_to_sys_path("../lib", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import mayavi_utils

parser = argparse.ArgumentParser()
parser.add_argument("--mesh_dir", required=True)
parser.add_argument("--camera_trajectory_dir", required=True)
parser.add_argument("--mesh_opacity", type=float)
parser.add_argument("--cameras_skip", type=int)
parser.add_argument("--cameras_scale_factor", type=float)
args = parser.parse_args()

assert os.path.exists(args.mesh_dir)
assert os.path.exists(args.camera_trajectory_dir)



print("[HYPERSIM: VISUALIZE_CAMERA_TRAJECTORY] Begin...")



if args.mesh_opacity is not None:
    mesh_opacity = args.mesh_opacity
else:
    mesh_opacity = 0.25

if args.cameras_skip is not None:
    cameras_skip = args.cameras_skip
else:
    cameras_skip = 1

if args.cameras_scale_factor is not None:
    cameras_scale_factor = args.cameras_scale_factor
else:
    cameras_scale_factor = 50.0

mesh_vertices_hdf5_file = os.path.join(args.mesh_dir, "mesh_vertices.hdf5")
mesh_faces_vi_hdf5_file = os.path.join(args.mesh_dir, "mesh_faces_vi.hdf5")

camera_keyframe_frame_indices_hdf5_file     = os.path.join(args.camera_trajectory_dir, "camera_keyframe_frame_indices.hdf5")
camera_keyframe_positions_hdf5_file         = os.path.join(args.camera_trajectory_dir, "camera_keyframe_positions.hdf5")
camera_keyframe_look_at_positions_hdf5_file = os.path.join(args.camera_trajectory_dir, "camera_keyframe_look_at_positions.hdf5")
camera_keyframe_orientations_hdf5_file      = os.path.join(args.camera_trajectory_dir, "camera_keyframe_orientations.hdf5")

with h5py.File(mesh_vertices_hdf5_file, "r") as f: mesh_vertices = f["dataset"][:]
with h5py.File(mesh_faces_vi_hdf5_file, "r") as f: mesh_faces_vi = f["dataset"][:]

with h5py.File(camera_keyframe_frame_indices_hdf5_file, "r") as f: camera_keyframe_frame_indices = f["dataset"][:]
with h5py.File(camera_keyframe_positions_hdf5_file,     "r") as f: camera_keyframe_positions     = f["dataset"][:]
with h5py.File(camera_keyframe_orientations_hdf5_file,  "r") as f: camera_keyframe_orientations  = f["dataset"][:]

if os.path.exists(camera_keyframe_look_at_positions_hdf5_file):
    with h5py.File(camera_keyframe_look_at_positions_hdf5_file, "r") as f: camera_keyframe_look_at_positions = f["dataset"][:]
else:
    camera_keyframe_look_at_positions = None



mayavi_utils.points3d_color_by_scalar(camera_keyframe_positions, scalars=camera_keyframe_frame_indices, scale_factor=2.0, colormap="summer")
mayavi.mlab.plot3d(camera_keyframe_positions[:,0], camera_keyframe_positions[:,1], camera_keyframe_positions[:,2], camera_keyframe_frame_indices, tube_radius=0.5, opacity=0.5, colormap="summer")

if camera_keyframe_look_at_positions is not None:
    mayavi_utils.points3d_color_by_scalar(camera_keyframe_look_at_positions, scalars=camera_keyframe_frame_indices, scale_factor=2.0, colormap="winter")
    mayavi.mlab.plot3d(camera_keyframe_look_at_positions[:,0], camera_keyframe_look_at_positions[:,1], camera_keyframe_look_at_positions[:,2], camera_keyframe_frame_indices, tube_radius=0.5, opacity=0.5, colormap="winter")

c_face = (0.75,0.75,0.75)

mayavi.mlab.triangular_mesh(mesh_vertices[:,0], mesh_vertices[:,1], mesh_vertices[:,2], mesh_faces_vi, representation="surface", color=c_face, opacity=mesh_opacity)

# mayavi.mlab.axes()

c_camera_x_axis = (1.0,0.0,0.0)
c_camera_y_axis = (0.0,1.0,0.0)
c_camera_z_axis = (0.0,0.0,1.0)

camera_x_axis_cam = matrix([1.0,0.0,0.0]).T
camera_y_axis_cam = matrix([0.0,1.0,0.0]).T
camera_z_axis_cam = matrix([0.0,0.0,1.0]).T

num_views = camera_keyframe_positions.shape[0]

for i in arange(num_views)[::cameras_skip]:

    R_world_from_cam = camera_keyframe_orientations[i]

    camera_x_axis_world = (R_world_from_cam*camera_x_axis_cam).T.A
    camera_y_axis_world = (R_world_from_cam*camera_y_axis_cam).T.A
    camera_z_axis_world = (R_world_from_cam*camera_z_axis_cam).T.A

    mayavi.mlab.quiver3d(camera_keyframe_positions[i:i+1,0], camera_keyframe_positions[i:i+1,1], camera_keyframe_positions[i:i+1,2],
                         camera_x_axis_world[0:1,0],         camera_x_axis_world[0:1,1],         camera_x_axis_world[0:1,2],
                         mode="arrow", scale_factor=cameras_scale_factor, color=c_camera_x_axis)

    mayavi.mlab.quiver3d(camera_keyframe_positions[i:i+1,0], camera_keyframe_positions[i:i+1,1], camera_keyframe_positions[i:i+1,2],
                         camera_y_axis_world[0:1,0],         camera_y_axis_world[0:1,1],         camera_y_axis_world[0:1,2],
                         mode="arrow", scale_factor=cameras_scale_factor, color=c_camera_y_axis)

    mayavi.mlab.quiver3d(camera_keyframe_positions[i:i+1,0], camera_keyframe_positions[i:i+1,1], camera_keyframe_positions[i:i+1,2],
                         camera_z_axis_world[0:1,0],         camera_z_axis_world[0:1,1],         camera_z_axis_world[0:1,2],
                         mode="arrow", scale_factor=cameras_scale_factor, color=c_camera_z_axis)

# mayavi.mlab.orientation_axes()

mayavi.mlab.show()



print("[HYPERSIM: VISUALIZE_CAMERA_TRAJECTORY] Finished.")
