# Working with per-scene camera intrinsics in Hypersim

Each Hypersim scene uses slightly different camera intrinsics for rendering. This behavior arises because some scenes use non-standard tilt-shift photography parameters in their scene definition files.

In this directory, we provide: (1) a modified perspective projection matrix for each scene that can be used as a drop-in replacement for the usual OpenGL perspective projection matrix; (2) example code demonstrating how the modified projection matrix can be used in applications; and (3) code for computing the modified projection matrix for each scene.

&nbsp;
## Obtaining the perspective projection matrix for a given scene

The `metadata_camera_parameters.csv` file contains every camera parameter for every scene obtained directly from the corresponding vrscene file. Each row in this CSV file describes a scene, and the `M_proj_00`, `M_proj_01`, ..., `M_proj_33` columns define the entries of the 4x4 perspective projection matrix for that scene, assuming that camera-space points are stored as [x,y,z,w] column-vectors. For many scenes, this matrix will be identical to the usual OpenGL perspective projection matrix. For other scenes with non-standard tilt-shift parameters, this matrix will be slightly modified to account for the tilt-shift parameters.

This [example notebook](jupyter/00_projecting_points_into_hypersim_images.ipynb) demonstrates how to use this matrix to project world-space points into a Hypersim image.

&nbsp;
## Casting rays that match a given image

The `metadata_camera_parameters.csv` file also contains `M_cam_from_uv_00`, `M_cam_from_uv_01`, ..., `M_cam_from_uv_22` columns that define a 3x3 matrix that is useful for raycasting. In particular, this matrix can be used to transform pixel coordinates into camera-space rays.

This [example notebook](jupyter/01_casting_rays_that_match_hypersim_images.ipynb) demonstrates how use this matrix to cast rays that exactly match a Hypersim image.

&nbsp;
## Rendering with PyTorch3D

This [example notebook](jupyter/02_rendering_hypersim_meshes_with_pytorch3d.ipynb) demonstrates how render Hypersim meshes with PyTorch3D, such that the rendering exactly aligns with a pre-rendered Hypersim image.

&nbsp;
## Computing camera intrinsics for each scene

The `python/dataset_generate_camera_parameters_metadata.py` script computes modified camera intrinsics for each scene. This script assumes that all the Hypersim scenes have already been exported into vrscene files, and has the same dependencies as the Hypersim High-Level Toolkit. The output from this script has been checked in, so most users will not need to execute this script, but we provide it here for reference.

```
python python/dataset_generate_camera_parameters_metadata.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --out_file metadata_camera_parameters.csv
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory.

`out_file` is the output CSV file containing all camera parameters.

&nbsp;
## Acknowledgements

We thank: Ainaz99, alex-sax, Frank-Mic, jatentaki, liuzhy71, rpautrat, and rikba for reporting this issue; liuzhy71 for helping to export camera parameters from vrscenes; rpautrat for helping to derive the intrinsics from V-Ray's camera parameters; Boris Bozhinov and Momchil Lukanov from Chaos for their excellent support with the V-Ray CameraPhysical plugin; and Georgia Gkioxari for her PyTorch3D support.


