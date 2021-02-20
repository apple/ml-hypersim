#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import h5py
import inspect
import os
import pandas as pd

import path_utils



def load_exr_file(filename, tmp_dir):

    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

    tmp_output_file_prefix       = os.path.join(tmp_dir, "_tmp_output")
    tmp_output_header_csv_file   = os.path.join(tmp_dir, "_tmp_output.header.csv")
    tmp_output_channels_csv_file = os.path.join(tmp_dir, "_tmp_output.channels.csv")

    current_source_path        = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    generate_hdf5_from_exr_bin = os.path.abspath(os.path.join(current_source_path, "..", "..", "cpp", "bin", "generate_hdf5_from_exr"))

    cmd = \
        generate_hdf5_from_exr_bin + \
        " --input_file="  + filename               + \
        " --output_file=" + tmp_output_file_prefix + \
        " --silent"
    # print("")
    # print(cmd)
    # print("")
    retval = os.system(cmd)
    assert retval == 0

    df_header   = pd.read_csv(tmp_output_header_csv_file)
    df_channels = pd.read_csv(tmp_output_channels_csv_file)

    channels = {}

    for dfi in df_channels.itertuples():

        params       = df_channels.loc[dfi.Index].copy()
        channel_name = params["channel_name"]

        tmp_output_channel_hdf5_file = tmp_output_file_prefix + "." + channel_name + ".hdf5"

        with h5py.File(tmp_output_channel_hdf5_file, "r") as f: channel = f["dataset"][:]
        channels[channel_name] = channel

    return df_header, df_channels, channels
