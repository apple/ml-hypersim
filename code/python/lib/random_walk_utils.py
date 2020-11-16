#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import h5py
import inspect
import os

import path_utils


def generate_camera_trajectory_random_walk(
    mesh_vertices,
    mesh_faces_vi,
    octomap_file,
    octomap_free_space_min,
    octomap_free_space_max,
    start_camera_position,
    start_camera_orientation,
    n_width_pixels,
    n_height_pixels,
    n_fov_x,
    n_samples_random_walk,
    n_samples_octomap_query,
    n_samples_camera_pose_candidates,
    n_voxel_size,
    n_query_half_extent_relative_to_current,
    n_query_half_extent_relative_to_start,
    tmp_dir):

    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    tmp_mesh_vertices_hdf5_file                           = os.path.join(tmp_dir, "_tmp_mesh_vertices.hdf5")
    tmp_mesh_faces_vi_hdf5_file                           = os.path.join(tmp_dir, "_tmp_mesh_faces_vi.hdf5")
    tmp_octomap_free_space_min_hdf5_file                  = os.path.join(tmp_dir, "_tmp_octomap_free_space_min.hdf5")
    tmp_octomap_free_space_max_hdf5_file                  = os.path.join(tmp_dir, "_tmp_octomap_free_space_max.hdf5")
    tmp_start_camera_position_hdf5_file                   = os.path.join(tmp_dir, "_tmp_start_camera_position.hdf5")
    tmp_start_camera_orientation_hdf5_file                = os.path.join(tmp_dir, "_tmp_start_camera_orientation.hdf5")
    tmp_camera_rays_hdf5_file                             = os.path.join(tmp_dir, "_tmp_camera_rays.hdf5")
    tmp_camera_rays_distances_to_center_hdf5_file         = os.path.join(tmp_dir, "_tmp_camera_rays_distances_to_center.hdf5")
    tmp_n_query_half_extent_relative_to_start_hdf5_file   = os.path.join(tmp_dir, "_tmp_n_query_half_extent_relative_to_start.hdf5")
    tmp_n_query_half_extent_relative_to_current_hdf5_file = os.path.join(tmp_dir, "_tmp_n_query_half_extent_relative_to_current.hdf5")
    tmp_output_camera_look_from_positions_hdf5_file       = os.path.join(tmp_dir, "_tmp_output_camera_look_from_positions.hdf5")
    tmp_output_camera_look_at_positions_hdf5_file         = os.path.join(tmp_dir, "_tmp_output_camera_look_at_positions.hdf5")
    tmp_output_camera_orientations_hdf5_file              = os.path.join(tmp_dir, "_tmp_output_camera_orientations.hdf5")
    tmp_output_intersection_distances_hdf5_file           = os.path.join(tmp_dir, "_tmp_output_intersection_distances.hdf5")
    tmp_output_prim_ids_hdf5_file                         = os.path.join(tmp_dir, "_tmp_output_prim_ids.hdf5")

    fov_y = 2.0 * arctan(n_height_pixels * tan(n_fov_x/2) / n_width_pixels)

    uv_min  = -1.0
    uv_max  = 1.0
    half_du = 0.5 * (uv_max - uv_min) / n_width_pixels
    half_dv = 0.5 * (uv_max - uv_min) / n_height_pixels

    u, v = meshgrid(linspace(uv_min+half_du, uv_max-half_du, n_width_pixels),
                    linspace(uv_min+half_dv, uv_max-half_dv, n_height_pixels)[::-1])

    ray_offset_x = u*tan(n_fov_x/2.0)
    ray_offset_y = v*tan(fov_y/2.0)
    ray_offset_z = -ones_like(ray_offset_x)

    rays_cam = dstack((ray_offset_x,ray_offset_y,ray_offset_z))
    V_cam    = matrix(rays_cam.reshape(-1,3)).T

    half_dx = 0.5
    half_dy = 0.5
    pixel_center = array([(n_width_pixels+1)/2.0, (n_height_pixels+1)/2.0])
    pixel_x, pixel_y = meshgrid(linspace(half_dx, n_width_pixels+half_dx,  n_width_pixels),
                                linspace(half_dy, n_height_pixels+half_dy, n_height_pixels))

    pixels                     = dstack((pixel_x,pixel_y)).reshape(-1,2)
    center_to_pixels           = pixels - pixel_center
    center_to_pixels_distances = linalg.norm(center_to_pixels, axis=1)

    with h5py.File(tmp_mesh_vertices_hdf5_file,                           "w") as f: f.create_dataset("dataset", data=mesh_vertices)
    with h5py.File(tmp_mesh_faces_vi_hdf5_file,                           "w") as f: f.create_dataset("dataset", data=mesh_faces_vi)
    with h5py.File(tmp_octomap_free_space_min_hdf5_file,                  "w") as f: f.create_dataset("dataset", data=octomap_free_space_min)
    with h5py.File(tmp_octomap_free_space_max_hdf5_file,                  "w") as f: f.create_dataset("dataset", data=octomap_free_space_max)
    with h5py.File(tmp_start_camera_position_hdf5_file,                   "w") as f: f.create_dataset("dataset", data=start_camera_position)
    with h5py.File(tmp_start_camera_orientation_hdf5_file,                "w") as f: f.create_dataset("dataset", data=start_camera_orientation)
    with h5py.File(tmp_camera_rays_hdf5_file,                             "w") as f: f.create_dataset("dataset", data=V_cam.T)
    with h5py.File(tmp_camera_rays_distances_to_center_hdf5_file,         "w") as f: f.create_dataset("dataset", data=center_to_pixels_distances)
    with h5py.File(tmp_n_query_half_extent_relative_to_start_hdf5_file,   "w") as f: f.create_dataset("dataset", data=n_query_half_extent_relative_to_start)
    with h5py.File(tmp_n_query_half_extent_relative_to_current_hdf5_file, "w") as f: f.create_dataset("dataset", data=n_query_half_extent_relative_to_current)

    current_source_path                        = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    generate_camera_trajectory_random_walk_bin = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_camera_trajectory_random_walk"))

    cmd = \
        generate_camera_trajectory_random_walk_bin + \
        " --mesh_vertices_file="                           + tmp_mesh_vertices_hdf5_file                           + \
        " --mesh_faces_vi_file="                           + tmp_mesh_faces_vi_hdf5_file                           + \
        " --start_camera_position_file="                   + tmp_start_camera_position_hdf5_file                   + \
        " --start_camera_orientation_file="                + tmp_start_camera_orientation_hdf5_file                + \
        " --camera_rays_file="                             + tmp_camera_rays_hdf5_file                             + \
        " --camera_rays_distances_to_center_file="         + tmp_camera_rays_distances_to_center_hdf5_file         + \
        " --octomap_file="                                 + octomap_file                                          + \
        " --octomap_free_space_min_file="                  + tmp_octomap_free_space_min_hdf5_file                  + \
        " --octomap_free_space_max_file="                  + tmp_octomap_free_space_max_hdf5_file                  + \
        " --n_samples_random_walk="                        + str(n_samples_random_walk)                            + \
        " --n_samples_octomap_query="                      + str(n_samples_octomap_query)                          + \
        " --n_samples_camera_pose_candidates="             + str(n_samples_camera_pose_candidates)                 + \
        " --n_voxel_size="                                 + str(n_voxel_size)                                     + \
        " --n_query_half_extent_relative_to_start_file="   + tmp_n_query_half_extent_relative_to_start_hdf5_file   + \
        " --n_query_half_extent_relative_to_current_file=" + tmp_n_query_half_extent_relative_to_current_hdf5_file + \
        " --output_camera_look_from_positions_file="       + tmp_output_camera_look_from_positions_hdf5_file       + \
        " --output_camera_look_at_positions_file="         + tmp_output_camera_look_at_positions_hdf5_file         + \
        " --output_camera_orientations_file="              + tmp_output_camera_orientations_hdf5_file              + \
        " --output_intersection_distances_file="           + tmp_output_intersection_distances_hdf5_file           + \
        " --output_prim_ids_file="                         + tmp_output_prim_ids_hdf5_file
        # " --silent"
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0 or retval == 256

    if retval == 256:
        print("[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK] WARNING: generate_camera_trajectory_random_walk DID NOT EXECUTE SUCCESSFULLY. GIVING UP.")
        return None, None, None, None, None

    with h5py.File(tmp_output_camera_look_from_positions_hdf5_file, "r") as f: camera_look_from_positions = f["dataset"][:]
    with h5py.File(tmp_output_camera_look_at_positions_hdf5_file,   "r") as f: camera_look_at_positions   = f["dataset"][:]
    with h5py.File(tmp_output_camera_orientations_hdf5_file,        "r") as f: camera_orientations        = f["dataset"][:]
    with h5py.File(tmp_output_intersection_distances_hdf5_file,     "r") as f: intersection_distances     = f["dataset"][:]
    with h5py.File(tmp_output_prim_ids_hdf5_file,                   "r") as f: prim_ids                   = f["dataset"][:]

    intersection_distances = intersection_distances.reshape(-1,n_height_pixels,n_width_pixels)
    prim_ids               = prim_ids.reshape(-1,n_height_pixels,n_width_pixels)

    for j in range(n_samples_random_walk):
        camera_orientations[j] = matrix(camera_orientations[j]).T.A

    return camera_look_from_positions, camera_look_at_positions, camera_orientations, intersection_distances, prim_ids
