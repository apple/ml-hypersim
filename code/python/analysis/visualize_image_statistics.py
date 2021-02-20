#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import glob
import h5py
import inspect
import mayavi.mlab
import os

import path_utils
path_utils.add_path_to_sys_path("../lib", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import mayavi_utils

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
parser.add_argument("--batch_names", required=True)
args = parser.parse_args()



print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Begin...")



#
# NOTE: all parameters below must match dataset_generate_image_statistics.py
#

# UNIQUE OBJECTS PER CLASS
# PIXELS PER CLASS
semantic_id_to_name_map = {
    1  : "wall",
    2  : "floor",
    3  : "cabinet",
    4  : "bed",
    5  : "chair",
    6  : "sofa",
    7  : "table",
    8  : "door",
    9  : "window",
    10 : "bookshelf",
    11 : "picture",
    12 : "counter",
    13 : "blinds",
    14 : "desk",
    15 : "shelves",
    16 : "curtain",
    17 : "dresser",
    18 : "pillow",
    19 : "mirror",
    20 : "floormat",
    21 : "clothes",
    22 : "ceiling",
    23 : "books",
    24 : "refrigerator",
    25 : "television",
    26 : "paper",
    27 : "towel",
    28 : "showercurtain",
    29 : "box",
    30 : "whiteboard",
    31 : "person",
    32 : "nightstand",
    33 : "toilet",
    34 : "sink",
    35 : "lamp",
    36 : "bathtub",
    37 : "bag",
    38 : "otherstructure",
    39 : "otherfurniture",
    40 : "otherprop" }

# UNIQUE OBJECTS PER IMAGE
unique_objects_per_image_hist_n_bins    = 10000
unique_objects_per_image_hist_bin_edges = arange(unique_objects_per_image_hist_n_bins+1)

# UNIQUE CLASSES PER IMAGE
unique_classes_per_image_hist_n_bins    = len(semantic_id_to_name_map) + 1 # +1 because we want to make room for the value 0
unique_classes_per_image_hist_bin_edges = arange(unique_classes_per_image_hist_n_bins+1)

# DEPTH (LINEAR)
depth_hist_linear_n_bins    = 1000
depth_hist_linear_min       = 0.0
depth_hist_linear_max       = 20.0
depth_hist_linear_bin_edges = linspace(depth_hist_linear_min, depth_hist_linear_max, depth_hist_linear_n_bins+1)

# DEPTH (LOG)
depth_hist_log_n_bins    = 1000
depth_hist_log_base      = 10.0
depth_hist_log_min       = -2.0 # 0.01
depth_hist_log_max       = 3.0  # 1000.0
depth_hist_log_bin_edges = logspace(depth_hist_log_min, depth_hist_log_max, depth_hist_log_n_bins+1, base=depth_hist_log_base)

# NORMAL
normal_hist_n_bins    = 100
normal_hist_min       = -1.0
normal_hist_max       = 1.0
normal_hist_bin_edges = linspace(normal_hist_min, normal_hist_max, normal_hist_n_bins+1)

# RGB COLOR
# DIFFUSE ILLUMINATION
# NON-DIFFUSE RESIDUAL
color_hist_denorm_n_bins    = 20
color_hist_denorm_min       = 0.0
color_hist_denorm_max       = 2.0
color_hist_denorm_bin_edges = linspace(color_hist_denorm_min, color_hist_denorm_max, color_hist_denorm_n_bins+1)

# DIFFUSE REFLECTANCE
color_hist_norm_n_bins    = 10
color_hist_norm_min       = 0.0
color_hist_norm_max       = 1.0
color_hist_norm_bin_edges = linspace(color_hist_norm_min, color_hist_norm_max, color_hist_norm_n_bins+1)

# RGB COLOR
# DIFFUSE ILLUMINATION
# NON-DIFFUSE RESIDUAL
# DIFFUSE REFLECTANCE
hue_saturation_hist_n_bins    = 100
hue_saturation_hist_min       = -1
hue_saturation_hist_max       = 1
hue_saturation_hist_bin_edges = linspace(hue_saturation_hist_min, hue_saturation_hist_max, hue_saturation_hist_n_bins+1)

brightness_hist_linear_n_bins    = 1000
brightness_hist_linear_min       = 0.0
brightness_hist_linear_max       = 10.0
brightness_hist_linear_bin_edges = linspace(brightness_hist_linear_min, brightness_hist_linear_max, brightness_hist_linear_n_bins+1)

brightness_hist_log_n_bins    = 1000
brightness_hist_log_base      = 10.0
brightness_hist_log_min       = -3.0 # 0.001
brightness_hist_log_max       = 1.0  # 10.0
brightness_hist_log_bin_edges = logspace(brightness_hist_log_min, brightness_hist_log_max, brightness_hist_log_n_bins+1, base=brightness_hist_log_base)

# OBJECT VOLUME (LINEAR)
object_volume_hist_linear_n_bins    = 1000
object_volume_hist_linear_min       = 0.0
object_volume_hist_linear_max       = 1000.0
object_volume_hist_linear_bin_edges = linspace(object_volume_hist_linear_min, object_volume_hist_linear_max, object_volume_hist_linear_n_bins+1)

# OBJECT VOLUME (LOG)
object_volume_hist_log_n_bins    = 1000
object_volume_hist_log_base      = 10.0
object_volume_hist_log_min       = -6.0 # 0.000001
object_volume_hist_log_max       = 3.0  # 1000.0
object_volume_hist_log_bin_edges = logspace(object_volume_hist_log_min, object_volume_hist_log_max, object_volume_hist_log_n_bins+1, base=object_volume_hist_log_base)



#
# derived parameters used for visualization
#

# NORMAL
normal_hist_bin_centers_x_1d = normal_hist_bin_edges[:-1] + diff(normal_hist_bin_edges)/2.0
normal_hist_bin_centers_y_1d = normal_hist_bin_edges[:-1] + diff(normal_hist_bin_edges)/2.0

normal_hist_bin_centers_Y, normal_hist_bin_centers_X = meshgrid(normal_hist_bin_centers_x_1d, normal_hist_bin_centers_y_1d, indexing="ij")

normal_hist_bin_corners_Y_00, normal_hist_bin_corners_X_00 = meshgrid(normal_hist_bin_edges[:-1], normal_hist_bin_edges[:-1], indexing="ij")
normal_hist_bin_corners_Y_01, normal_hist_bin_corners_X_01 = meshgrid(normal_hist_bin_edges[:-1], normal_hist_bin_edges[1:], indexing="ij")
normal_hist_bin_corners_Y_10, normal_hist_bin_corners_X_10 = meshgrid(normal_hist_bin_edges[1:],  normal_hist_bin_edges[:-1], indexing="ij")
normal_hist_bin_corners_Y_11, normal_hist_bin_corners_X_11 = meshgrid(normal_hist_bin_edges[1:],  normal_hist_bin_edges[1:], indexing="ij")

normal_hist_bin_corners_X         = dstack((normal_hist_bin_corners_X_00, normal_hist_bin_corners_X_01, normal_hist_bin_corners_X_10, normal_hist_bin_corners_X_11))
normal_hist_bin_corners_Y         = dstack((normal_hist_bin_corners_Y_00, normal_hist_bin_corners_Y_01, normal_hist_bin_corners_Y_10, normal_hist_bin_corners_Y_11))
normal_hist_bin_corners_X_abs_min = np.min(np.abs(normal_hist_bin_corners_X), axis=2)
normal_hist_bin_corners_Y_abs_min = np.min(np.abs(normal_hist_bin_corners_Y), axis=2)

normal_X                                     = normal_hist_bin_corners_X_abs_min
normal_Y                                     = normal_hist_bin_corners_Y_abs_min
normal_X_sqr                                 = normal_X*normal_X
normal_Y_sqr                                 = normal_Y*normal_Y
normal_valid_mask                            = 1 - normal_X_sqr - normal_Y_sqr >= 0
normal_invalid_mask                          = logical_not(normal_valid_mask)
normal_Z                                     = zeros_like(normal_X)
normal_Z[normal_valid_mask]                  = np.sqrt(1 - normal_X_sqr[normal_valid_mask] - normal_Y_sqr[normal_valid_mask])
normal_Z[normal_invalid_mask]                = nan
normal_hist_bin_corners_abs_min_valid_mask   = normal_valid_mask
normal_hist_bin_corners_abs_min_invalid_mask = normal_invalid_mask

normal_X                                     = normal_hist_bin_centers_X
normal_Y                                     = normal_hist_bin_centers_Y
normal_X_sqr                                 = normal_X*normal_X
normal_Y_sqr                                 = normal_Y*normal_Y
normal_valid_mask                            = 1 - normal_X_sqr - normal_Y_sqr >= 0
normal_invalid_mask                          = logical_not(normal_valid_mask)
normal_Z                                     = zeros_like(normal_X)
normal_Z[normal_valid_mask]                  = np.sqrt(1 - normal_X_sqr[normal_valid_mask] - normal_Y_sqr[normal_valid_mask])
normal_Z[normal_invalid_mask]                = nan
normal_hist_bin_centers_valid_mask           = normal_valid_mask
normal_hist_bin_centers_invalid_mask         = normal_invalid_mask
normal_hist_bin_centers_Z                    = normal_Z
normal_hist_bin_centers_XYZ                  = dstack((normal_hist_bin_centers_X, normal_hist_bin_centers_Y, normal_hist_bin_centers_Z))

# RGB COLOR
# DIFFUSE ILLUMINATION
# NON-DIFFUSE RESIDUAL
color_hist_denorm_bin_centers_x_1d = color_hist_denorm_bin_edges[:-1] + diff(color_hist_denorm_bin_edges)/2.0
color_hist_denorm_bin_centers_y_1d = color_hist_denorm_bin_edges[:-1] + diff(color_hist_denorm_bin_edges)/2.0
color_hist_denorm_bin_centers_z_1d = color_hist_denorm_bin_edges[:-1] + diff(color_hist_denorm_bin_edges)/2.0

color_hist_denorm_bin_centers_Z, color_hist_denorm_bin_centers_Y, color_hist_denorm_bin_centers_X = \
    meshgrid(color_hist_denorm_bin_centers_x_1d, color_hist_denorm_bin_centers_y_1d, color_hist_denorm_bin_centers_z_1d, indexing="ij")

color_hist_denorm_bin_centers_1d = c_[ color_hist_denorm_bin_centers_X.ravel(), color_hist_denorm_bin_centers_Y.ravel(), color_hist_denorm_bin_centers_Z.ravel() ]

# DIFFUSE REFLECTANCE
color_hist_norm_bin_centers_x_1d = color_hist_norm_bin_edges[:-1] + diff(color_hist_norm_bin_edges)/2.0
color_hist_norm_bin_centers_y_1d = color_hist_norm_bin_edges[:-1] + diff(color_hist_norm_bin_edges)/2.0
color_hist_norm_bin_centers_z_1d = color_hist_norm_bin_edges[:-1] + diff(color_hist_norm_bin_edges)/2.0

color_hist_norm_bin_centers_Z, color_hist_norm_bin_centers_Y, color_hist_norm_bin_centers_X = \
    meshgrid(color_hist_norm_bin_centers_x_1d, color_hist_norm_bin_centers_y_1d, color_hist_norm_bin_centers_z_1d, indexing="ij")

color_hist_norm_bin_centers_1d = c_[ color_hist_norm_bin_centers_X.ravel(), color_hist_norm_bin_centers_Y.ravel(), color_hist_norm_bin_centers_Z.ravel() ]

# RGB COLOR
# DIFFUSE ILLUMINATION
# NON-DIFFUSE RESIDUAL
# DIFFUSE REFLECTANCE
hue_saturation_hist_bin_centers_x_1d = hue_saturation_hist_bin_edges[:-1] + diff(hue_saturation_hist_bin_edges)/2.0
hue_saturation_hist_bin_centers_y_1d = hue_saturation_hist_bin_edges[:-1] + diff(hue_saturation_hist_bin_edges)/2.0

hue_saturation_hist_bin_centers_Y, hue_saturation_hist_bin_centers_X = meshgrid(hue_saturation_hist_bin_centers_x_1d, hue_saturation_hist_bin_centers_y_1d, indexing="ij")

hue_saturation_hist_bin_corners_Y_00, hue_saturation_hist_bin_corners_X_00 = meshgrid(hue_saturation_hist_bin_edges[:-1], hue_saturation_hist_bin_edges[:-1], indexing="ij")
hue_saturation_hist_bin_corners_Y_01, hue_saturation_hist_bin_corners_X_01 = meshgrid(hue_saturation_hist_bin_edges[:-1], hue_saturation_hist_bin_edges[1:], indexing="ij")
hue_saturation_hist_bin_corners_Y_10, hue_saturation_hist_bin_corners_X_10 = meshgrid(hue_saturation_hist_bin_edges[1:],  hue_saturation_hist_bin_edges[:-1], indexing="ij")
hue_saturation_hist_bin_corners_Y_11, hue_saturation_hist_bin_corners_X_11 = meshgrid(hue_saturation_hist_bin_edges[1:],  hue_saturation_hist_bin_edges[1:], indexing="ij")

hue_saturation_hist_bin_corners_X         = dstack((hue_saturation_hist_bin_corners_X_00, hue_saturation_hist_bin_corners_X_01, hue_saturation_hist_bin_corners_X_10, hue_saturation_hist_bin_corners_X_11))
hue_saturation_hist_bin_corners_Y         = dstack((hue_saturation_hist_bin_corners_Y_00, hue_saturation_hist_bin_corners_Y_01, hue_saturation_hist_bin_corners_Y_10, hue_saturation_hist_bin_corners_Y_11))
hue_saturation_hist_bin_corners_X_abs_min = np.min(np.abs(hue_saturation_hist_bin_corners_X), axis=2)
hue_saturation_hist_bin_corners_Y_abs_min = np.min(np.abs(hue_saturation_hist_bin_corners_Y), axis=2)

hue_saturation_hist_bin_corners_XY_abs_min           = dstack((hue_saturation_hist_bin_corners_X_abs_min, hue_saturation_hist_bin_corners_Y_abs_min))
hue_saturation_hist_bin_corners_abs_min_valid_mask   = linalg.norm(hue_saturation_hist_bin_corners_XY_abs_min, axis=2) <= 1.0
hue_saturation_hist_bin_corners_abs_min_invalid_mask = logical_not(hue_saturation_hist_bin_corners_abs_min_valid_mask)

hue_saturation_hist_bin_centers_XY           = dstack((hue_saturation_hist_bin_centers_X, hue_saturation_hist_bin_centers_Y))
hue_saturation_hist_bin_centers_valid_mask   = linalg.norm(hue_saturation_hist_bin_centers_XY, axis=2) <= 1.0
hue_saturation_hist_bin_centers_invalid_mask = logical_not(hue_saturation_hist_bin_centers_valid_mask)



batches_dir = os.path.join(args.analysis_dir, "image_statistics")
batch_names = [ os.path.basename(b) for b in sort(glob.glob(os.path.join(batches_dir, "*"))) ]
batch_dirs  = [ os.path.join(batches_dir, b) for b in batch_names if fnmatch.fnmatch(b, args.batch_names) ]

unique_objects_per_image_hist               = None
unique_classes_per_image_hist               = None
unique_objects_per_class_hist               = None
pixels_per_class_hist                       = None
depth_hist_linear                           = None
depth_hist_log                              = None
normal_hist                                 = None
rgb_color_hist                              = None
rgb_color_hue_saturation_hist               = None
rgb_color_brightness_hist_linear            = None
rgb_color_brightness_hist_log               = None
diffuse_illumination_hist                   = None
diffuse_illumination_hue_saturation_hist    = None
diffuse_illumination_brightness_hist_linear = None
diffuse_illumination_brightness_hist_log    = None
diffuse_reflectance_hist                    = None
diffuse_reflectance_hue_saturation_hist     = None
diffuse_reflectance_brightness_hist_linear  = None
diffuse_reflectance_brightness_hist_log     = None
residual_hist                               = None
residual_hue_saturation_hist                = None
residual_brightness_hist_linear             = None
residual_brightness_hist_log                = None
object_volume_hist_linear                   = None
object_volume_hist_log                      = None

for b in batch_dirs:

    print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Loading batch: " + b)

    unique_objects_per_image_hist_hdf5_file               = os.path.join(b, "metadata_unique_objects_per_image_hist.hdf5")
    unique_classes_per_image_hist_hdf5_file               = os.path.join(b, "metadata_unique_classes_per_image_hist.hdf5")
    unique_objects_per_class_hist_hdf5_file               = os.path.join(b, "metadata_unique_objects_per_class_hist.hdf5")
    pixels_per_class_hist_hdf5_file                       = os.path.join(b, "metadata_pixels_per_class_hist.hdf5")
    depth_hist_linear_hdf5_file                           = os.path.join(b, "metadata_depth_hist_linear.hdf5")
    depth_hist_log_hdf5_file                              = os.path.join(b, "metadata_depth_hist_log.hdf5")
    normal_hist_hdf5_file                                 = os.path.join(b, "metadata_normal_hist.hdf5")
    rgb_color_hist_hdf5_file                              = os.path.join(b, "metadata_rgb_color_hist.hdf5")
    rgb_color_hue_saturation_hist_hdf5_file               = os.path.join(b, "metadata_rgb_color_hue_saturation_hist.hdf5")
    rgb_color_brightness_hist_linear_hdf5_file            = os.path.join(b, "metadata_rgb_color_brightness_hist_linear.hdf5")
    rgb_color_brightness_hist_log_hdf5_file               = os.path.join(b, "metadata_rgb_color_brightness_hist_log.hdf5")
    diffuse_illumination_hist_hdf5_file                   = os.path.join(b, "metadata_diffuse_illumination_hist.hdf5")
    diffuse_illumination_hue_saturation_hist_hdf5_file    = os.path.join(b, "metadata_diffuse_illumination_hue_saturation_hist.hdf5")
    diffuse_illumination_brightness_hist_linear_hdf5_file = os.path.join(b, "metadata_diffuse_illumination_brightness_hist_linear.hdf5")
    diffuse_illumination_brightness_hist_log_hdf5_file    = os.path.join(b, "metadata_diffuse_illumination_brightness_hist_log.hdf5")
    diffuse_reflectance_hist_hdf5_file                    = os.path.join(b, "metadata_diffuse_reflectance_hist.hdf5")
    diffuse_reflectance_hue_saturation_hist_hdf5_file     = os.path.join(b, "metadata_diffuse_reflectance_hue_saturation_hist.hdf5")
    diffuse_reflectance_brightness_hist_linear_hdf5_file  = os.path.join(b, "metadata_diffuse_reflectance_brightness_hist_linear.hdf5")
    diffuse_reflectance_brightness_hist_log_hdf5_file     = os.path.join(b, "metadata_diffuse_reflectance_brightness_hist_log.hdf5")
    residual_hist_hdf5_file                               = os.path.join(b, "metadata_residual_hist.hdf5")
    residual_hue_saturation_hist_hdf5_file                = os.path.join(b, "metadata_residual_hue_saturation_hist.hdf5")
    residual_brightness_hist_linear_hdf5_file             = os.path.join(b, "metadata_residual_brightness_hist_linear.hdf5")
    residual_brightness_hist_log_hdf5_file                = os.path.join(b, "metadata_residual_brightness_hist_log.hdf5")
    object_volume_hist_linear_hdf5_file                   = os.path.join(b, "metadata_object_volume_hist_linear.hdf5")
    object_volume_hist_log_hdf5_file                      = os.path.join(b, "metadata_object_volume_hist_log.hdf5")

    with h5py.File(unique_objects_per_image_hist_hdf5_file,               "r") as f: unique_objects_per_image_hist_               = f["dataset"][:].astype(int64)
    with h5py.File(unique_classes_per_image_hist_hdf5_file,               "r") as f: unique_classes_per_image_hist_               = f["dataset"][:].astype(int64)
    with h5py.File(unique_objects_per_class_hist_hdf5_file,               "r") as f: unique_objects_per_class_hist_               = f["dataset"][:].astype(int64)
    with h5py.File(pixels_per_class_hist_hdf5_file,                       "r") as f: pixels_per_class_hist_                       = f["dataset"][:].astype(int64)
    with h5py.File(depth_hist_linear_hdf5_file,                           "r") as f: depth_hist_linear_                           = f["dataset"][:].astype(int64)
    with h5py.File(depth_hist_log_hdf5_file,                              "r") as f: depth_hist_log_                              = f["dataset"][:].astype(int64)
    with h5py.File(normal_hist_hdf5_file,                                 "r") as f: normal_hist_                                 = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_hist_hdf5_file,                              "r") as f: rgb_color_hist_                              = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_hue_saturation_hist_hdf5_file,               "r") as f: rgb_color_hue_saturation_hist_               = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_brightness_hist_linear_hdf5_file,            "r") as f: rgb_color_brightness_hist_linear_            = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_brightness_hist_log_hdf5_file,               "r") as f: rgb_color_brightness_hist_log_               = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_hist_hdf5_file,                   "r") as f: diffuse_illumination_hist_                   = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_hue_saturation_hist_hdf5_file,    "r") as f: diffuse_illumination_hue_saturation_hist_    = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_brightness_hist_linear_hdf5_file, "r") as f: diffuse_illumination_brightness_hist_linear_ = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_brightness_hist_log_hdf5_file,    "r") as f: diffuse_illumination_brightness_hist_log_    = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_hist_hdf5_file,                    "r") as f: diffuse_reflectance_hist_                    = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_hue_saturation_hist_hdf5_file,     "r") as f: diffuse_reflectance_hue_saturation_hist_     = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_brightness_hist_linear_hdf5_file,  "r") as f: diffuse_reflectance_brightness_hist_linear_  = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_brightness_hist_log_hdf5_file,     "r") as f: diffuse_reflectance_brightness_hist_log_     = f["dataset"][:].astype(int64)
    with h5py.File(residual_hist_hdf5_file,                               "r") as f: residual_hist_                               = f["dataset"][:].astype(int64)
    with h5py.File(residual_hue_saturation_hist_hdf5_file,                "r") as f: residual_hue_saturation_hist_                = f["dataset"][:].astype(int64)
    with h5py.File(residual_brightness_hist_linear_hdf5_file,             "r") as f: residual_brightness_hist_linear_             = f["dataset"][:].astype(int64)
    with h5py.File(residual_brightness_hist_log_hdf5_file,                "r") as f: residual_brightness_hist_log_                = f["dataset"][:].astype(int64)
    with h5py.File(object_volume_hist_linear_hdf5_file,                   "r") as f: object_volume_hist_linear_                   = f["dataset"][:].astype(int64)
    with h5py.File(object_volume_hist_log_hdf5_file,                      "r") as f: object_volume_hist_log_                      = f["dataset"][:].astype(int64)

    unique_objects_per_image_hist               = unique_objects_per_image_hist_               if unique_objects_per_image_hist               is None else unique_objects_per_image_hist               + unique_objects_per_image_hist_
    unique_classes_per_image_hist               = unique_classes_per_image_hist_               if unique_classes_per_image_hist               is None else unique_classes_per_image_hist               + unique_classes_per_image_hist_
    unique_objects_per_class_hist               = unique_objects_per_class_hist_               if unique_objects_per_class_hist               is None else unique_objects_per_class_hist               + unique_objects_per_class_hist_
    pixels_per_class_hist                       = pixels_per_class_hist_                       if pixels_per_class_hist                       is None else pixels_per_class_hist                       + pixels_per_class_hist_
    depth_hist_linear                           = depth_hist_linear_                           if depth_hist_linear                           is None else depth_hist_linear                           + depth_hist_linear_
    depth_hist_log                              = depth_hist_log_                              if depth_hist_log                              is None else depth_hist_log                              + depth_hist_log_
    normal_hist                                 = normal_hist_                                 if normal_hist                                 is None else normal_hist                                 + normal_hist_
    rgb_color_hist                              = rgb_color_hist_                              if rgb_color_hist                              is None else rgb_color_hist                              + rgb_color_hist_
    rgb_color_hue_saturation_hist               = rgb_color_hue_saturation_hist_               if rgb_color_hue_saturation_hist               is None else rgb_color_hue_saturation_hist               + rgb_color_hue_saturation_hist_
    rgb_color_brightness_hist_linear            = rgb_color_brightness_hist_linear_            if rgb_color_brightness_hist_linear            is None else rgb_color_brightness_hist_linear            + rgb_color_brightness_hist_linear_
    rgb_color_brightness_hist_log               = rgb_color_brightness_hist_log_               if rgb_color_brightness_hist_log               is None else rgb_color_brightness_hist_log               + rgb_color_brightness_hist_log_
    diffuse_illumination_hist                   = diffuse_illumination_hist_                   if diffuse_illumination_hist                   is None else diffuse_illumination_hist                   + diffuse_illumination_hist_
    diffuse_illumination_hue_saturation_hist    = diffuse_illumination_hue_saturation_hist_    if diffuse_illumination_hue_saturation_hist    is None else diffuse_illumination_hue_saturation_hist    + diffuse_illumination_hue_saturation_hist_
    diffuse_illumination_brightness_hist_linear = diffuse_illumination_brightness_hist_linear_ if diffuse_illumination_brightness_hist_linear is None else diffuse_illumination_brightness_hist_linear + diffuse_illumination_brightness_hist_linear_
    diffuse_illumination_brightness_hist_log    = diffuse_illumination_brightness_hist_log_    if diffuse_illumination_brightness_hist_log    is None else diffuse_illumination_brightness_hist_log    + diffuse_illumination_brightness_hist_log_
    diffuse_reflectance_hist                    = diffuse_reflectance_hist_                    if diffuse_reflectance_hist                    is None else diffuse_reflectance_hist                    + diffuse_reflectance_hist_
    diffuse_reflectance_hue_saturation_hist     = diffuse_reflectance_hue_saturation_hist_     if diffuse_reflectance_hue_saturation_hist     is None else diffuse_reflectance_hue_saturation_hist     + diffuse_reflectance_hue_saturation_hist_
    diffuse_reflectance_brightness_hist_linear  = diffuse_reflectance_brightness_hist_linear_  if diffuse_reflectance_brightness_hist_linear  is None else diffuse_reflectance_brightness_hist_linear  + diffuse_reflectance_brightness_hist_linear_
    diffuse_reflectance_brightness_hist_log     = diffuse_reflectance_brightness_hist_log_     if diffuse_reflectance_brightness_hist_log     is None else diffuse_reflectance_brightness_hist_log     + diffuse_reflectance_brightness_hist_log_
    residual_hist                               = residual_hist_                               if residual_hist                               is None else residual_hist                               + residual_hist_
    residual_hue_saturation_hist                = residual_hue_saturation_hist_                if residual_hue_saturation_hist                is None else residual_hue_saturation_hist                + residual_hue_saturation_hist_
    residual_brightness_hist_linear             = residual_brightness_hist_linear_             if residual_brightness_hist_linear             is None else residual_brightness_hist_linear             + residual_brightness_hist_linear_
    residual_brightness_hist_log                = residual_brightness_hist_log_                if residual_brightness_hist_log                is None else residual_brightness_hist_log                + residual_brightness_hist_log_
    object_volume_hist_linear                   = object_volume_hist_linear_                   if object_volume_hist_linear                   is None else object_volume_hist_linear                   + object_volume_hist_linear_
    object_volume_hist_log                      = object_volume_hist_log_                      if object_volume_hist_log                      is None else object_volume_hist_log                      + object_volume_hist_log_



# UNIQUE OBJECTS PER IMAGE
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] UNIQUE OBJECTS PER IMAGE...")
H = unique_objects_per_image_hist
hist(unique_objects_per_image_hist_bin_edges[:-1], unique_objects_per_image_hist_bin_edges, weights=H)
xlim((0,200))
title("Distribution of unique objects per image")
xlabel("Number of unique objects per image")
ylabel("Frequency")
show()

H_ = H.astype(float64)
H_norm  = H_ / sum(H_)
C = cumsum(H_norm)
C_ = r_[0.0, C]
mean_objects_per_image = dot(H_norm, unique_objects_per_image_hist_bin_edges[:-1])

plot(unique_objects_per_image_hist_bin_edges, C_)
xlim((0,200))
title("Cumulative distribution of unique objects per image")
xlabel("Number of unique objects per image")
ylabel("Cumulative distribution")
show()

# ptile = 0.48
# i = where(C_ <= ptile)[0][-1]
# print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] %0.2f%% of images have fewer than %d objects (%0.2f%% of images have %d objects or more)" % (100*C_[i], unique_objects_per_image_hist_bin_edges[i], 100 - 100*C_[i], unique_objects_per_image_hist_bin_edges[i]))

num_cdf_entries_to_print = 30
for i in range(num_cdf_entries_to_print):
    print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] %0.2f%% of images have fewer than %d objects (%0.2f%% of images have %d or more objects)" % (100*C_[i], unique_objects_per_image_hist_bin_edges[i], 100 - 100*C_[i], unique_objects_per_image_hist_bin_edges[i]))

print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] %0.2f objects per image (mean)" % mean_objects_per_image)

# UNIQUE CLASSES PER IMAGE
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] UNIQUE CLASSES PER IMAGE...")
H = unique_classes_per_image_hist
hist(unique_classes_per_image_hist_bin_edges[:-1], unique_classes_per_image_hist_bin_edges, weights=H)
title("Distribution of unique semantic classes per image")
xlabel("Number of unique semantic classes per image")
ylabel("Frequency")
show()

H_ = H.astype(float64)
H_norm = H_ / sum(H_)
num_classes_per_image = dot(H_norm, unique_classes_per_image_hist_bin_edges[:-1])

print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] %0.2f classes per image (mean)" % num_classes_per_image)

# UNIQUE OBJECTS PER CLASS
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] UNIQUE OBJECTS PER CLASS...")
H = unique_objects_per_class_hist
tick_label = ["NO LABEL"] + [""] + [ semantic_id_to_name_map[i] for i in sort(list(semantic_id_to_name_map.keys())) ]
barh(arange(0, len(tick_label)), H, tick_label=tick_label)
gca().invert_yaxis()
title("Number of unique objects per class")
xlabel("Number of unique objects")
ylabel("Classes")
show()

num_scenes = 461
num_objects = sum(H)
num_objects_per_scene = float(num_objects)/float(num_scenes)

print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Hypersim: %d scenes" % num_scenes)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Hypersim: %d objects" % num_objects)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Hypersim: %0.2f objects per scene (mean)" % num_objects_per_scene)

# estimated visually from Figure 8 in the ScanNet paper using https://automeris.io/WebPlotDigitizer/
scan_net_objects_per_scene_hist_bin_edges = array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45])
scan_net_objects_per_scene_hist = array([
    179.10,
    576.58,
    425.21,
    202.21,
    95.90,
    26.58,
    13.87,
    5.78,
    2.31 ])

 # assume that all entries that contribute to a histogram bin are at the right-most edge of the bin, which is as favorable to ScanNet as possible
H = scan_net_objects_per_scene_hist
H_ = H.astype(float64)
H_norm = H_ / sum(H_)

num_scenes = sum(H_)
num_objects = dot(H_, scan_net_objects_per_scene_hist_bin_edges[1:])
num_objects_per_scene = dot(H_norm, scan_net_objects_per_scene_hist_bin_edges[1:])

print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] ScanNet: %0.2f scenes (estimated)" % num_scenes)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] ScanNet: %0.2f objects (estimated)" % num_objects)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] ScanNet: %0.2f objects per scene (mean, estimated)" % num_objects_per_scene)

# estimated visually from Figure 10 in the Replica paper using https://automeris.io/WebPlotDigitizer/
replica_objects_per_class_hist = array([
    55.84,
    48.05,
    37.16,
    32.30,
    15.76,
    02.14,
    2.96,
    9.07,
    7.12,
    9.34,
    57.39,
    54.47,
    54.47,
    50.58,
    46.69,
    38.91,
    36.96,
    37.94,
    35.99,
    34.05,
    31.13,
    31.13,
    29.18,
    29.18,
    29.18,
    27.24,
    27.24,
    26.26,
    26.26,
    25.29,
    24.32,
    24.32,
    23.35,
    23.35,
    23.35,
    23.35,
    19.46,
    18.48,
    17.51,
    15.56,
    15.56,
    14.59,
    13.62,
    13.62,
    13.62,
    13.62,
    13.62,
    12.65,
    10.70,
    10.70,
    11.67,
    11.67,
    10.70,
    10.70,
    9.73,
    9.73,
    9.73,
    8.75,
    8.75,
    8.75,
    6.81,
    6.81,
    6.81,
    6.81,
    5.84,
    5.84,
    5.84,
    5.84,
    4.86,
    5.84,
    4.86,
    4.86,
    3.89,
    3.89,
    3.89,
    3.89,
    3.89,
    3.89,
    3.89,
    4.86,
    3.89,
    1.95,
    1.95,
    1.95,
    0.97,
    0.97,
    0.97,
    0.97])

H = replica_objects_per_class_hist

num_scenes = 18
num_objects = sum(H)
num_objects_per_scene = float(num_objects)/float(num_scenes)

print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Replica: %d scenes" % num_scenes)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Replica: %0.2f objects (estimated)" % num_objects)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Replica: %0.2f objects per scene (mean, estimated)" % num_objects_per_scene)

# PIXELS PER CLASS
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] PIXELS PER CLASS...")

semantic_name_to_id_map = {v:k for k,v in semantic_id_to_name_map.items()}
semantic_names_objects = [
    "cabinet",
    "bed",
    "chair",
    "sofa",
    "table",
    "door",
    "window",
    "bookshelf",
    "picture",
    "counter",
    "blinds",
    "desk",
    "shelves",
    "curtain",
    "dresser",
    "pillow",
    "mirror",
    "floormat",
    "clothes",
    "books",
    "refrigerator",
    "television",
    "paper",
    "towel",
    "showercurtain",
    "box",
    "whiteboard",
    "person",
    "nightstand",
    "toilet",
    "sink",
    "lamp",
    "bathtub",
    "bag",
    "otherstructure",
    "otherfurniture",
    "otherprop" ]

semantic_ids_objects = [ semantic_name_to_id_map[n] for n in semantic_names_objects ]
total_pixels         = sum(pixels_per_class_hist)
labeled_pixels       = sum(pixels_per_class_hist[1:])
object_pixels        = sum(pixels_per_class_hist[semantic_ids_objects])

print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Total labeled pixels (any semantic label): " + str(labeled_pixels) + " / " + str(total_pixels) + " = " + str(float(labeled_pixels)/float(total_pixels)))
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Total labeled pixels (foreground semantic labels only): " + str(object_pixels)  + " / " + str(total_pixels) + " = " + str(float(object_pixels)/float(total_pixels)))

H = pixels_per_class_hist
tick_label = ["NO LABEL"] + [""] + [ semantic_id_to_name_map[i] for i in sort(list(semantic_id_to_name_map.keys())) ]
barh(arange(0, len(tick_label)), H, tick_label=tick_label)
gca().invert_yaxis()
title("Number of pixels per class")
xlabel("Number of pixels")
ylabel("Classes")
show()

# DEPTH (LINEAR)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] DEPTH (LINEAR)...")
H = depth_hist_linear
hist(depth_hist_linear_bin_edges[:-1], depth_hist_linear_bin_edges, weights=H)  
title("Distribution of depths (meters, x-axis is linear)")
xlabel("Depth (meters)")
ylabel("Frequency")
show()

H_ = H.astype(float64)
H_norm = H_ / sum(H_)

depth_hist_linear_bin_centers = depth_hist_linear_bin_edges[:-1] + (diff(depth_hist_linear_bin_edges)/2.0)
depth_linear_mean = dot(H_norm, depth_hist_linear_bin_centers)

print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Linear depth (mean): %0.4f" % depth_linear_mean)

# DEPTH (LOG)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] DEPTH (LOG)...")
H = depth_hist_log
hist(depth_hist_log_bin_edges[:-1], depth_hist_log_bin_edges, weights=H)
xscale("log")
title("Distribution of depths (meters, x-axis is log-scaled)")
xlabel("Depth (meters)")
ylabel("Frequency")
show()

# NORMAL
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] NORMAL...")

H = normal_hist.astype(float64)
eps = 1.0 # small value to avoid log(0)
log_H = log(H + eps)
log_H[normal_hist_bin_corners_abs_min_invalid_mask] = nan

normal_hist_bin_centers_ = (normal_hist_bin_centers_XYZ + 1.0)/2.0
normal_hist_bin_centers_[normal_hist_bin_centers_invalid_mask]         = array([1,1,1])
normal_hist_bin_centers_[normal_hist_bin_corners_abs_min_invalid_mask] = array([0,0,0])
imshow(normal_hist_bin_centers_, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
title("Normal reference chart\n(color indicates normal vector mapped onto into the RGB cube)")
xlabel("Normal (x-coordinate)")
ylabel("Normal (y-coordinate)")
show()

imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
colorbar()
title("Distribution of normals\n(color indicates log-frequency)")
xlabel("Normal (x-coordinate)")
ylabel("Normal (y-coordinate)")
show()

# k = 200
# normal_hist_bin_centers_ = (normal_hist_bin_centers + 1.0)/2.0
# normal_hist_bin_centers_[normal_hist_bin_centers_invalid_mask]                           = array([1,1,1])
# normal_hist_bin_centers_[normal_hist_bin_corners_abs_min_invalid_mask]                   = nan
# normal_hist_bin_centers_[logical_and(H < k, normal_hist_bin_corners_abs_min_valid_mask)] = array([0.5,0.5,0.5])
# imshow(normal_hist_bin_centers_, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
# show()

# RGB COLOR
# DIFFUSE ILLUMINATION
# DIFFUSE REFLECTANCE
# NON-DIFFUSE RESIDUAL
hue_saturation_hist_theta = arctan2(hue_saturation_hist_bin_centers_Y, hue_saturation_hist_bin_centers_X)
hue_saturation_hist_theta[hue_saturation_hist_theta < 0] = hue_saturation_hist_theta[hue_saturation_hist_theta < 0]+(2*pi)
hue_saturation_hist_h   = hue_saturation_hist_theta/(2*pi)
hue_saturation_hist_s   = linalg.norm(hue_saturation_hist_bin_centers_XY, axis=2)
hue_saturation_hist_hsv = dstack((hue_saturation_hist_h, hue_saturation_hist_s, 1.0*ones_like(hue_saturation_hist_h)))
hue_saturation_hist_rgb = matplotlib.colors.hsv_to_rgb(hue_saturation_hist_hsv)
hue_saturation_hist_rgb[hue_saturation_hist_bin_centers_invalid_mask]         = array([1,1,1])
hue_saturation_hist_rgb[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = array([0,0,0])

imshow(hue_saturation_hist_rgb, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest");
title("Hue saturation reference chart")
show()

# RGB COLOR
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] RGB COLOR...")
H             = rgb_color_hist.astype(float64)
H             = sqrt(H)
H_norm        = H / H.sum()
H_norm_1d     = H_norm.ravel()
eps           = 1.0 # small value to avoid log(0)
log_H         = log(H + eps)
log_H_norm    = log_H / log_H.sum()
log_H_norm_1d = log_H_norm.ravel()
# k             = 10.0 # size multiplier
# sizes         = k*log_H_norm_1d
k             = 10.0 # size multiplier
sizes         = k*H_norm_1d
mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=(512, 512))
mayavi_utils.points3d_color_by_rgb_value(color_hist_denorm_bin_centers_1d, colors=clip(color_hist_denorm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
mayavi.mlab.axes()
mayavi.mlab.xlabel("R")
mayavi.mlab.ylabel("G")
mayavi.mlab.zlabel("B")
mayavi.mlab.show()

H = rgb_color_hue_saturation_hist
eps = 1e-1 # small value to avoid log(0)
log_H = log(H + eps)
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan

imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
title("Distribution of hue saturation observations (RGB color)\n(color indicates log-frequency)")
show()

H = rgb_color_brightness_hist_linear
hist(brightness_hist_linear_bin_edges[:-1], brightness_hist_linear_bin_edges, weights=H)
title("Distribution of brightness observations (RGB color, x-axis is linear)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

H = rgb_color_brightness_hist_log
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges, weights=H)
xscale("log")
title("Distribution of brightness observations (RGB color, x-axis is log-scaled)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

# DIFFUSE ILLUMINATION
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] DIFFUSE ILLUMINATION...")
H             = diffuse_illumination_hist.astype(float64)
H             = sqrt(H)
H_norm        = H / H.sum()
H_norm_1d     = H_norm.ravel()
eps           = 1.0 # small value to avoid log(0)
log_H         = log(H + eps)
log_H_norm    = log_H / log_H.sum()
log_H_norm_1d = log_H_norm.ravel()
# k             = 10.0 # size multiplier
# sizes         = k*log_H_norm_1d
k             = 10.0 # size multiplier
sizes         = k*H_norm_1d
mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=(512, 512))
mayavi_utils.points3d_color_by_rgb_value(color_hist_denorm_bin_centers_1d, colors=clip(color_hist_denorm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
mayavi.mlab.axes()
mayavi.mlab.xlabel("R")
mayavi.mlab.ylabel("G")
mayavi.mlab.zlabel("B")
mayavi.mlab.show()

H = diffuse_illumination_hue_saturation_hist
eps = 1e-1 # small value to avoid log(0)
log_H = log(H + eps)
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan
imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
title("Distribution of hue saturation observations (diffuse illumination)\n(color indicates log-frequency)")
show()

H = diffuse_illumination_brightness_hist_linear
hist(brightness_hist_linear_bin_edges[:-1], brightness_hist_linear_bin_edges, weights=H)
title("Distribution of brightness observations (diffuse illumination, x-axis is linear)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

H = diffuse_illumination_brightness_hist_log
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges, weights=H)
xscale("log")
title("Distribution of brightness observations (diffuse illumination, x-axis is log-scaled)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

# DIFFUSE REFLECTANCE
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] DIFFUSE REFLECTANCE...")
H             = diffuse_reflectance_hist.astype(float64)
H             = sqrt(H)
H_norm        = H / H.sum()
H_norm_1d     = H_norm.ravel()
eps           = 1.0 # small value to avoid log(0)
log_H         = log(H + eps)
log_H_norm    = log_H / log_H.sum()
log_H_norm_1d = log_H_norm.ravel()
# k             = 10.0 # size multiplier
# sizes         = k*log_H_norm_1d
k             = 10.0 # size multiplier
sizes         = k*H_norm_1d
mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=(512, 512))
mayavi_utils.points3d_color_by_rgb_value(color_hist_norm_bin_centers_1d, colors=clip(color_hist_norm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
mayavi.mlab.axes()
mayavi.mlab.xlabel("R")
mayavi.mlab.ylabel("G")
mayavi.mlab.zlabel("B")
mayavi.mlab.show()

H = diffuse_reflectance_hue_saturation_hist
eps = 1e-1 # small value to avoid log(0)
log_H = log(H + eps)
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan
imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
title("Distribution of hue saturation observations (diffuse reflectance)\n(color indicates log-frequency)")
show()

H = diffuse_reflectance_brightness_hist_linear
hist(brightness_hist_linear_bin_edges[:-1], brightness_hist_linear_bin_edges, weights=H)
title("Distribution of brightness observations (diffuse reflectance, x-axis is linear)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

H = diffuse_reflectance_brightness_hist_log
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges, weights=H)
xscale("log")
title("Distribution of brightness observations (diffuse reflectance, x-axis is log-scaled)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

# NON-DIFFUSE RESIDUAL
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] NON-DIFFUSE RESIDUAL...")
H             = residual_hist.astype(float64)
H             = sqrt(H)
H_norm        = H / H.sum()
H_norm_1d     = H_norm.ravel()
eps           = 1.0 # small value to avoid log(0)
log_H         = log(H + eps)
log_H_norm    = log_H / log_H.sum()
log_H_norm_1d = log_H_norm.ravel()
# k             = 10.0 # size multiplier
# sizes         = k*log_H_norm_1d
k             = 10.0 # size multiplier
sizes         = k*H_norm_1d
mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=(512, 512))
mayavi_utils.points3d_color_by_rgb_value(color_hist_denorm_bin_centers_1d, colors=clip(color_hist_denorm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
mayavi.mlab.axes()
mayavi.mlab.xlabel("R")
mayavi.mlab.ylabel("G")
mayavi.mlab.zlabel("B")
mayavi.mlab.show()

H = residual_hue_saturation_hist
eps = 1e-1 # small value to avoid log(0)
log_H = log(H + eps)
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan

imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
title("Distribution of hue saturation observations (residual)\n(color indicates log-frequency)")
show()

H = residual_brightness_hist_linear
hist(brightness_hist_linear_bin_edges[:-1], brightness_hist_linear_bin_edges, weights=H)
title("Distribution of brightness observations (residual, x-axis is linear)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

H = residual_brightness_hist_log
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges, weights=H)
xscale("log")
title("Distribution of brightness observations (residual, x-axis is log-scaled)")
xlabel("Brightness (unitless)")
ylabel("Frequency")
show()

# OBJECT_VOLUME (LINEAR)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] OBJECT VOLUME (LINEAR)...")
H = object_volume_hist_linear
hist(object_volume_hist_linear_bin_edges[:-1], object_volume_hist_linear_bin_edges, weights=H)
title("Distribution of object volumes (x-axis is linear)")
xlabel("Object volume (meters^3)")
ylabel("Frequency")
show()

# DEPTH (LOG)
print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] OBJECT VOLUME (LOG)...")
H = object_volume_hist_log
hist(object_volume_hist_log_bin_edges[:-1], object_volume_hist_log_bin_edges, weights=H)
xscale("log")
title("Distribution of object volumes (x-axis is log-scaled)")
xlabel("Object volume (meters^3)")
ylabel("Frequency")
show()



print("[HYPERSIM: VISUALIZE_IMAGE_STATISTICS] Finished.")
