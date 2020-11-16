#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import inspect
import ntpath
import os
import pandas as pd
import posixpath
import shutil

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--platform_when_rendering", required=True)
parser.add_argument("--dataset_dir_when_rendering", required=True)
parser.add_argument("--scene_names")
parser.add_argument("--skip_generate_node_metadata_from_vrscene", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)
assert args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix" or args.platform_when_rendering == "windows"

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config

if args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix":
    os_path_module_when_rendering = posixpath
else:
    os_path_module_when_rendering = ntpath



print("[HYPERSIM: DATASET_MODIFY_VRSCENES_FOR_HYPERSIM_RENDERING] Begin...")



in_scene_fileroot                   = "scene"
tmp_scene_fileroot                  = "_tmp_scene"
out_scene_fileroot                  = "scene"
dataset_scenes_dir                  = os.path.join(args.dataset_dir, "scenes")
dataset_scenes_dir_when_rendering   = os_path_module_when_rendering.join(args.dataset_dir_when_rendering, "scenes")
generate_node_metadata_from_vrscene = not args.skip_generate_node_metadata_from_vrscene

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



for s in scenes:

    scene_name                = s["name"]
    scene_dir                 = os.path.abspath(os.path.join(dataset_scenes_dir, scene_name))
    scene_dir_when_rendering  = os_path_module_when_rendering.join(dataset_scenes_dir_when_rendering, scene_name)
    tmp_dir                   = os.path.abspath(os.path.join(scene_dir, "_tmp"))
    detail_dir                = os.path.abspath(os.path.join(scene_dir, "_detail"))
    detail_dir_when_rendering = os_path_module_when_rendering.join(scene_dir_when_rendering, "_detail")
    vrscenes_dir              = os.path.abspath(os.path.join(scene_dir, "vrscenes"))
    images_dir                = os.path.abspath(os.path.join(scene_dir, "images"))
    
    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    #
    # copy input vrscene from vrscenes folder into tmp folder
    #

    in_file  = os.path.abspath(os.path.join(vrscenes_dir, in_scene_fileroot + ".vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    shutil.copy(in_file, out_file)

    #
    # set unique node IDs
    #

    in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    shutil.move(in_file, out_file)

    in_vrscene_file               = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    in_mesh_metadata_objects_file = os.path.abspath(os.path.join(detail_dir, "mesh", "metadata_objects.csv"))
    out_vrscene_file              = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))

    current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cwd = os.getcwd()
    os.chdir(current_source_file_path)

    cmd = \
        _system_config.python_bin + " modify_vrscene_set_unique_render_entity_ids.py" + \
        " --in_vrscene_file "               + in_vrscene_file               + \
        " --in_mesh_metadata_objects_file " + in_mesh_metadata_objects_file + \
        " --out_vrscene_file "              + out_vrscene_file              + \
        " --set_nodes_invisible_if_not_in_mesh" + \
        " --set_lights_invisible"
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    os.chdir(cwd)

    #
    # generate node metadata
    #

    if generate_node_metadata_from_vrscene:

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        shutil.move(in_file, out_file)

        in_vrscene_file                = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        in_mesh_metadata_objects_file  = os.path.abspath(os.path.join(detail_dir, "mesh", "metadata_objects.csv"))
        out_metadata_nodes_file        = os.path.abspath(os.path.join(tmp_dir, "_tmp_metadata_nodes.csv"))
        out_metadata_node_strings_file = os.path.abspath(os.path.join(tmp_dir, "_tmp_metadata_node_strings.csv"))

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " generate_node_metadata_from_vrscene.py" + \
            " --in_vrscene_file "                + in_vrscene_file                + \
            " --in_mesh_metadata_objects_file "  + in_mesh_metadata_objects_file  + \
            " --out_metadata_nodes_file "        + out_metadata_nodes_file        + \
            " --out_metadata_node_strings_file " + out_metadata_node_strings_file
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        shutil.move(in_file, out_file)

        #
        # copy metadata csv files from tmp folder into detail folder
        #

        in_file  = os.path.abspath(os.path.join(tmp_dir, "_tmp_metadata_nodes.csv"))
        out_file = os.path.abspath(os.path.join(detail_dir, "metadata_nodes.csv"))
        shutil.copy(in_file, out_file)

        in_file  = os.path.abspath(os.path.join(tmp_dir, "_tmp_metadata_node_strings.csv"))
        out_file = os.path.abspath(os.path.join(detail_dir, "metadata_node_strings.csv"))
        shutil.copy(in_file, out_file)

    #
    # remove anti-aliasing filters
    #

    in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    shutil.move(in_file, out_file)

    remove_plugins = [ "FilterPoint", "FilterMitNet", "FilterCookVariable", "FilterGaussian", "FilterSinc", "FilterCatmullRom", "FilterLanczos", "FilterTriangle", "FilterBox", "FilterArea" ]

    in_file             = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    out_file            = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    remove_plugins_args = " --remove_plugins " + " ".join(remove_plugins)

    current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cwd = os.getcwd()
    os.chdir(current_source_file_path)

    cmd = \
        _system_config.python_bin + " modify_vrscene_remove_plugins.py" + \
        " --in_file "  + in_file  + \
        " --out_file " + out_file + \
        remove_plugins_args
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    os.chdir(cwd)

    #
    # modify scene for metadata rendering
    #

    in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    shutil.move(in_file, out_file)

    in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))

    current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cwd = os.getcwd()
    os.chdir(current_source_file_path)

    cmd = \
        _system_config.python_bin + " modify_vrscene_for_metadata_rendering.py" + \
        " --in_file "                              + in_file  + \
        " --out_file "                             + out_file + \
        " --generate_images_for_geometry_metadata" + \
        " --generate_images_for_compositing"       + \
        " --generate_images_for_denoising"
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    os.chdir(cwd)

    #
    # for each camera...
    #

    metadata_cameras_csv_file = os.path.abspath(os.path.join(detail_dir, "metadata_cameras.csv"))
    df = pd.read_csv(metadata_cameras_csv_file)

    for c in df.to_records():

        camera_name = c["camera_name"]

        print("[HYPERSIM: DATASET_MODIFY_VRSCENES_FOR_HYPERSIM_RENDERING] Processing scene " + scene_name + ", adding camera " + camera_name + "...")

        #
        # add camera trajectory
        #

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        shutil.move(in_file, out_file)

        in_file               = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        out_file              = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        vray_user_params_dir  = os.path.abspath(args.dataset_dir)
        camera_trajectory_dir = os.path.abspath(os.path.join(detail_dir, camera_name))

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_add_camera.py" + \
            " --in_file "               + in_file              + \
            " --out_file "              + out_file             + \
            " --vray_user_params_dir "  + vray_user_params_dir + \
            " --camera_trajectory_dir " + camera_trajectory_dir
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        #
        # copy tmp vrscene to separate locations to be processed independently for each pass
        #
        
        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_geometry_in.vrscene"))
        shutil.copy(in_file, out_file)

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_in.vrscene"))
        shutil.copy(in_file, out_file)

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_final_in.vrscene"))
        shutil.copy(in_file, out_file)

        #
        # remove extra channels from geometry pass
        #

        remove_plugins = [ "SettingsGI", "RenderChannelColor", "RenderChannelDenoiser" ]

        in_file             = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_geometry_in.vrscene"))
        out_file            = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_geometry_out.vrscene"))
        remove_plugins_args = " --remove_plugins " + " ".join(remove_plugins)

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_remove_plugins.py" + \
            " --in_file "  + in_file  + \
            " --out_file " + out_file + \
            remove_plugins_args
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        #
        # reduce image quality for geometry pass
        #

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_geometry_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_geometry_in.vrscene"))
        shutil.move(in_file, out_file)

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_geometry_in.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_geometry_out.vrscene"))

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_reduce_image_quality.py" + \
            " --in_file "  + in_file  + \
            " --out_file " + out_file
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        #
        # save GI cache files for pre-rendering pass
        #

        in_file                         = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_in.vrscene"))
        out_file                        = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_out.vrscene"))
        light_cache_name                = "_hypersim_light_cache.%04d"
        irradiance_map_name             = "_hypersim_irradiance_map.%04d"
        shared_asset_dir                = os.path.abspath(os.path.join(detail_dir, in_scene_fileroot + "_" + camera_name + "_shared"))
        shared_asset_dir_when_rendering = os_path_module_when_rendering.join(detail_dir_when_rendering, in_scene_fileroot + "_" + camera_name + "_shared").replace("\\", "\\\\")

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_save_gi_cache_files.py" + \
            " --in_file "                         + in_file                         + \
            " --out_file "                        + out_file                        + \
            " --light_cache_name "                + light_cache_name                + \
            " --irradiance_map_name "             + irradiance_map_name             + \
            " --shared_asset_dir "                + shared_asset_dir                + \
            " --platform_when_rendering "         + args.platform_when_rendering    + \
            " --shared_asset_dir_when_rendering " + shared_asset_dir_when_rendering + \
            " --reduce_image_quality"
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        #
        # remove extra channels from pre-rendering pass
        #

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_in.vrscene"))
        shutil.move(in_file, out_file)

        remove_plugins = [ "RenderChannelExtraTex", "RenderChannelRenderID", "RenderChannelNodeID", "RenderChannelColor", "RenderChannelDenoiser" ]

        in_file             = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_in.vrscene"))
        out_file            = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_out.vrscene"))
        remove_plugins_args = " --remove_plugins " + " ".join(remove_plugins)

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_remove_plugins.py" + \
            " --in_file "  + in_file  + \
            " --out_file " + out_file + \
            remove_plugins_args
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        #
        # load GI cache files for final rendering pass
        #

        in_file                         = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_final_in.vrscene"))
        out_file                        = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_final_out.vrscene"))
        light_cache_name                = "_hypersim_light_cache"
        irradiance_map_name             = "_hypersim_irradiance_map"
        shared_asset_dir                = os.path.abspath(os.path.join(detail_dir, in_scene_fileroot + "_" + camera_name + "_shared"))
        shared_asset_dir_when_rendering = os_path_module_when_rendering.join(detail_dir_when_rendering, in_scene_fileroot + "_" + camera_name + "_shared").replace("\\", "\\\\")

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_load_gi_cache_files.py" + \
            " --in_file "                         + in_file                         + \
            " --out_file "                        + out_file                        + \
            " --light_cache_name "                + light_cache_name                + \
            " --irradiance_map_name "             + irradiance_map_name             + \
            " --shared_asset_dir "                + shared_asset_dir                + \
            " --platform_when_rendering "         + args.platform_when_rendering    + \
            " --shared_asset_dir_when_rendering " + shared_asset_dir_when_rendering
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        #
        # remove extra channels from final pass
        #

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_final_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_final_in.vrscene"))
        shutil.move(in_file, out_file)

        remove_plugins = [ "RenderChannelExtraTex", "RenderChannelRenderID", "RenderChannelNodeID" ]

        in_file             = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_final_in.vrscene"))
        out_file            = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_final_out.vrscene"))
        remove_plugins_args = " --remove_plugins " + " ".join(remove_plugins)

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_remove_plugins.py" + \
            " --in_file "  + in_file  + \
            " --out_file " + out_file + \
            remove_plugins_args
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

        #
        # copy vrscenes for all passes from detail folder into vrscenes folder
        #

        in_file  = os.path.abspath(os.path.join(detail_dir, tmp_dir, tmp_scene_fileroot + "_geometry_out.vrscene"))
        out_file = os.path.abspath(os.path.join(vrscenes_dir, out_scene_fileroot + "_" + camera_name + "_geometry.vrscene"))
        shutil.copy(in_file, out_file)

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_pre_out.vrscene"))
        out_file = os.path.abspath(os.path.join(vrscenes_dir, out_scene_fileroot + "_" + camera_name + "_pre.vrscene"))
        shutil.copy(in_file, out_file)

        in_file  = os.path.abspath(os.path.join(detail_dir, tmp_dir, tmp_scene_fileroot + "_final_out.vrscene"))
        out_file = os.path.abspath(os.path.join(vrscenes_dir, out_scene_fileroot + "_" + camera_name + "_final.vrscene"))
        shutil.copy(in_file, out_file)

        #
        # create image folders for all passes
        #

        out_dir = os.path.abspath(os.path.join(images_dir, out_scene_fileroot + "_" + camera_name + "_geometry"))
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        out_dir = os.path.abspath(os.path.join(images_dir, out_scene_fileroot + "_" + camera_name + "_geometry_hdf5"))
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        out_dir = os.path.abspath(os.path.join(images_dir, out_scene_fileroot + "_" + camera_name + "_geometry_preview"))
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        out_dir = os.path.abspath(os.path.join(images_dir, out_scene_fileroot + "_" + camera_name + "_pre"))
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        out_dir = os.path.abspath(os.path.join(images_dir, out_scene_fileroot + "_" + camera_name + "_final"))
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        out_dir = os.path.abspath(os.path.join(images_dir, out_scene_fileroot + "_" + camera_name + "_final_hdf5"))
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        out_dir = os.path.abspath(os.path.join(images_dir, out_scene_fileroot + "_" + camera_name + "_final_preview"))
        if not os.path.exists(out_dir): os.makedirs(out_dir)



print("[HYPERSIM: DATASET_MODIFY_VRSCENES_FOR_HYPERSIM_RENDERING] Finished.")
