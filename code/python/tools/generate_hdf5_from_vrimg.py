#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import inspect
import glob
import os
import pandas as pd
import shutil

import path_utils

parser = argparse.ArgumentParser()
parser.add_argument("--in_vrimg_files", required=True)
parser.add_argument("--in_camera_trajectory_dir")
parser.add_argument("--in_metadata_nodes_file")
parser.add_argument("--in_metadata_scene_file")
parser.add_argument("--out_hdf5_dir", required=True)
parser.add_argument("--out_preview_dir", required=True)
parser.add_argument("--tmp_dir", required=True)
parser.add_argument("--render_pass", required=True)
parser.add_argument("--denoise", action="store_true")
args = parser.parse_args()

assert args.render_pass == "geometry" or args.render_pass == "final"
assert not (args.render_pass == "geometry" and args.denoise)

if args.render_pass == "geometry":
    assert args.in_camera_trajectory_dir is not None
    assert args.in_metadata_nodes_file is not None
    assert args.in_metadata_scene_file is not None
    assert os.path.exists(args.in_camera_trajectory_dir)

path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config



print("[HYPERSIM: GENERATE_HDF5_FROM_VRIMG] Begin...")



input_dir = os.path.dirname(args.in_vrimg_files)
if input_dir == "":
    input_dir = "."

assert os.path.exists(input_dir)

if not os.path.exists(args.out_hdf5_dir): os.makedirs(args.out_hdf5_dir)
if not os.path.exists(args.out_preview_dir): os.makedirs(args.out_preview_dir)
if not os.path.exists(args.tmp_dir): os.makedirs(args.tmp_dir)



if args.render_pass == "geometry":

    camera_keyframe_frame_indices_hdf5_file = os.path.join(args.in_camera_trajectory_dir, "camera_keyframe_frame_indices.hdf5")
    camera_keyframe_positions_hdf5_file     = os.path.join(args.in_camera_trajectory_dir, "camera_keyframe_positions.hdf5")
    camera_keyframe_orientations_hdf5_file  = os.path.join(args.in_camera_trajectory_dir, "camera_keyframe_orientations.hdf5")

    with h5py.File(camera_keyframe_frame_indices_hdf5_file, "r") as f: camera_keyframe_frame_indices = f["dataset"][:]
    with h5py.File(camera_keyframe_positions_hdf5_file,     "r") as f: camera_keyframe_positions     = f["dataset"][:]
    with h5py.File(camera_keyframe_orientations_hdf5_file,  "r") as f: camera_keyframe_orientations  = f["dataset"][:]

    assert all(camera_keyframe_frame_indices == arange(camera_keyframe_frame_indices.shape[0]))

    # What we'd really like is metadata for all render entities, but we currently aren't saving that, so we use node metadata instead.
    # In practice this is fine because we set all lights to be invisible, so we only expect to see nodes in the rendered images.
    df_nodes = pd.read_csv(args.in_metadata_nodes_file)
    np.random.seed(0)
    node_ids_unique   = df_nodes["node_id"].to_numpy()
    color_vals_unique = arange(node_ids_unique.shape[0])
    np.random.shuffle(color_vals_unique)

    df_scene = pd.read_csv(args.in_metadata_scene_file, index_col="parameter_name")
    meters_per_asset_unit = df_scene.loc["meters_per_asset_unit"][0]



in_filenames = [ os.path.basename(f) for f in sort(glob.glob(args.in_vrimg_files)) ]

for in_filename in in_filenames:

    in_file  = os.path.join(input_dir, in_filename)
    out_file = os.path.join(args.tmp_dir, "_tmp_frame.vrimg")
    shutil.copy(in_file, out_file)

    if args.denoise:

        #
        # denoise
        #

        in_file  = os.path.join(args.tmp_dir, "_tmp_frame.vrimg")

        cmd = _system_config.vdenoise_bin + \
            " -inputFile=" + in_file + \
            ' -mode=default -denoiseElements="RGB Color;VRayAtmosphere;VRayBackground;VRayCaustics;VRayDiffuseFilter;VRayGlobalIllumination;VRayLighting;VRayRawTotalLighting;VRayReflection;VRayRefraction;VRaySelfIllumination;VRaySpecular;VRaySSS2;VRayTotalLighting" -verboseLevel=4 -display=0'
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        in_file  = os.path.join(args.tmp_dir, "_tmp_frame_denoised.vrimg")
        out_file = os.path.join(args.tmp_dir, "_tmp_frame.vrimg")
        shutil.move(in_file, out_file)

    #
    # convert to exr
    #

    input_file = os.path.join(args.tmp_dir, "_tmp_frame.vrimg")

    cmd = _system_config.vrimg2exr_bin + \
        " " + input_file
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    #
    # convert to hdf5
    #

    if args.render_pass == "geometry":

        output_channels_allow_list = [
            "R",
            "G",
            "B",
            "VRayRenderEntityID",
            "VRayPosition.R",
            "VRayPosition.G",
            "VRayPosition.B",
            "VRayNormal.R",
            "VRayNormal.G",
            "VRayNormal.B",
            "VRayNormalBump.R",
            "VRayNormalBump.G",
            "VRayNormalBump.B",
            "VRayTexCoord.R",
            "VRayTexCoord.G",
            "VRayTexCoord.B" ]

    if args.render_pass == "final":

        output_channels_allow_list = [
            "R",
            "G",
            "B",
            "VRayDiffuseFilter.R",
            "VRayDiffuseFilter.G",
            "VRayDiffuseFilter.B",
            "VRayRawTotalLighting.R",
            "VRayRawTotalLighting.G",
            "VRayRawTotalLighting.B",
            "VRayReflection.R",
            "VRayReflection.G",
            "VRayReflection.B",
            "VRayRefraction.R",
            "VRayRefraction.G",
            "VRayRefraction.B",
            "VRaySpecular.R",
            "VRaySpecular.G",
            "VRaySpecular.B",
            "VRaySSS2.R",
            "VRaySSS2.G",
            "VRaySSS2.B",
            "VRaySelfIllumination.R",
            "VRaySelfIllumination.G",
            "VRaySelfIllumination.B",
            "VRayCaustics.R",
            "VRayCaustics.G",
            "VRayCaustics.B",
            "VRayAtmosphere.R",
            "VRayAtmosphere.G",
            "VRayAtmosphere.B",
            "VRayBackground.R",
            "VRayBackground.G",
            "VRayBackground.B" ]

    current_source_path             = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    generate_hdf5_from_exr_bin      = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_hdf5_from_exr"))
    input_file                      = os.path.join(args.tmp_dir, "_tmp_frame.exr")
    output_file                     = os.path.join(args.tmp_dir, "_tmp_frame")
    output_channels_allow_list_args = " --o " + " --o ".join(output_channels_allow_list)

    cmd = generate_hdf5_from_exr_bin + \
        " --input_file "  + input_file  + \
        " --output_file " + output_file + \
        output_channels_allow_list_args
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    #
    # generate hdf5 output
    #

    in_file_root = in_filename.replace(".vrimg", "")

    if args.render_pass == "geometry":

        in_vray_rgb_color_r_hdf5_file      = os.path.join(args.tmp_dir, "_tmp_frame.R.hdf5")
        in_vray_rgb_color_g_hdf5_file      = os.path.join(args.tmp_dir, "_tmp_frame.G.hdf5")
        in_vray_rgb_color_b_hdf5_file      = os.path.join(args.tmp_dir, "_tmp_frame.B.hdf5")
        in_vray_render_entity_id_hdf5_file = os.path.join(args.tmp_dir, "_tmp_frame.VRayRenderEntityID.hdf5")
        in_vray_position_r_hdf5_file       = os.path.join(args.tmp_dir, "_tmp_frame.VRayPosition.R.hdf5")
        in_vray_position_g_hdf5_file       = os.path.join(args.tmp_dir, "_tmp_frame.VRayPosition.G.hdf5")
        in_vray_position_b_hdf5_file       = os.path.join(args.tmp_dir, "_tmp_frame.VRayPosition.B.hdf5")
        in_vray_normal_r_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayNormal.R.hdf5")
        in_vray_normal_g_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayNormal.G.hdf5")
        in_vray_normal_b_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayNormal.B.hdf5")
        in_vray_normal_bump_r_hdf5_file    = os.path.join(args.tmp_dir, "_tmp_frame.VRayNormalBump.R.hdf5")
        in_vray_normal_bump_g_hdf5_file    = os.path.join(args.tmp_dir, "_tmp_frame.VRayNormalBump.G.hdf5")
        in_vray_normal_bump_b_hdf5_file    = os.path.join(args.tmp_dir, "_tmp_frame.VRayNormalBump.B.hdf5")
        in_vray_tex_coord_r_hdf5_file      = os.path.join(args.tmp_dir, "_tmp_frame.VRayTexCoord.R.hdf5")
        in_vray_tex_coord_g_hdf5_file      = os.path.join(args.tmp_dir, "_tmp_frame.VRayTexCoord.G.hdf5")
        in_vray_tex_coord_b_hdf5_file      = os.path.join(args.tmp_dir, "_tmp_frame.VRayTexCoord.B.hdf5")

        out_render_entity_id_hdf5_file  = os.path.join(args.out_hdf5_dir, in_file_root + ".render_entity_id.hdf5")
        out_position_hdf5_file          = os.path.join(args.out_hdf5_dir, in_file_root + ".position.hdf5")
        out_depth_meters_hdf5_file      = os.path.join(args.out_hdf5_dir, in_file_root + ".depth_meters.hdf5")
        out_normal_world_hdf5_file      = os.path.join(args.out_hdf5_dir, in_file_root + ".normal_world.hdf5")
        out_normal_cam_hdf5_file        = os.path.join(args.out_hdf5_dir, in_file_root + ".normal_cam.hdf5")
        out_normal_bump_world_hdf5_file = os.path.join(args.out_hdf5_dir, in_file_root + ".normal_bump_world.hdf5")
        out_normal_bump_cam_hdf5_file   = os.path.join(args.out_hdf5_dir, in_file_root + ".normal_bump_cam.hdf5")
        out_tex_coord_hdf5_file         = os.path.join(args.out_hdf5_dir, in_file_root + ".tex_coord.hdf5")

        out_color_jpg_file             = os.path.join(args.out_preview_dir, in_file_root + ".color.jpg")
        out_gamma_jpg_file             = os.path.join(args.out_preview_dir, in_file_root + ".gamma.jpg")
        out_render_entity_id_png_file  = os.path.join(args.out_preview_dir, in_file_root + ".render_entity_id.png")
        out_depth_meters_png_file      = os.path.join(args.out_preview_dir, in_file_root + ".depth_meters.png")
        out_normal_world_png_file      = os.path.join(args.out_preview_dir, in_file_root + ".normal_world.png")
        out_normal_cam_png_file        = os.path.join(args.out_preview_dir, in_file_root + ".normal_cam.png")
        out_normal_bump_world_png_file = os.path.join(args.out_preview_dir, in_file_root + ".normal_bump_world.png")
        out_normal_bump_cam_png_file   = os.path.join(args.out_preview_dir, in_file_root + ".normal_bump_cam.png")
        out_tex_coord_png_file         = os.path.join(args.out_preview_dir, in_file_root + ".tex_coord.png")

        with h5py.File(in_vray_rgb_color_r_hdf5_file,      "r") as f: vray_rgb_color_r      = f["dataset"][:]
        with h5py.File(in_vray_rgb_color_g_hdf5_file,      "r") as f: vray_rgb_color_g      = f["dataset"][:]
        with h5py.File(in_vray_rgb_color_b_hdf5_file,      "r") as f: vray_rgb_color_b      = f["dataset"][:]
        with h5py.File(in_vray_render_entity_id_hdf5_file, "r") as f: vray_render_entity_id = f["dataset"][:]
        with h5py.File(in_vray_position_r_hdf5_file,       "r") as f: vray_position_r       = f["dataset"][:]
        with h5py.File(in_vray_position_g_hdf5_file,       "r") as f: vray_position_g       = f["dataset"][:]
        with h5py.File(in_vray_position_b_hdf5_file,       "r") as f: vray_position_b       = f["dataset"][:]
        with h5py.File(in_vray_normal_r_hdf5_file,         "r") as f: vray_normal_r         = f["dataset"][:]
        with h5py.File(in_vray_normal_g_hdf5_file,         "r") as f: vray_normal_g         = f["dataset"][:]
        with h5py.File(in_vray_normal_b_hdf5_file,         "r") as f: vray_normal_b         = f["dataset"][:]
        with h5py.File(in_vray_normal_bump_r_hdf5_file,    "r") as f: vray_normal_bump_r    = f["dataset"][:]
        with h5py.File(in_vray_normal_bump_g_hdf5_file,    "r") as f: vray_normal_bump_g    = f["dataset"][:]
        with h5py.File(in_vray_normal_bump_b_hdf5_file,    "r") as f: vray_normal_bump_b    = f["dataset"][:]
        with h5py.File(in_vray_tex_coord_r_hdf5_file,      "r") as f: vray_tex_coord_r      = f["dataset"][:]
        with h5py.File(in_vray_tex_coord_g_hdf5_file,      "r") as f: vray_tex_coord_g      = f["dataset"][:]
        with h5py.File(in_vray_tex_coord_b_hdf5_file,      "r") as f: vray_tex_coord_b      = f["dataset"][:]

        rgb_color         = dstack([vray_rgb_color_r, vray_rgb_color_g, vray_rgb_color_b])
        render_entity_id  = vray_render_entity_id.astype(int32)
        position          = dstack([vray_position_r,    vray_position_g,    vray_position_b])
        normal_world      = dstack([vray_normal_r,      vray_normal_g,      vray_normal_b])
        normal_bump_world = dstack([vray_normal_bump_r, vray_normal_bump_g, vray_normal_bump_b])
        tex_coord         = dstack([vray_tex_coord_r,   vray_tex_coord_g,   vray_tex_coord_b])

        # get image parameters
        height_pixels = rgb_color.shape[0] 
        width_pixels  = rgb_color.shape[1]

        # get camera parameters
        in_filename_ids = [int(t) for t in in_filename.split(".") if t.isdigit()]
        assert len(in_filename_ids) == 1
        frame_id     = in_filename_ids[0]
        keyframe_ids = where(camera_keyframe_frame_indices == frame_id)[0]
        assert len(keyframe_ids) == 1

        keyframe_id        = keyframe_ids[0]
        camera_position    = camera_keyframe_positions[keyframe_id]
        camera_orientation = camera_keyframe_orientations[keyframe_id]
        R_world_from_cam   = matrix(camera_orientation)
        R_cam_from_world   = R_world_from_cam.T

        # generate derived images
        invalid_mask                    = logical_or(render_entity_id == -1, render_entity_id == 0)
        render_entity_id[invalid_mask]  = -1
        position[invalid_mask]          = np.nan
        normal_world[invalid_mask]      = np.nan
        normal_bump_world[invalid_mask] = np.nan

        render_entity_id_ = ones_like(render_entity_id)*np.nan
        for node_id,color_val in zip(node_ids_unique,color_vals_unique):
            render_entity_id_[node_id == render_entity_id] = color_val
        render_entity_id_[invalid_mask] = np.nan

        depth        = linalg.norm(position - camera_position[newaxis,newaxis,:], axis=2)
        depth_meters = meters_per_asset_unit*depth

        N_world       = matrix(normal_world.reshape(-1,3)).T
        N_cam         = R_cam_from_world*N_world
        normal_cam    = N_cam.T.A.reshape(height_pixels, width_pixels, -1)
        normal_world_ = (normal_world + 1.0)/2.0
        normal_cam_   = (normal_cam + 1.0)/2.0

        N_bump_world       = matrix(normal_bump_world.reshape(-1,3)).T
        N_bump_cam         = R_cam_from_world*N_bump_world
        normal_bump_cam    = N_bump_cam.T.A.reshape(height_pixels, width_pixels, -1)
        normal_bump_world_ = (normal_bump_world + 1.0)/2.0
        normal_bump_cam_   = (normal_bump_cam + 1.0)/2.0

        gamma           = 1.0/2.2 # standard gamma correction exponent
        rgb_color_gamma = np.power(np.maximum(rgb_color,0), gamma)

        print("[HYPERSIM: GENERATE_HDF5_FROM_VRIMG] Saving output files for the input file: " + in_file_root + "...")

        with h5py.File(out_render_entity_id_hdf5_file,  "w") as f: f.create_dataset("dataset", data=render_entity_id.astype(int16),    compression="gzip", compression_opts=9)
        with h5py.File(out_position_hdf5_file,          "w") as f: f.create_dataset("dataset", data=position.astype(float16),          compression="gzip", compression_opts=9)
        with h5py.File(out_depth_meters_hdf5_file,      "w") as f: f.create_dataset("dataset", data=depth_meters.astype(float16),      compression="gzip", compression_opts=9)
        with h5py.File(out_normal_world_hdf5_file,      "w") as f: f.create_dataset("dataset", data=normal_world.astype(float16),      compression="gzip", compression_opts=9)
        with h5py.File(out_normal_cam_hdf5_file,        "w") as f: f.create_dataset("dataset", data=normal_cam.astype(float16),        compression="gzip", compression_opts=9)
        with h5py.File(out_normal_bump_world_hdf5_file, "w") as f: f.create_dataset("dataset", data=normal_bump_world.astype(float16), compression="gzip", compression_opts=9)
        with h5py.File(out_normal_bump_cam_hdf5_file,   "w") as f: f.create_dataset("dataset", data=normal_bump_cam.astype(float16),   compression="gzip", compression_opts=9)
        with h5py.File(out_tex_coord_hdf5_file,         "w") as f: f.create_dataset("dataset", data=tex_coord.astype(float16),         compression="gzip", compression_opts=9)

        eps = 0.000001 # amount of numerical slack when checking if normal images are in the range [0,1]
        assert all(np.min(normal_world_.reshape(-1,3),      axis=0)) > 0.0 - eps
        assert all(np.min(normal_cam_.reshape(-1,3),        axis=0)) > 0.0 - eps
        assert all(np.min(normal_bump_world_.reshape(-1,3), axis=0)) > 0.0 - eps
        assert all(np.min(normal_bump_cam_.reshape(-1,3),   axis=0)) > 0.0 - eps
        assert all(np.max(normal_world_.reshape(-1,3),      axis=0)) < 1.0 + eps
        assert all(np.max(normal_cam_.reshape(-1,3),        axis=0)) < 1.0 + eps
        assert all(np.max(normal_bump_world_.reshape(-1,3), axis=0)) < 1.0 + eps
        assert all(np.max(normal_bump_cam_.reshape(-1,3),   axis=0)) < 1.0 + eps

        # ideally we would normalize depth consistently for each scene, but we don't know a good depth range, so don't try to normalize
        # normals are already unit-length, but due to occasional numerical artifacts we need to clip anyway
        imsave(out_color_jpg_file,             clip(rgb_color,0,1))
        imsave(out_gamma_jpg_file,             clip(rgb_color_gamma,0,1))
        imsave(out_render_entity_id_png_file,  render_entity_id_, vmin=np.min(color_vals_unique), vmax=np.max(color_vals_unique))
        imsave(out_depth_meters_png_file,      depth_meters)
        imsave(out_normal_world_png_file,      clip(normal_world_,0,1))
        imsave(out_normal_cam_png_file,        clip(normal_cam_,0,1))
        imsave(out_normal_bump_world_png_file, clip(normal_bump_world_,0,1))
        imsave(out_normal_bump_cam_png_file,   clip(normal_bump_cam_,0,1))
        imsave(out_tex_coord_png_file,         clip(tex_coord,0,1))

    if args.render_pass == "final":

        in_vray_rgb_color_r_hdf5_file          = os.path.join(args.tmp_dir, "_tmp_frame.R.hdf5")
        in_vray_rgb_color_g_hdf5_file          = os.path.join(args.tmp_dir, "_tmp_frame.G.hdf5")
        in_vray_rgb_color_b_hdf5_file          = os.path.join(args.tmp_dir, "_tmp_frame.B.hdf5")
        in_vray_diffuse_filter_r_hdf5_file     = os.path.join(args.tmp_dir, "_tmp_frame.VRayDiffuseFilter.R.hdf5")
        in_vray_diffuse_filter_g_hdf5_file     = os.path.join(args.tmp_dir, "_tmp_frame.VRayDiffuseFilter.G.hdf5")
        in_vray_diffuse_filter_b_hdf5_file     = os.path.join(args.tmp_dir, "_tmp_frame.VRayDiffuseFilter.B.hdf5")
        in_vray_raw_total_lighting_r_hdf5_file = os.path.join(args.tmp_dir, "_tmp_frame.VRayRawTotalLighting.R.hdf5")
        in_vray_raw_total_lighting_g_hdf5_file = os.path.join(args.tmp_dir, "_tmp_frame.VRayRawTotalLighting.G.hdf5")
        in_vray_raw_total_lighting_b_hdf5_file = os.path.join(args.tmp_dir, "_tmp_frame.VRayRawTotalLighting.B.hdf5")
        in_vray_reflection_r_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayReflection.R.hdf5")
        in_vray_reflection_g_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayReflection.G.hdf5")
        in_vray_reflection_b_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayReflection.B.hdf5")
        in_vray_refraction_r_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayRefraction.R.hdf5")
        in_vray_refraction_g_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayRefraction.G.hdf5")
        in_vray_refraction_b_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayRefraction.B.hdf5")
        in_vray_specular_r_hdf5_file           = os.path.join(args.tmp_dir, "_tmp_frame.VRaySpecular.R.hdf5")
        in_vray_specular_g_hdf5_file           = os.path.join(args.tmp_dir, "_tmp_frame.VRaySpecular.G.hdf5")
        in_vray_specular_b_hdf5_file           = os.path.join(args.tmp_dir, "_tmp_frame.VRaySpecular.B.hdf5")
        in_vray_sss2_r_hdf5_file               = os.path.join(args.tmp_dir, "_tmp_frame.VRaySSS2.R.hdf5")
        in_vray_sss2_g_hdf5_file               = os.path.join(args.tmp_dir, "_tmp_frame.VRaySSS2.G.hdf5")
        in_vray_sss2_b_hdf5_file               = os.path.join(args.tmp_dir, "_tmp_frame.VRaySSS2.B.hdf5")
        in_vray_self_illumination_r_hdf5_file  = os.path.join(args.tmp_dir, "_tmp_frame.VRaySelfIllumination.R.hdf5")
        in_vray_self_illumination_g_hdf5_file  = os.path.join(args.tmp_dir, "_tmp_frame.VRaySelfIllumination.G.hdf5")
        in_vray_self_illumination_b_hdf5_file  = os.path.join(args.tmp_dir, "_tmp_frame.VRaySelfIllumination.B.hdf5")
        in_vray_caustics_r_hdf5_file           = os.path.join(args.tmp_dir, "_tmp_frame.VRayCaustics.R.hdf5")
        in_vray_caustics_g_hdf5_file           = os.path.join(args.tmp_dir, "_tmp_frame.VRayCaustics.G.hdf5")
        in_vray_caustics_b_hdf5_file           = os.path.join(args.tmp_dir, "_tmp_frame.VRayCaustics.B.hdf5")
        in_vray_atmosphere_r_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayAtmosphere.R.hdf5")
        in_vray_atmosphere_g_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayAtmosphere.G.hdf5")
        in_vray_atmosphere_b_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayAtmosphere.B.hdf5")
        in_vray_background_r_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayBackground.R.hdf5")
        in_vray_background_g_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayBackground.G.hdf5")
        in_vray_background_b_hdf5_file         = os.path.join(args.tmp_dir, "_tmp_frame.VRayBackground.B.hdf5")

        out_color_hdf5_file                = os.path.join(args.out_hdf5_dir, in_file_root + ".color.hdf5")
        out_diffuse_reflectance_hdf5_file  = os.path.join(args.out_hdf5_dir, in_file_root + ".diffuse_reflectance.hdf5")
        out_diffuse_illumination_hdf5_file = os.path.join(args.out_hdf5_dir, in_file_root + ".diffuse_illumination.hdf5")
        out_residual_hdf5_file             = os.path.join(args.out_hdf5_dir, in_file_root + ".residual.hdf5")

        out_color_jpg_file                = os.path.join(args.out_preview_dir, in_file_root + ".color.jpg")
        out_gamma_jpg_file                = os.path.join(args.out_preview_dir, in_file_root + ".gamma.jpg")
        out_diffuse_reflectance_jpg_file  = os.path.join(args.out_preview_dir, in_file_root + ".diffuse_reflectance.jpg")
        out_diffuse_illumination_jpg_file = os.path.join(args.out_preview_dir, in_file_root + ".diffuse_illumination.jpg")
        out_residual_jpg_file             = os.path.join(args.out_preview_dir, in_file_root + ".residual.jpg")
        out_lambertian_jpg_file           = os.path.join(args.out_preview_dir, in_file_root + ".lambertian.jpg")
        out_non_lambertian_jpg_file       = os.path.join(args.out_preview_dir, in_file_root + ".non_lambertian.jpg")
        out_diff_jpg_file                 = os.path.join(args.out_preview_dir, in_file_root + ".diff.jpg")

        with h5py.File(in_vray_rgb_color_r_hdf5_file,          "r") as f: vray_rgb_color_r          = f["dataset"][:]
        with h5py.File(in_vray_rgb_color_g_hdf5_file,          "r") as f: vray_rgb_color_g          = f["dataset"][:]
        with h5py.File(in_vray_rgb_color_b_hdf5_file,          "r") as f: vray_rgb_color_b          = f["dataset"][:]
        with h5py.File(in_vray_diffuse_filter_r_hdf5_file,     "r") as f: vray_diffuse_filter_r     = f["dataset"][:]
        with h5py.File(in_vray_diffuse_filter_g_hdf5_file,     "r") as f: vray_diffuse_filter_g     = f["dataset"][:]
        with h5py.File(in_vray_diffuse_filter_b_hdf5_file,     "r") as f: vray_diffuse_filter_b     = f["dataset"][:]
        with h5py.File(in_vray_raw_total_lighting_r_hdf5_file, "r") as f: vray_raw_total_lighting_r = f["dataset"][:]
        with h5py.File(in_vray_raw_total_lighting_g_hdf5_file, "r") as f: vray_raw_total_lighting_g = f["dataset"][:]
        with h5py.File(in_vray_raw_total_lighting_b_hdf5_file, "r") as f: vray_raw_total_lighting_b = f["dataset"][:]
        with h5py.File(in_vray_reflection_r_hdf5_file,         "r") as f: vray_reflection_r         = f["dataset"][:]
        with h5py.File(in_vray_reflection_g_hdf5_file,         "r") as f: vray_reflection_g         = f["dataset"][:]
        with h5py.File(in_vray_reflection_b_hdf5_file,         "r") as f: vray_reflection_b         = f["dataset"][:]
        with h5py.File(in_vray_refraction_r_hdf5_file,         "r") as f: vray_refraction_r         = f["dataset"][:]
        with h5py.File(in_vray_refraction_g_hdf5_file,         "r") as f: vray_refraction_g         = f["dataset"][:]
        with h5py.File(in_vray_refraction_b_hdf5_file,         "r") as f: vray_refraction_b         = f["dataset"][:]
        with h5py.File(in_vray_specular_r_hdf5_file,           "r") as f: vray_specular_r           = f["dataset"][:]
        with h5py.File(in_vray_specular_g_hdf5_file,           "r") as f: vray_specular_g           = f["dataset"][:]
        with h5py.File(in_vray_specular_b_hdf5_file,           "r") as f: vray_specular_b           = f["dataset"][:]
        with h5py.File(in_vray_sss2_r_hdf5_file,               "r") as f: vray_sss2_r               = f["dataset"][:]
        with h5py.File(in_vray_sss2_g_hdf5_file,               "r") as f: vray_sss2_g               = f["dataset"][:]
        with h5py.File(in_vray_sss2_b_hdf5_file,               "r") as f: vray_sss2_b               = f["dataset"][:]
        with h5py.File(in_vray_self_illumination_r_hdf5_file,  "r") as f: vray_self_illumination_r  = f["dataset"][:]
        with h5py.File(in_vray_self_illumination_g_hdf5_file,  "r") as f: vray_self_illumination_g  = f["dataset"][:]
        with h5py.File(in_vray_self_illumination_b_hdf5_file,  "r") as f: vray_self_illumination_b  = f["dataset"][:]
        with h5py.File(in_vray_caustics_r_hdf5_file,           "r") as f: vray_caustics_r           = f["dataset"][:]
        with h5py.File(in_vray_caustics_g_hdf5_file,           "r") as f: vray_caustics_g           = f["dataset"][:]
        with h5py.File(in_vray_caustics_b_hdf5_file,           "r") as f: vray_caustics_b           = f["dataset"][:]
        with h5py.File(in_vray_atmosphere_r_hdf5_file,         "r") as f: vray_atmosphere_r         = f["dataset"][:]
        with h5py.File(in_vray_atmosphere_g_hdf5_file,         "r") as f: vray_atmosphere_g         = f["dataset"][:]
        with h5py.File(in_vray_atmosphere_b_hdf5_file,         "r") as f: vray_atmosphere_b         = f["dataset"][:]
        with h5py.File(in_vray_background_r_hdf5_file,         "r") as f: vray_background_r         = f["dataset"][:]
        with h5py.File(in_vray_background_g_hdf5_file,         "r") as f: vray_background_g         = f["dataset"][:]
        with h5py.File(in_vray_background_b_hdf5_file,         "r") as f: vray_background_b         = f["dataset"][:]

        rgb_color          = dstack([vray_rgb_color_r,          vray_rgb_color_g,          vray_rgb_color_b])
        diffuse_filter     = dstack([vray_diffuse_filter_r,     vray_diffuse_filter_g,     vray_diffuse_filter_b])
        raw_total_lighting = dstack([vray_raw_total_lighting_r, vray_raw_total_lighting_g, vray_raw_total_lighting_b])
        reflection         = dstack([vray_reflection_r,         vray_reflection_g,         vray_reflection_b])
        refraction         = dstack([vray_refraction_r,         vray_refraction_g,         vray_refraction_b])
        specular           = dstack([vray_specular_r,           vray_specular_g,           vray_specular_b])
        sss2               = dstack([vray_sss2_r,               vray_sss2_g,               vray_sss2_b])
        self_illumination  = dstack([vray_self_illumination_r,  vray_self_illumination_g,  vray_self_illumination_b])
        caustics           = dstack([vray_caustics_r,           vray_caustics_g,           vray_caustics_b])
        atmosphere         = dstack([vray_atmosphere_r,         vray_atmosphere_g,         vray_atmosphere_b])
        background         = dstack([vray_background_r,         vray_background_g,         vray_background_b])

        residual = reflection + refraction + specular + sss2 + self_illumination + caustics + atmosphere + background

        total_lighting_ = diffuse_filter*raw_total_lighting
        rgb_color_      = total_lighting_ + residual

        diff = abs(rgb_color - rgb_color_)

        gamma           = 1.0/2.2 # standard gamma correction exponent
        rgb_color_gamma = np.power(np.maximum(rgb_color,0), gamma)

        print("[HYPERSIM: GENERATE_HDF5_FROM_VRIMG] Saving output files for the input file: " + in_file_root + "...")

        with h5py.File(out_color_hdf5_file,                "w") as f: f.create_dataset("dataset", data=rgb_color.astype(float16),          compression="gzip", compression_opts=9)
        with h5py.File(out_diffuse_reflectance_hdf5_file,  "w") as f: f.create_dataset("dataset", data=diffuse_filter.astype(float16),     compression="gzip", compression_opts=9)
        with h5py.File(out_diffuse_illumination_hdf5_file, "w") as f: f.create_dataset("dataset", data=raw_total_lighting.astype(float16), compression="gzip", compression_opts=9)
        with h5py.File(out_residual_hdf5_file,             "w") as f: f.create_dataset("dataset", data=residual.astype(float16),           compression="gzip", compression_opts=9)

        imsave(out_color_jpg_file,                clip(rgb_color,0,1))
        imsave(out_gamma_jpg_file,                clip(rgb_color_gamma,0,1))
        imsave(out_diffuse_reflectance_jpg_file,  clip(diffuse_filter,0,1))
        imsave(out_diffuse_illumination_jpg_file, clip(raw_total_lighting,0,1))
        imsave(out_residual_jpg_file,             clip(residual,0,1))
        imsave(out_lambertian_jpg_file,           clip(total_lighting_,0,1))
        imsave(out_non_lambertian_jpg_file,       clip(rgb_color_,0,1))
        imsave(out_diff_jpg_file,                 clip(diff,0,1))



print("[HYPERSIM: GENERATE_HDF5_FROM_VRIMG] Finished.")
