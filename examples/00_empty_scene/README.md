In this tutorial example, we use the _Hypersim Low-Level Toolkit_ to add a camera trajectory and a collection of textured quads to a V-Ray scene.

&nbsp;
## Downloading AprilTag images
In this tutorial example, we will be using AprilTag images, which are available [here](https://github.com/AprilRobotics/apriltag-imgs/tree/master/tag36h11).

_You need to create a `00_empty_scene/data` directory, and manually download the `tag36h11` AprilTag images into it, before you can proceed through this tutorial example._

&nbsp;
## Quick start

To complete this tutorial example, we execute the following command-line tools. See below for additional details on each tool.

_In this example, we will be rendering with a custom lens distortion model, and therefore we need the OpenCV Python bindings with OpenEXR support enabled. If you don't have the OpenCV Python bindings, or you have them but OpenEXR support is not enabled, you can omit the `camera_lens_distortion_file`, `shared_asset_dir`, `platform_when_rendering`, and `shared_asset_dir_when_rendering` parameters when executing `modify_vrscene_add_camera.py` and proceed through the rest of the tutorial example._

```
# render the scene before making any modifications
vray -sceneFile="empty.vrscene" -imgFile="empty.jpg"

# generate a camera trajectory
python generate_camera_trajectory.py

# generate a custom lens distortion model
python generate_camera_lens_distortion.py

# add camera trajectory and lens distortion model to the vrscene
python ../../code/python/tools/modify_vrscene_add_camera.py --in_file empty.vrscene --out_file empty_cam.vrscene --vray_user_params_dir . --camera_trajectory_dir . --camera_lens_distortion_file camera_lens_distortion.hdf5 --shared_asset_dir data --platform_when_rendering mac --shared_asset_dir_when_rendering data

# render the scene from the new camera trajectory and lens distortion function
vray -sceneFile="empty_cam.vrscene" -imgFile="empty_cam.jpg" -frames=0

# generate textured quads in their own vrscene
python generate_vrscene_textured_quads.py --in_file quads_params.csv --shared_asset_dir data --platform_when_rendering mac --shared_asset_dir_when_rendering data

# include the textured quads in the top-level vrscene
python modify_vrscene_include_files.py --in_file empty_cam.vrscene --out_file empty_cam_quads.vrscene --include_files "data/*.vrscene" --shared_asset_dir data --platform_when_rendering mac --shared_asset_dir_when_rendering data

# render the scene with textured quads
vray -sceneFile="empty_cam_quads.vrscene" -imgFile="empty_cam_quads.jpg" -frames=0
```

&nbsp;
## Rendering a preliminary image

Before manipulating our vrscene, we render it to get a sense of what it looks like.

```
vray -sceneFile="empty.vrscene" -imgFile="empty.jpg"
```

See `00_empty_scene/_empty.jpg` for what the rendered image should look like.

&nbsp;
## Generating a camera trajectory

A typical use case of the Hypersim Toolkit is to facilitate rendering with programmatically generated camera trajectories. In this step, we generate our own camera trajectory. In a subsequent processing step, we will add our camera trajectory to the vrscene. We execute the following simple example script to generate our camera trajectory.

```
python generate_camera_trajectory.py
```

This script generates an orbit camera trajectory around the origin.

A Hypersim camera trajectory consists of 4 files.

`camera_keyframe_positions.hdf5` contains an Nx3 array of camera positions, where N is the number of camera keyframes, and each position is stored in [x,y,z] order.

`camera_keyframe_orientations.hdf5` contains an Nx3x3 array of camera orientations, where N is the number of camera keyframes, and each orientation is represented as a 3x3 rotation matrix that maps points to world-space from camera-space, assuming that points are stored as [x,y,z] column vectors. The convention in the Hypersim Toolkit is that the camera's positive x-axis points right, the positive y axis points up, and the positive z axis points away from where the camera is looking.

`camera_keyframe_frame_indices.hdf5` contains an array of length N, where N is the number of camera keyframes. The Hypersim Toolkit allows users to specify camera keyframes in a sparse way, such that there can be more frames in a sequence of rendered images than there are keyframes. For example, you could specify keyframes at frames 0, 10, and 100. In this case, you would specify 3 different camera poses, and specify keyframe frame indicies of [0,10,100]. Camera poses are interpolated internally by V-Ray at all in-between frames.

`metadata_camera.csv` specifies the desired amount of time elapsed during a single frame. This value establishes a link between integer frame indices and time in seconds. Establishing this link is necessary to correctly render lens effects like motion blur, since a camera's exposure time is typically specified in seconds.

&nbsp;
## Generating a custom lens distortion model

We execute the following simple example script to generate a custom lens distortion model.

```
python generate_camera_lens_distortion.py
```

This script generates an identity distortion model, i.e., a distortion model that exactly mimics the case when lens distortion is turned off.

The lens distortion model consists of a single file. In this tutorial example it is named `camera_lens_distortion.hdf5`. The file contains an RxCx3 array of rays in camera-space. Each ray is stored in [x,y,z] order. The convention in the Hypersim Toolkit is that the top-left value in this array is the desired ray at the top-left corner of the top-left pixel in the rendered image. Likewise for the bottom-right value. All other rays are assumed to be evenly spaced in a grid pattern, relative to the underlying pixel grid. The ratio (R-1)/(C-1) must equal the ratio H/W, where H and W are the height and width of the rendered images in pixels.

&nbsp;
## Adding the camera trajectory to a vrscene file

Our next step is to add our camera trajectory to a vrscene file, and save the result as a new vrscene file.

_Since we are specifying a custom lens distortion model, this step requires the OpenCV Python bindings with OpenEXR support enabled. If you don't have the OpenCV Python bindings, or you have them but OpenEXR support is not enabled, you can omit the `camera_lens_distortion_file`, `shared_asset_dir`, `platform_when_rendering`, and `shared_asset_dir_when_rendering` parameters below and proceed through the rest of the tutorial example._

```
python ../../code/python/tools/modify_vrscene_add_camera.py --in_file empty.vrscene --out_file empty_cam.vrscene --vray_user_params_dir . --camera_trajectory_dir . --camera_lens_distortion_file camera_lens_distortion.hdf5 --shared_asset_dir data --platform_when_rendering mac --shared_asset_dir_when_rendering data
```

The command-line parameters to this tool are as follows.

`in_file` is the input vrscene file.

`out_file` is the output vrscene file.

`vray_user_params_dir` is the directory that contains a `_vray_user_params.py` file. This file contains code to configure the V-Ray physical camera, as well as various other V-Ray settings. An example `_vray_user_params.py` file is included in this tutorial. See the V-Ray documentation for more details.

`camera_trajectory_dir` is the directory that contains the camera trajectory files.

The following command-line parameters are optional, but must be specified together. If these parameters are specified, then you need to have the OpenCV Python bindings with OpenEXR support enabled.

`camera_lens_distortion_file` is the custom lens distortion model file. If this parameter is not specified, then V-Ray will use whatever lens distortion model is defined in the vrscene file (or in `_vray_user_params.py`), which in this example is an equirectangular pinhole model.

`shared_asset_dir` is a directory where rendering assets should be auto-generated.

`platform_when_rendering` is the platform of the machine where rendering will ultimately take place. It must be either `mac`, `unix`, or `windows`.

`shared_asset_dir_when_rendering` is the `shared_asset_dir` as it appears on the machine where rendering will ultimately take place. This design allows for Hypersim Toolkit code to be executed on a different machine from where the rendering will ultimately take place.

&nbsp;
## Rendering an intermediate image

We can see the effect of adding our camera trajectory by rendering our modified scene.

```
vray -sceneFile="empty_cam.vrscene" -imgFile="empty_cam.jpg" -frames=0
```

We can render our full image sequence by omitting the `-frames=0` parameter. See `00_empty_scene/_empty_cam.0000.jpg` for what the rendered image should look like.

&nbsp;
## Generating textured quads in a separate vrscene file

Our next step is to generate textured quads in their own vrscene file. In a subsequent processing step, we will include the generated vrscene file in our top-level vrscene file.

```
python generate_vrscene_textured_quads.py --in_file quads_params.csv --shared_asset_dir data --shared_asset_dir data --platform_when_rendering mac --shared_asset_dir_when_rendering data
```

The command-line parameters to this tool are as follows.

`in_file` is a CSV file that defines all the quads that should be generated. An example CSV file, `quads_params.csv`, is included in this tutorial (see details below).

`shared_asset_dir` is a directory where rendering assets should be auto-generated.

`platform_when_rendering` is the platform of the machine where rendering will ultimately take place. It must be either `mac`, `unix`, or `windows`.

`shared_asset_dir_when_rendering` is the `shared_asset_dir` as it appears on the machine where rendering will ultimately take place. This design allows for Hypersim Toolkit code to be executed on a different machine from where the rendering will ultimately take place.

### Specifying textured quads in a CSV file

In order to specify the textured quads we would like to include in our scene, we provide a CSV file. Each row in the CSV file specifies a single quad, and must include the following entries. See `00_empty_scene/quads_params.csv` for details.

`obj_len_x` is the horizontal length of the quad in world units.

`obj_len_y` is the vertical length of the quad in world units.

`rotation_world_from_obj_00`, `rotation_world_from_obj_01`, ..., `rotation_world_from_obj_33` are the entries of the rotation matrix that maps points to world-space from object-space, assuming that points are stored as [x,y,z] column vectors. `rotation_world_from_obj_ij` is the entry at the _ith_ row and the _jth_ column of the rotation matrix. The convention used here is that the quad's positive x-axis points from left to right, the positive y-axis points from bottom to top, and the positive z-axis points out of the image.

`translation_world_from_obj_x`, `translation_world_from_obj_y`, `translation_world_from_obj_z` is the position of the quad's lower left corner.

`image_file` is the file that will be applied to the quad as a texture.

&nbsp;
## Including textured quads in the top-level vrscene file

In our final processing step, we include the textured quads in our top-level vrscene file, saving the result as a new vrscene file.

```
python modify_vrscene_include_files.py --in_file empty_cam.vrscene --out_file empty_cam_quads.vrscene --include_files "data/*.vrscene" --shared_asset_dir data --platform_when_rendering mac --shared_asset_dir_when_rendering data
```

The command-line parameters to this tool are as follows.

`in_file` is the input vrscene file.

`out_file` is the output vrscene file.

`include_files` is a wildcard string for all the vrscene files we want to include.

`shared_asset_dir` is a directory where rendering assets should be auto-generated.

`platform_when_rendering` is the platform of the machine where rendering will ultimately take place. It must be either `mac`, `unix`, or `windows`.

`shared_asset_dir_when_rendering` is the `shared_asset_dir` as it appears on the machine where rendering will ultimately take place. This design allows for Hypersim Toolkit code to be executed on a different machine from where the rendering will ultimately take place.

&nbsp;
## Rendering a final image

At this point, we can render the final scene.

```
vray -sceneFile="empty_cam_quads.vrscene" -imgFile="empty_cam_quads.jpg" -frames=0
```

See `00_empty_scene/_empty_cam_quads.0000.jpg` for what the rendered image should look like.

&nbsp;
## Disabling all image post-processing in V-Ray (optional)

In many computer vision applications, it is helpful to disable all post-processing performed by V-Ray (e.g., tone mapping, gamma correction, color space conversion). To disable all V-Ray post-processing, we modify our vrscene as follows.

```
python modify_vrscene_for_linear_rendering.py --in_file empty_cam_quads.vrscene --out_file empty_cam_quads_linear.vrscene
```

The command-line parameters to this tool are as follows.

`in_file` is the input vrscene file.

`out_file` is the output vrscene file.

We obtain a clean high dynamic range image with no post-processing by saving as an EXR file.

```
vray -sceneFile="empty_cam_quads_linear.vrscene" -imgFile="empty_cam_quads_linear.exr" -frames=0
```

&nbsp;
## Converting from EXR to JPG (optional)

We can convert high dynamic range EXR files to low dynamic range JPG files and perform our own post-processing as follows. Note that this optional step requires the OpenCV Python bindings with OpenEXR support enabled.

```
python generate_jpg_from_exr.py --in_files "empty_cam_quads_linear.*.exr" --out_dir . --tone_mapping_mode linear --gamma_correction
```

The command-line parameters to this tool are as follows.

`in_files` is a wildcard string for the input EXR files to be processed.

`out_dir` is the desired location for the output JPG files.

`tone_mapping_mode` must be either `linear` (do not do any tone mapping) or `exponential` (mimic V-Ray's exponential tone mapping mode with sensible default parameters).

`gamma_correction` is optional, and mimics V-Ray's gamma correction mode with sensible default parameters.
