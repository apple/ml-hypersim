#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import h5py
import inspect
import os
import scipy.spatial

import path_utils
import sphere_sampling_utils



def generate_octomap(mesh_vertices, mesh_faces_vi, start_camera_positions, octomap_min, octomap_max, n_rays, n_iters, n_voxel_size, n_ray_nearest_neighbors, octomap_file, tmp_dir):

    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    tmp_mesh_vertices_hdf5_file          = os.path.join(tmp_dir, "_tmp_mesh_vertices.hdf5")
    tmp_mesh_faces_vi_hdf5_file          = os.path.join(tmp_dir, "_tmp_mesh_faces_vi.hdf5")
    tmp_start_camera_positions_hdf5_file = os.path.join(tmp_dir, "_tmp_start_camera_positions.hdf5")
    tmp_ray_directions_hdf5_file         = os.path.join(tmp_dir, "_tmp_ray_directions.hdf5")
    tmp_ray_neighbor_indices_hdf5_file   = os.path.join(tmp_dir, "_tmp_ray_neighbor_indices.hdf5")
    tmp_octomap_min_hdf5_file            = os.path.join(tmp_dir, "_tmp_octomap_min.hdf5")
    tmp_octomap_max_hdf5_file            = os.path.join(tmp_dir, "_tmp_octomap_max.hdf5")
    tmp_free_space_min_hdf5_file         = os.path.join(tmp_dir, "_tmp_free_space_min.hdf5")
    tmp_free_space_max_hdf5_file         = os.path.join(tmp_dir, "_tmp_free_space_max.hdf5")

    # compute ray directions
    ray_directions = sphere_sampling_utils.generate_evenly_distributed_samples_on_sphere(n_rays)

    # compute ray neighbor indices
    pset                 = ray_directions.astype(float64)
    ckdtree              = scipy.spatial.cKDTree(pset, balanced_tree=False)
    d,i                  = ckdtree.query(pset, k=n_ray_nearest_neighbors)
    ray_neighbor_indices = i

    with h5py.File(tmp_mesh_vertices_hdf5_file,          "w") as f: f.create_dataset("dataset", data=mesh_vertices)
    with h5py.File(tmp_mesh_faces_vi_hdf5_file,          "w") as f: f.create_dataset("dataset", data=mesh_faces_vi)
    with h5py.File(tmp_start_camera_positions_hdf5_file, "w") as f: f.create_dataset("dataset", data=start_camera_positions)
    with h5py.File(tmp_ray_directions_hdf5_file,         "w") as f: f.create_dataset("dataset", data=ray_directions)
    with h5py.File(tmp_ray_neighbor_indices_hdf5_file,   "w") as f: f.create_dataset("dataset", data=ray_neighbor_indices)
    with h5py.File(tmp_octomap_min_hdf5_file,            "w") as f: f.create_dataset("dataset", data=octomap_min)
    with h5py.File(tmp_octomap_max_hdf5_file,            "w") as f: f.create_dataset("dataset", data=octomap_max)

    current_source_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cpp_bin             = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_octomap"))

    cmd = \
        cpp_bin + \
        " --mesh_vertices_file="          + tmp_mesh_vertices_hdf5_file          + \
        " --mesh_faces_vi_file="          + tmp_mesh_faces_vi_hdf5_file          + \
        " --start_camera_positions_file=" + tmp_start_camera_positions_hdf5_file + \
        " --ray_directions_file="         + tmp_ray_directions_hdf5_file         + \
        " --ray_neighbor_indices_file="   + tmp_ray_neighbor_indices_hdf5_file   + \
        " --octomap_min_file="            + tmp_octomap_min_hdf5_file            + \
        " --octomap_max_file="            + tmp_octomap_max_hdf5_file            + \
        " --n_iters="                     + str(n_iters)                         + \
        " --n_voxel_size="                + str(n_voxel_size)                    + \
        " --octomap_file="                + octomap_file                         + \
        " --free_space_min_file="         + tmp_free_space_min_hdf5_file         + \
        " --free_space_max_file="         + tmp_free_space_max_hdf5_file
        # " --silent"
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    with h5py.File(tmp_free_space_min_hdf5_file, "r") as f: free_space_min = matrix(f["dataset"][:]).A1
    with h5py.File(tmp_free_space_max_hdf5_file, "r") as f: free_space_max = matrix(f["dataset"][:]).A1

    return free_space_min, free_space_max



def generate_octomap_samples(octomap_file, query_positions, tmp_dir):

    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    tmp_query_positions_hdf5_file = os.path.join(tmp_dir, "_tmp_query_positions.hdf5")
    tmp_octomap_samples_hdf5_file = os.path.join(tmp_dir, "_tmp_octomap_samples.hdf5")

    with h5py.File(tmp_query_positions_hdf5_file, "w") as f: f.create_dataset("dataset", data=query_positions)

    current_source_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cpp_bin             = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_octomap_samples"))

    cmd = \
        cpp_bin + \
        " --octomap_file="         + octomap_file                  + \
        " --query_positions_file=" + tmp_query_positions_hdf5_file + \
        " --output_file="          + tmp_octomap_samples_hdf5_file + \
        " --silent"
    # print("")
    # print(cmd)
    # print("")
    retval = os.system(cmd)
    assert retval == 0

    with h5py.File(tmp_octomap_samples_hdf5_file, "r") as f: octomap_samples = matrix(f["dataset"][:]).A1

    return octomap_samples
