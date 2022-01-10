#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import h5py
import inspect
import os

import path_utils



def generate_ray_intersections(vertices, faces, ray_positions, ray_directions, tmp_dir):

    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    tmp_vertices_hdf5_file                  = os.path.join(tmp_dir, "_tmp_vertices.hdf5")
    tmp_faces_hdf5_file                     = os.path.join(tmp_dir, "_tmp_faces.hdf5")
    tmp_ray_positions_hdf5_file             = os.path.join(tmp_dir, "_tmp_ray_positions.hdf5")
    tmp_ray_directions_hdf5_file            = os.path.join(tmp_dir, "_tmp_ray_directions.hdf5")
    tmp_output_ray_hit_data_float_hdf5_file = os.path.join(tmp_dir, "_tmp_output_ray_hit_data_float.hdf5")
    tmp_output_ray_hit_data_int_hdf5_file   = os.path.join(tmp_dir, "_tmp_output_ray_hit_data_int.hdf5")

    with h5py.File(tmp_vertices_hdf5_file,       "w") as f: f.create_dataset("dataset", data=vertices)
    with h5py.File(tmp_faces_hdf5_file,          "w") as f: f.create_dataset("dataset", data=faces)
    with h5py.File(tmp_ray_positions_hdf5_file,  "w") as f: f.create_dataset("dataset", data=ray_positions)
    with h5py.File(tmp_ray_directions_hdf5_file, "w") as f: f.create_dataset("dataset", data=ray_directions)

    current_source_path            = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    generate_ray_intersections_bin = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_ray_intersections"))

    cmd = \
        generate_ray_intersections_bin + \
        " --vertices_file="                  + tmp_vertices_hdf5_file                  + \
        " --faces_file="                     + tmp_faces_hdf5_file                     + \
        " --ray_positions_file="             + tmp_ray_positions_hdf5_file             + \
        " --ray_directions_file="            + tmp_ray_directions_hdf5_file            + \
        " --output_ray_hit_data_float_file=" + tmp_output_ray_hit_data_float_hdf5_file + \
        " --output_ray_hit_data_int_file="   + tmp_output_ray_hit_data_int_hdf5_file   + \
        " --silent"
    # print("")
    # print(cmd)
    # print("")
    retval = os.system(cmd)
    assert retval == 0

    with h5py.File(tmp_output_ray_hit_data_float_hdf5_file, "r") as f: ray_hit_data_float = f["dataset"][:]
    with h5py.File(tmp_output_ray_hit_data_int_hdf5_file,   "r") as f: ray_hit_data_int   = f["dataset"][:]

    intersection_distances = matrix(ray_hit_data_float[:,0]).A1
    intersection_normals   = matrix(ray_hit_data_float[:,1:4]).A
    prim_ids               = matrix(ray_hit_data_int[:,0]).A1

    return intersection_distances, intersection_normals, prim_ids
