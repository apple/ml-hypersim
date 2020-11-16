#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import pandas as pd
import os
import time
import vray

import path_utils

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_file", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_file)



print("[HYPERSIM: GENERATE_SCENE_METADATA_FROM_VRSCENE] Begin...")



output_dir = os.path.dirname(args.out_file)
if output_dir == "":
    output_dir = "."

if not os.path.exists(output_dir): os.makedirs(output_dir)



renderer = vray.VRayRenderer()
def log_msg(renderer, message, level, instant):
    print(str(instant) + " " + str(level) + " " + message)
renderer.setOnLogMessage(log_msg)
renderer.load(args.in_file)
time.sleep(0.5)



# SettingsUnitsInfo
settings_units_info   = renderer.classes.SettingsUnitsInfo.getInstances()[0]
meters_per_asset_unit = settings_units_info.meters_scale

df = pd.DataFrame(columns=["parameter_name", "parameter_value"], data={"parameter_name": ["meters_per_asset_unit"], "parameter_value": [meters_per_asset_unit]})
df.to_csv(args.out_file, index=False)

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: GENERATE_SCENE_METADATA_FROM_VRSCENE] Finished.")
