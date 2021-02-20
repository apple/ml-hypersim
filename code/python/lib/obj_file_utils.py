#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import os
import pandas as pd



def load_mtl_file(filename):
    
    class mtl_file:

        def __init__(self, filename):

            self.material_param_map = {}

            material_name_curr = None

            print("[HYPERSIM: OBJ_FILE_UTILS] Begin load_mtl_file...")
            print("[HYPERSIM: OBJ_FILE_UTILS] Parsing " + filename + "...")
            
            for line in open(filename, "r"):
                
                line = line.strip()

                # hack for OBJ files exported from Unreal
                if line.startswith("#") or line.startswith("\xef\xbb\xbf#"):
                    continue

                values = line.split()
                
                if not values or len(values) == 0:
                    continue

                if values[0] in ["newmtl", "newmat"]:
                    try:
                        material_name_curr = values[1]
                    except ValueError:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + values)
                        material_name_curr = "ERROR MATERIAL"
                    self.material_param_map[material_name_curr] = {}
                    
                else:
                    material_param_key = values[0]
                    try:
                        material_param_values = " ".join(values[1:])
                    except ValueError:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + values)
                        material_param_values = 0.0
                    self.material_param_map[material_name_curr][material_param_key] = material_param_values

            print("[HYPERSIM: OBJ_FILE_UTILS] Finished.")

        def __repr__(self):

            _str = ""
            _str = _str + "material_param_map\n" + str(self.material_param_map) + "\n"

            return _str

    return mtl_file(filename)



def load_obj_file(filename):
    
    class obj_file:

        def __init__(self, filename):

            self._vertices  = []
            self._texcoords = []
            self._normals   = []
            self._faces     = []
            
            self._material_files = []
            self._material_names = []
            self._object_names   = []
            self._group_names    = []
            
            object_name_curr   = "_NULL_OBJECT"
            group_name_curr    = "_NULL_GROUP"
            material_name_curr = "_NULL_MATERIAL"

            print("[HYPERSIM: OBJ_FILE_UTILS] Begin load_obj_file...")
            print("[HYPERSIM: OBJ_FILE_UTILS] Parsing " + filename + "...")

            for line in open(filename, "r"):
                
                line = line.strip()

                # hack for OBJ files exported from Unreal
                if line.startswith("#") or line.startswith("\xef\xbb\xbf#"):
                    continue

                values = line.split()
                
                if not values or len(values) == 0:
                    continue

                if values[0] in ["mtllib", "matlib"]:
                    try:
                        material_file = values[1]
                    except ValueError:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        material_file = "_ERROR_MATERIAL_FILE"
                    self._material_files.append(material_file)

                elif values[0] == "v":
                    if len(values) == 4:
                        try:
                            vertex = [float(values[1]), float(values[2]), float(values[3])]
                        except ValueError:
                            print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                            vertex = [0.0,0.0,0.0]
                    else:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        vertex = [0.0,0.0,0.0]
                    self._vertices.append(vertex)

                elif values[0] == "vn":
                    if len(values) == 4:
                        try:
                            vertex_normal = [float(values[1]), float(values[2]), float(values[3])]
                        except ValueError:
                            print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + values)
                            vertex_normal = [0.0,0.0,0.0]
                    else:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        vertex_normal = [0.0,0.0,0.0]
                    self._normals.append(vertex_normal)

                elif values[0] == "vt":
                    if len(values) == 3:
                        try:
                            vertex_texcoords = [float(values[1]), float(values[2])]
                        except ValueError:
                            print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                            vertex_texcoords = [0.0,0.0]
                    elif len(values) == 4:
                        try:
                            # HACK: in this case we assume 3 texture coordinates are exported in the obj file, but only the first 2 are stored
                            vertex_texcoords = [float(values[1]), float(values[2])]
                        except ValueError:
                            print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                            vertex_texcoords = [0.0,0.0]
                    else:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        vertex_texcoords = [0.0,0.0]                        
                    self._texcoords.append(vertex_texcoords)

                elif values[0] == "o":
                    try:
                        object_name_curr = values[1]
                    except ValueError:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        object_name_curr = "_ERROR_OBJECT"
                    self._object_names.append(object_name_curr)

                elif values[0] == "g":
                    try:
                        group_name_curr = values[1]
                    except ValueError:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        group_name_curr = "_ERROR_GROUP"
                    self._group_names.append(group_name_curr)

                elif values[0] in ("usemtl", "usemat"):
                    try:
                        material_name_curr = values[1]
                    except ValueError:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        material_name_curr = "_ERROR_MATERIAL"
                    self._material_names.append(material_name_curr)

                elif values[0] == "f":

                    face_vi  = []
                    face_vti = []
                    face_vni = []

                    if len(values) == 4:

                        for v in values[1:4]:
                            w = v.split("/")
                            # v1
                            if len(w) == 1:
                                try:
                                    f_vi = int(w[0])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vi = 0
                                face_vi.append(f_vi)
                            # v1/vt1
                            elif len(w) == 2:
                                try:
                                    f_vi = int(w[0])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vi = 0
                                try:
                                    f_vti = int(w[1])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vti = 0
                                face_vi.append(f_vi)
                                face_vti.append(f_vti)
                            # v1//vn1
                            elif len(w) == 3 and len(w[1]) == 0:
                                try:
                                    f_vi = int(w[0])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vi = 0
                                try:
                                    f_vni = int(w[2])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vni = 0
                                face_vi.append(f_vi)
                                face_vni.append(f_vni)
                            # v1/vt1/vn1
                            elif len(w) == 3 and len(w[1]) > 0:
                                try:
                                    f_vi = int(w[0])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vi = 0
                                try:
                                    f_vti = int(w[1])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vti = 0
                                try:
                                    f_vni = int(w[2])
                                except ValueError:
                                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                                    f_vni = 0
                                face_vi.append(f_vi)
                                face_vti.append(f_vti)
                                face_vni.append(f_vni)
                            else:
                                print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))

                    else:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))

                    if len(face_vi) != 3:
                        print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        face_vi = [0,0,0] # OBJ files are 1-indexed, so [0,0,0] is equivalent to assigning [null,null,null]

                    if len(face_vti) != 3:
                        if len(face_vti) != 0:
                            print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        face_vti = [0,0,0] # OBJ files are 1-indexed, so [0,0,0] is equivalent to assigning [null,null,null]

                    if len(face_vni) != 3:
                        if len(face_vni) != 0:
                            print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + " ".join(values))
                        face_vni = [0,0,0]  # OBJ files are 1-indexed, so [0,0,0] is equivalent to assigning [null,null,null]

                    self._faces.append((object_name_curr, group_name_curr, material_name_curr, face_vi, face_vti, face_vni))

                else:
                    print("[HYPERSIM: OBJ_FILE_UTILS] ERROR: Couldn't parse: " + line)
        
            print("[HYPERSIM: OBJ_FILE_UTILS] Loading material files...")

            self.material_file_data = {}
            self.material_param_map = {}

            for material_file in self._material_files:
                material_file_data = load_mtl_file(os.path.dirname(os.path.abspath(filename)) + "/" + material_file)
                self.material_file_data[material_file] = material_file_data
                self.material_param_map.update(material_file_data.material_param_map)

            print("[HYPERSIM: OBJ_FILE_UTILS] Uniquifying object names, group names, and material names...")

            self.object_names   = pd.Series(self._object_names).drop_duplicates().tolist()
            self.group_names    = pd.Series(self._group_names).drop_duplicates().tolist()
            self.material_names = pd.Series(self._material_names).drop_duplicates().tolist()

            print("[HYPERSIM: OBJ_FILE_UTILS] Constructing numpy arrays...")

            self.vertices  = array(self._vertices)
            self.texcoords = array(self._texcoords)
            self.normals   = array(self._normals)

            object_name_id_map   = dict(zip(self.object_names,   range(len(self.object_names))))
            group_name_id_map    = dict(zip(self.group_names,    range(len(self.group_names))))
            material_name_id_map = dict(zip(self.material_names, range(len(self.material_names))))

            object_name_id_map["_NULL_OBJECT"] = -1
            group_name_id_map["_NULL_GROUP"] = -1
            material_name_id_map["_NULL_MATERIAL"] = -1

            self.faces_oi  = array([ object_name_id_map[f[0]]   for f in self._faces ])
            self.faces_gi  = array([ group_name_id_map[f[1]]    for f in self._faces ])
            self.faces_mi  = array([ material_name_id_map[f[2]] for f in self._faces ])
            self.faces_vi  = array([ f[3] for f in self._faces ]) - 1
            self.faces_vti = array([ f[4] for f in self._faces ]) - 1
            self.faces_vni = array([ f[5] for f in self._faces ]) - 1

            print("[HYPERSIM: OBJ_FILE_UTILS] Finished.")

        def __repr__(self):
            
            _str = ""
            _str = _str + "material_file_data\n" + str(self.material_file_data) + "\n"
            _str = _str + "object_names\n"       + str(self.object_names)       + "\n"
            _str = _str + "group_names\n"        + str(self.group_names)        + "\n"
            _str = _str + "material_names\n"     + str(self.material_names)     + "\n"
            _str = _str + "material_param_map\n" + str(self.material_param_map) + "\n"
            _str = _str + "vertices\n"           + str(self.vertices.dtype)     + "\n" + str(self.vertices.shape)  + "\n" + str(self.vertices)  + "\n"
            _str = _str + "texcoords\n"          + str(self.texcoords.dtype)    + "\n" + str(self.texcoords.shape) + "\n" + str(self.texcoords) + "\n"
            _str = _str + "normals\n"            + str(self.normals.dtype)      + "\n" + str(self.normals.shape)   + "\n" + str(self.normals)   + "\n"
            _str = _str + "faces_oi\n"           + str(self.faces_oi.dtype)     + "\n" + str(self.faces_oi.shape)  + "\n" + str(self.faces_oi)  + "\n"
            _str = _str + "faces_gi\n"           + str(self.faces_gi.dtype)     + "\n" + str(self.faces_gi.shape)  + "\n" + str(self.faces_gi)  + "\n"
            _str = _str + "faces_mi\n"           + str(self.faces_mi.dtype)     + "\n" + str(self.faces_mi.shape)  + "\n" + str(self.faces_mi)  + "\n"
            _str = _str + "faces_vi\n"           + str(self.faces_vi.dtype)     + "\n" + str(self.faces_vi.shape)  + "\n" + str(self.faces_vi)  + "\n"
            _str = _str + "faces_vti\n"          + str(self.faces_vti.dtype)    + "\n" + str(self.faces_vti.shape) + "\n" + str(self.faces_vti) + "\n"
            _str = _str + "faces_vni\n"          + str(self.faces_vni.dtype)    + "\n" + str(self.faces_vni.shape) + "\n" + str(self.faces_vni) + "\n"

            return _str

    return obj_file(filename)
