#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import pandas as pd

import path_utils

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
parser.add_argument("--split_mode", required=True)
parser.add_argument("--train_fraction", type=float)
parser.add_argument("--val_fraction", type=float)
args = parser.parse_args()

assert os.path.exists(args.analysis_dir)
assert args.split_mode == "scene_v1"



print("[HYPERSIM: DATASET_GENERATE_SPLIT] Begin...")



metadata_images_csv_file = os.path.join(args.analysis_dir, "metadata_images.csv")
df_images = pd.read_csv(metadata_images_csv_file)



if args.split_mode == "scene_v1":

    assert args.train_fraction is not None
    assert args.val_fraction is not None    
    assert args.train_fraction + args.val_fraction < 1.0

    metadata_images_split_file = os.path.join(args.analysis_dir, "metadata_images_split_scene_v1.csv")

    df_images_public = df_images[df_images["included_in_public_release"] == True]
    scene_names_shuffled = df_images_public.scene_name.unique()
    np.random.seed(0)
    np.random.shuffle(scene_names_shuffled)
    num_scenes = len(scene_names_shuffled)

    scene_ind_train_begin = 0
    scene_ind_val_begin   = int(args.train_fraction*num_scenes)
    scene_ind_test_begin  = int((args.train_fraction + args.val_fraction)*num_scenes)

    scene_ind_train_end = scene_ind_val_begin - 1
    scene_ind_val_end   = scene_ind_test_begin - 1
    scene_ind_test_end  = num_scenes - 1

    num_scenes_train = scene_ind_train_end - scene_ind_train_begin + 1
    num_scenes_val   = scene_ind_val_end - scene_ind_val_begin + 1
    num_scenes_test  = scene_ind_test_end - scene_ind_test_begin + 1

    scene_names_train = scene_names_shuffled[scene_ind_train_begin:scene_ind_train_end+1]
    scene_names_val   = scene_names_shuffled[scene_ind_val_begin:scene_ind_val_end+1]
    scene_names_test  = scene_names_shuffled[scene_ind_test_begin:scene_ind_test_end+1]

    assert num_scenes == num_scenes_train + num_scenes_val + num_scenes_test

    print("[HYPERSIM: DATASET_GENERATE_SPLIT] train:")
    print(sort(scene_names_train))
    print("[HYPERSIM: DATASET_GENERATE_SPLIT] val:")
    print(sort(scene_names_val))
    print("[HYPERSIM: DATASET_GENERATE_SPLIT] test:")
    print(sort(scene_names_test))

    df_images.loc[ df_images["included_in_public_release"] & df_images["scene_name"].isin(scene_names_train), "split_partition_name" ] = "train"
    df_images.loc[ df_images["included_in_public_release"] & df_images["scene_name"].isin(scene_names_val),   "split_partition_name" ] = "val"
    df_images.loc[ df_images["included_in_public_release"] & df_images["scene_name"].isin(scene_names_test),  "split_partition_name" ] = "test"

    df_images.to_csv(metadata_images_split_file, index=False)



print("[HYPERSIM: DATASET_GENERATE_SPLIT] Finished.")
