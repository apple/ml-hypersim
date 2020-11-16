#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import h5py
import pandas as pd
import sklearn.preprocessing

print("Begin...")

# parameters
reconstruction_roi_min = array([ -8000.0, -8000.0, 0.0 ])
reconstruction_roi_max = array([  8000.0,  8000.0, 0.0 ])

camera_roi_min = reconstruction_roi_min + array([ -9000.0,  -9000.0,     0.0 ])
camera_roi_max = reconstruction_roi_max + array([  9000.0,   9000.0, 20000.0 ])

num_keyframes = 20

camera_frame_time_seconds = 1.0

# output
camera_keyframe_frame_indices_hdf5_file = "camera_keyframe_frame_indices.hdf5"
camera_keyframe_positions_hdf5_file     = "camera_keyframe_positions.hdf5"
camera_keyframe_orientations_hdf5_file  = "camera_keyframe_orientations.hdf5"
metadata_camera_csv_file                = "metadata_camera.csv"

#
# Compute camera keyframe positions and orientations.
#

# Specify a keyframe at every frame.
camera_keyframe_frame_indices = arange(num_keyframes)

camera_lookat_pos      = (reconstruction_roi_max + reconstruction_roi_min) / 2.0
camera_roi_extent      = camera_roi_max - camera_roi_min
camera_roi_half_extent = camera_roi_extent / 2.0
camera_roi_center      = (camera_roi_min + camera_roi_max) / 2.0

# The convention here is that positive z in world-space is up.
theta = linspace(0,2*np.pi,num_keyframes)
camera_keyframe_positions = c_[ cos(theta)*camera_roi_half_extent[0] + camera_roi_center[0],
                                sin(theta)*camera_roi_half_extent[1] + camera_roi_center[1],
                                ones_like(theta)*camera_roi_max[2] ]

camera_keyframe_orientations = zeros((num_keyframes,3,3))

for i in range(num_keyframes):

    # The convention here is that positive z in world-space is up.
    camera_position     = camera_keyframe_positions[i]
    camera_lookat_dir   = sklearn.preprocessing.normalize(array([camera_lookat_pos - camera_position]))[0]
    camera_up_axis_hint = array([0.0,0.0,1.0])

    # The convention here is that the camera's positive x axis points right, the positive y
    # axis points up, and the positive z axis points away from where the camera is looking.
    camera_z_axis = -sklearn.preprocessing.normalize(array([camera_lookat_dir]))
    camera_x_axis = -sklearn.preprocessing.normalize(cross(camera_z_axis, camera_up_axis_hint))
    camera_y_axis = sklearn.preprocessing.normalize(cross(camera_z_axis, camera_x_axis))

    R_world_from_cam = c_[ matrix(camera_x_axis).T, matrix(camera_y_axis).T, matrix(camera_z_axis).T ]

    camera_keyframe_orientations[i] = R_world_from_cam

with h5py.File(camera_keyframe_frame_indices_hdf5_file, "w") as f: f.create_dataset("dataset", data=camera_keyframe_frame_indices)
with h5py.File(camera_keyframe_positions_hdf5_file,     "w") as f: f.create_dataset("dataset", data=camera_keyframe_positions)
with h5py.File(camera_keyframe_orientations_hdf5_file,  "w") as f: f.create_dataset("dataset", data=camera_keyframe_orientations)

df = pd.DataFrame(columns=["parameter_name", "parameter_value"], data={"parameter_name": ["frame_time_seconds"], "parameter_value": [camera_frame_time_seconds]})
df.to_csv(metadata_camera_csv_file, index=False)

print("Finished.")
