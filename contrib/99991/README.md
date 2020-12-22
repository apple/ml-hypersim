# Download partial dataset

The script `download.py` can be used to retrieve a subset of the Hypersim dataset, which can be much faster than downloading the full ZIP archives if you are only interested in specific files.

First, list all files with the command:

```
./download.py --list
```

Output:

```
ai_001_001/_detail/cam_00/camera_keyframe_frame_indices.hdf5
ai_001_001/_detail/cam_00/camera_keyframe_look_at_positions.hdf5
ai_001_001/_detail/cam_00/camera_keyframe_orientations.hdf5
ai_001_001/_detail/cam_00/camera_keyframe_positions.hdf5
ai_001_001/_detail/cam_00/metadata_camera.csv
ai_001_001/_detail/metadata_cameras.csv
ai_001_001/_detail/metadata_node_strings.csv
ai_001_001/_detail/metadata_nodes.csv
ai_001_001/_detail/metadata_scene.csv
ai_001_001/images/scene_cam_00_final_hdf5/frame.0000.color.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0000.diffuse_illumination.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0000.diffuse_reflectance.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0000.residual.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0001.color.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0001.diffuse_illumination.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0001.diffuse_reflectance.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0001.residual.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0002.color.hdf5
ai_001_001/images/scene_cam_00_final_hdf5/frame.0002.diffuse_illumination.hdf5
...
ai_001_001/images/scene_cam_00_final_preview/frame.0000.color.jpg
ai_001_001/images/scene_cam_00_final_preview/frame.0000.diff.jpg
...
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.depth_meters.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.normal_bump_cam.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.normal_bump_world.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.normal_cam.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.normal_world.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.position.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.render_entity_id.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.semantic.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.semantic_instance.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0000.tex_coord.hdf5
ai_001_002/images/scene_cam_03_geometry_hdf5/frame.0001.depth_meters.hdf5
...
ai_001_002/images/scene_cam_03_geometry_preview/frame.0000.color.jpg
...
```

Next, specify which files you are interested in and download them.
For example, the following command will download the first preview image of each scene:

```
./download.py --contains scene_cam_00_final_preview --contains frame.0000.color.jpg --silent
```

# Help


```
usage: download.py [-h] [-d DIRECTORY] [-o] [-c [CONTAINS [CONTAINS ...]]]
                   [-s] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        directory to download to
  -o, --overwrite       overwrite existing files
  -c [CONTAINS [CONTAINS ...]], --contains [CONTAINS [CONTAINS ...]]
                        only download file if name contains specific word(s)
  -s, --silent          only print downloaded files
  -l, --list            only list files, do not download

example: list files without downloading

    ./download.py --list

example: download the first preview of each scene:

    ./download.py --contains scene_cam_00_final_preview --contains frame.0000.color.jpg --silent

example: download all files to "all hypersim images" directory

    ./download.py --directory 'all hypersim images'

example: print help

    ./download.py --help
```
