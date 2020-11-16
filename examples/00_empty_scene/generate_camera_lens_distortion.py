#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import h5py

print("Begin...")

# parameters
fov_x = 45.0 * np.pi / 180.0

width_pixels  = 1024
height_pixels = 768

width_texels  = 2*width_pixels + 1
height_texels = 2*height_pixels + 1

# output
camera_lens_distortion_hdf5_file = "camera_lens_distortion.hdf5"

# Generate rays in camera space. The convention here is that the camera's positive x
# axis points right, the positive y axis points up, and the positive z axis points
# away from where the camera is looking.
fov_y = 2.0 * arctan((height_texels-1) * tan(fov_x/2) / (width_texels-1))

uv_min = -1.0
uv_max = 1.0

u, v = meshgrid(linspace(uv_min, uv_max, width_texels), linspace(uv_min, uv_max, height_texels)[::-1])

rays_cam_x = u*tan(fov_x/2.0)
rays_cam_y = v*tan(fov_y/2.0)
rays_cam_z = -ones_like(rays_cam_x)

rays_cam = dstack((rays_cam_x,rays_cam_y,rays_cam_z))

with h5py.File(camera_lens_distortion_hdf5_file, "w") as f: f.create_dataset("dataset", data=rays_cam)

print("Finished.")
