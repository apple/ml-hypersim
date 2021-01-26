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
import mpl_toolkits.axes_grid1
import os
import pandas as pd

import path_utils
path_utils.add_path_to_sys_path("../lib", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import mayavi_utils

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
parser.add_argument("--batch_names", required=True)
parser.add_argument("--plots_dir", required=True)
args = parser.parse_args()



print("[HYPERSIM: PLOT_STATS_COLOR] Begin...")



#
# NOTE: all parameters below must match hypersim/code/python/analysis/dataset_generate_image_statistics.py
#

# # RGB COLOR
# # DIFFUSE ILLUMINATION
# # NON-DIFFUSE RESIDUAL
# color_hist_denorm_n_bins    = 20
# color_hist_denorm_min       = 0.0
# color_hist_denorm_max       = 2.0
# color_hist_denorm_bin_edges = linspace(color_hist_denorm_min, color_hist_denorm_max, color_hist_denorm_n_bins+1)

# # DIFFUSE REFLECTANCE
# color_hist_norm_n_bins    = 10
# color_hist_norm_min       = 0.0
# color_hist_norm_max       = 1.0
# color_hist_norm_bin_edges = linspace(color_hist_norm_min, color_hist_norm_max, color_hist_norm_n_bins+1)

# RGB COLOR
# DIFFUSE ILLUMINATION
# NON-DIFFUSE RESIDUAL
# DIFFUSE REFLECTANCE
hue_saturation_hist_n_bins    = 100
hue_saturation_hist_min       = -1
hue_saturation_hist_max       = 1
hue_saturation_hist_bin_edges = linspace(hue_saturation_hist_min, hue_saturation_hist_max, hue_saturation_hist_n_bins+1)

brightness_hist_log_n_bins    = 1000
brightness_hist_log_base      = 10.0
brightness_hist_log_min       = -3.0 # 0.001
brightness_hist_log_max       = 1.0  # 10.0
brightness_hist_log_bin_edges = logspace(brightness_hist_log_min, brightness_hist_log_max, brightness_hist_log_n_bins+1, base=brightness_hist_log_base)

#
# derived parameters used for visualization
#

# # RGB COLOR
# # DIFFUSE ILLUMINATION
# # NON-DIFFUSE RESIDUAL
# color_hist_denorm_bin_centers_x_1d = color_hist_denorm_bin_edges[:-1] + diff(color_hist_denorm_bin_edges)/2.0
# color_hist_denorm_bin_centers_y_1d = color_hist_denorm_bin_edges[:-1] + diff(color_hist_denorm_bin_edges)/2.0
# color_hist_denorm_bin_centers_z_1d = color_hist_denorm_bin_edges[:-1] + diff(color_hist_denorm_bin_edges)/2.0

# color_hist_denorm_bin_centers_Z, color_hist_denorm_bin_centers_Y, color_hist_denorm_bin_centers_X = \
#     meshgrid(color_hist_denorm_bin_centers_x_1d, color_hist_denorm_bin_centers_y_1d, color_hist_denorm_bin_centers_z_1d, indexing="ij")

# color_hist_denorm_bin_centers_1d = c_[ color_hist_denorm_bin_centers_X.ravel(), color_hist_denorm_bin_centers_Y.ravel(), color_hist_denorm_bin_centers_Z.ravel() ]

# # DIFFUSE REFLECTANCE
# color_hist_norm_bin_centers_x_1d = color_hist_norm_bin_edges[:-1] + diff(color_hist_norm_bin_edges)/2.0
# color_hist_norm_bin_centers_y_1d = color_hist_norm_bin_edges[:-1] + diff(color_hist_norm_bin_edges)/2.0
# color_hist_norm_bin_centers_z_1d = color_hist_norm_bin_edges[:-1] + diff(color_hist_norm_bin_edges)/2.0

# color_hist_norm_bin_centers_Z, color_hist_norm_bin_centers_Y, color_hist_norm_bin_centers_X = \
#     meshgrid(color_hist_norm_bin_centers_x_1d, color_hist_norm_bin_centers_y_1d, color_hist_norm_bin_centers_z_1d, indexing="ij")

# color_hist_norm_bin_centers_1d = c_[ color_hist_norm_bin_centers_X.ravel(), color_hist_norm_bin_centers_Y.ravel(), color_hist_norm_bin_centers_Z.ravel() ]

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

rgb_color_hist                              = None
rgb_color_hue_saturation_hist               = None
rgb_color_brightness_hist_log               = None
diffuse_illumination_hist                   = None
diffuse_illumination_hue_saturation_hist    = None
diffuse_illumination_brightness_hist_log    = None
diffuse_reflectance_hist                    = None
diffuse_reflectance_hue_saturation_hist     = None
diffuse_reflectance_brightness_hist_log     = None
residual_hist                               = None
residual_hue_saturation_hist                = None
residual_brightness_hist_log                = None

for b in batch_dirs:

    print("[HYPERSIM: PLOT_STATS_COLOR] Loading batch: " + b)

    rgb_color_hist_hdf5_file                           = os.path.join(b, "metadata_rgb_color_hist.hdf5")
    rgb_color_hue_saturation_hist_hdf5_file            = os.path.join(b, "metadata_rgb_color_hue_saturation_hist.hdf5")
    rgb_color_brightness_hist_log_hdf5_file            = os.path.join(b, "metadata_rgb_color_brightness_hist_log.hdf5")
    diffuse_illumination_hist_hdf5_file                = os.path.join(b, "metadata_diffuse_illumination_hist.hdf5")
    diffuse_illumination_hue_saturation_hist_hdf5_file = os.path.join(b, "metadata_diffuse_illumination_hue_saturation_hist.hdf5")
    diffuse_illumination_brightness_hist_log_hdf5_file = os.path.join(b, "metadata_diffuse_illumination_brightness_hist_log.hdf5")
    diffuse_reflectance_hist_hdf5_file                 = os.path.join(b, "metadata_diffuse_reflectance_hist.hdf5")
    diffuse_reflectance_hue_saturation_hist_hdf5_file  = os.path.join(b, "metadata_diffuse_reflectance_hue_saturation_hist.hdf5")
    diffuse_reflectance_brightness_hist_log_hdf5_file  = os.path.join(b, "metadata_diffuse_reflectance_brightness_hist_log.hdf5")
    residual_hist_hdf5_file                            = os.path.join(b, "metadata_residual_hist.hdf5")
    residual_hue_saturation_hist_hdf5_file             = os.path.join(b, "metadata_residual_hue_saturation_hist.hdf5")
    residual_brightness_hist_log_hdf5_file             = os.path.join(b, "metadata_residual_brightness_hist_log.hdf5")

    with h5py.File(rgb_color_hist_hdf5_file,                           "r") as f: rgb_color_hist_                           = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_hue_saturation_hist_hdf5_file,            "r") as f: rgb_color_hue_saturation_hist_            = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_brightness_hist_log_hdf5_file,            "r") as f: rgb_color_brightness_hist_log_            = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_hist_hdf5_file,                "r") as f: diffuse_illumination_hist_                = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_hue_saturation_hist_hdf5_file, "r") as f: diffuse_illumination_hue_saturation_hist_ = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_brightness_hist_log_hdf5_file, "r") as f: diffuse_illumination_brightness_hist_log_ = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_hist_hdf5_file,                 "r") as f: diffuse_reflectance_hist_                 = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_hue_saturation_hist_hdf5_file,  "r") as f: diffuse_reflectance_hue_saturation_hist_  = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_brightness_hist_log_hdf5_file,  "r") as f: diffuse_reflectance_brightness_hist_log_  = f["dataset"][:].astype(int64)
    with h5py.File(residual_hist_hdf5_file,                            "r") as f: residual_hist_                            = f["dataset"][:].astype(int64)
    with h5py.File(residual_hue_saturation_hist_hdf5_file,             "r") as f: residual_hue_saturation_hist_             = f["dataset"][:].astype(int64)
    with h5py.File(residual_brightness_hist_log_hdf5_file,             "r") as f: residual_brightness_hist_log_             = f["dataset"][:].astype(int64)

    rgb_color_hist                           = rgb_color_hist_                           if rgb_color_hist                           is None else rgb_color_hist                           + rgb_color_hist_
    rgb_color_hue_saturation_hist            = rgb_color_hue_saturation_hist_            if rgb_color_hue_saturation_hist            is None else rgb_color_hue_saturation_hist            + rgb_color_hue_saturation_hist_
    rgb_color_brightness_hist_log            = rgb_color_brightness_hist_log_            if rgb_color_brightness_hist_log            is None else rgb_color_brightness_hist_log            + rgb_color_brightness_hist_log_
    diffuse_illumination_hist                = diffuse_illumination_hist_                if diffuse_illumination_hist                is None else diffuse_illumination_hist                + diffuse_illumination_hist_
    diffuse_illumination_hue_saturation_hist = diffuse_illumination_hue_saturation_hist_ if diffuse_illumination_hue_saturation_hist is None else diffuse_illumination_hue_saturation_hist + diffuse_illumination_hue_saturation_hist_
    diffuse_illumination_brightness_hist_log = diffuse_illumination_brightness_hist_log_ if diffuse_illumination_brightness_hist_log is None else diffuse_illumination_brightness_hist_log + diffuse_illumination_brightness_hist_log_
    diffuse_reflectance_hist                 = diffuse_reflectance_hist_                 if diffuse_reflectance_hist                 is None else diffuse_reflectance_hist                 + diffuse_reflectance_hist_
    diffuse_reflectance_hue_saturation_hist  = diffuse_reflectance_hue_saturation_hist_  if diffuse_reflectance_hue_saturation_hist  is None else diffuse_reflectance_hue_saturation_hist  + diffuse_reflectance_hue_saturation_hist_
    diffuse_reflectance_brightness_hist_log  = diffuse_reflectance_brightness_hist_log_  if diffuse_reflectance_brightness_hist_log  is None else diffuse_reflectance_brightness_hist_log  + diffuse_reflectance_brightness_hist_log_
    residual_hist                            = residual_hist_                            if residual_hist                            is None else residual_hist                            + residual_hist_
    residual_hue_saturation_hist             = residual_hue_saturation_hist_             if residual_hue_saturation_hist             is None else residual_hue_saturation_hist             + residual_hue_saturation_hist_
    residual_brightness_hist_log             = residual_brightness_hist_log_             if residual_brightness_hist_log             is None else residual_brightness_hist_log             + residual_brightness_hist_log_



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



fig_file = os.path.join(args.plots_dir, "stats_color_hue_saturation.pdf")
fig = plt.figure(figsize=(9.0, 2.5))
matplotlib.rcParams.update({'font.size': 14})

# fig.suptitle("Hue-saturation distributions")
grid = mpl_toolkits.axes_grid1.ImageGrid(fig, 111, nrows_ncols=(1,5), axes_pad=0.05, share_all=True, cbar_location="right", cbar_mode="single", cbar_size="7%", cbar_pad=0.2)

vmin  = -20.0
vmax  = -4.0
ticks = [-4.0, -12.0, -20.0]



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
hue_saturation_hist_rgb[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = array([1,1,1])

ax = grid[0]
im = ax.imshow(hue_saturation_hist_rgb, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest")
ax.set_title("Hue-saturation\ncolor wheel")
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
# hue_saturation_hist_rgb = hue_saturation_hist_rgb[::-1]
# imsave(os.path.join(args.plots_dir, "stats_color_2d_hsv_wheel.png"), hue_saturation_hist_rgb)



# RGB COLOR
H      = rgb_color_hue_saturation_hist
H_     = H.astype(float64) / H.sum()
eps    = 1e-9 # small value to avoid log(0)
log_H  = log(H_ + eps)
log_H_ = log_H.copy()
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan

ax = grid[1]
im = ax.imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest", vmin=vmin, vmax=vmax)
ax.cax.colorbar(im, ticks=ticks)
ax.set_title("Final\ncolor")
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
# normalize_ = matplotlib.colors.Normalize(vmin=-20.0, vmax=-2.0)
# log_H_rgb = matplotlib.cm.viridis(normalize_(log_H_))
# log_H_rgb[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = array([1.0,1.0,1.0,1.0])
# log_H_rgb = log_H_rgb[::-1]
# imsave(os.path.join(args.plots_dir, "stats_color_2d_rgb.png"), log_H_rgb)



# DIFFUSE REFLECTANCE
H      = diffuse_reflectance_hue_saturation_hist
H_     = H.astype(float64) / H.sum()
eps    = 1e-9 # small value to avoid log(0)
log_H  = log(H_ + eps)
log_H_ = log_H.copy()
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan

ax = grid[2]
im = ax.imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest", vmin=vmin, vmax=vmax)
ax.cax.colorbar(im, ticks=ticks)
ax.set_title("Diffuse\nreflectance")
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
# normalize_ = matplotlib.colors.Normalize(vmin=-20.0, vmax=-2.0)
# log_H_rgb = matplotlib.cm.viridis(normalize_(log_H_))
# log_H_rgb[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = array([1.0,1.0,1.0,1.0])
# log_H_rgb = log_H_rgb[::-1]
# imsave(os.path.join(args.plots_dir, "stats_color_2d_diffuse_reflectance.png"), log_H_rgb)



# DIFFUSE ILLUMINATION
H      = diffuse_illumination_hue_saturation_hist
H_     = H.astype(float64) / H.sum()
eps    = 1e-9 # small value to avoid log(0)
log_H  = log(H_ + eps)
log_H_ = log_H.copy()
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan

ax = grid[3]
im = ax.imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest", vmin=vmin, vmax=vmax)
ax.cax.colorbar(im, ticks=ticks)
ax.set_title("Diffuse\nillumination")
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
# normalize_ = matplotlib.colors.Normalize(vmin=-20.0, vmax=-2.0)
# log_H_rgb = matplotlib.cm.viridis(normalize_(log_H_))
# log_H_rgb[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = array([1.0,1.0,1.0,1.0])
# log_H_rgb = log_H_rgb[::-1]
# imsave(os.path.join(args.plots_dir, "stats_color_2d_diffuse_illumination.png"), log_H_rgb)



# NON-DIFFUSE RESIDUAL
H      = residual_hue_saturation_hist
H_     = H.astype(float64) / H.sum()
eps    = 1e-9 # small value to avoid log(0)
log_H  = log(H_ + eps)
log_H_ = log_H.copy()
log_H[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = nan

ax = grid[4]
im = ax.imshow(log_H, origin="lower", extent=[-1,1,-1,1], aspect="equal", interpolation="nearest", vmin=vmin, vmax=vmax)
ax.cax.colorbar(im, ticks=ticks)
ax.set_title("Non-diffuse\nresidual")
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
# normalize_ = matplotlib.colors.Normalize(vmin=-20.0, vmax=-2.0)
# log_H_rgb = matplotlib.cm.viridis(normalize_(log_H_))
# log_H_rgb[hue_saturation_hist_bin_corners_abs_min_invalid_mask] = array([1.0,1.0,1.0,1.0])
# log_H_rgb = log_H_rgb[::-1]
# imsave(os.path.join(args.plots_dir, "stats_color_2d_residual.png"), log_H_rgb)

fig.tight_layout(rect=(0.0,0,0.95,0.95))
savefig(fig_file)



fig_file = os.path.join(args.plots_dir, "stats_color_brightness.pdf")
fig = plt.figure(figsize=(9.0,2.85))
matplotlib.rcParams.update({'font.size': 14})

# fig.suptitle("Brightness distributions")
# grid = mpl_toolkits.axes_grid1.ImageGrid(fig, 111, nrows_ncols=(1,4), axes_pad=0.05, share_all=True)



# RGB COLOR

# redefine number of bins and bin edges for visualization
brightness_hist_log_n_bins_    = int(brightness_hist_log_n_bins/25)
brightness_hist_log_bin_edges_ = logspace(brightness_hist_log_min, brightness_hist_log_max, brightness_hist_log_n_bins_+1, base=brightness_hist_log_base)

H = rgb_color_brightness_hist_log
H_ = H/float(sum(H))

subplot(141)
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges_, weights=H_, color=tableau_colors[0])
xscale("log")
title("Final\ncolor")
xlabel("Brightness\n(unitless)")
ylabel("Probability")
xlim((1e-3, 1e1))
ylim((0, 0.2))

# DIFFUSE REFLECTANCE

# redefine number of bins and bin edges for visualization
brightness_hist_log_n_bins_    = int(brightness_hist_log_n_bins/25)
brightness_hist_log_bin_edges_ = logspace(brightness_hist_log_min, brightness_hist_log_max, brightness_hist_log_n_bins_+1, base=brightness_hist_log_base)

H = diffuse_reflectance_brightness_hist_log
H_ = H/float(sum(H))

subplot(142)
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges_, weights=H_, color=tableau_colors[0])
xscale("log")
title("Diffuse\nreflectance")
xlabel("Brightness\n(unitless)")
xlim((1e-3, 1e1))
ylim((0, 0.2))
setp(gca().get_yticklabels(), visible=False)

# DIFFUSE ILLUMINATION

# redefine number of bins and bin edges for visualization
brightness_hist_log_n_bins_    = int(brightness_hist_log_n_bins/25)
brightness_hist_log_bin_edges_ = logspace(brightness_hist_log_min, brightness_hist_log_max, brightness_hist_log_n_bins_+1, base=brightness_hist_log_base)

H = diffuse_illumination_brightness_hist_log
H_ = H/float(sum(H))

subplot(143)
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges_, weights=H_, color=tableau_colors[0])
xscale("log")
title("Diffuse\nillumination")
xlabel("Brightness\n(unitless)")
xlim((1e-3, 1e1))
ylim((0, 0.2))
setp(gca().get_yticklabels(), visible=False)

# RESIDUAL

# redefine number of bins and bin edges for visualization
brightness_hist_log_n_bins_    = int(brightness_hist_log_n_bins/25)
brightness_hist_log_bin_edges_ = logspace(brightness_hist_log_min, brightness_hist_log_max, brightness_hist_log_n_bins_+1, base=brightness_hist_log_base)

H = residual_brightness_hist_log
H_ = H/float(sum(H))

subplot(144)
hist(brightness_hist_log_bin_edges[:-1], brightness_hist_log_bin_edges_, weights=H_, color=tableau_colors[0])
xscale("log")
title("Non-diffuse\nresidual")
xlabel("Brightness\n(unitless)")
xlim((1e-3, 1e1))
ylim((0, 0.2))
setp(gca().get_yticklabels(), visible=False)



fig.tight_layout(rect=(0.0,0,1.0,1.0))
savefig(fig_file)



# size       = (1100, 1000)
# azimuth    = 340
# elevation  = 90
# roll       = 270
# distance   = 3.0
# focalpoint = [0.5, 0.575, 0.475]

# # RGB COLOR
# H             = rgb_color_hist.astype(float64)
# H             = sqrt(H)
# H_norm        = H / H.sum()
# H_norm_1d     = H_norm.ravel()
# eps           = 1.0 # small value to avoid log(0)
# log_H         = log(H + eps)
# log_H_norm    = log_H / log_H.sum()
# log_H_norm_1d = log_H_norm.ravel()
# # k             = 10.0 # size multiplier
# # sizes         = k*log_H_norm_1d
# k             = 10.0 # size multiplier
# sizes         = k*H_norm_1d
# mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=size)
# mayavi_utils.points3d_color_by_rgb_value(color_hist_denorm_bin_centers_1d, colors=clip(color_hist_denorm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
# mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
# mayavi.mlab.axes()
# mayavi.mlab.xlabel("R")
# mayavi.mlab.ylabel("G")
# mayavi.mlab.zlabel("B")
# mayavi.mlab.view(azimuth=azimuth, elevation=elevation, roll=roll, distance=distance, focalpoint=focalpoint, reset_roll=False)
# mayavi.mlab.savefig(os.path.join(args.plots_dir, "stats_color_rgb.png"))

# # DIFFUSE ILLUMINATION
# H             = diffuse_illumination_hist.astype(float64)
# H             = sqrt(H)
# H_norm        = H / H.sum()
# H_norm_1d     = H_norm.ravel()
# eps           = 1.0 # small value to avoid log(0)
# log_H         = log(H + eps)
# log_H_norm    = log_H / log_H.sum()
# log_H_norm_1d = log_H_norm.ravel()
# # k             = 10.0 # size multiplier
# # sizes         = k*log_H_norm_1d
# k             = 10.0 # size multiplier
# sizes         = k*H_norm_1d
# mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=size)
# mayavi_utils.points3d_color_by_rgb_value(color_hist_denorm_bin_centers_1d, colors=clip(color_hist_denorm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
# mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
# mayavi.mlab.axes()
# mayavi.mlab.xlabel("R")
# mayavi.mlab.ylabel("G")
# mayavi.mlab.zlabel("B")
# mayavi.mlab.view(azimuth=azimuth, elevation=elevation, roll=roll, distance=distance, focalpoint=focalpoint, reset_roll=False)
# mayavi.mlab.savefig(os.path.join(args.plots_dir, "stats_color_illumination.png"))

# # NON-DIFFUSE RESIDUAL
# H             = residual_hist.astype(float64)
# H             = sqrt(H)
# H_norm        = H / H.sum()
# H_norm_1d     = H_norm.ravel()
# eps           = 1.0 # small value to avoid log(0)
# log_H         = log(H + eps)
# log_H_norm    = log_H / log_H.sum()
# log_H_norm_1d = log_H_norm.ravel()
# # k             = 10.0 # size multiplier
# # sizes         = k*log_H_norm_1d
# k             = 10.0 # size multiplier
# sizes         = k*H_norm_1d
# mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=size)
# mayavi_utils.points3d_color_by_rgb_value(color_hist_denorm_bin_centers_1d, colors=clip(color_hist_denorm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
# mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
# mayavi.mlab.axes()
# mayavi.mlab.xlabel("R")
# mayavi.mlab.ylabel("G")
# mayavi.mlab.zlabel("B")
# mayavi.mlab.view(azimuth=azimuth, elevation=elevation, roll=roll, distance=distance, focalpoint=focalpoint, reset_roll=False)
# mayavi.mlab.savefig(os.path.join(args.plots_dir, "stats_color_residual.png"))

# # DIFFUSE REFLECTANCE
# H             = diffuse_reflectance_hist.astype(float64)
# H             = sqrt(H)
# H_norm        = H / H.sum()
# H_norm_1d     = H_norm.ravel()
# eps           = 1.0 # small value to avoid log(0)
# log_H         = log(H + eps)
# log_H_norm    = log_H / log_H.sum()
# log_H_norm_1d = log_H_norm.ravel()
# # k             = 10.0 # size multiplier
# # sizes         = k*log_H_norm_1d
# k             = 10.0 # size multiplier
# sizes         = k*H_norm_1d
# mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=size)
# mayavi_utils.points3d_color_by_rgb_value(color_hist_norm_bin_centers_1d, colors=clip(color_hist_norm_bin_centers_1d,0,1), sizes=sizes, scale_factor=1.0)
# mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
# mayavi.mlab.axes()
# mayavi.mlab.xlabel("R")
# mayavi.mlab.ylabel("G")
# mayavi.mlab.zlabel("B")
# mayavi.mlab.view(azimuth=azimuth, elevation=elevation, roll=roll, distance=distance, focalpoint=focalpoint, reset_roll=False)
# mayavi.mlab.savefig(os.path.join(args.plots_dir, "stats_color_reflectance.png"))



print("[HYPERSIM: PLOT_STATS_COLOR] Finished.")
