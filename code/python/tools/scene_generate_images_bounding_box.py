#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import glob
import os
import PIL.ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", required=True)
parser.add_argument("--camera_name", required=True)
parser.add_argument("--bounding_box_type", required=True)
parser.add_argument("--frame_id", type=int)
parser.add_argument("--num_pixels_per_fragment", type=int)
args = parser.parse_args()

assert args.bounding_box_type == "axis_aligned" or args.bounding_box_type == "object_aligned_2d" or args.bounding_box_type == "object_aligned_3d"



print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX] Begin...")



eps = 5.0              # slack value for depth test; a fragment must be closer to the camera by a margin of eps to be rendered
lw = 4                 # line width
back_face_cull = False # cull fragments based on whether they come from a geometric primitive that is facing away from the camera

if args.num_pixels_per_fragment is not None:
    num_pixels_per_fragment = args.num_pixels_per_fragment
else:
    num_pixels_per_fragment = 10 # generate relatively coarse fragments by default

images_dir = os.path.join(args.scene_dir, "images")

camera_keyframe_frame_indices_hdf5_file = os.path.join(args.scene_dir, "_detail", args.camera_name, "camera_keyframe_frame_indices.hdf5")
camera_keyframe_positions_hdf5_file     = os.path.join(args.scene_dir, "_detail", args.camera_name, "camera_keyframe_positions.hdf5")
camera_keyframe_orientations_hdf5_file  = os.path.join(args.scene_dir, "_detail", args.camera_name, "camera_keyframe_orientations.hdf5")

in_scene_fileroot    = "scene"
in_rgb_jpg_dir       = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_final_preview")
in_rgb_jpg_files     = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_final_preview", "frame.*.tonemap.jpg")
in_position_hdf5_dir = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_geometry_hdf5")
out_preview_dir      = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_final_preview")

mesh_objects_sii_hdf5_file                  = os.path.join(args.scene_dir, "_detail", "mesh", "mesh_objects_sii.hdf5")
metadata_semantic_instance_colors_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_colors.hdf5")
metadata_semantic_colors_hdf5_file          = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_colors.hdf5")

if args.bounding_box_type == "axis_aligned":
    metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_axis_aligned_positions.hdf5")
    metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_axis_aligned_orientations.hdf5")
    metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_axis_aligned_extents.hdf5")
if args.bounding_box_type == "object_aligned_2d":
    metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_2d_positions.hdf5")
    metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_2d_orientations.hdf5")
    metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_2d_extents.hdf5")
if args.bounding_box_type == "object_aligned_3d":
    metadata_semantic_instance_bounding_box_positions_hdf5_file    = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_3d_positions.hdf5")
    metadata_semantic_instance_bounding_box_orientations_hdf5_file = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_3d_orientations.hdf5")
    metadata_semantic_instance_bounding_box_extents_hdf5_file      = os.path.join(args.scene_dir, "_detail", "mesh", "metadata_semantic_instance_bounding_box_object_aligned_3d_extents.hdf5")

with h5py.File(camera_keyframe_frame_indices_hdf5_file,                        "r") as f: camera_keyframe_frame_indices = f["dataset"][:]
with h5py.File(camera_keyframe_positions_hdf5_file,                            "r") as f: camera_keyframe_positions     = f["dataset"][:]
with h5py.File(camera_keyframe_orientations_hdf5_file,                         "r") as f: camera_keyframe_orientations  = f["dataset"][:]
with h5py.File(mesh_objects_sii_hdf5_file,                                     "r") as f: mesh_objects_sii              = f["dataset"][:]
with h5py.File(metadata_semantic_instance_colors_hdf5_file,                    "r") as f: semantic_instance_colors      = f["dataset"][:]
with h5py.File(metadata_semantic_instance_bounding_box_positions_hdf5_file,    "r") as f: bounding_box_positions        = f["dataset"][:]
with h5py.File(metadata_semantic_instance_bounding_box_orientations_hdf5_file, "r") as f: bounding_box_orientations     = f["dataset"][:]
with h5py.File(metadata_semantic_instance_bounding_box_extents_hdf5_file,      "r") as f: bounding_box_extents          = f["dataset"][:]

assert all(camera_keyframe_frame_indices == arange(camera_keyframe_frame_indices.shape[0]))

if not os.path.exists(out_preview_dir): os.makedirs(out_preview_dir)



in_filenames = [ os.path.basename(f) for f in sort(glob.glob(in_rgb_jpg_files)) ]

for in_filename in in_filenames:

    in_filename_ids = [int(t) for t in in_filename.split(".") if t.isdigit()]
    assert len(in_filename_ids) == 1
    frame_id = in_filename_ids[0]

    if args.frame_id is not None and frame_id != args.frame_id:
        continue

    in_file_root = in_filename.replace(".tonemap.jpg", "")

    in_rgb_jpg_file       = os.path.join(in_rgb_jpg_dir, in_filename)
    in_position_hdf5_file = os.path.join(in_position_hdf5_dir, in_file_root + ".position.hdf5")
    out_rgb_bb_jpg_file   = os.path.join(out_preview_dir, in_file_root + ".bb_" + args.bounding_box_type + ".jpg")

    try:
        rgb_color = imread(in_rgb_jpg_file)
    except:
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]") 
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX] WARNING: COULD NOT LOAD COLOR IMAGE: " + in_rgb_hdf5_file + "...")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        continue

    try:
        with h5py.File(in_position_hdf5_file, "r") as f: position = f["dataset"][:].astype(float32)
    except:
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]") 
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX] WARNING: COULD NOT LOAD POSITION IMAGE: " + in_position_hdf5_file + "...")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX]")
        continue

    # get image parameters
    height_pixels = rgb_color.shape[0] 
    width_pixels  = rgb_color.shape[1]

    # fov_x and fov_y need to match the _vray_user_params.py that was used to generate the images
    fov_x         = pi/3.0
    fov_y         = 2.0 * arctan(height_pixels * tan(fov_x/2.0) / width_pixels)
    near          = 1.0
    far           = 1000.0

    #
    # construct projection matrix
    #
    # HACK: we should use the per-scene projection matrix defined in contrib/mikeroberts3000
    # because this matrix will be incorrect for some scenes
    #

    f_h    = tan(fov_y/2.0)*near
    f_w    = f_h*width_pixels/height_pixels
    left   = -f_w
    right  = f_w
    bottom = -f_h
    top    = f_h

    M_proj      = matrix(zeros((4,4)))
    M_proj[0,0] = (2.0*near)/(right - left)
    M_proj[1,1] = (2.0*near)/(top - bottom)
    M_proj[0,2] = (right + left)/(right - left)
    M_proj[1,2] = (top + bottom)/(top - bottom)
    M_proj[2,2] = -(far + near)/(far - near)
    M_proj[3,2] = -1.0
    M_proj[2,3] = -(2.0*far*near)/(far - near)

    # get camera parameters
    keyframe_ids = where(camera_keyframe_frame_indices == frame_id)[0]
    assert len(keyframe_ids) == 1

    keyframe_id        = keyframe_ids[0]
    camera_position    = camera_keyframe_positions[keyframe_id]
    camera_orientation = camera_keyframe_orientations[keyframe_id]

    R_world_from_cam = matrix(camera_orientation)
    t_world_from_cam = matrix(camera_position).T
    R_cam_from_world = R_world_from_cam.T
    t_cam_from_world = -R_cam_from_world*t_world_from_cam



    print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX] Generating fragments...")

    num_fragments_per_pixel = 1.0/num_pixels_per_fragment

    fragments_p1_world  = []
    fragments_p2_world  = []
    fragments_p1_cam    = []
    fragments_p2_cam    = []
    fragments_p1_ndc    = []
    fragments_p2_ndc    = []
    fragments_p1_screen = []
    fragments_p2_screen = []
    fragments_color     = []

    for sii in unique(mesh_objects_sii):
        if sii == -1:
            continue

        color_sii = semantic_instance_colors[sii]

        bounding_box_center_world = matrix(bounding_box_positions[sii]).A
        bounding_box_extent_world = matrix(bounding_box_extents[sii]).A

        R_world_from_obj = matrix(bounding_box_orientations[sii])
        t_world_from_obj = matrix(bounding_box_positions[sii]).T

        def transform_point_screen_from_world(p_world):
            p_cam      = t_cam_from_world + R_cam_from_world*p_world
            p_cam_     = matrix(r_[ p_cam.A1, 1 ]).T
            p_clip     = M_proj*p_cam_
            p_ndc      = p_clip/p_clip[3]
            p_ndc_     = p_ndc.A1
            p_screen_x = 0.5*(p_ndc_[0]+1)*(width_pixels-1)
            p_screen_y = (1 - 0.5*(p_ndc_[1]+1))*(height_pixels-1)
            p_screen_z = (p_ndc_[2]+1)/2.0
            p_screen   = matrix([p_screen_x, p_screen_y, p_screen_z]).T
            return p_screen, p_ndc, p_clip, p_cam

        def transform_point_world_from_obj(p_obj):
            p_world = t_world_from_obj + R_world_from_obj*p_obj
            return p_world

        def transform_point_screen_from_obj(p_obj):
            p_world = transform_point_world_from_obj(p_obj)
            p_screen, p_ndc, p_clip, p_cam = transform_point_screen_from_world(p_world)
            return p_screen, p_ndc, p_clip, p_cam, p_world

        def generate_fragment(p1_obj, p2_obj, n_obj, color):
            p1_screen, p1_ndc, p1_clip, p1_cam, p1_world = transform_point_screen_from_obj(p1_obj)
            p2_screen, p2_ndc, p2_clip, p2_cam, p2_world = transform_point_screen_from_obj(p2_obj)
            p1_inside_frustum = all(p1_ndc == clip(p1_ndc,-1,1))
            p2_inside_frustum = all(p2_ndc == clip(p2_ndc,-1,1))

            p_center_world = (p1_world+p2_world)/2.0
            p_camera_world = matrix(camera_position).T
            v_world        = p_camera_world - p_center_world
            n_world        = R_world_from_obj*n_obj
            front_facing   = dot(v_world.A1, n_world.A1) > 0

            if back_face_cull and not front_facing:
                return
            if not (p1_inside_frustum or p2_inside_frustum):
                return

            fragments_p1_world.append(p1_world.A1)
            fragments_p2_world.append(p2_world.A1)
            fragments_p1_cam.append(p1_cam.A1)
            fragments_p2_cam.append(p1_cam.A1)
            fragments_p1_ndc.append(p1_ndc.A1)
            fragments_p2_ndc.append(p2_ndc.A1)
            fragments_p1_screen.append(p1_screen.A1)
            fragments_p2_screen.append(p2_screen.A1)
            fragments_color.append(color)

        def generate_fragments_for_line(p1_obj, p2_obj, n_obj, color):
            p1_screen, p1_ndc, p1_clip, p1_cam, p1_world = transform_point_screen_from_obj(p1_obj)
            p2_screen, p2_ndc, p2_clip, p2_cam, p2_world = transform_point_screen_from_obj(p2_obj)
            p1_inside_frustum = all(p1_ndc == clip(p1_ndc,-1,1))
            p2_inside_frustum = all(p2_ndc == clip(p2_ndc,-1,1))

            # HACK: strictly speaking this frustum culling test is incorrect, because it will discard lines
            # that pass through the frustum but whose endpoints are both outside the frustum; but this is a
            # rare case, and frustum culling in this way is a lot faster, so we do it anyway
            if p1_inside_frustum or p2_inside_frustum:
                num_pixels_per_line = linalg.norm(p2_screen - p1_screen)
                num_fragments_per_line = int(ceil(num_pixels_per_line*num_fragments_per_pixel))
                t = linspace(0,1,num_fragments_per_line+1)
                for ti in range(num_fragments_per_line):
                    t_curr     = t[ti]
                    t_next     = t[ti+1]
                    p_curr_obj = t_curr*p1_obj + (1-t_curr)*p2_obj
                    p_next_obj = t_next*p1_obj + (1-t_next)*p2_obj
                    generate_fragment(p_curr_obj, p_next_obj, n_obj, color)

        bounding_box_corner_000_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,0.0,0.0]).T - 0.5)
        bounding_box_corner_100_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,0.0,0.0]).T - 0.5)
        bounding_box_corner_010_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,1.0,0.0]).T - 0.5)
        bounding_box_corner_110_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,1.0,0.0]).T - 0.5)
        bounding_box_corner_001_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,0.0,1.0]).T - 0.5)
        bounding_box_corner_101_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,0.0,1.0]).T - 0.5)
        bounding_box_corner_011_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([0.0,1.0,1.0]).T - 0.5)
        bounding_box_corner_111_obj = diag(matrix(bounding_box_extent_world).A1)*(matrix([1.0,1.0,1.0]).T - 0.5)

        # x=0
        v_plane_normal_obj = matrix([-1,0,0]).T
        generate_fragments_for_line(bounding_box_corner_000_obj, bounding_box_corner_010_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_010_obj, bounding_box_corner_011_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_011_obj, bounding_box_corner_001_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_001_obj, bounding_box_corner_000_obj, v_plane_normal_obj, color_sii)

        # x=1
        v_plane_normal_obj = matrix([1,0,0]).T
        generate_fragments_for_line(bounding_box_corner_100_obj, bounding_box_corner_110_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_110_obj, bounding_box_corner_111_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_111_obj, bounding_box_corner_101_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_101_obj, bounding_box_corner_100_obj, v_plane_normal_obj, color_sii)

        # y=0
        v_plane_normal_obj = matrix([0,-1,0]).T
        generate_fragments_for_line(bounding_box_corner_000_obj, bounding_box_corner_100_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_100_obj, bounding_box_corner_101_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_101_obj, bounding_box_corner_001_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_001_obj, bounding_box_corner_000_obj, v_plane_normal_obj, color_sii)

        # y=1
        v_plane_normal_obj = matrix([0,1,0]).T
        generate_fragments_for_line(bounding_box_corner_010_obj, bounding_box_corner_110_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_110_obj, bounding_box_corner_111_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_111_obj, bounding_box_corner_011_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_011_obj, bounding_box_corner_010_obj, v_plane_normal_obj, color_sii)

        # z=0
        v_plane_normal_obj = matrix([0,0,-1]).T
        generate_fragments_for_line(bounding_box_corner_000_obj, bounding_box_corner_100_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_100_obj, bounding_box_corner_110_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_110_obj, bounding_box_corner_010_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_010_obj, bounding_box_corner_000_obj, v_plane_normal_obj, color_sii)

        # z=1
        v_plane_normal_obj = matrix([0,0,1]).T
        generate_fragments_for_line(bounding_box_corner_001_obj, bounding_box_corner_101_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_101_obj, bounding_box_corner_111_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_111_obj, bounding_box_corner_011_obj, v_plane_normal_obj, color_sii)
        generate_fragments_for_line(bounding_box_corner_011_obj, bounding_box_corner_001_obj, v_plane_normal_obj, color_sii)

    fragments_p1_world  = array(fragments_p1_world)
    fragments_p2_world  = array(fragments_p2_world)
    fragments_p1_cam    = array(fragments_p1_cam)
    fragments_p2_cam    = array(fragments_p2_cam)
    fragments_p1_ndc    = array(fragments_p1_ndc)
    fragments_p2_ndc    = array(fragments_p2_ndc)
    fragments_p1_screen = array(fragments_p1_screen)
    fragments_p2_screen = array(fragments_p2_screen)
    fragments_color     = array(fragments_color)



    num_fragments = fragments_p1_world.shape[0]

    print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX] Generated " + str(num_fragments) + " fragments...")

    fragments_p_center_world = (fragments_p1_world+fragments_p2_world)/2.0
    fragments_p_center_cam   = (fragments_p1_cam+fragments_p2_cam)/2.0

    # sort fragments in back-to-front order, i.e., by z-axis coordinate in camera space
    fragment_inds_sorted = argsort(fragments_p_center_cam[:,2])

    # discard fragments based on a depth test
    fragment_inds_sorted_depth_test_pass = []
    for fi in fragment_inds_sorted:

        p1_world = matrix(fragments_p1_world[fi]).T
        p2_world = matrix(fragments_p2_world[fi]).T    
        p_center_world = matrix(fragments_p_center_world[fi]).T    
        p_center_screen, p_center_ndc, p_center_clip, p_center_cam = transform_point_screen_from_world(p_center_world)
        p_center_inside_frustum = all(p_center_ndc == clip(p_center_ndc,-1,1))

        if p_center_inside_frustum:
            p_test_world  = p_center_world
            p_test_screen = p_center_screen
        else:
            p1_ndc    = matrix(fragments_p1_ndc[fi]).T
            p2_ndc    = matrix(fragments_p2_ndc[fi]).T
            p1_screen = matrix(fragments_p1_screen[fi]).T
            p2_screen = matrix(fragments_p2_screen[fi]).T
            p1_inside_frustum = all(p1_ndc == clip(p1_ndc,-1,1))
            p2_inside_frustum = all(p2_ndc == clip(p2_ndc,-1,1))
            assert p1_inside_frustum + p2_inside_frustum == 1
            if p1_inside_frustum:
                p_test_world  = p1_world
                p_test_screen = p1_screen
            if p2_inside_frustum:
                p_test_world  = p2_world
                p_test_screen = p2_screen

        p_test_screen_int = p_test_screen.astype(int32)
        p_img_world = position[p_test_screen_int[1], p_test_screen_int[0]]
        if linalg.norm(camera_position - p_test_world.A1) - eps < linalg.norm(camera_position - p_img_world):
            fragment_inds_sorted_depth_test_pass.append(fi)

    fragment_inds_sorted_depth_test_pass = array(fragment_inds_sorted_depth_test_pass)

    fragments_p1_world  = fragments_p1_world[fragment_inds_sorted_depth_test_pass]
    fragments_p2_world  = fragments_p2_world[fragment_inds_sorted_depth_test_pass]
    fragments_p1_cam    = fragments_p1_cam[fragment_inds_sorted_depth_test_pass]
    fragments_p2_cam    = fragments_p2_cam[fragment_inds_sorted_depth_test_pass]
    fragments_p1_ndc    = fragments_p1_ndc[fragment_inds_sorted_depth_test_pass]
    fragments_p2_ndc    = fragments_p2_ndc[fragment_inds_sorted_depth_test_pass]
    fragments_p1_screen = fragments_p1_screen[fragment_inds_sorted_depth_test_pass]
    fragments_p2_screen = fragments_p2_screen[fragment_inds_sorted_depth_test_pass]
    fragments_color     = fragments_color[fragment_inds_sorted_depth_test_pass]

    num_fragments = fragments_p1_world.shape[0]

    print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX] Kept " + str(num_fragments) + " fragments after depth test...")

    img = rgb_color
    img_pil = PIL.Image.fromarray(img)
    draw = PIL.ImageDraw.Draw(img_pil)
    for fi in range(num_fragments):
        p1_screen = matrix(fragments_p1_screen[fi]).T
        p2_screen = matrix(fragments_p2_screen[fi]).T
        color     = fragments_color[fi]
        draw.line([(p1_screen[0],p1_screen[1]), (p2_screen[0],p2_screen[1])], fill=tuple(color), width=lw, joint="none")
    img_ = asarray(img_pil)

    print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP] Saving output file: " + out_rgb_bb_jpg_file)

    imsave(out_rgb_bb_jpg_file, img_)



print("[HYPERSIM: SCENE_GENERATE_IMAGES_BOUNDING_BOX] Finished.")
