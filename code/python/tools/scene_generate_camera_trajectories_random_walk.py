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
import scipy.linalg
import sklearn.preprocessing
import sklearn.metrics

import path_utils
path_utils.add_path_to_sys_path("../lib", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import embree_utils
import octomap_utils
import random_walk_utils

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", required=True)
parser.add_argument("--use_python_reference_implementation", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.scene_dir)

path_utils.add_path_to_sys_path(os.path.join(args.scene_dir, "..", ".."), mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK] Begin...")



scene_name       = os.path.basename(args.scene_dir)
asset_export_dir = os.path.join(args.scene_dir, "_asset_export")
detail_dir       = os.path.join(args.scene_dir, "_detail")
mesh_dir         = os.path.join(detail_dir, "mesh")
octomap_dir      = os.path.join(detail_dir, "octomap")
tmp_dir          = os.path.join(args.scene_dir, "_tmp")

metadata_cameras_asset_export_csv_file = os.path.join(asset_export_dir, "metadata_cameras_asset_export.csv")
metadata_cameras_csv_file              = os.path.join(detail_dir, "metadata_cameras.csv")
metadata_scene_csv_file                = os.path.join(detail_dir, "metadata_scene.csv")
mesh_vertices_hdf5_file                = os.path.join(mesh_dir, "mesh_vertices.hdf5")
mesh_faces_vi_hdf5_file                = os.path.join(mesh_dir, "mesh_faces_vi.hdf5")
mesh_faces_oi_hdf5_file                = os.path.join(mesh_dir, "mesh_faces_oi.hdf5")
octomap_bt_file                        = os.path.join(octomap_dir, "octomap.bt")
octomap_free_space_min_hdf5_file       = os.path.join(octomap_dir, "octomap_free_space_min.hdf5")
octomap_free_space_max_hdf5_file       = os.path.join(octomap_dir, "octomap_free_space_max.hdf5")

scene = [ s for s in _dataset_config.scenes if s["name"] == scene_name ][0]
with h5py.File(mesh_vertices_hdf5_file,          "r") as f: mesh_vertices          = f["dataset"][:]
with h5py.File(mesh_faces_vi_hdf5_file,          "r") as f: mesh_faces_vi          = f["dataset"][:]
with h5py.File(mesh_faces_oi_hdf5_file,          "r") as f: mesh_faces_oi          = f["dataset"][:]
with h5py.File(octomap_free_space_min_hdf5_file, "r") as f: octomap_free_space_min = f["dataset"][:]
with h5py.File(octomap_free_space_max_hdf5_file, "r") as f: octomap_free_space_max = f["dataset"][:]

obj_ids_unique    = unique(mesh_faces_oi)
color_vals_unique = arange(obj_ids_unique.shape[0])
np.random.seed(0)
np.random.shuffle(color_vals_unique)

df_scene              = pd.read_csv(metadata_scene_csv_file, index_col="parameter_name")
meters_per_asset_unit = df_scene.loc["meters_per_asset_unit"][0]
asset_units_per_meter = 1.0 / meters_per_asset_unit



# parameters

# when sampling views, generate images using these image and camera parameters
n_width_pixels  = 256
n_height_pixels = 192
n_fov_x         = pi/3

n_samples_random_walk            = 100  # each final generated camera trajectory consists of this many views
n_samples_octomap_query          = 1000 # generate this many preliminary candidates from a local neighborhood, test if they're in free space
n_samples_camera_pose_candidates = 20   # generate this many candidates from free space, compute view scores

n_voxel_size = scene["voxel_extent_meters"]*asset_units_per_meter

# local neighborhood bounding boxes for random walk
n_query_half_extent_relative_to_start   = array([np.inf,np.inf,0.25])*asset_units_per_meter
n_query_half_extent_relative_to_current = array([1.5,1.5,0.25])*asset_units_per_meter



if args.use_python_reference_implementation:

    height_pixels = n_height_pixels
    width_pixels  = n_width_pixels
    fov_x         = n_fov_x

    # when randomly sampling an up vector, perturb it according to these parameters
    n_camera_up_hint_noise_std_dev = 0.1
    n_camera_up_hint_nominal       = array([0,0,1])

    fov_y = 2.0 * arctan(height_pixels * tan(fov_x/2) / width_pixels)

    uv_min  = -1.0
    uv_max  = 1.0
    half_du = 0.5 * (uv_max - uv_min) / width_pixels
    half_dv = 0.5 * (uv_max - uv_min) / height_pixels

    u, v = meshgrid(linspace(uv_min+half_du, uv_max-half_du, width_pixels),
                    linspace(uv_min+half_dv, uv_max-half_dv, height_pixels)[::-1])

    ray_offset_x = u*tan(fov_x/2.0)
    ray_offset_y = v*tan(fov_y/2.0)
    ray_offset_z = -ones_like(ray_offset_x)

    rays_cam = dstack((ray_offset_x,ray_offset_y,ray_offset_z))
    V_cam    = matrix(rays_cam.reshape(-1,3)).T

    # margin parameter for line-of-sight queries: point A must be closer than the scene geometry to point B,
    # along the ray from B to A, by a margin of eps percent, in order for A to be considered visible from B
    eps = 0.01

    # when attempting to find the initial look-at position, sample the occupancy map slightly closer to the
    # initial look-from position than the point of mesh intersection, but at least delta units away from the
    # initial look-from position to avoid a degenerate (look-from, look-at) pair
    delta = 0.0001

    # constant term added to the view saliency score; as lamb goes to infinty, the distribution of view saliency
    # scores will approach a uniform distribution
    lamb = 0.0

    np.random.seed(0)



# get cameras from the original asset file
df_cameras_asset_export = pd.read_csv(metadata_cameras_asset_export_csv_file)
df_cameras = pd.DataFrame(columns=["camera_name"])
i = 0

for c in df_cameras_asset_export.to_records():

    in_camera_name                            = c["camera_name"]
    in_camera_dir                             = os.path.join(asset_export_dir, in_camera_name)
    in_camera_keyframe_positions_hdf5_file    = os.path.join(in_camera_dir, "camera_keyframe_positions.hdf5")
    in_camera_keyframe_orientations_hdf5_file = os.path.join(in_camera_dir, "camera_keyframe_orientations.hdf5")

    assert len(in_camera_name.lstrip("cam_")) != 2 or not in_camera_name.lstrip("cam_").isdigit()

    out_camera_name                                 = "cam_%02d" % i
    out_camera_dir                                  = os.path.join(args.scene_dir, "_detail", out_camera_name)
    out_camera_preview_dir                          = os.path.join(args.scene_dir, "_detail", out_camera_name, "preview")
    out_camera_keyframe_frame_indices_hdf5_file     = os.path.join(out_camera_dir, "camera_keyframe_frame_indices.hdf5")
    out_camera_keyframe_positions_hdf5_file         = os.path.join(out_camera_dir, "camera_keyframe_positions.hdf5")
    out_camera_keyframe_look_at_positions_hdf5_file = os.path.join(out_camera_dir, "camera_keyframe_look_at_positions.hdf5")
    out_camera_keyframe_orientations_hdf5_file      = os.path.join(out_camera_dir, "camera_keyframe_orientations.hdf5")
    out_metadata_camera_csv_file                    = os.path.join(out_camera_dir, "metadata_camera.csv")

    if not os.path.exists(out_camera_dir): os.makedirs(out_camera_dir)
    if not os.path.exists(out_camera_preview_dir): os.makedirs(out_camera_preview_dir)

    with h5py.File(in_camera_keyframe_positions_hdf5_file,    "r") as f: in_camera_keyframe_positions    = f["dataset"][:]
    with h5py.File(in_camera_keyframe_orientations_hdf5_file, "r") as f: in_camera_keyframe_orientations = f["dataset"][:]

    print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK] Input camera " + in_camera_name + ", output camera " + out_camera_name + "...")



    if not args.use_python_reference_implementation:

        camera_look_from_positions, camera_look_at_positions, camera_orientations, intersection_distances, prim_ids = \
            random_walk_utils.generate_camera_trajectory_random_walk(
                mesh_vertices,
                mesh_faces_vi,
                octomap_bt_file,
                octomap_free_space_min,
                octomap_free_space_max,
                in_camera_keyframe_positions[0],
                in_camera_keyframe_orientations[0],
                n_width_pixels,
                n_height_pixels,
                n_fov_x,
                n_samples_random_walk,
                n_samples_octomap_query,
                n_samples_camera_pose_candidates,
                n_voxel_size,
                n_query_half_extent_relative_to_current,
                n_query_half_extent_relative_to_start,
                tmp_dir=tmp_dir)

        if camera_look_from_positions is None or camera_look_at_positions is None or camera_orientations is None or intersection_distances is None or prim_ids is None:
            print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK] WARNING: random_walk_utils.generate_camera_trajectory_random_walk DID NOT EXECUTE SUCCESSFULLY. SKIPPING.")
            if not os.listdir(out_camera_preview_dir): os.rmdir(out_camera_preview_dir)
            if not os.listdir(out_camera_dir): os.rmdir(out_camera_dir)
            i = i+1
            continue

        #
        # save preview images
        #

        for j in range(n_samples_random_walk):

            prim_ids_curr = prim_ids[j]
            obj_ids_curr  = mesh_faces_oi[prim_ids_curr]

            color_vals = ones_like(obj_ids_curr)*np.nan
            for obj_id,color_val in zip(obj_ids_unique,color_vals_unique):
                color_vals[obj_id == obj_ids_curr] = color_val
            color_vals[prim_ids_curr == -1] = np.nan

            out_camera_preview_jpg_file = os.path.join(out_camera_preview_dir, "frame.%04d.jpg" % j)
            imsave(out_camera_preview_jpg_file, color_vals, vmin=np.min(color_vals_unique), vmax=np.max(color_vals_unique))

        #
        # final output values
        #

        num_keyframes                         = n_samples_random_walk
        out_camera_keyframe_frame_indices     = arange(num_keyframes)
        out_camera_keyframe_positions         = camera_look_from_positions
        out_camera_keyframe_look_at_positions = camera_look_at_positions
        out_camera_keyframe_orientations      = camera_orientations
        out_camera_frame_time_seconds         = 1.0



    if args.use_python_reference_implementation:

        # # note that skipping a camera trajectory like this will mean that metadata_cameras.csv will be
        # # incorrectly exported, so this if statement should be uncommented for debugging purposes only
        # if out_camera_name == "cam_00":
        #     i = i+1
        #     continue

        #
        # start_camera_look_from_position
        #

        start_camera_look_from_position = in_camera_keyframe_positions[0]

        #
        # start_camera_look_at_position
        #

        start_camera_R_world_from_cam = in_camera_keyframe_orientations[0]
        start_camera_look_at_dir      = -start_camera_R_world_from_cam[:,2]

        # compute intersection distance for center ray
        intersection_distances, intersection_normals, prim_ids = embree_utils.generate_ray_intersections(mesh_vertices, mesh_faces_vi, matrix(start_camera_look_from_position).A, matrix(start_camera_look_at_dir).A, tmp_dir=tmp_dir)
        intersection_distance = max(intersection_distances[0] - 1.75*n_voxel_size, delta)
        query_position        = start_camera_look_from_position + intersection_distance*start_camera_look_at_dir
        octomap_sample        = octomap_utils.generate_octomap_samples(octomap_bt_file, array([query_position]), tmp_dir)[0]

        if isfinite(intersection_distance) and octomap_sample == 0:
            start_camera_look_at_position = start_camera_look_from_position + intersection_distance*start_camera_look_at_dir
            computed_intersection_distance_image = False

        else:

            # try to find an unoccupied cell for the initial look-at position by shooting camera rays,
            # testing for intersections with the scene mesh, and testing the occupancy map cells slightly
            # before the intersections (when proceeding from the optical center of the camera to the
            # mesh intersection point); if no unoccupied cells can be found, try perturbing the camera
            # forwards along the camera's look-at vector slightly and trying again
            camera_z_axis                          = start_camera_R_world_from_cam[:,2]
            camera_perturb_attempts                = 8
            camera_perturb_length                  = 0.25*n_voxel_size
            all_intersection_distances_at_infinity = False
            encountered_unoccupied_cell            = False

            for p in range(camera_perturb_attempts):

                V_world              = start_camera_R_world_from_cam*V_cam
                ray_directions_world = V_world.T.A
                ray_positions_world  = ones_like(ray_directions_world) * (start_camera_look_from_position + p*camera_perturb_length*camera_z_axis)

                intersection_distances, intersection_normals, prim_ids = embree_utils.generate_ray_intersections(mesh_vertices, mesh_faces_vi, ray_positions_world, ray_directions_world, tmp_dir=tmp_dir)

                if not any(isfinite(intersection_distances)):
                    all_intersection_distances_at_infinity = True
                    break

                # clip rays against octomap bounding box, see https://tavianator.com/fast-branchless-raybounding-box-intersections/
                ray_directions_world = sklearn.preprocessing.normalize(ray_directions_world)
                t_min                = ones_like(intersection_distances)*-np.inf
                t_max                = ones_like(intersection_distances)*np.inf

                t_x0 = (octomap_free_space_min[0] - ray_positions_world[:,0]) / ray_directions_world[:,0]
                t_x1 = (octomap_free_space_max[0] - ray_positions_world[:,0]) / ray_directions_world[:,0]
                mask = logical_not(isclose(ray_directions_world[:,0], 0))
                t_min[mask] = np.maximum(t_min[mask], np.minimum(t_x0[mask], t_x1[mask]))
                t_max[mask] = np.minimum(t_max[mask], np.maximum(t_x0[mask], t_x1[mask]))

                t_y0 = (octomap_free_space_min[1] - ray_positions_world[:,1]) / ray_directions_world[:,1]
                t_y1 = (octomap_free_space_max[1] - ray_positions_world[:,1]) / ray_directions_world[:,1]
                mask = logical_not(isclose(ray_directions_world[:,1], 0))
                t_min[mask] = np.maximum(t_min[mask], np.minimum(t_y0[mask], t_y1[mask]))
                t_max[mask] = np.minimum(t_max[mask], np.maximum(t_y0[mask], t_y1[mask]))

                t_z0 = (octomap_free_space_min[2] - ray_positions_world[mask][:,2]) / ray_directions_world[:,2]
                t_z1 = (octomap_free_space_max[2] - ray_positions_world[mask][:,2]) / ray_directions_world[:,2]
                mask = logical_not(isclose(ray_directions_world[:,2], 0))
                t_min[mask] = np.maximum(t_min[mask], np.minimum(t_z0[mask], t_z1[mask]))
                t_max[mask] = np.minimum(t_max[mask], np.maximum(t_z0[mask], t_z1[mask]))

                assert all(isfinite(t_min))
                assert all(isfinite(t_max))
                assert all(t_max > t_min) # assert all rays intersect bounding box
                assert all(t_min < 0.5*1.75*n_voxel_size) # assert all rays start from inside bounding box (with a bit of slack because bounding box min and max might be off by a half voxel)

                # import mayavi_utils
                # import mayavi.mlab
                # tmp = ray_positions_world + t_max[:,newaxis]*ray_directions_world
                # mayavi_utils.points3d_color_by_scalar(tmp, scalars=zeros_like(t_max), scale_factor=1.0, opacity=1.0)
                # mayavi.mlab.triangular_mesh(mesh_vertices[:,0], mesh_vertices[:,1], mesh_vertices[:,2], mesh_faces_vi, representation="surface", color=(0.75,0.75,0.75), opacity=0.25)
                # mayavi.mlab.show()

                t_max[logical_not(isfinite(intersection_distances))] = np.inf
                intersection_distances = np.maximum(np.minimum(intersection_distances, t_max) - 1.75*n_voxel_size,  delta)

                query_positions = (start_camera_look_from_position + p*camera_perturb_length*camera_z_axis) + intersection_distances[:,newaxis]*ray_directions_world
                octomap_samples = octomap_utils.generate_octomap_samples(octomap_bt_file, query_positions, tmp_dir)

                # import mayavi_utils
                # import mayavi.mlab
                # tmp = query_positions
                # mayavi_utils.points3d_color_by_scalar(tmp, scalars=octomap_samples, scale_factor=1.0, opacity=1.0)
                # mayavi.mlab.triangular_mesh(mesh_vertices[:,0], mesh_vertices[:,1], mesh_vertices[:,2], mesh_faces_vi, representation="surface", color=(0.75,0.75,0.75), opacity=0.25)
                # mayavi.mlab.show()

                if any(octomap_samples == 0):
                    encountered_unoccupied_cell = True
                    break

            if all_intersection_distances_at_infinity:
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK] WARNING: CAMERA DOESN'T OBSERVE ANY PART OF THE SCENE. ALL INTERSECTION DISTANCES ARE AT INFINITY. GIVING UP.")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                continue

            if not encountered_unoccupied_cell:
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK] WARNING: CAMERA DOESN'T OBSERVE ANY PART OF THE SCENE. ALL OBSERVED OCTOMAP SAMPLES ARE UNKNOWN OR OCCUPIED. GIVING UP.")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK]")
                continue

            computed_intersection_distance_image = True

            half_dx = 0.5
            half_dy = 0.5
            pixel_center = array([(width_pixels+1)/2.0, (height_pixels+1)/2.0])
            pixel_x, pixel_y = meshgrid(linspace(half_dx, width_pixels+half_dx,  width_pixels),
                                        linspace(half_dy, height_pixels+half_dy, height_pixels))

            pixels                     = dstack((pixel_x,pixel_y)).reshape(-1,2)
            center_to_pixels           = pixels - pixel_center
            center_to_pixels_distances = linalg.norm(center_to_pixels, axis=1)
            center_to_pixels_distances[logical_not(isfinite(intersection_distances))] = np.inf
            center_to_pixels_distances[octomap_samples != 0]                          = np.inf
            assert any(isfinite(center_to_pixels_distances))

            selected_index                = argsort(center_to_pixels_distances)[0]
            ray_direction_world           = ray_directions_world[selected_index]
            intersection_distance         = intersection_distances[selected_index]
            start_camera_look_at_position = start_camera_look_from_position + intersection_distance*ray_direction_world

        #
        # save preview image
        #

        if not computed_intersection_distance_image:
            V_world = start_camera_R_world_from_cam*V_cam
            ray_directions_world = V_world.T.A
            ray_positions_world  = ones_like(ray_directions_world) * start_camera_look_from_position
            intersection_distances, intersection_normals, prim_ids = \
                embree_utils.generate_ray_intersections(mesh_vertices, mesh_faces_vi, ray_positions_world, ray_directions_world, tmp_dir=tmp_dir)

        prim_ids      = prim_ids.reshape(height_pixels, width_pixels)
        prim_ids_curr = prim_ids
        obj_ids_curr  = mesh_faces_oi[prim_ids_curr]

        color_vals = ones_like(obj_ids_curr)*np.nan
        for obj_id,color_val in zip(obj_ids_unique,color_vals_unique):
            color_vals[obj_id == obj_ids_curr] = color_val
        color_vals[prim_ids_curr == -1] = np.nan

        out_camera_preview_jpg_file = os.path.join(out_camera_preview_dir, "frame.%04d.jpg" % 0)
        imsave(out_camera_preview_jpg_file, color_vals, vmin=np.min(color_vals_unique), vmax=np.max(color_vals_unique))

        #
        # camera_up_hints
        #

        camera_up_hint_noise = np.random.randn(n_samples_random_walk,3)*n_camera_up_hint_noise_std_dev
        camera_up_hints      = n_camera_up_hint_nominal + camera_up_hint_noise

        #
        # compute random walk
        #

        current_camera_look_from_position = start_camera_look_from_position
        current_camera_look_at_position   = start_camera_look_at_position
        current_camera_orientation        = start_camera_R_world_from_cam

        random_walk_camera_look_from_positions = [current_camera_look_from_position]
        random_walk_camera_look_at_positions   = [current_camera_look_at_position]
        random_walk_camera_orientations        = [current_camera_orientation]

        for j in range(1,n_samples_random_walk):

            print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK] j = " + str(j))

            #
            # look_from_position_candidates
            #

            current_position = current_camera_look_from_position
            start_position   = start_camera_look_from_position

            query_extent    = 2*n_query_half_extent_relative_to_current
            query_offsets   = np.random.rand(n_samples_octomap_query, 3)*query_extent - n_query_half_extent_relative_to_current
            query_positions = current_position + query_offsets

            # filter according to global min and max boundaries
            query_positions = query_positions[all(query_positions >= start_position - n_query_half_extent_relative_to_start, axis=1)]
            query_positions = query_positions[all(query_positions <= start_position + n_query_half_extent_relative_to_start, axis=1)]
            assert query_positions.shape[0] > 0

            # filter according to occupancy
            octomap_samples = octomap_utils.generate_octomap_samples(octomap_bt_file, query_positions, tmp_dir)
            query_positions = query_positions[octomap_samples == 0]
            assert query_positions.shape[0] > 0

            # filter according to line of sight
            current_to_query           = query_positions - current_position
            current_to_query_distances = linalg.norm(current_to_query, axis=1)
            query_ray_directions       = current_to_query / current_to_query_distances[:,newaxis]
            query_ray_positions        = ones_like(query_ray_directions)*current_position
            intersection_distances, intersection_normals, prim_ids = embree_utils.generate_ray_intersections(mesh_vertices, mesh_faces_vi, query_ray_positions, query_ray_directions, tmp_dir=tmp_dir)
            query_positions = query_positions[(1-eps)*intersection_distances >= current_to_query_distances]
            assert query_positions.shape[0] > 0

            look_from_position_candidates = query_positions

            #
            # look_at_position_candidates
            #

            current_position = current_camera_look_at_position
            start_position   = start_camera_look_at_position

            query_extent    = 2*n_query_half_extent_relative_to_current
            query_offsets   = np.random.rand(n_samples_octomap_query, 3)*query_extent - n_query_half_extent_relative_to_current
            query_positions = current_position + query_offsets

            # filter according to global min and max boundaries
            query_positions = query_positions[all(query_positions >= start_position - n_query_half_extent_relative_to_start, axis=1)]
            query_positions = query_positions[all(query_positions <= start_position + n_query_half_extent_relative_to_start, axis=1)]
            assert query_positions.shape[0] > 0

            # filter according to occupancy
            octomap_samples = octomap_utils.generate_octomap_samples(octomap_bt_file, query_positions, tmp_dir)
            query_positions = query_positions[octomap_samples == 0]
            assert query_positions.shape[0] > 0

            # filter according to line of sight
            current_to_query           = query_positions - current_position
            current_to_query_distances = linalg.norm(current_to_query, axis=1)
            query_ray_directions       = current_to_query
            query_ray_positions        = ones_like(query_ray_directions)*current_position
            intersection_distances, intersection_normals, prim_ids = embree_utils.generate_ray_intersections(mesh_vertices, mesh_faces_vi, query_ray_positions, query_ray_directions, tmp_dir=tmp_dir)
            query_positions = query_positions[(1-eps)*intersection_distances >= current_to_query_distances]
            assert query_positions.shape[0] > 0

            look_at_position_candidates = query_positions

            # import mayavi_utils
            # import mayavi.mlab
            # tmp = array([current_camera_look_from_position, current_camera_look_at_position])
            # mayavi.mlab.plot3d(tmp[:,0], tmp[:,1], tmp[:,2], tube_radius=0.2, opacity=1.0, color=(0.75,0.0,0.0))
            # mayavi_utils.points3d_color_by_scalar(tmp, scalars=[0,0], scale_factor=0.4, opacity=1.0)
            # # mayavi_utils.points3d_color_by_scalar(query_positions, scalars=octomap_samples, scale_factor=0.2, opacity=1.0)
            # mayavi.mlab.triangular_mesh(mesh_vertices[:,0], mesh_vertices[:,1], mesh_vertices[:,2], mesh_faces_vi, representation="surface", color=(0.75,0.75,0.75), opacity=0.25)
            # mayavi.mlab.show()
            # assert False

            #
            # raycast against triangle mesh for each camera pose candidate
            #

            look_from_position_candidates = look_from_position_candidates[np.random.choice(look_from_position_candidates.shape[0], size=n_samples_camera_pose_candidates)]
            look_at_position_candidates   = look_at_position_candidates[np.random.choice(look_at_position_candidates.shape[0],     size=n_samples_camera_pose_candidates)]
            camera_up_hint                = camera_up_hints[j]

            camera_orientation_candidates = zeros((n_samples_camera_pose_candidates,3,3))

            for k in range(n_samples_camera_pose_candidates):

                camera_look_from_position = look_from_position_candidates[k]
                camera_look_at_position   = look_at_position_candidates[k]
                camera_look_at_dir        = sklearn.preprocessing.normalize(array([camera_look_at_position - camera_look_from_position]))[0]

                # The convention here is that the camera's positive x axis points right, the positive y
                # axis points up, and the positive z axis points away from where the camera is looking.
                camera_z_axis = -sklearn.preprocessing.normalize(array([camera_look_at_dir]))
                camera_x_axis = -sklearn.preprocessing.normalize(cross(camera_z_axis, camera_up_hint))
                camera_y_axis = sklearn.preprocessing.normalize(cross(camera_z_axis, camera_x_axis))

                R_world_from_cam = c_[ matrix(camera_x_axis).T, matrix(camera_y_axis).T, matrix(camera_z_axis).T ]
                V_world = R_world_from_cam*V_cam

                camera_orientation_candidates[k] = R_world_from_cam

                if k == 0:
                    ray_directions_world = V_world.T.A
                    ray_positions_world  = ones_like(V_world.T.A) * camera_look_from_position
                else:
                    ray_directions_world = r_[ray_directions_world, V_world.T.A]
                    ray_positions_world  = r_[ray_positions_world,  ones_like(V_world.T.A) * camera_look_from_position]

            intersection_distances, intersection_normals, prim_ids = \
                embree_utils.generate_ray_intersections(mesh_vertices, mesh_faces_vi, ray_positions_world, ray_directions_world, tmp_dir=tmp_dir)

            #
            # select a camera pose candidate with probability proportional to the view score
            #

            prim_ids    = prim_ids.reshape(n_samples_camera_pose_candidates, height_pixels, width_pixels)
            view_scores = zeros((n_samples_camera_pose_candidates))
            for k in range(n_samples_camera_pose_candidates):
                prim_ids_curr    = prim_ids[k]
                prim_ids_unique  = unique(prim_ids_curr)
                valid_fraction   = float(count_nonzero(prim_ids_curr != -1)) / float(height_pixels*width_pixels)
                num_unique_prims = prim_ids_unique.shape[0]
                view_scores[k]   = (valid_fraction**2)*num_unique_prims + lamb

            selected_index = np.random.choice(n_samples_camera_pose_candidates, p=view_scores/sum(view_scores))
            # selected_index = np.argmax(view_scores)

            #
            # save preview image
            #

            prim_ids_curr = prim_ids[selected_index]
            obj_ids_curr  = mesh_faces_oi[prim_ids_curr]

            color_vals = ones_like(obj_ids_curr)*np.nan
            for obj_id,color_val in zip(obj_ids_unique,color_vals_unique):
                color_vals[obj_id == obj_ids_curr] = color_val
            color_vals[prim_ids_curr == -1] = np.nan

            out_camera_preview_jpg_file = os.path.join(out_camera_preview_dir, "frame.%04d.jpg" % j)
            imsave(out_camera_preview_jpg_file, color_vals, vmin=np.min(color_vals_unique), vmax=np.max(color_vals_unique))

            #
            # append selected camera pose to random walk
            #

            current_camera_look_from_position = look_from_position_candidates[selected_index]
            current_camera_look_at_position   = look_at_position_candidates[selected_index]
            current_camera_orientation        = camera_orientation_candidates[selected_index]

            random_walk_camera_look_from_positions.append(current_camera_look_from_position)
            random_walk_camera_look_at_positions.append(current_camera_look_at_position)
            random_walk_camera_orientations.append(current_camera_orientation)

        random_walk_camera_look_from_positions = array(random_walk_camera_look_from_positions)
        random_walk_camera_look_at_positions   = array(random_walk_camera_look_at_positions)
        random_walk_camera_orientations        = array(random_walk_camera_orientations)

        num_keyframes                         = n_samples_random_walk
        out_camera_keyframe_frame_indices     = arange(num_keyframes)
        out_camera_keyframe_positions         = random_walk_camera_look_from_positions
        out_camera_keyframe_look_at_positions = random_walk_camera_look_at_positions
        out_camera_keyframe_orientations      = random_walk_camera_orientations
        out_camera_frame_time_seconds         = 1.0



    df_cameras = df_cameras.append({"camera_name":out_camera_name}, ignore_index=True)

    with h5py.File(out_camera_keyframe_frame_indices_hdf5_file,     "w") as f: f.create_dataset("dataset", data=out_camera_keyframe_frame_indices)
    with h5py.File(out_camera_keyframe_positions_hdf5_file,         "w") as f: f.create_dataset("dataset", data=out_camera_keyframe_positions)
    with h5py.File(out_camera_keyframe_look_at_positions_hdf5_file, "w") as f: f.create_dataset("dataset", data=out_camera_keyframe_look_at_positions)
    with h5py.File(out_camera_keyframe_orientations_hdf5_file,      "w") as f: f.create_dataset("dataset", data=out_camera_keyframe_orientations)

    df_camera = pd.DataFrame(columns=["parameter_name", "parameter_value"], data={"parameter_name": ["frame_time_seconds"], "parameter_value": [out_camera_frame_time_seconds]})
    df_camera.to_csv(out_metadata_camera_csv_file, index=False)

    i = i+1

df_cameras.to_csv(metadata_cameras_csv_file, index=False)



print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_RANDOM_WALK] Finished.")
