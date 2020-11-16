#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import h5py
import inspect
import os

import path_utils



def generate_oriented_bounding_box_2d(points, tmp_dir):

    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    tmp_points_hdf5_file                          = os.path.join(tmp_dir, "_tmp_points.hdf5")
    tmp_output_bounding_box_center_hdf5_file      = os.path.join(tmp_dir, "_tmp_output_bounding_box_center.hdf5")
    tmp_output_bounding_box_extent_hdf5_file      = os.path.join(tmp_dir, "_tmp_output_bounding_box_extent.hdf5")
    tmp_output_bounding_box_orientation_hdf5_file = os.path.join(tmp_dir, "_tmp_output_bounding_box_orientation.hdf5")

    with h5py.File(tmp_points_hdf5_file, "w") as f: f.create_dataset("dataset", data=points)

    current_source_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cpp_bin             = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_oriented_bounding_box"))

    cmd = \
        cpp_bin + \
        " --points_file="                          + tmp_points_hdf5_file                          + \
        " --n_epsilon="                            + str(0.0)                                      + \
        " --n_point_samples="                      + str(0)                                        + \
        " --n_grid_size="                          + str(0)                                        + \
        " --n_diam_opt_loops="                     + str(0)                                        + \
        " --n_grid_search_opt_loops="              + str(0)                                        + \
        " --output_bounding_box_center_file="      + tmp_output_bounding_box_center_hdf5_file      + \
        " --output_bounding_box_extent_file="      + tmp_output_bounding_box_extent_hdf5_file      + \
        " --output_bounding_box_orientation_file=" + tmp_output_bounding_box_orientation_hdf5_file + \
        " --silent"
    # print("")
    # print(cmd)
    # print("")
    retval = os.system(cmd)
    assert retval == 0

    with h5py.File(tmp_output_bounding_box_center_hdf5_file,      "r") as f: bounding_box_center      = matrix(f["dataset"][:]).A1
    with h5py.File(tmp_output_bounding_box_extent_hdf5_file,      "r") as f: bounding_box_extent      = matrix(f["dataset"][:]).A1
    with h5py.File(tmp_output_bounding_box_orientation_hdf5_file, "r") as f: bounding_box_orientation = matrix(f["dataset"][:]).A

    assert bounding_box_extent[0] >= bounding_box_extent[1]
    assert isclose(linalg.det(bounding_box_orientation), 1)

    return bounding_box_center, bounding_box_extent, bounding_box_orientation



def generate_oriented_bounding_box_3d(points, n_epsilon, n_point_samples, n_grid_size, n_diam_opt_loops, n_grid_search_opt_loops, tmp_dir):

    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    tmp_points_hdf5_file                          = os.path.join(tmp_dir, "_tmp_points.hdf5")
    tmp_output_bounding_box_center_hdf5_file      = os.path.join(tmp_dir, "_tmp_output_bounding_box_center.hdf5")
    tmp_output_bounding_box_extent_hdf5_file      = os.path.join(tmp_dir, "_tmp_output_bounding_box_extent.hdf5")
    tmp_output_bounding_box_orientation_hdf5_file = os.path.join(tmp_dir, "_tmp_output_bounding_box_orientation.hdf5")

    with h5py.File(tmp_points_hdf5_file, "w") as f: f.create_dataset("dataset", data=points)

    current_source_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cpp_bin             = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_oriented_bounding_box"))

    cmd = \
        cpp_bin + \
        " --points_file="                          + tmp_points_hdf5_file                     + \
        " --n_epsilon="                            + str(n_epsilon)                           + \
        " --n_point_samples="                      + str(n_point_samples)                     + \
        " --n_grid_size="                          + str(n_grid_size)                         + \
        " --n_diam_opt_loops="                     + str(n_diam_opt_loops)                    + \
        " --n_grid_search_opt_loops="              + str(n_grid_search_opt_loops)             + \
        " --output_bounding_box_center_file="      + tmp_output_bounding_box_center_hdf5_file + \
        " --output_bounding_box_extent_file="      + tmp_output_bounding_box_extent_hdf5_file + \
        " --output_bounding_box_orientation_file=" + tmp_output_bounding_box_orientation_hdf5_file
        # " --silent"
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    with h5py.File(tmp_output_bounding_box_center_hdf5_file,      "r") as f: bounding_box_center      = matrix(f["dataset"][:]).A1
    with h5py.File(tmp_output_bounding_box_extent_hdf5_file,      "r") as f: bounding_box_extent      = matrix(f["dataset"][:]).A1
    with h5py.File(tmp_output_bounding_box_orientation_hdf5_file, "r") as f: bounding_box_orientation = matrix(f["dataset"][:]).A

    assert bounding_box_extent[0] >= bounding_box_extent[1]
    assert bounding_box_extent[1] >= bounding_box_extent[2]
    assert isclose(linalg.det(bounding_box_orientation), 1)

    return bounding_box_center, bounding_box_extent, bounding_box_orientation
