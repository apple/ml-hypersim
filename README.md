![The Hypersim Toolkit](assets/teaser_web.jpg "The Hypersim Toolkit")

# The Hypersim Toolkit

The Hypersim Toolkit is a set of tools for generating photorealistic synthetic datasets from V-Ray scenes. By building on top of V-Ray, the datasets generated using the Hypersim Toolkit can leverage advanced rendering effects (e.g., rolling shutter, motion and defocus blur, chromatic aberration), as well as abundant high-quality 3D content from online marketplaces.

The Hypersim Toolkit consists of tools that operate at two distinct levels of abstraction. The _Hypersim Low-Level Toolkit_ is concerned with manipulating individual V-Ray scene files. The _Hypersim High-Level Toolkit_ is concerned with manipulating collections of scenes. You can use the Hypersim Low-Level Toolkit to output richly annotated ground truth labels, programmatically specify camera trajectories and custom lens distortion models, and programmatically insert geometry into a scene. You can use the Hypersim High-Level Toolkit to generate collision-free camera trajectories that are biased towards the salient parts of a scene, and interactively apply semantic labels to scenes.

&nbsp;
## Citation

If you find the Hypersim Toolkit useful in your research, please cite the following [paper](https://arxiv.org/abs/2011.02523):

```
@misc{roberts:2020,
    author       = {Mike Roberts AND Nathan Paczan},
    title        = {{Hypersim}: {A} Photorealistic Synthetic Dataset for Holistic Indoor Scene Understanding},
    howpublished = {arXiv 2020},
}
```

&nbsp;
## Disclaimer

This software depends on several open-source projects. Some of the dependent projects have portions that are licensed under the GPL, but this software does not depend on those GPL-licensed portions. The GPL-licensed portions may be omitted from builds of those dependent projects.

V-Ray Standalone and the V-Ray AppSDK are available under their own terms [here](http://www.chaosgroup.com). The authors of this software are not responsible for the contents of third-party websites.

&nbsp;
## Installing the prerequisite applications, tools, and libraries

### Quick start for Anaconda Python

If you're using Anaconda, you can install all of the required Python libraries using our `requirements.txt` file.

```
conda create --name hypersim-env --file requirements.txt
conda activate hypersim-env
```

Optional Python libraries (see below) can be installed separately. For example,

```
pip install mayavi
conda install -c conda-forge opencv
conda install -c anaconda pillow
```

### Hypersim Low-Level Toolkit

- Install Python (we recommend Anaconda Python 3.7)
- Install the following Python libraries: h5py, matplotlib, pandas, scikit-learn
  - http://www.h5py.org
  - http://matplotlib.org
  - http://pandas.pydata.org
  - http://scikit-learn.org
- Install V-Ray Standalone and the V-Ray AppSDK (version Next Standalone, update 2.1 for x64 or later; see below)
- Configure the Hypersim Python tools for your system (see below)

### Hypersim High-Level Toolkit

- Complete all the prerequisite steps for the Hypersim Low-Level Toolkit (see above).
- Install the following Python libraries: joblib, scipy
  - http://joblib.readthedocs.io
  - http://www.scipy.org
- Install the following C++ libraries: args, Armadillo, Embree, HDF5, Octomap, OpenEXR
  - http://github.com/Taywee/args
  - http://arma.sourceforge.net
  - http://www.hdfgroup.org/solutions/hdf5
  - http://www.embree.org
  - http://octomap.github.io
  - http://www.openexr.com
- Build the Hypersim C++ tools (see below)

### Optional components

The following components are optional, so you only need to install these prerequisites if you intend to use a particular component.

- Using the Hypersim debug visualization tools
  - Install the following Python libraries: mayavi
    - http://docs.enthought.com/mayavi/mayavi
- Specifying custom non-parametric lens distortion models for rendering
  - Install the OpenCV Python bindings with OpenEXR support enabled
    - http://opencv.org
- Using the Hypersim Scene Annotation Tool
  - Install the following C++ libraries: Font-Awesome, IconFontCppHeaders, libigl
    - http://github.com/FortAwesome/Font-Awesome
    - http://github.com/juliettef/IconFontCppHeaders
    - http://libigl.github.io
- Computing bounding boxes around objects
  - Install the following C++ libraries: ApproxMVBB
    - http://github.com/gabyx/ApproxMVBB
- Generating images of bounding boxes overlaid on top of rendered images
  - Install the following Python libraries: pillow
    - http://pillow.readthedocs.io

### Installing V-Ray Standalone and the V-Ray AppSDK

Make sure the `bin` directory from V-Ray Standalone is in your `PATH` environment variable. Also make sure that the `bin` directory from the V-Ray AppSDK is in your `DYLD_LIBRARY_PATH` environment variable. For example, I add the following to my `~/.bash_profile` file.

```
export PATH=$PATH:/Applications/ChaosGroup/V-Ray/Standalone_for_mavericks_x64/bin
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/Applications/ChaosGroup/V-Ray/AppSDK/bin
```

Manually copy `vray.so` from the AppSDK directory so it is visible to your Python distribution.

Manually copy the following files and subdirectories from the AppSDK `bin` directory to the `hypersim/code/python/tools` directory. For example,

```
cp /Applications/ChaosGroup/V-Ray/AppSDK/bin/libcgauth.dylib          /Users/mike/code/github/hypersim/code/python/tools
cp /Applications/ChaosGroup/V-Ray/AppSDK/bin/libvray.dylib            /Users/mike/code/github/hypersim/code/python/tools
cp /Applications/ChaosGroup/V-Ray/AppSDK/bin/libvrayopenimageio.dylib /Users/mike/code/github/hypersim/code/python/tools
cp /Applications/ChaosGroup/V-Ray/AppSDK/bin/libvrayosl.dylib         /Users/mike/code/github/hypersim/code/python/tools
cp /Applications/ChaosGroup/V-Ray/AppSDK/bin/libVRaySDKLibrary.dylib  /Users/mike/code/github/hypersim/code/python/tools
cp -a /Applications/ChaosGroup/V-Ray/AppSDK/bin/plugins               /Users/mike/code/github/hypersim/code/python/tools
```

You can verify that the V-Ray AppSDK is installed correctly by executing the following command-line tool.

```
python code/python/tools/check_vray_appsdk_install.py
```

If the V-Ray AppSDK is installed correctly, this tool will print out the following message.

```
[HYPERSIM: CHECK_VRAY_APPSDK_INSTALL] The V-Ray AppSDK is configured correctly on your system.
```

### Configuring the Hypersim Python tools for your system

You need to rename `hypersim/code/python/_system_config.py.example -> _system_config.py`, and modify the paths contained in this file for your system.

### Building the Hypersim C++ tools

You need to rename `hypersim/code/cpp/system_config.inc.example -> system_config.inc`, and modify the paths contained in this file for your system. Then you need to build the Hypersim C++ tools. The easiest way to do this is to use the top-level makefile in `hypersim/code/cpp/tools`.

```
cd code/cpp/tools
make
```

If you intend to use the Hypersim Scene Annotation Tool, you need to build it separately.

```
cd code/cpp/tools/scene_annotation_tool
make
```

If you intend to compute bounding boxes around objects, you need to build the following tool separately.

```
cd code/cpp/tools/generate_oriented_bounding_boxes
make
```

&nbsp;
## Using the Hypersim Toolkit

The Hypersim Low-Level Toolkit consists of the following Python command-line tools.

- `hypersim/code/python/tools/generate_*.py`
- `hypersim/code/python/tools/modify_vrscene_*.py`

The Hypersim High-Level Toolkit consists of the following Python command-line tools.

- `hypersim/code/python/tools/dataset_*.py`
- `hypersim/code/python/tools/scene_*.py`
- `hypersim/code/python/tools/visualize_*.py`

The Hypersim High-Level Toolkit also includes the Hypersim Scene Annotation Tool executable, which is located in the `hypersim/code/cpp/bin` directory, and can be launched from the command-line as follows.

```
cd code/cpp/bin
./scene_annotation_tool
```

The following tutorial examples demonstrate the functionality in the Hypersim Toolkit.

- [`00_empty_scene`](examples/00_empty_scene) In this tutorial example, we use the Hypersim Low-Level Toolkit to add a camera trajectory and a collection of textured quads to a V-Ray scene.

- [`01_marketplace_dataset`](examples/01_marketplace_dataset) In this tutorial example, we use the Hypersim High-Level Toolkit to export and manipulate a scene downloaded from a content marketplace. We generate a collection of richly annotated ground truth images based on a random walk camera trajectory through the scene.

&nbsp;
## Generating the full Hypersim dataset

We recommend completing the [`00_empty_scene`](examples/00_empty_scene) and [`01_marketplace_dataset`](examples/01_marketplace_dataset) tutorial examples before attempting to generate the full Hypersim dataset.

### Downloading scenes

In order to generate the full Hypersim dataset, we use Evermotion Archinteriors Volumes 1-55 excluding 20,25,40,49. All the Evermotion Archinteriors volumes are available for purchase [here](https://www.turbosquid.com/Search/3D-Models?include_artist=evermotion).

You need to create a `downloads` directory, and manually download the Evermotion Archinteriors RAR and 7z archives into it. Almost all the archives have clear filenames that include the volume number and scene number, and do not need to be renamed to avoid confusion. The exception to this rule is Evermotion Archinteriors Volume 11, whose archives are named {`01.rar`, `02.rar`, ...}. You need to manually rename these archives to {`AI11_01.rar`, `AI11_02.rar`, ...} in order to match the dataset configuration file (`_dataset_config.py`) we provide.

### Running our pipeline on multiple operating systems

Some of our pipeline steps require Windows, and others require macOS or Linux. It is therefore desriable to specify an output directory for the various steps of our pipeline that is visible to both operating systems. Ideally, you would specify an output directory on a fast network drive with lots of storage space. However, our pipeline generates a lot of intermediate data, and disk I/O can become a significant bottleneck, even on relatively fast network drives. We therefore recommend the quick-and-dirty solution of generating the Hypersim dataset on portable hard drives that you can read and write from Windows and macOS (or Linux).

You need to make sure that the absolute path to the dataset on Windows is consistent (i.e., always has the same drive letter) when executing the Windows-only steps of our pipeline. We recommend making a note of the absolute Windows path to the dataset, because you will need to supply it whenever a subsequent pipeline step requires the `dataset_dir_when_rendering` argument.

If you are generating data on portable hard drives, we recommend running our pipeline in batches of 10 volumes at a time (i.e., roughly 100 scenes at a time), and storing each batch on its own 4TB drive. If you attempt to run our pipeline in batches that are too large, the pipeline will eventually generate too much intermediate data, and you will run out of storage space. In our experience, the most straightforward way to run our pipeline in batches is to include the optional `scene_names` argument when executing each step of the pipeline.

The `scene_names` argument works in the following way. We give each scene in our dataset a unique name, `ai_VVV_NNN`, where `VVV` is the volume number, and `NNN` is the scene number within the volume (e.g., the name `ai_001_002` refers to Volume 1 Scene 2). Each step of our pipeline can process a particular scene (or scenes) by specifying the `scene_names` argument, which accepts wildcard expressions. For example, `ai_001_001` specifies Volume 1 Scene 1, `ai_001_*` specifies all scenes from Volume 1, `ai_00*` specifies all scenes from Volumes 1-9, `ai_01*` specifies all scenes from Volumes 10-19, and so on. We include the argument `--scene_names ai_00*` in our instructions below.

### Handling scenes and camera trajectories that have been manually excluded

When preparing the Hypersim dataset, we chose to manually exclude some scenes and automatically generated camera trajectories. Most of the scenes we excluded are simply commented out in our `_dataset_config.py` file, and therefore our pipeline never processes these scenes. However, for some scenes, we needed to run some of our pipeline in order to decide to exclude them. These scenes are un-commmented in our `dataset_config.py` file, and therefore our pipeline will process these scenes by default. There is no harm in running our pipeline for these scenes, but it is possible to save a bit of time and money by not rendering images for these manually excluded scenes and camera trajectories.

The camera trajectories we manually excluded from our dataset are listed in `hypersim/evermotion_dataset/analysis/metadata_camera_trajectories.csv`. If the `Scene type` column is listed as `OUTSIDE VIEWING AREA (BAD INITIALIZATION)` or `OUTSIDE VIEWING AREA (BAD TRAJECTORY)`, then we consider that trajectory to be manually excluded from our dataset. If all the camera trajectories for a scene have been manually excluded, then we consider the scene to be manually excluded. We recommend excluding these scenes and camera trajectories in downstream learning applications for consistency with other publications, and to obtain the cleanest possible training data.

### Using our mesh annotations

Our mesh annotations for each scene are checked in at `hypersim/evermotion_dataset/scenes/ai_VVV_NNN/_detail/mesh`, where `VVV` is the volume number and `NNN` is the scene number within the volume. So, you can use our automatic pipeline to generate instance-level semantic segmentation images without needing to manually annotate any scenes.

### Analyzing the value and cost of each image in downstream applications

We include the cost of rendering each image in our dataset in `hypersim/evermotion_dataset/analysis/metadata_rendering_tasks.csv`. We include this rendering metadata so the marginal value and marginal cost of each image can be analyzed jointly in downstream applications.

In our pipeline, we divide rendering into 3 passes. Each rendering pass for each image in each camera trajectory corresponds to a particular task, and the costs in `metadata_rendering_tasks.csv` are specified per task. To compute the total cost of the image `frame.0000` in the camera trajectory `cam_00` in the scene `ai_001_001`, we add up the `vray_cost_dollars` and `cloud_cost_dollars` columns for the rows where `job_name == {ai_001_001@scene_cam_00_geometry, ai_001_001@scene_cam_00_pre, ai_001_001@scene_cam_00_final}` and `task_id == 0`.

### Running the full pipeline

To process the first batch of scenes (Volumes 1-9) in the Hypersim dataset, we execute the following pipeline steps. We process subsequent batches by executing these steps repeatedly, substituting the `scene_names` argument as described above.  See the [`01_marketplace_dataset`](examples/01_marketplace_dataset) tutorial example for more details on each of these pipeline steps.

_You must substitute your own `dataset_dir_when_rendering` when executing these pipeline steps, and it must be an absolute path. You must also substitute your own `dataset_dir` and `downloads_dir`, but these arguments do not need to be absolute paths. You must wait until each rendering pass is complete, and all data has finished downloading from the cloud, before proceeding to the next pipeline step._

```
# pre-processing

# unpack scene data
python code/python/tools/dataset_initialize_scenes.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --downloads_dir downloads --dataset_dir_to_copy evermotion_dataset --scene_names "ai_00*"

# export scene data from native asset file into vrscene file (not provided)

# correct bad default export options
python code/python/tools/dataset_modify_vrscenes_normalize.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --platform_when_rendering windows --dataset_dir_when_rendering Z:\\evermotion_dataset --scene_names "ai_00*"

# generate a fast binary triangle mesh representation
python code/python/tools/dataset_generate_meshes.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --scene_names "ai_00*"
```

```
# generate an occupancy map (must be run on macOS or Linux)
python code/python/tools/dataset_generate_octomaps.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --scene_names "ai_00*"
```

```
# generate camera trajectories (must be run on macOS or Linux)
python code/python/tools/dataset_generate_camera_trajectories.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --scene_names "ai_00*"
```

```
# modify vrscene to render camera trajectories with appropriate ground truth layers
python code/python/tools/dataset_modify_vrscenes_for_hypersim_rendering.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --platform_when_rendering windows --dataset_dir_when_rendering Z:\\evermotion_dataset --scene_names "ai_00*"
```

```
# cloud rendering

# output rendering job description files for geometry pass
python code/python/tools/dataset_submit_rendering_jobs.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --render_pass geometry --scene_names "ai_00*"

# render geometry pass in the cloud (not provided)

# output rendering job description files for pre pass
python code/python/tools/dataset_submit_rendering_jobs.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --render_pass pre --scene_names "ai_00*"

# render pre pass in the cloud (not provided)

# merge per-image lighting data into per-scene lighting data
python code/python/tools/dataset_generate_merged_gi_cache_files.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --scene_names "ai_00*"

# output rendering job description files for final pass
python code/python/tools/dataset_submit_rendering_jobs.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --render_pass final --scene_names "ai_00*"

# render final pass in the cloud (not provided)
```

```
# post-processing

# generate tone-mapped images for visualization
python code/python/tools/dataset_generate_images_tonemap.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --scene_names "ai_00*"

# generate semantic segmentation images
python code/python/tools/dataset_generate_images_semantic_segmentation.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --scene_names "ai_00*"

# generate 3D bounding boxes (must be run on macOS or Linux)
python code/python/tools/dataset_generate_bounding_boxes.py --dataset_dir /Volumes/portable_hard_drive/evermotion_dataset --bounding_box_type object_aligned_2d --scene_names "ai_00*"
```
