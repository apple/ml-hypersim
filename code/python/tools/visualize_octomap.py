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
import octomap_utils

parser = argparse.ArgumentParser()
parser.add_argument("--mesh_dir", required=True)
parser.add_argument("--octomap_dir", required=True)
parser.add_argument("--tmp_dir", required=True)
parser.add_argument("--mesh_opacity", type=float)
parser.add_argument("--octomap_opacity", type=float)
parser.add_argument("--octomap_scale", type=float)
args = parser.parse_args()

assert os.path.exists(args.mesh_dir)
assert os.path.exists(args.octomap_dir)



print("[HYPERSIM: VISUALIZE_OCTOMAP] Begin...")



if args.mesh_opacity is not None:
    mesh_opacity = args.mesh_opacity
else:
    mesh_opacity = 0.25

if args.octomap_opacity is not None:
    octomap_opacity = args.octomap_opacity
else:
    octomap_opacity = 0.25

if args.octomap_scale is not None:
    octomap_scale = args.octomap_scale
else:
    octomap_scale = 3.25

mesh_vertices_hdf5_file = os.path.join(args.mesh_dir, "mesh_vertices.hdf5")
mesh_faces_vi_hdf5_file = os.path.join(args.mesh_dir, "mesh_faces_vi.hdf5")

octomap_bt_file                  = os.path.join(args.octomap_dir, "octomap.bt")
octomap_free_space_min_hdf5_file = os.path.join(args.octomap_dir, "octomap_free_space_min.hdf5")
octomap_free_space_max_hdf5_file = os.path.join(args.octomap_dir, "octomap_free_space_max.hdf5")

with h5py.File(mesh_vertices_hdf5_file, "r") as f: mesh_vertices = f["dataset"][:]
with h5py.File(mesh_faces_vi_hdf5_file, "r") as f: mesh_faces_vi = f["dataset"][:]

with h5py.File(octomap_free_space_min_hdf5_file, "r") as f: free_space_min = f["dataset"][:]
with h5py.File(octomap_free_space_max_hdf5_file, "r") as f: free_space_max = f["dataset"][:]



np.random.seed(0)

num_samples       = 250000
free_space_extent = free_space_max - free_space_min
query_positions   = np.random.rand(num_samples, 3)*free_space_extent + free_space_min

octomap_samples = octomap_utils.generate_octomap_samples(octomap_bt_file, query_positions, args.tmp_dir)

mayavi_utils.points3d_color_by_scalar(query_positions, scalars=octomap_samples, scale_factor=octomap_scale, opacity=octomap_opacity)

c_face = (0.75,0.75,0.75)

mayavi.mlab.triangular_mesh(mesh_vertices[:,0], mesh_vertices[:,1], mesh_vertices[:,2], mesh_faces_vi, representation="surface", color=c_face, opacity=mesh_opacity)

mayavi.mlab.show()



print("[HYPERSIM: VISUALIZE_OCTOMAP] Finished.")
