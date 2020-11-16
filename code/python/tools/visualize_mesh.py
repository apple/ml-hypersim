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
parser.add_argument("--mesh_opacity", type=float)
parser.add_argument("--randomize_vertex_colors", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.mesh_dir)



print("[HYPERSIM: VISUALIZE_MESH] Begin...")



if args.mesh_opacity is not None:
    mesh_opacity = args.mesh_opacity
else:
    mesh_opacity = 0.25

mesh_vertices_hdf5_file = os.path.join(args.mesh_dir, "mesh_vertices.hdf5")
mesh_faces_vi_hdf5_file = os.path.join(args.mesh_dir, "mesh_faces_vi.hdf5")
mesh_faces_oi_hdf5_file = os.path.join(args.mesh_dir, "mesh_faces_oi.hdf5")

with h5py.File(mesh_vertices_hdf5_file, "r") as f: mesh_vertices = f["dataset"][:]
with h5py.File(mesh_faces_vi_hdf5_file, "r") as f: mesh_faces_vi = f["dataset"][:]
with h5py.File(mesh_faces_oi_hdf5_file, "r") as f: mesh_faces_oi = f["dataset"][:]



np.random.seed(0)

if args.randomize_vertex_colors:
    mesh_color_vals = arange(mesh_vertices.shape[0])
    np.random.shuffle(mesh_color_vals)
else:
    mesh_faces_oi_unique = unique(mesh_faces_oi)
    color_vals_unique = arange(mesh_faces_oi_unique.shape[0])
    np.random.shuffle(color_vals_unique)
    
    mesh_color_vals = zeros((mesh_vertices.shape[0]))
    for oi,color_val in zip(mesh_faces_oi_unique,color_vals_unique):
        mesh_color_vals[ mesh_faces_vi[ oi == mesh_faces_oi ].ravel() ] = color_val

mayavi.mlab.triangular_mesh(mesh_vertices[:,0], mesh_vertices[:,1], mesh_vertices[:,2], mesh_faces_vi, scalars=mesh_color_vals, representation="surface", opacity=mesh_opacity)

mayavi.mlab.show()



print("[HYPERSIM: VISUALIZE_MESH] Finished.")
