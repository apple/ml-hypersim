In this tutorial example, we use the _Hypersim High-Level Toolkit_ to manipulate a scene downloaded from a content marketplace. We generate a collection of richly annotated ground truth images based on a random walk camera trajectory through the scene.

&nbsp;
## Downloading data

In this tutorial example, we will be using Evermotion Archinteriors Volume 1 Scene 1, which is available [here](https://www.turbosquid.com/3d-models/archinteriors-vol-1-scenes-3d/343621).

_You need to create a `01_marketplace_dataset/downloads` directory, and manually download `AI1_001.rar` into it, before you can proceed through this tutorial example._

&nbsp;
## Quick start

To complete this tutorial example, we execute the following command-line tools. See below for additional details on each tool.

_You must substitute your own `replace_old_path`, `replace_new_path`, and `dataset_dir_when_rendering` when executing these tools, and they must be absolute paths._

```
# pre-processing

# unpack scene data
python ../../code/python/tools/dataset_initialize_scenes.py --dataset_dir . --downloads_dir downloads

# export scene data from native asset file into vrscene file (not provided)

# replace the Windows path in our exported scene with a valid macOS path, so we can execute the rest of the tutorial example on macOS
python ../../code/python/tools/modify_vrscene_replace_paths.py --in_file scenes/ai_001_001/_asset_export/scene.vrscene --out_file scenes/ai_001_001/_asset_export/scene.vrscene --replace_old_path C:\\Users\\mike_roberts2\\code\\github\\ml-hypersim\\examples\\01_marketplace_dataset --replace_new_path /Users/mike/code/github/ml-hypersim/examples/01_marketplace_dataset

# correct bad default export options
python ../../code/python/tools/dataset_modify_vrscenes_normalize.py --dataset_dir . --platform_when_rendering mac --dataset_dir_when_rendering /Users/mike/code/github/ml-hypersim/examples/01_marketplace_dataset

# render intermediate image
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --render_pass none --save_image

# generate a fast binary triangle mesh representation
python ../../code/python/tools/dataset_generate_meshes.py --dataset_dir .

# visualize the mesh
python ../../code/python/tools/visualize_mesh.py --mesh_dir scenes/ai_001_001/_detail/mesh
```

```
# occupancy map

# generate an occupancy map (must be run on macOS or Linux)
python ../../code/python/tools/dataset_generate_octomaps.py --dataset_dir .

# visualize the occupancy map
python ../../code/python/tools/visualize_octomap.py --mesh_dir scenes/ai_001_001/_detail/mesh --octomap_dir scenes/ai_001_001/_detail/octomap --tmp_dir scenes/ai_001_001/_tmp
```

```
# camera trajectories

# generate camera trajectories (must be run on macOS or Linux)
python ../../code/python/tools/dataset_generate_camera_trajectories.py --dataset_dir .

# visualize the camera trajectory
python ../../code/python/tools/visualize_camera_trajectory.py --mesh_dir scenes/ai_001_001/_detail/mesh --camera_trajectory_dir scenes/ai_001_001/_detail/cam_00 --cameras_scale_factor 10.0
```

```
# modify vrscene to render camera trajectories with appropriate ground truth layers
python ../../code/python/tools/dataset_modify_vrscenes_for_hypersim_rendering.py --dataset_dir . --platform_when_rendering mac --dataset_dir_when_rendering /Users/mike/code/github/ml-hypersim/examples/01_marketplace_dataset
```

```
# rendering

# render geometry pass locally
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --camera_name cam_00 --render_pass geometry --save_image

# generate HDF5 images for downstream analysis, and JPG images for visualization
python ../../code/python/tools/dataset_generate_hdf5_from_vrimg.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00 --render_pass geometry

# render pre pass locally
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --camera_name cam_00 --render_pass pre --save_image --save_gi_cache_files

# merge per-image lighting data into per-scene lighting data
python ../../code/python/tools/dataset_generate_merged_gi_cache_files.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00

# render final pass locally
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --camera_name cam_00 --render_pass final --save_image

# generate HDF5 images for downstream analysis, and JPG images for visualization
python ../../code/python/tools/dataset_generate_hdf5_from_vrimg.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00 --render_pass final
```

&nbsp;
## Hypersim High-Level Toolkit directory structure

The Hypersim High-Level Toolkit is designed to work with datasets that consist of multiple scenes, and assumes a particular directory structure. The Hypersim High-Level Toolkit also assumes that all scenes in a dataset are distributed as RAR or 7z archives containing native asset files, and all scenes are renderable with V-Ray. Before running any of our pipeline steps, the Hypersim High-Level Toolkit assumes there is a top-level dataset directory that includes the following files.

```
my_dataset
├── _dataset_config.py
└── _vray_user_params.py
```

`my_dataset/_dataset_config.py` is a Python file that describes each scene in the dataset. For each scene, this file specifies a unique name, the RAR or 7z archive corresponding to the scene, the location of the top-level native asset file within the archive, and some other minor accounting details. There is a `_dataset_config.py` file included in this tutorial example.

`my_dataset/_vray_user_params.py` is a Python file that describes various user-specified parameters that will be used during rendering. There is a `_vray_user_params.py` file included in this tutorial example. See the V-Ray documentation for more details.

Throughout this tutorial, the command-line tools we execute will add new files and directories to this directory structure. We will make a note of these modifications as we proceed.

&nbsp;
## Initializing the dataset

We begin with an initialization step. This step creates a directory for each scene and unpacks each RAR or 7z file.

```
python ../../code/python/tools/dataset_initialize_scenes.py --dataset_dir . --downloads_dir downloads
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`downloads_dir` is the directory containing the RAR or 7z files obtained from the content marketplace.

`dataset_dir_to_copy` is optional, and specifies a directory that will be copied into `dataset_dir` during initialization.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

After completing this step, our directory structure will look like this.

```
my_dataset
├── _dataset_config.py
├── _vray_user_params.py
└── scenes
    ├── my_scene_N
    │   └── _asset
    └── ...
```

`my_dataset/scenes/my_scene_N/_asset` is a directory containing native asset files for the scene `my_scene_N`.

&nbsp;
## Exporting scene data

### Getting scene data from native asset files

We do not provide code for this step, but this step is responsible for generating the following files:

```
my_dataset
├── _asset
└── scenes
    ├── my_scene_N
    │   └── _asset_export
    │       ├── cam_my_camera_X.csv
    │       ├── ...
    │       ├── metadata_cameras_asset_export.csv
    │       ├── scene.obj
    │       └── scene.vrscene
    └── ...
```

`my_dataset/_asset` is a directory containing any native asset files that are shared across the dataset.

`my_dataset/my_scene_N/_asset_export/cam_my_camera_X.csv` contains a camera trajectory for the camera named `cam_my_camera_X`. See `ml-hypersim/code/python/tools/scene_generate_camera_trajectories_asset_export.py` for more details on the expected format of this CSV file.

`my_dataset/my_scene_N/_asset_export/scene.obj` is a standard OBJ file that represents the scene.

`my_dataset/my_scene_N/_asset_export/scene.vrscene` is a V-Ray Standalone scene description file that represents the scene.

`my_dataset/my_scene_N/_asset_export/metadata_cameras_asset_export.csv` contains a list of exported camera names. See `ml-hypersim/code/python/tools/scene_generate_camera_trajectories_asset_export.py` for more details on the expected format of this CSV file.

### Replacing Windows paths

Exported vrscene files typically contain absolute Windows paths. These paths will not be valid if we are executing most of this tutorial example on macOS, but using a Windows computer to export vrscenes. Therefore, we need to replace the Windows paths with their macOS equivalents.

_You must substitute your own `replace_old_path` and `replace_new_path` when executing this tool and it must be an absolute path._

```
python ../../code/python/tools/modify_vrscene_replace_paths.py --in_file scenes/ai_001_001/_asset_export/scene.vrscene --out_file scenes/ai_001_001/_asset_export/scene.vrscene --replace_old_path C:\\Users\\mike_roberts2\\code\\github\\ml-hypersim\\examples\\01_marketplace_dataset --replace_new_path /Users/mike/code/github/ml-hypersim/examples/01_marketplace_dataset
```

The command-line parameters to this tool are as follows.

`in_file` is the input vrscene file.

`out_file` is the output vrscene file.

`replace_old_path` is the path to be replaced.

`replace_new_path` is that new path to be used instead of `replace_old_path`. `replace_new_path` must be an absolute path.

### Correcting bad default export options

In some situations, vrscenes get exported in a way that is not optimal for high-quality rendering, and the resulting vrscene files must be modified. The Hypersim High-Level Toolkit addresses this problem by running a per-scene _normalization_ script. The particular normalization script that gets executed for each scene is controlled by the `normalization_policy` option in the top-level `_dataset_config.py` file.

The command-line tool below will call the appropriate normalization script for each scene, and will also perform some other minor modifications to the vrscene that we think are always a good idea (e.g., configuring V-Ray to save its lighting solution so it can be used for future rendering).

_You must substitute your own `dataset_dir_when_rendering` when executing this tool and it must be an absolute path._

```
python ../../code/python/tools/dataset_modify_vrscenes_normalize.py --dataset_dir . --platform_when_rendering mac --dataset_dir_when_rendering /Users/mike/code/github/ml-hypersim/examples/01_marketplace_dataset
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

`platform_when_rendering` is the platform of the machine where rendering will ultimately take place. It must be either `mac`, `unix`, or `windows`.

`dataset_dir_when_rendering` is the `dataset_dir` as it appears on the machine where rendering will ultimately take place. This design allows for Hypersim Toolkit code to be executed on a different machine from where the rendering will ultimately take place. `dataset_dir_when_rendering` must be an absolute path.

After completing this step, our directory structure will look like this.

```
my_dataset
├── _dataset_config.py
├── _vray_user_params.py
├── _asset
└── scenes
    ├── my_scene_N
    │   ├── _asset
    │   ├── _asset_export
    │   ├── _detail
    │   ├── images
    │   │   └── scene
    │   └── vrscenes
    │       └── scene.vrscene
    └── ...
```

`my_dataset/scenes/my_scene_N/_detail` is a directory that contains various intermediate outputs generated by the Hypersim Toolkit.

`my_dataset/scenes/my_scene_N/images/scene` is an empty directory, intended to store the rendering output of our scene.

`my_dataset/scenes/my_scene_N/vrscenes/scene.vrscene` is the vrscene file after it has been normalized, and is therefore ready for high-quality rendering.

### Rendering an intermediate image

Before manipulating our vrscene any further, we render it to make sure it looks correct. We use the `dataset_render_scene.py` tool as a matter of convenience, but this tool is a very thin wrapper over V-Ray Standalone.

```
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --render_pass none --save_image
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_name` is the name of the scene we want to render.

`render_pass` is the name of the rendering pass we want to render. Specifying `none` means rendering the vrscene file after it has been normalized, i.e., `dataset_dir/scenes/scene_name/vrscenes/scene.vrscene`.

`save_image` is an optional parameter that specifies that we want to save the output image. If not specfied, V-Ray will render without saving the output image, which is useful for debugging.

&nbsp;
## Generating a binary mesh representation

Our next step is to generate a mesh representation of our scene. Note that `dataset_export_scenes.py` already generated an OBJ file. But OBJ files are time-consuming to load, so in this step, we generate an efficient binary representation of the mesh that will be more convenient to load in subsequent pipeline steps.

```
python ../../code/python/tools/dataset_generate_meshes.py --dataset_dir .
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

We can visually inspect the mesh using our `visualize_mesh.py` tool.

```
python ../../code/python/tools/visualize_mesh.py --mesh_dir scenes/ai_001_001/_detail/mesh
```

&nbsp;
## Estimating the reachable free space

Our next step is to estimate the reachable free space in the scene.

_You must execute `dataset_generate_octomaps.py` on a macOS or Linux computer._

```
python ../../code/python/tools/dataset_generate_octomaps.py --dataset_dir .
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

We can visually inspect the Octomap (i.e., the data structure used to store occupancy information) using our `visualize_octomap.py` tool, or using the visualization tools that ship with the Octomap C++ library.

```
python ../../code/python/tools/visualize_octomap.py --mesh_dir scenes/ai_001_001/_detail/mesh --octomap_dir scenes/ai_001_001/_detail/octomap --tmp_dir scenes/ai_001_001/_tmp
```

&nbsp;
## Generating a camera trajectory

Our next step is to generate a random walk camera trajectory through the scene. By default, the Hypersim High-Level Toolkit will generate random walk camera trajectories that are constrained to the reachable free space, and will generate one camera trajectory for each exported camera from the original asset file. Each random walk will start from the location of its corresponding exported camera.

_You must execute `dataset_generate_camera_trajectories.py` on a macOS or Linux computer._

```
python ../../code/python/tools/dataset_generate_camera_trajectories.py --dataset_dir .
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

The `dataset_generate_camera_trajectories.py` tool saves debug preview images (colored according to triangle ID) for the camera trajectory in `my_dataset/scenes/my_scene_N/_detail/cam_X/preview`. We can also visually inspect the camera trajectories generated in this step using our `visualize_camera_trajectory.py` tool.

```
python ../../code/python/tools/visualize_camera_trajectory.py --mesh_dir scenes/ai_001_001/_detail/mesh --camera_trajectory_dir scenes/ai_001_001/_detail/cam_00  --cameras_scale_factor 10.0
```

&nbsp;
## Adding our camera trajectory to the vrscene

Our next step is to add our generated camera trajectory to the vrscene, and to perform several other modifications to generate appropriate ground truth images.

_You must substitute your own `dataset_dir_when_rendering` when executing this tool and it must be an absolute path._

```
python ../../code/python/tools/dataset_modify_vrscenes_for_hypersim_rendering.py --dataset_dir . --platform_when_rendering mac --dataset_dir_when_rendering /Users/mike/code/github/ml-hypersim/examples/01_marketplace_dataset
```

The command-line parameters to this tool are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

`platform_when_rendering` is the platform of the machine where rendering will ultimately take place. It must be either `mac`, `unix`, or `windows`.

`dataset_dir_when_rendering` is the `dataset_dir` as it appears on the machine where rendering will ultimately take place. This design allows for Hypersim Toolkit code to be executed on a different machine from where the rendering will ultimately take place. `dataset_dir_when_rendering` must be an absolute path.

After completing this step, our directory structure will look like this.

```
my_dataset
├── _dataset_config.py
├── _vray_user_params.py
├── _asset
└── scenes
    ├── my_scene_N
    │   ├── _asset
    │   ├── _asset_export
    │   ├── _detail
    │   ├── images
    │   │   ├── scene
    │   │   ├── scene_cam_X_final
    │   │   ├── scene_cam_X_final_hdf5
    │   │   ├── scene_cam_X_final_preview
    │   │   ├── scene_cam_X_geometry
    │   │   ├── scene_cam_X_geometry_hdf5
    │   │   ├── scene_cam_X_geometry_preview
    │   │   ├── scene_cam_X_pre
    │   │   └── ...
    │   └── vrscenes
    │       ├── scene.vrscene
    │       ├── scene_cam_X_final.vrscene
    │       ├── scene_cam_X_geometry.vrscene
    │       ├── scene_cam_X_pre.vrscene
    │       └── ...
    └── ...
```

The directories in `my_dataset/scenes/my_scene_N/images` are empty, and are intended to store the rendering output of a particular camera trajectory and rendering pass. The preview directories contain JPG and PNG files that are useful for debugging, and the HDF5 directories contain 16-bit HDR images that are useful for downstream analysis.

`my_dataset/scenes/my_scene_N/vrscenes/scene_cam_X_final.vrscene` is a vrscene file containing a particular camera trajectory, and is set up to render final high-quality images.

`my_dataset/scenes/my_scene_N/vrscenes/scene_cam_X_geometry.vrscene` is a vrscene file containing a particular camera trajectory, and is set up to render geometry metadata images (e.g., per-pixel depth, per-pixel normals, etc).

`my_dataset/scenes/my_scene_N/vrscenes/scene_cam_X_pre.vrscene` is a vrscene file containing a particular camera trajectory, and is set up to precompute a lighting solution used for final rendering.

&nbsp;
## Rendering the scene

Finally, we can render images from our automatically generated camera trajectory. The Hypersim High-Level Toolkit assumes that rendering is divided into 3 passes. In the _geometry_ pass, we render geometry metadata (e.g., per-pixel depth, per-pixel normals, etc). This stage is very fast because it doesn't require accurate shading. In the _pre_ pass, we precompute a lighting solution. In the _final_ pass, we render final images using the precomputed lighting solution. When rendering each pass, we use the `dataset_render_scene.py` tool as a matter of convenience, but this tool is a very thin wrapper over V-Ray Standalone.

```
# rendering

# render geometry pass locally
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --camera_name cam_00 --render_pass geometry --save_image

# generate HDF5 images for downstream analysis, and JPG images for visualization
python ../../code/python/tools/dataset_generate_hdf5_from_vrimg.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00 --render_pass geometry

# render pre pass locally
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --camera_name cam_00 --render_pass pre --save_image --save_gi_cache_files

# merge per-image lighting data into per-scene lighting data
python ../../code/python/tools/dataset_generate_merged_gi_cache_files.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00

# render final pass locally
python ../../code/python/tools/dataset_render_scene.py --dataset_dir . --scene_name ai_001_001 --camera_name cam_00 --render_pass final --save_image

# generate HDF5 images for downstream analysis, and JPG images for visualization
python ../../code/python/tools/dataset_generate_hdf5_from_vrimg.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00 --render_pass final
```

The command-line parameters to `dataset_render_scene.py` are as follows.

`dataset_dir` is the top-level dataset directory, which in this example is named `01_marketplace_dataset`.

`scene_name` is the name of the scene we want to render.

`camera_name` is the name of the camera trajectory we want to render.

`render_pass` is the name of the rendering pass we want to render. It must be either `none`, `geometry`, `pre`, or `final`.

`frames` is an optional parameter that specifies the frame range (in Python range syntax) to be rendered. If not specified, frame 0 is rendered.

`save_image` is an optional parameter that specifies that we want to save the output image. If not specfied, VRay will render without saving the output image, which is useful for debugging.

`save_gi_cache_files` is an optional parameter that specifies that we want to save the lighting solution. If not specified, VRay will render without saving the lighting solution, which is useful for debugging.

The command-line parameters to `dataset_generate_merged_gi_cache_files.py` and `dataset_generate_hdf5_from_vrimg.py` are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

`camera_names`  is optional, and specifies that a specific camera trajectory (or specific camera trajectories) should be processed. `camera_names` can be a wildcard expression.

Additionally, `dataset_generate_hdf5_from_vrimg.py` accepts the following command-line parameter.

`render_pass` is optional, and is the name of the rendering pass we want to process. It must be either `geometry` or `final`.

The `dataset_render_scene.py` tool generates images in `my_dataset/scenes/my_scene_N/images`.

&nbsp;
## Post-processing the rendering output (optional)

After the rendering output has been generated, we can perform several useful post-processing operations. First, we can tone-map the rendered HDR color data into LDR. Second, if we have labeled our scene using the Hypersim Scene Annotation Tool (located at `ml-hypersim/code/cpp/bin/scene_annotation_tool`), we can generate semantic segmentation images. The scene in this tutorial example has already been labeled, and the segmentation data has been checked in, so we can generate segmentation images without needing to label the scene manually. Third, we can generate animations of our rendered output.

```
# generate tone-mapped images for visualization
python ../../code/python/tools/dataset_generate_images_tonemap.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00

# generate semantic segmentation images
python ../../code/python/tools/dataset_generate_images_semantic_segmentation.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00

# generate animations
python ../../code/python/tools/dataset_generate_animations.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00 --img_name tonemap
```

The command-line parameters to these tools are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

`camera_names`  is optional, and specifies that a specific camera trajectory (or specific camera trajectories) should be processed. `camera_names` can be a wildcard expression.

Additionally, `dataset_generate_animations.py` accepts the following command-line parameter.

`img_name` specifies the name of the images used to create an animation. For example, if we want to make an animation from `frame.*.tonemap.jpg`, then we should specify `tonemap` as the `img_name`.

The `dataset_generate_images_tonemap.py` tool generates images in `my_dataset/scenes/my_scene_N/images/cam_X_final_preview`.

The `dataset_generate_images_semantic_segmentation.py` tool generates images in `my_dataset/scenes/my_scene_N/images/cam_X_geometry_preview`.

The `dataset_generate_animations.py` tool generates animations in `my_dataset/animations`.

&nbsp;
## Generating bounding boxes around objects (optional)

If we have labeled our scene using the Hypersim Scene Annotation Tool (located at `ml-hypersim/code/cpp/bin/scene_annotation_tool`), then we can generate bounding boxes around objects. The scene in this tutorial example has already been labeled, and the segmentation data has been checked in, so we can generate bounding boxes without needing to label the scene manually.

_You must execute `dataset_generate_bounding_boxes.py` on a macOS or Linux computer._

```
python ../../code/python/tools/dataset_generate_bounding_boxes.py --dataset_dir . --scene_names ai_001_001 --bounding_box_type object_aligned_2d
```

The command-line parameters to this tool is as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies that a specific scene (or specific scenes) should be processed. `scene_names` can be a wildcard expression.

`bounding_box_type` specifies the type of bounding box we want to compute. It must be either `axis_aligned`, `object_aligned_2d`, or `object_aligned_3d`.

We can visually inspect the bounding boxes using our `visualize_semantic_semantic_segmentation.py` tool. Note that this tool takes roughly 30 seconds to load.

```
python ../../code/python/tools/visualize_semantic_segmentation.py --mesh_dir scenes/ai_001_001/_detail/mesh --show_bounding_boxes --bounding_box_type object_aligned_2d
```

We can also generate an image of our bounding boxes overlaid on a rendered image using our `scene_generate_images_bounding_box.py` tool.

```
python ../../code/python/tools/scene_generate_images_bounding_box.py --scene_dir scenes/ai_001_001 --camera_name cam_00 --bounding_box_type object_aligned_2d --frame_id 0 --num_pixels_per_fragment 1
```

The command-line parameters to this tool is as follows.

`scene_dir` is the top-level scene directory.

`camera_name` is the camera trajectory we want to render.

`frame_id` is the image we want to render.

`num_pixels_per_fragment` is a quality parameter for rendering bounding boxes. A value of 1 handles occlusions pixel-perfectly. Higher values handle occlusions less accurately but are faster.

The `dataset_generate_bounding_boxes.py` tool generates bounding box data in `my_dataset/scenes/my_scene_N/_detail/mesh`.

The `scene_generate_images_bounding_box.py` tool generates images in `my_dataset/scenes/my_scene_N/images/cam_X_final_preview`.

&nbsp;
## Submitting jobs to a cloud rendering service (optional)

Rather than rendering images locally, we can submit rendering jobs to a cloud rendering service. We don't provide code for this step, but we do include an example submission script that generates text files containing useful metadata about each rendering job, and could be used for cloud rendering with minor modifications.

```
python ../../code/python/tools/dataset_submit_rendering_jobs.py --dataset_dir . --scene_names ai_001_001 --camera_names cam_00 --render_pass final
```

The command-line parameters to `dataset_submit_jobs.py` are as follows.

`dataset_dir` is the top-level dataset directory, which in this tutorial example is named `01_marketplace_dataset`.

`scene_names` is optional, and specifies the scene (or scenes) that we want to render. `scene_names` can be a wildcard expression.

`camera_names` is optional, and specifies the camera (or cameras) that we want to render. `camera_names` can be a wildcard expression.

`render_pass` is the name of the rendering pass we want to render. It must be either `geometry`, `pre`, or `final`.

`frames` is an optional parameter that specifies the frame range (in Python range syntax) to be rendered. If not specified, all frames are rendered.

The `dataset_submit_rendering_jobs.py` tool generates text files in `my_dataset/scenes/my_scene_N/jobs`.
