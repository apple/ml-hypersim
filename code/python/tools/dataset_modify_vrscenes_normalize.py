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
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)
assert args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix" or args.platform_when_rendering == "windows"

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config

if args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix":
    os_path_module_when_rendering = posixpath
else:
    os_path_module_when_rendering = ntpath



print("[HYPERSIM: DATASET_MODIFY_VRSCENES_NORMALIZE] Begin...")



in_scene_fileroot                                = "scene"
tmp_scene_fileroot                               = "_tmp_scene"
out_scene_fileroot                               = "scene"
dataset_scenes_dir                               = os.path.join(args.dataset_dir, "scenes")
dataset_scenes_dir_when_rendering                = os_path_module_when_rendering.join(args.dataset_dir_when_rendering, "scenes")
asset_sceneassets_photometric_dir_when_rendering = os_path_module_when_rendering.join(args.dataset_dir_when_rendering, "_asset", "sceneassets", "photometric")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



for s in scenes:

    scene_name                = s["name"]
    scene_dir                 = os.path.abspath(os.path.join(dataset_scenes_dir, scene_name))
    scene_dir_when_rendering  = os_path_module_when_rendering.join(dataset_scenes_dir_when_rendering, scene_name)
    tmp_dir                   = os.path.abspath(os.path.join(scene_dir, "_tmp"))
    asset_export_dir          = os.path.abspath(os.path.join(scene_dir, "_asset_export"))
    detail_dir                = os.path.abspath(os.path.join(scene_dir, "_detail"))
    detail_dir_when_rendering = os_path_module_when_rendering.join(scene_dir_when_rendering, "_detail")
    vrscenes_dir              = os.path.abspath(os.path.join(scene_dir, "vrscenes"))
    images_scene_dir          = os.path.abspath(os.path.join(scene_dir, "images", "scene"))
    
    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)
    if not os.path.exists(vrscenes_dir): os.makedirs(vrscenes_dir)
    if not os.path.exists(images_scene_dir): os.makedirs(images_scene_dir)

    #
    # generate camera trajectories from asset export
    #

    current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cwd = os.getcwd()
    os.chdir(current_source_file_path)

    cmd = \
        _system_config.python_bin + " scene_generate_camera_trajectories_asset_export.py" + \
        " --scene_dir " + scene_dir
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    os.chdir(cwd)
    
    #
    # generate scene metadata
    #

    in_file  = os.path.abspath(os.path.join(asset_export_dir, in_scene_fileroot + ".vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, "_tmp_metadata_scene.csv"))

    current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cwd = os.getcwd()
    os.chdir(current_source_file_path)

    cmd = \
        _system_config.python_bin + " generate_scene_metadata_from_vrscene.py" + \
        " --in_file "  + in_file + \
        " --out_file " + out_file
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    os.chdir(cwd)

    #
    # copy metadata csv from tmp folder into detail folder
    #

    in_file  = os.path.abspath(os.path.join(tmp_dir, "_tmp_metadata_scene.csv"))
    out_file = os.path.abspath(os.path.join(detail_dir, "metadata_scene.csv"))
    shutil.copy(in_file, out_file)

    #
    # copy input vrscene from asset export folder into tmp folder
    #

    in_file  = os.path.abspath(os.path.join(asset_export_dir, in_scene_fileroot + ".vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    shutil.copy(in_file, out_file)

    #
    # replace hard-coded paths with portable paths
    #

    for asset_sceneassets_photometric_replace_dir in _system_config.asset_sceneassets_photometric_replace_dirs:

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        shutil.move(in_file, out_file)

        in_file          = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        out_file         = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        replace_old_path = '"' + asset_sceneassets_photometric_replace_dir + '"'
        replace_new_path = asset_sceneassets_photometric_dir_when_rendering.replace("\\", "\\\\")

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " modify_vrscene_replace_paths.py" + \
            " --in_file "          + in_file          + \
            " --out_file "         + out_file         + \
            " --replace_old_path " + replace_old_path + \
            " --replace_new_path " + replace_new_path
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

    #
    # save GI cache files
    #

    in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    shutil.move(in_file, out_file)

    in_file                         = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    out_file                        = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    light_cache_name                = "_hypersim_light_cache"
    irradiance_map_name             = "_hypersim_irradiance_map"
    shared_asset_dir                = os.path.abspath(os.path.join(detail_dir, in_scene_fileroot + "_shared"))
    shared_asset_dir_when_rendering = os_path_module_when_rendering.join(detail_dir_when_rendering, in_scene_fileroot + "_shared").replace("\\", "\\\\")

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
        " --shared_asset_dir_when_rendering " + shared_asset_dir_when_rendering
    print("")
    print(cmd)
    print("")
    retval = os.system(cmd)
    assert retval == 0

    os.chdir(cwd)

    #
    # execute scene-specific normalization script
    #

    assert s["normalization_policy"] in ["none", "v0", "v1", "v2"]

    in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
    shutil.move(in_file, out_file)

    if s["normalization_policy"] == "none":

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
        shutil.move(in_file, out_file)

    else:

        in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_in.vrscene"))
        out_file = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        modify_vrscene_normalize_scene_file = os.path.join(current_source_file_path, "modify_vrscene_normalize_scene_" + s["normalization_policy"] + ".py")

        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " " + modify_vrscene_normalize_scene_file + \
            " --in_file "  + in_file + \
            " --out_file " + out_file
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)

    #
    # copy output vrscene from tmp folder into vrscenes folder
    #

    in_file  = os.path.abspath(os.path.join(tmp_dir, tmp_scene_fileroot + "_out.vrscene"))
    out_file = os.path.abspath(os.path.join(vrscenes_dir, out_scene_fileroot + ".vrscene"))
    shutil.copy(in_file, out_file)



print("[HYPERSIM: DATASET_MODIFY_VRSCENES_NORMALIZE] Finished.")
