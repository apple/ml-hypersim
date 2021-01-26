#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import glob
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
parser.add_argument("--batch_names", required=True)
args = parser.parse_args()



print("[HYPERSIM: VISUALIZE_SCENE_LABELING_STATISTICS] Begin...")



batches_dir = os.path.join(args.analysis_dir, "scene_labeling_statistics")
batch_names = [ os.path.basename(b) for b in sort(glob.glob(os.path.join(batches_dir, "*"))) ]
batch_dirs  = [ os.path.join(batches_dir, b) for b in batch_names if fnmatch.fnmatch(b, args.batch_names) ]

labeling_time_seconds = None

for b in batch_dirs:

    print("[HYPERSIM: VISUALIZE_SCENE_LABELING_STATISTICS] Loading batch: " + b)

    metadata_labeling_time_csv_file = os.path.join(b, "metadata_scene_labeling_time.csv")
    df = pd.read_csv(metadata_labeling_time_csv_file)

    if labeling_time_seconds is None:
        labeling_time_seconds = df[df["scene_included_in_dataset"]]["labeling_time_seconds"].to_numpy()
    else:
        labeling_time_seconds = r_[ labeling_time_seconds, df[df["scene_included_in_dataset"]]["labeling_time_seconds"].to_numpy() ]



labeling_time_minutes     = labeling_time_seconds / 60.0
labeling_time_hist_n_bins = 48 # bin width == 5 minutes
labeling_time_hist_min    = 0.0
labeling_time_hist_max    = 240.0

print("[HYPERSIM: VISUALIZE_SCENE_LABELING_STATISTICS] Mean scene labeling time (minutes) = %0.4f" % (sum(labeling_time_minutes)/labeling_time_minutes.shape[0]))
print("[HYPERSIM: VISUALIZE_SCENE_LABELING_STATISTICS] Total scene labeling time (minutes) = %0.4f" % sum(labeling_time_minutes))

H, H_edges = histogram(labeling_time_minutes, bins=labeling_time_hist_n_bins, range=(labeling_time_hist_min, labeling_time_hist_max))

hist(H_edges[:-1], H_edges, weights=H)
title("Distribution of labeling times (minutes)")
xlabel("Labeling time (minutes)")
ylabel("Frequency")
show()



print("[HYPERSIM: VISUALIZE_SCENE_LABELING_STATISTICS] Finished.")
