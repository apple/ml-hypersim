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



print("[HYPERSIM: PLOT_STATS_COSTS] Begin...")



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



fig_file = os.path.join(args.plots_dir, "stats_costs.pdf")
fig = plt.figure(figsize=(9.0,3.75))
matplotlib.rcParams.update({'font.size': 14})



# TIME
# MONEY
metadata_camera_trajectories_csv_file = os.path.join(args.analysis_dir, "metadata_camera_trajectories.csv")
metadata_rendering_tasks_csv_file     = os.path.join(args.analysis_dir, "metadata_rendering_tasks.csv")

camera_trajectories = pd.read_csv(metadata_camera_trajectories_csv_file).to_records()

# rename_axis() sets the name of the current index
# reset_index() demotes the existing index to a column and creates a new unnamed index
# set_index() sets the current index 
df_rendering_tasks = pd.read_csv(metadata_rendering_tasks_csv_file).rename_axis("task_guid").reset_index().set_index(["job_name", "task_id"])

render_passes = [ "geometry", "pre", "final" ]

image_costs_dollars = []
image_times_vcpu_seconds = []
for c in camera_trajectories:

    # alternatively, could check camera_trajectory_included_in_dataset flag in metadata_rendering_tasks.csv
    scene_type = c["Scene type"]
    if scene_type == "OUTSIDE VIEWING AREA (BAD INITIALIZATION)" or scene_type == "OUTSIDE VIEWING AREA (BAD TRAJECTORY)":
        print("[HYPERSIM: PLOT_STATS_COSTS] Camera trajectory " + c["Animation"] + " is outside the viewing area, skipping...")
        continue

    print("[HYPERSIM: PLOT_STATS_COSTS] Processing camera trajectory " + c["Animation"] + "...")

    df_tasks = {}
    for r in render_passes:
        job_name = c["Rendering job (" + r + ")"]
        df_tasks[r] = df_rendering_tasks.loc[job_name]

    assert df_tasks["geometry"].shape[0] == df_tasks["pre"].shape[0] == df_tasks["final"].shape[0]
    num_tasks = df_tasks["geometry"].shape[0]

    for t in range(num_tasks):
        image_cost_dollars = 0.0
        image_time_vcpu_seconds = 0.0
        for r in render_passes:
            df_task = df_tasks[r].loc[t]
            image_cost_dollars += df_task["cost_cloud_dollars"] + df_task["cost_vray_dollars"]
            image_time_vcpu_seconds += df_task["time_vcpu_seconds"]
        image_costs_dollars.append(image_cost_dollars)
        image_times_vcpu_seconds.append(image_time_vcpu_seconds)

image_costs_dollars = array(image_costs_dollars)
image_times_vcpu_seconds = array(image_times_vcpu_seconds)

image_cost_hist_n_bins = 20
image_cost_hist_min    = 0.0
image_cost_hist_max    = 3.0

H, H_edges = histogram(image_costs_dollars, bins=image_cost_hist_n_bins, range=(image_cost_hist_min, image_cost_hist_max))

subplot(131)
hist(H_edges[:-1], H_edges, weights=H, color=tableau_colors[0])
title("Histogram of\nrendering costs\nper image")
xlabel("Cost\n(USD)\n\n(a)")
ylabel("Frequency")
xlim((0.0, 2.0))
ylim((0, 23000))

seconds_per_hour = 60*60
hours_per_second = 1.0/seconds_per_hour
image_times_vcpu_hours = image_times_vcpu_seconds*hours_per_second

image_time_hist_n_bins = 20
image_time_hist_min    = 0.0
image_time_hist_max    = 150.0

H, H_edges = histogram(image_times_vcpu_hours, bins=image_time_hist_n_bins, range=(image_time_hist_min, image_time_hist_max))

subplot(132)
hist(H_edges[:-1], H_edges, weights=H, color=tableau_colors[0])
title("Histogram of\nrendering times\nper image")
xlabel("Rendering time\n(vCPU hours)\n\n(b)")
ylabel("Frequency")
xlim((0.0, 100.0))
ylim((0, 23000))



# EFFORT
batches_dir = os.path.join(args.analysis_dir, "scene_labeling_statistics")
batch_names = [ os.path.basename(b) for b in sort(glob.glob(os.path.join(batches_dir, "*"))) ]
batch_dirs  = [ os.path.join(batches_dir, b) for b in batch_names if fnmatch.fnmatch(b, args.batch_names) ]

labeling_time_seconds = None

for b in batch_dirs:

    print("[HYPERSIM: PLOT_STATS_COSTS] Loading batch: " + b)

    metadata_labeling_time_csv_file = os.path.join(b, "metadata_scene_labeling_time.csv")
    df = pd.read_csv(metadata_labeling_time_csv_file)

    if labeling_time_seconds is None:
        labeling_time_seconds = df.loc[df["scene_included_in_dataset"] == True]["labeling_time_seconds"].to_numpy()
    else:
        labeling_time_seconds = r_[ labeling_time_seconds, df.loc[df["scene_included_in_dataset"] == True]["labeling_time_seconds"].to_numpy() ]

labeling_time_minutes     = labeling_time_seconds / 60.0
labeling_time_hist_n_bins = 20
labeling_time_hist_min    = 0.0
labeling_time_hist_max    = 180.0

print("[HYPERSIM: PLOT_STATS_COSTS] Total scene labeling time (minutes) = " + str(sum(labeling_time_minutes)))

H, H_edges = histogram(labeling_time_minutes, bins=labeling_time_hist_n_bins, range=(labeling_time_hist_min, labeling_time_hist_max))

subplot(133)
hist(H_edges[:-1], H_edges, weights=H, color=tableau_colors[0])
title("Histogram of\nannotation times\nper scene")
xlabel("Time\n(minutes)\n\n(c)")
ylabel("Frequency")
xlim((labeling_time_hist_min, labeling_time_hist_max))
xticks([0,60,120])



fig.tight_layout()
savefig(fig_file)



print("[HYPERSIM: PLOT_STATS_COSTS] Finished.")
