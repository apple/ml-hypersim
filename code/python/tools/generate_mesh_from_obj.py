#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import inspect
import os
import pandas as pd

import path_utils
path_utils.add_path_to_sys_path("../lib", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import obj_file_utils

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_dir", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_file)



print("[HYPERSIM: GENERATE_MESH_FROM_OBJ] Begin...")



mesh_vertices_hdf5_file          = os.path.join(args.out_dir, "mesh_vertices.hdf5")
mesh_texcoords_hdf5_file         = os.path.join(args.out_dir, "mesh_texcoords.hdf5")
mesh_normals_hdf5_file           = os.path.join(args.out_dir, "mesh_normals.hdf5")
mesh_faces_oi_hdf5_file          = os.path.join(args.out_dir, "mesh_faces_oi.hdf5")
mesh_faces_gi_hdf5_file          = os.path.join(args.out_dir, "mesh_faces_gi.hdf5")
mesh_faces_mi_hdf5_file          = os.path.join(args.out_dir, "mesh_faces_mi.hdf5")
mesh_faces_vi_hdf5_file          = os.path.join(args.out_dir, "mesh_faces_vi.hdf5")
mesh_faces_vni_hdf5_file         = os.path.join(args.out_dir, "mesh_faces_vti.hdf5")
mesh_faces_vti_hdf5_file         = os.path.join(args.out_dir, "mesh_faces_vni.hdf5")
mesh_metadata_materials_csv_file = os.path.join(args.out_dir, "metadata_materials.csv")
mesh_metadata_objects_csv_file   = os.path.join(args.out_dir, "metadata_objects.csv")
mesh_metadata_groups_csv_file    = os.path.join(args.out_dir, "metadata_groups.csv")

if not os.path.exists(args.out_dir): os.makedirs(args.out_dir)



# load vertices and faces
obj_data = obj_file_utils.load_obj_file(args.in_file)



# save vertices and faces
with h5py.File(mesh_vertices_hdf5_file,  "w") as f: f.create_dataset("dataset", data=obj_data.vertices)
with h5py.File(mesh_texcoords_hdf5_file, "w") as f: f.create_dataset("dataset", data=obj_data.texcoords)
with h5py.File(mesh_normals_hdf5_file,   "w") as f: f.create_dataset("dataset", data=obj_data.normals)
with h5py.File(mesh_faces_oi_hdf5_file,  "w") as f: f.create_dataset("dataset", data=obj_data.faces_oi)
with h5py.File(mesh_faces_gi_hdf5_file,  "w") as f: f.create_dataset("dataset", data=obj_data.faces_gi)
with h5py.File(mesh_faces_mi_hdf5_file,  "w") as f: f.create_dataset("dataset", data=obj_data.faces_mi)
with h5py.File(mesh_faces_vi_hdf5_file,  "w") as f: f.create_dataset("dataset", data=obj_data.faces_vi)
with h5py.File(mesh_faces_vni_hdf5_file, "w") as f: f.create_dataset("dataset", data=obj_data.faces_vni)
with h5py.File(mesh_faces_vti_hdf5_file, "w") as f: f.create_dataset("dataset", data=obj_data.faces_vti)

df_objects = pd.DataFrame({"object_name": obj_data.object_names})
df_objects.to_csv(mesh_metadata_objects_csv_file, index=False)

df_groups = pd.DataFrame({"group_name": obj_data.group_names})
df_groups.to_csv(mesh_metadata_groups_csv_file, index=False)

# rename_axis() sets the name of the current index
# reset_index() demotes the existing index to a column and creates a new unnamed index
df_materials = pd.DataFrame.from_dict(obj_data.material_param_map, orient="index")
df_materials_ = df_materials.loc[obj_data.material_names].rename_axis("material_name").reset_index()
df_materials_.to_csv(mesh_metadata_materials_csv_file, index=False)



print("[HYPERSIM: GENERATE_MESH_FROM_OBJ] Finished.")
