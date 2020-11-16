#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import inspect
import ntpath
import os
import pandas as pd
import posixpath
import time
import vray

import path_utils

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_file", required=True)
parser.add_argument("--vray_user_params_dir")
parser.add_argument("--camera_trajectory_dir")
parser.add_argument("--camera_lens_distortion_file")
parser.add_argument("--shared_asset_dir")
parser.add_argument("--platform_when_rendering")
parser.add_argument("--shared_asset_dir_when_rendering")
args = parser.parse_args()

use_vray_user_params_dir        = args.vray_user_params_dir is not None
use_camera_trajectory_dir       = args.camera_trajectory_dir is not None
use_camera_lens_distortion_file = args.camera_lens_distortion_file is not None

assert os.path.exists(args.in_file)

if use_vray_user_params_dir:
    assert os.path.exists(args.vray_user_params_dir)

if use_camera_trajectory_dir:
    assert os.path.exists(args.camera_trajectory_dir)

if use_camera_lens_distortion_file:
    assert args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix" or args.platform_when_rendering == "windows"
    assert args.shared_asset_dir_when_rendering is not None

if use_camera_lens_distortion_file:
    if args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix":
        os_path_module_when_rendering = posixpath
    else:
        os_path_module_when_rendering = ntpath



print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Begin...")



in_file = args.in_file

if use_camera_trajectory_dir:
    camera_keyframe_frame_indices_hdf5_file = os.path.join(args.camera_trajectory_dir, "camera_keyframe_frame_indices.hdf5")
    camera_keyframe_positions_hdf5_file     = os.path.join(args.camera_trajectory_dir, "camera_keyframe_positions.hdf5")
    camera_keyframe_orientations_hdf5_file  = os.path.join(args.camera_trajectory_dir, "camera_keyframe_orientations.hdf5")
    metadata_camera_csv_file                = os.path.join(args.camera_trajectory_dir, "metadata_camera.csv")

if use_camera_lens_distortion_file:
    camera_lens_distortion_exr_file                = os.path.join(args.shared_asset_dir, "_hypersim_camera_lens_distortion.exr")
    camera_lens_distortion_exr_file_when_rendering = os_path_module_when_rendering.join(args.shared_asset_dir_when_rendering, "_hypersim_camera_lens_distortion.exr")

output_dir = os.path.dirname(args.out_file)
if output_dir == "":
    output_dir = "."

if not os.path.exists(output_dir): os.makedirs(output_dir)

if use_camera_lens_distortion_file:
    if not os.path.exists(args.shared_asset_dir): os.makedirs(args.shared_asset_dir)



if use_camera_trajectory_dir:

    with h5py.File(camera_keyframe_frame_indices_hdf5_file, "r") as f: camera_keyframe_frame_indices = f["dataset"][:]
    with h5py.File(camera_keyframe_positions_hdf5_file,     "r") as f: camera_keyframe_positions     = f["dataset"][:]
    with h5py.File(camera_keyframe_orientations_hdf5_file,  "r") as f: camera_keyframe_orientations  = f["dataset"][:]

    df_camera = pd.read_csv(metadata_camera_csv_file, index_col="parameter_name")
    camera_frame_time_seconds = df_camera.loc["frame_time_seconds"][0]

    assert all(camera_keyframe_frame_indices == camera_keyframe_frame_indices.astype(int64))
    assert all(camera_keyframe_frame_indices == sort(camera_keyframe_frame_indices))
    assert all(camera_keyframe_frame_indices[0] == 0)

if use_camera_lens_distortion_file:
    
    with h5py.File(args.camera_lens_distortion_file, "r") as f: rays = f["dataset"][:]



renderer = vray.VRayRenderer()
def log_msg(renderer, message, level, instant):
    print(str(instant) + " " + str(level) + " " + message)
renderer.setOnLogMessage(log_msg)
renderer.load(args.in_file)
time.sleep(0.5)



if use_vray_user_params_dir:

    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Using user-specied rendering parameters...")

    path_utils.add_path_to_sys_path(args.vray_user_params_dir, mode="relative_to_cwd", frame=inspect.currentframe())
    import _vray_user_params

    camera_params = _vray_user_params._set_vray_user_params(renderer)



if use_camera_trajectory_dir:

    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Using user-specified camera trajectory...")

    settings_output = renderer.classes.SettingsOutput.getInstanceOrCreate()
    settings_output.img_file_needFrameNumber = 1 # force VRay to append the frame number to all output files
    settings_output.anim_start               = 0
    settings_output.anim_end                 = camera_keyframe_frame_indices[-1]*camera_frame_time_seconds
    settings_output.frame_start              = 0
    settings_output.frames_per_second        = 1.0 / camera_frame_time_seconds
    settings_output.frames                   = vray.List(range(camera_keyframe_frame_indices[-1] + 1)) # create a list from 0 to the last value in camera_keyframe_frame_indices (inclusive)

    settings_camera = renderer.classes.SettingsCamera.getInstanceOrCreate()
    render_view     = renderer.classes.RenderView.getInstanceOrCreate()
    render_view.fov = settings_camera.fov

    renderer.useAnimatedValues = True
    
    num_keyframes = camera_keyframe_frame_indices.shape[0]
    for fi in range(num_keyframes):

        f                = camera_keyframe_frame_indices[fi]
        camera_position  = camera_keyframe_positions[fi]
        R_world_from_cam = camera_keyframe_orientations[fi]

        vray_view_x = R_world_from_cam[:,0]
        vray_view_y = R_world_from_cam[:,1]
        vray_view_z = R_world_from_cam[:,2]

        renderer.frame = int(f)
        render_view.transform = \
            vray.Transform(vray.Matrix(vray.Vector(vray_view_x[0],vray_view_x[1],vray_view_x[2]),
                                       vray.Vector(vray_view_y[0],vray_view_y[1],vray_view_y[2]),
                                       vray.Vector(vray_view_z[0],vray_view_z[1],vray_view_z[2])),
                           vray.Vector(camera_position[0],camera_position[1],camera_position[2]))

    renderer.useAnimatedValues = False



if use_camera_lens_distortion_file:

    import cv2

    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Using user-specified lens distortion...")

    if not os.path.exists(args.shared_asset_dir): os.makedirs(args.shared_asset_dir)

    settings_output = renderer.classes.SettingsOutput.getInstanceOrCreate()
    camera_physical = renderer.classes.CameraPhysical.getInstanceOrCreate()

    width_pixels  = settings_output.img_width
    height_pixels = settings_output.img_height

    width_texels  = rays.shape[1]
    height_texels = rays.shape[0]

    assert rays.shape[2] == 3
    assert all(rays[:,:,2] < 0.0)

    uv_min = -1.0
    uv_max = 1.0

    # compute fov_x, fov_y implied by the rays projected onto the XZ plane
    rays_xz = rays[:,:,[0,2]]

    rays_xz_norm = rays_xz / linalg.norm(rays_xz, axis=2)[:,:,newaxis]

    rays_xz_norm_x = rays_xz_norm[:,:,0]
    rays_xz_norm_z = rays_xz_norm[:,:,1]

    rays_xz_norm_argmin_x = unravel_index(argmin(rays_xz_norm_x), rays_xz_norm_x.shape)
    rays_xz_norm_argmax_x = unravel_index(argmax(rays_xz_norm_x), rays_xz_norm_x.shape)

    rays_xz_norm_min_x_x = rays_xz_norm_x[rays_xz_norm_argmin_x]
    rays_xz_norm_max_x_x = rays_xz_norm_x[rays_xz_norm_argmax_x]

    if abs(rays_xz_norm_min_x_x) > abs(rays_xz_norm_max_x_x):
        rays_xz_norm_argmaxabs_x = rays_xz_norm_argmin_x
    else:
        rays_xz_norm_argmaxabs_x = rays_xz_norm_argmax_x

    rays_xz_norm_maxabs_x_absx = abs(rays_xz_norm_x[rays_xz_norm_argmaxabs_x])
    rays_xz_norm_maxabs_x_absz = abs(rays_xz_norm_z[rays_xz_norm_argmaxabs_x])

    fov_x_xz = 2.0*arctan(rays_xz_norm_maxabs_x_absx / (rays_xz_norm_maxabs_x_absz * uv_max))
    fov_y_xz = 2.0*arctan((height_texels-1) * tan(fov_x_xz/2.0) / (width_texels-1))

    # compute fov_x, fov_y implied by the rays projected onto the YZ plane
    rays_yz = rays[:,:,[1,2]]

    rays_yz_norm = rays_yz / linalg.norm(rays_yz, axis=2)[:,:,newaxis]

    rays_yz_norm_y = rays_yz_norm[:,:,0]
    rays_yz_norm_z = rays_yz_norm[:,:,1]

    rays_yz_norm_argmin_y = unravel_index(argmin(rays_yz_norm_y), rays_yz_norm_y.shape)
    rays_yz_norm_argmax_y = unravel_index(argmax(rays_yz_norm_y), rays_yz_norm_y.shape)

    rays_yz_norm_min_y_y = rays_yz_norm_y[rays_yz_norm_argmin_y]
    rays_yz_norm_max_y_y = rays_yz_norm_y[rays_yz_norm_argmax_y]

    if abs(rays_yz_norm_min_y_y) > abs(rays_yz_norm_max_y_y):
        rays_yz_norm_argmaxabs_y = rays_yz_norm_argmin_y
    else:
        rays_yz_norm_argmaxabs_y = rays_yz_norm_argmax_y

    rays_yz_norm_maxabs_y_absy = abs(rays_yz_norm_y[rays_yz_norm_argmaxabs_y])
    rays_yz_norm_maxabs_y_absz = abs(rays_yz_norm_z[rays_yz_norm_argmaxabs_y])

    fov_y_yz = 2.0*arctan(rays_yz_norm_maxabs_y_absy / (rays_yz_norm_maxabs_y_absz * uv_max))
    fov_x_yz = 2.0*arctan((width_texels-1) * tan(fov_y_yz/2.0) / (height_texels-1))

    # set fov_x, fov_y based on the larger of the two estimates
    if fov_x_xz > fov_x_yz:
        assert fov_y_xz > fov_y_yz
        fov_x = fov_x_xz
        fov_y = fov_y_xz
    else:
        fov_x = fov_x_yz
        fov_y = fov_y_yz

    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Exact fov_x = " + str(fov_x))
    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Exact fov_y = " + str(fov_y))

    fov_y_implied_by_pixel_grid = 2.0*arctan(height_pixels * tan(fov_x/2.0) / width_pixels)
    print(fov_y_implied_by_pixel_grid)
    assert isclose(fov_y, fov_y_implied_by_pixel_grid)

    # Hack to work around the rounding error when writing to vrscene files.
    # Mathematically speaking, there is no harm in setting fov to be slightly
    # larger than neccesary, and then computing a uv value for each ray that
    # accounts for the slightly-too-large fov value stored in the vscene file.
    # So, we add a small value to the correct fov, perform the rounding ourselves,
    # and then compute uv values accordingly. This hack enables us to obtain more
    # accurate raycasting results, since our uv values exactly match the fov stored
    # in the vrscene file.
    eps    = 0.1 * pi / 180.0
    fov_x_ = round(fov_x+eps,7)
    fov_y_ = 2.0*arctan((height_texels-1) * tan(fov_x_/2.0) / (width_texels-1))

    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Inexact fov_x = " + str(fov_x_))
    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Inexact fov_y = " + str(fov_y_))

    # compute uv values from rays
    u = rays[:,:,0] / (-rays[:,:,2]*tan(fov_x_/2.0))
    v = rays[:,:,1] / (-rays[:,:,2]*tan(fov_y_/2.0))

    assert all(abs(u) <= uv_max)
    assert all(abs(v) <= uv_max)

    # scale and translate so u,v are in the range [0,1] and save to image
    u_01 = (u / 2.0) + 0.5
    v_01 = (v / 2.0) + 0.5
    w_01 = zeros_like(u_01)

    exr_img = dstack((w_01[:,:,newaxis], v_01[:,:,newaxis], u_01[:,:,newaxis])).astype(float32)

    print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Saving " + camera_lens_distortion_exr_file + "...")

    cv2.imwrite(camera_lens_distortion_exr_file, exr_img)

    # check that OpenCV can successfully read and write EXR files
    exr_img_ = cv2.imread(camera_lens_distortion_exr_file, cv2.IMREAD_UNCHANGED)
    assert allclose(exr_img, exr_img_)

    # UVWGenChannel
    a_u = (width_texels - 1.0)  / width_texels
    a_v = (height_texels - 1.0) / height_texels
    b_u = 1.0 / (2.0*width_texels)
    b_v = 1.0 / (2.0*height_texels)

    uvw_gen_channel = renderer.classes.UVWGenChannel("HYPERSIM_UVW_GEN_CHANNEL_CAMERA_LENS_DISTORTION")
    uvw_gen_channel.uvw_transform = \
        vray.Transform(vray.Matrix(vray.Vector(a_u, 0,   0),
                                   vray.Vector(0,   a_v, 0),
                                   vray.Vector(0,   0,   1)),
                       vray.Vector(b_u, b_v, 0))

    uvw_gen_channel.wrap_u      = 1
    uvw_gen_channel.wrap_v      = 1
    uvw_gen_channel.crop_u      = 0
    uvw_gen_channel.crop_v      = 0
    uvw_gen_channel.wrap_mode   = 1
    uvw_gen_channel.duvw_scale  = 1
    uvw_gen_channel.uvw_channel = 1

    # BitmapBuffer
    bitmap_buffer = renderer.classes.BitmapBuffer("HYPERSIM_BITMAP_BUFFER_CAMERA_LENS_DISTORTION")
    bitmap_buffer.filter_type     = 0
    bitmap_buffer.filter_blur     = 1
    bitmap_buffer.color_space     = 0
    bitmap_buffer.gamma           = 1
    bitmap_buffer.maya_compatible = 0
    bitmap_buffer.interpolation   = 0

    bitmap_buffer.file = camera_lens_distortion_exr_file_when_rendering

    bitmap_buffer.load_file         = 1
    bitmap_buffer.ifl_start_frame   = 0
    bitmap_buffer.ifl_playback_rate = 1
    bitmap_buffer.ifl_end_condition = 0

    # TexBitmap
    tex_bitmap = renderer.classes.TexBitmap("HYPERSIM_TEX_BITMAP_CAMERA_LENS_DISTORTION")
    tex_bitmap.alpha_from_intensity = 0
    tex_bitmap.nouvw_color          = vray.AColor(0, 0, 0, 0)
    tex_bitmap.tile                 = 0
    tex_bitmap.uvwgen               = uvw_gen_channel
    tex_bitmap.placement_type       = 0
    tex_bitmap.u                    = 0
    tex_bitmap.v                    = 0
    tex_bitmap.w                    = 1
    tex_bitmap.h                    = 1
    tex_bitmap.bitmap               = bitmap_buffer

    # set camera to use lens distortion
    # camera_physical.distortion      = np.nan   # distortion amount (not used)
    camera_physical.distortion_type = 3        # distortion type == texture
    camera_physical.lens_file       = ""       # vrlens file
    camera_physical.distortion_tex  = tex_bitmap # distortion texture

    # set camera fov to be consistent with the fov implied by the user rays
    camera_physical.fov = fov_x_



renderer.export(args.out_file)
print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: MODIFY_VRSCENE_ADD_CAMERA] Finished.")
