#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
args = parser.parse_args()



print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Begin...")



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
        print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Camera trajectory " + c["Animation"] + " is outside the viewing area, skipping...")
        continue

    print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Processing camera trajectory " + c["Animation"] + "...")

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

image_cost_hist_n_bins = 100
image_cost_hist_min    = 0.0
image_cost_hist_max    = 5.0

H, H_edges = histogram(image_costs_dollars, bins=image_cost_hist_n_bins, range=(image_cost_hist_min, image_cost_hist_max))

hist(H_edges[:-1], H_edges, weights=H)
# xscale("log")
title("Distribution of rendering costs per image (dollars)")
xlabel("Rendering cost per image (dollars)")
ylabel("Frequency")
show()

seconds_per_hour = 60*60
hours_per_second = 1.0/seconds_per_hour
image_times_vcpu_hours = image_times_vcpu_seconds*hours_per_second

image_time_hist_n_bins = 100
image_time_hist_min    = 0.0
image_time_hist_max    = 200.0

H, H_edges = histogram(image_times_vcpu_hours, bins=image_time_hist_n_bins, range=(image_time_hist_min, image_time_hist_max))

hist(H_edges[:-1], H_edges, weights=H)
# xscale("log")
title("Distribution of rendering times per image (vCPU hours)")
xlabel("Rendering time per image (vCPU hours)")
ylabel("Frequency")
show()

print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Mean rendering cost (dollars): %0.4f" % (sum(image_costs_dollars)/image_costs_dollars.shape[0]))
print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Mean rendering time (vCPU hours): %0.4f" % (sum(image_times_vcpu_hours)/image_times_vcpu_hours.shape[0]))
print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Total rendering cost (dollars) = %0.4f" % sum(image_costs_dollars))
print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Total rendering times (vCPU hours) = %0.4f" % sum(image_times_vcpu_hours))



print("[HYPERSIM: VISUALIZE_RENDERING_JOBS_STATISTICS] Finished.")
