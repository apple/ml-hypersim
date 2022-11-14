#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import glob
import h5py
import fnmatch
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
parser.add_argument("--batch_names", required=True)
parser.add_argument("--plots_dir", required=True)
args = parser.parse_args()



print("[HYPERSIM: PLOT_STATS_SCENES_OBJECTS_IMAGES] Begin...")



# SCENES PER SCENE TYPE
metadata_camera_trajectories_csv_file = os.path.join(args.analysis_dir, "metadata_camera_trajectories.csv")

df = pd.read_csv(metadata_camera_trajectories_csv_file)
camera_trajectories = df.to_records()

scene_types = [
    "Living room",
    "Dining room",
    "Kitchen",
    "Bedroom",
    "Bathroom",
    "Office (home)",
    "Office",
    "Office (waiting area)",
    "Office (building foyer)",
    "Office (conference room)",
    "Restaurant",
    "Retail space",
    "Hotel lobby",
    "Hall",
    "Transit station",
    "Lecture theater",
    "Library",
    "Art gallery",
    "Courtyard",
    "Staircase",
    "Hallway",
    "Other",
    "OUTSIDE VIEWING AREA (BAD INITIALIZATION)",
    "OUTSIDE VIEWING AREA (BAD TRAJECTORY)" ]

scene_type_name_to_id_map = dict([ (scene_types[i],i) for i in range(len(scene_types)) ])
scene_type_id_to_name_map = dict([ (i,scene_types[i]) for i in range(len(scene_types)) ])

scene_type_names = [ c["Scene type"] for c in camera_trajectories ]
scene_type_ids   = [ scene_type_name_to_id_map[n] for n in scene_type_names ]

scene_type_hist_n_bins         = len(scene_type_id_to_name_map)
scene_type_hist_min_bin_center = 0
scene_type_hist_max_bin_center = len(scene_type_id_to_name_map)-1

#
# NOTE: all parameters below must match analysis/dataset_generate_image_statistics.py
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
    38 : "otherstruct",
    39 : "otherfurniture",
    40 : "otherprop" }

# UNIQUE OBJECTS PER IMAGE
unique_objects_per_image_hist_n_bins    = 10000
unique_objects_per_image_hist_bin_edges = arange(unique_objects_per_image_hist_n_bins+1)

# UNIQUE CLASSES PER IMAGE
unique_classes_per_image_hist_n_bins    = len(semantic_id_to_name_map) + 1 # +1 because we want to make room for the value 0
unique_classes_per_image_hist_bin_edges = arange(unique_classes_per_image_hist_n_bins+1)

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



batches_dir = os.path.join(args.analysis_dir, "image_statistics")
batch_names = [ os.path.basename(b) for b in sort(glob.glob(os.path.join(batches_dir, "*"))) ]
batch_dirs  = [ os.path.join(batches_dir, b) for b in batch_names if fnmatch.fnmatch(b, args.batch_names) ]

unique_objects_per_image_hist = None
unique_classes_per_image_hist = None
unique_objects_per_class_hist = None
pixels_per_class_hist         = None
depth_hist_log                = None
normal_hist                   = None
object_volume_hist_log        = None

for b in batch_dirs:

    print("[HYPERSIM: PLOT_STATS_SCENES_OBJECTS_IMAGES] Loading batch: " + b)

    unique_objects_per_image_hist_hdf5_file = os.path.join(b, "metadata_unique_objects_per_image_hist.hdf5")
    unique_classes_per_image_hist_hdf5_file = os.path.join(b, "metadata_unique_classes_per_image_hist.hdf5")
    unique_objects_per_class_hist_hdf5_file = os.path.join(b, "metadata_unique_objects_per_class_hist.hdf5")
    pixels_per_class_hist_hdf5_file         = os.path.join(b, "metadata_pixels_per_class_hist.hdf5")
    depth_hist_log_hdf5_file                = os.path.join(b, "metadata_depth_hist_log.hdf5")
    normal_hist_hdf5_file                   = os.path.join(b, "metadata_normal_hist.hdf5")
    object_volume_hist_log_hdf5_file        = os.path.join(b, "metadata_object_volume_hist_log.hdf5")

    with h5py.File(unique_objects_per_image_hist_hdf5_file, "r") as f: unique_objects_per_image_hist_ = f["dataset"][:].astype(int64)
    with h5py.File(unique_classes_per_image_hist_hdf5_file, "r") as f: unique_classes_per_image_hist_ = f["dataset"][:].astype(int64)
    with h5py.File(unique_objects_per_class_hist_hdf5_file, "r") as f: unique_objects_per_class_hist_ = f["dataset"][:].astype(int64)
    with h5py.File(pixels_per_class_hist_hdf5_file,         "r") as f: pixels_per_class_hist_         = f["dataset"][:].astype(int64)
    with h5py.File(depth_hist_log_hdf5_file,                "r") as f: depth_hist_log_                = f["dataset"][:].astype(int64)
    with h5py.File(normal_hist_hdf5_file,                   "r") as f: normal_hist_                   = f["dataset"][:].astype(int64)
    with h5py.File(object_volume_hist_log_hdf5_file,        "r") as f: object_volume_hist_log_        = f["dataset"][:].astype(int64)

    unique_objects_per_image_hist = unique_objects_per_image_hist_ if unique_objects_per_image_hist is None else unique_objects_per_image_hist + unique_objects_per_image_hist_
    unique_classes_per_image_hist = unique_classes_per_image_hist_ if unique_classes_per_image_hist is None else unique_classes_per_image_hist + unique_classes_per_image_hist_
    unique_objects_per_class_hist = unique_objects_per_class_hist_ if unique_objects_per_class_hist is None else unique_objects_per_class_hist + unique_objects_per_class_hist_
    pixels_per_class_hist         = pixels_per_class_hist_         if pixels_per_class_hist         is None else pixels_per_class_hist         + pixels_per_class_hist_
    depth_hist_log                = depth_hist_log_                if depth_hist_log                is None else depth_hist_log                + depth_hist_log_
    normal_hist                   = normal_hist_                   if normal_hist                   is None else normal_hist                   + normal_hist_
    object_volume_hist_log        = object_volume_hist_log_        if object_volume_hist_log        is None else object_volume_hist_log        + object_volume_hist_log_



if not os.path.exists(args.plots_dir): os.makedirs(args.plots_dir)

tableau_colors_denorm_rev = array( [ [ 158, 218, 229 ], \
                                     [ 219, 219, 141 ], \
                                     [ 199, 199, 199 ], \
                                     [ 247, 182, 210 ], \
                                     [ 196, 156, 148 ], \
                                     [ 197, 176, 213 ], \
                                     [ 225, 122, 120 ], \
                                     [ 122, 193, 108 ], \
                                     [ 225, 157, 90  ], \
                                     [ 144, 169, 202 ], \
                                     [ 109, 204, 218 ], \
                                     [ 205, 204, 93  ], \
                                     [ 162, 162, 162 ], \
                                     [ 237, 151, 202 ], \
                                     [ 168, 120, 110 ], \
                                     [ 173, 139, 201 ], \
                                     [ 237, 102, 93  ], \
                                     [ 103, 191, 92  ], \
                                     [ 255, 158, 74  ], \
                                     [ 114, 158, 206 ] ] )

tableau_colors_denorm = tableau_colors_denorm_rev[::-1]
tableau_colors        = tableau_colors_denorm / 255.0



fig_file = os.path.join(args.plots_dir, "stats_scenes_objects_images.pdf")
fig = plt.figure(figsize=(18.0,8.25))
matplotlib.rcParams.update({"font.size": 16})
matplotlib.rcParams.update({"mathtext.fontset": "cm"})

vmin  = -12.0
vmax  = -7.0
ticks = [-12.0, -9.5, -7.0]



# SCENES PER SCENE TYPE
H, H_edges = histogram(scene_type_ids, bins=scene_type_hist_n_bins, range=(scene_type_hist_min_bin_center - 0.5, scene_type_hist_max_bin_center + 0.5))
tick_label = [ scene_type_id_to_name_map[i] for i in sort(list(scene_type_id_to_name_map.keys())) ]

tick_label_ignore_list  = [ "OUTSIDE VIEWING AREA (BAD INITIALIZATION)", "OUTSIDE VIEWING AREA (BAD TRAJECTORY)" ]
num_tick_labels_include = 10

H_sorted_inds      = argsort(H)[::-1]
H_sorted_inds_     = [ i for i in H_sorted_inds if tick_label[i] not in tick_label_ignore_list ]
H_sorted_inds_     = H_sorted_inds_[0:num_tick_labels_include]
H_sorted_          = H[H_sorted_inds_]
tick_label_sorted_ = [ tick_label[i] for i in H_sorted_inds_ ]

subplot(241)
barh(arange(len(tick_label_sorted_)), H_sorted_, tick_label=tick_label_sorted_, color=tableau_colors[0])
gca().invert_yaxis()
title("Histogram of\nscene types")
xlabel("Frequency\n\n(a)")
# ylabel("Scene type")



# UNIQUE OBJECTS PER CLASS
H = unique_objects_per_class_hist
tick_label = ["NO LABEL"] + [""] + [ semantic_id_to_name_map[i] for i in sort(list(semantic_id_to_name_map.keys())) ]

tick_label_ignore_list  = [ "NO LABEL", "", "wall", "floor", "ceiling" ]
num_tick_labels_include = 10

H_sorted_inds      = argsort(H)[::-1]
H_sorted_inds_     = [ i for i in H_sorted_inds if tick_label[i] not in tick_label_ignore_list ]
H_sorted_inds_     = H_sorted_inds_[0:num_tick_labels_include]
H_sorted_          = H[H_sorted_inds_]
tick_label_sorted_ = [ tick_label[i] for i in H_sorted_inds_ ]

subplot(242)
barh(arange(len(tick_label_sorted_)), H_sorted_, tick_label=tick_label_sorted_, color=tableau_colors[0])
gca().invert_yaxis()
title("Histogram of\nobjects per class")
xlabel("Frequency\n\n(b)")
# ylabel("Class")



# OBJECT VOLUME (LOG)

# redefine number of bins and bin edges for visualization
object_volume_hist_log_n_bins_    = int(object_volume_hist_log_n_bins/25)
object_volume_hist_log_bin_edges_ = logspace(object_volume_hist_log_min, object_volume_hist_log_max, object_volume_hist_log_n_bins_+1, base=object_volume_hist_log_base)

H = object_volume_hist_log

subplot(243)
hist(object_volume_hist_log_bin_edges[:-1], object_volume_hist_log_bin_edges_, weights=H, color=tableau_colors[0])
xscale("log")
title("Histogram of\nbounding box volumes")
xlabel("Volume (meters$^3$)\n\n(c)")
ylabel("Frequency")
xlim((1e-5,1e1))
# xticks([1e-3,1e-1,1e1])



# PIXELS PER CLASS
H = pixels_per_class_hist
tick_label = [r"$\star$"] + [""] + [ semantic_id_to_name_map[i] for i in sort(list(semantic_id_to_name_map.keys())) ]

tick_label_ignore_list  = [""]
num_tick_labels_include = 10

H_sorted_inds      = argsort(H)[::-1]
H_sorted_inds_     = [ i for i in H_sorted_inds if tick_label[i] not in tick_label_ignore_list ]
H_sorted_inds_     = H_sorted_inds_[0:num_tick_labels_include]
H_sorted_          = H[H_sorted_inds_]
tick_label_sorted_ = [ tick_label[i] for i in H_sorted_inds_ ]

subplot(244)
barh(arange(len(tick_label_sorted_)), H_sorted_/float(1000*1000), tick_label=tick_label_sorted_, color=tableau_colors[0])
gca().invert_yaxis()
title("Histogram of\npixels per class")
xlabel("Megapixels\n\n(d)")
# ylabel("Classes")



# UNIQUE OBJECTS PER IMAGE

# redefine number of bins and bin edges for visualization
unique_objects_per_image_hist_n_bins_    = int(unique_objects_per_image_hist_n_bins/5)
unique_objects_per_image_hist_bin_edges_ = linspace(0, unique_objects_per_image_hist_n_bins, unique_objects_per_image_hist_n_bins_+1)

H = unique_objects_per_image_hist

subplot(245)
hist(unique_objects_per_image_hist_bin_edges[:-1], unique_objects_per_image_hist_bin_edges_, weights=H, color=tableau_colors[0])
title("Histogram of\nobjects per image")
xlabel("Number of objects per image\n\n(e)")
ylabel("Frequency")
xlim((0,150))



# UNIQUE CLASSES PER IMAGE
H = unique_classes_per_image_hist

subplot(246)
hist(unique_classes_per_image_hist_bin_edges[:-1], unique_classes_per_image_hist_bin_edges, weights=H, color=tableau_colors[0])
title("Histogram of\nclasses per image")
xlabel("Number of classes per image\n\n(f)")
ylabel("Frequency")
xlim((0,20))



# DEPTH (LOG)

# redefine number of bins and bin edges for visualization
depth_hist_log_n_bins_    = int(depth_hist_log_n_bins/20)
depth_hist_log_bin_edges_ = logspace(depth_hist_log_min, depth_hist_log_max, depth_hist_log_n_bins_+1, base=depth_hist_log_base)

H = depth_hist_log
H_ = H/float(sum(H))

subplot(247)
hist(depth_hist_log_bin_edges[:-1], depth_hist_log_bin_edges_, weights=H_, color=tableau_colors[0])
xscale("log")
title("Distribution of\ndepth values")
xlabel("Depth (meters)\n\n(g)")
ylabel("Probability")
xlim((1e-1,1e2))



# NORMAL
H = normal_hist.astype(float64)
H_ = H / sum(H)

eps = 1e-9 # small value to avoid log(0)
log_H = log(H_ + eps)
log_H[normal_hist_bin_corners_abs_min_invalid_mask] = nan

subplot(248)
imshow(log_H, origin="lower", extent=[-1,1,-1,1], interpolation="nearest", vmin=vmin, vmax=vmax)
cbar = colorbar(ticks=ticks)
title("Distribution of\nsurface normals")
xlabel(r"$x$" + "\n\n(h)")
ylabel(r"$y$")
xticks([-1,0,1])
yticks([-1,0,1])



fig.tight_layout()
savefig(fig_file)



fig_file = os.path.join(args.plots_dir, "stats_normals_inset.png")

normal_hist_bin_centers_ = (normal_hist_bin_centers_XYZ + 1.0)/2.0
normal_hist_bin_centers_[normal_hist_bin_centers_invalid_mask]         = array([1,1,1])
normal_hist_bin_centers_[normal_hist_bin_corners_abs_min_invalid_mask] = array([1,1,1])

imsave(fig_file, normal_hist_bin_centers_, origin="lower")



print("[HYPERSIM: PLOT_STATS_SCENES_OBJECTS_IMAGES] Finished.")
