#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import ntpath
import os
import pandas as pd
import posixpath
import time
import shutil
import vray

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--shared_asset_dir", required=True)
parser.add_argument("--platform_when_rendering", required=True)
parser.add_argument("--shared_asset_dir_when_rendering", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_file)
assert args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix" or args.platform_when_rendering == "windows"

if args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix":
    os_path_module_when_rendering = posixpath
else:
    os_path_module_when_rendering = ntpath



print("Begin...")



fragment_file = os.path.join(args.shared_asset_dir, "_hypersim_textured_quads.vrscene")

if not os.path.exists(args.shared_asset_dir): os.makedirs(args.shared_asset_dir)



# read params file
df = pd.read_csv(args.in_file)
assert df.shape[0] <= 9999



def generate_plugins_for_quad(quad_id, params):

    plugins = []

    #
    # BitmapBuffer
    #
    # These parameters may or may not be appropriate, in particular the "gamma" and "color_space"
    # parameters, depending on the image file. See the "Bitmaps" section of the V-Ray documentation
    # for more details: https://docs.chaosgroup.com/display/APPSDK/Creating+scenes+for+V-Ray
    #
    
    bitmap_buffer = renderer.classes.BitmapBuffer("HYPERSIM_BITMAP_BUFFER_" + quad_id)
    bitmap_buffer.filter_type       = -1
    bitmap_buffer.filter_blur       = 1
    bitmap_buffer.color_space       = 0
    bitmap_buffer.gamma             = 1
    bitmap_buffer.maya_compatible   = 0
    bitmap_buffer.interpolation     = 3
    bitmap_buffer.file              = params["image_file"]
    bitmap_buffer.load_file         = 1
    bitmap_buffer.ifl_start_frame   = 0
    bitmap_buffer.ifl_playback_rate = 1
    bitmap_buffer.ifl_end_condition = 0
    plugins.append(bitmap_buffer)

    # UVWGenChannel
    uvw_gen_channel = renderer.classes.UVWGenChannel("HYPERSIM_UVW_GEN_CHANNEL_" + quad_id)
    uvw_gen_channel.uvw_transform = \
        vray.Transform(vray.Matrix(vray.Vector(1, 0, 0),
                                   vray.Vector(0, 1, 0),
                                   vray.Vector(0, 0, 1)),
                       vray.Vector(0, 0, 0))
    uvw_gen_channel.wrap_u        = 1
    uvw_gen_channel.wrap_v        = 1
    uvw_gen_channel.crop_u        = 0
    uvw_gen_channel.crop_v        = 0
    uvw_gen_channel.wrap_mode     = 1
    uvw_gen_channel.duvw_scale    = 1
    uvw_gen_channel.uvw_channel   = 1
    plugins.append(uvw_gen_channel)

    # TexBitmap
    tex_bitmap = renderer.classes.TexBitmap("HYPERSIM_TEX_BITMAP_" + quad_id)
    tex_bitmap.alpha_from_intensity = 2
    tex_bitmap.nouvw_color          = vray.AColor(0, 0, 0, 0)
    tex_bitmap.uvwgen               = uvw_gen_channel
    tex_bitmap.placement_type       = 0
    tex_bitmap.u                    = 0
    tex_bitmap.v                    = 0
    tex_bitmap.w                    = 1
    tex_bitmap.h                    = 1
    tex_bitmap.bitmap               = bitmap_buffer
    plugins.append(tex_bitmap)

    # TexCombineColor
    tex_combine_color = renderer.classes.TexCombineColor("HYPERSIM_TEX_COMBINE_COLOR_" + quad_id)
    tex_combine_color.color              = vray.Color(0, 0, 0)
    tex_combine_color.texture            = tex_bitmap
    tex_combine_color.texture_multiplier = 1
    plugins.append(tex_combine_color)

    # BRDFVRayMtl
    brdf_vray_mtl = renderer.classes.BRDFVRayMtl("HYPERSIM_BRDF_VRAY_MTL_" + quad_id)
    brdf_vray_mtl.opacity                      = 1
    brdf_vray_mtl.opacity_mode                 = 2
    brdf_vray_mtl.diffuse                      = tex_combine_color
    brdf_vray_mtl.roughness                    = 0
    brdf_vray_mtl.roughness_model              = 0
    brdf_vray_mtl.self_illumination            = vray.AColor(0, 0, 0, 1)
    brdf_vray_mtl.self_illumination_gi         = 0
    brdf_vray_mtl.compensate_camera_exposure   = 0
    brdf_vray_mtl.brdf_type                    = 4
    brdf_vray_mtl.reflect                      = vray.AColor(0, 0, 0, 1)
    brdf_vray_mtl.reflect_glossiness           = 1
    brdf_vray_mtl.hilight_glossiness_lock      = 1
    brdf_vray_mtl.gtr_gamma                    = 2
    brdf_vray_mtl.gtr_oldGamma                 = 0
    brdf_vray_mtl.fresnel                      = 1
    brdf_vray_mtl.fresnel_ior                  = 1.6
    brdf_vray_mtl.fresnel_ior_lock             = 1
    brdf_vray_mtl.metalness                    = 0
    brdf_vray_mtl.reflect_subdivs              = 8
    brdf_vray_mtl.reflect_trace                = 1
    brdf_vray_mtl.reflect_depth                = 5
    brdf_vray_mtl.reflect_exit_color           = vray.Color(0, 0, 0)
    brdf_vray_mtl.hilight_soften               = 0
    brdf_vray_mtl.reflect_dim_distance_on      = 0
    brdf_vray_mtl.reflect_dim_distance         = 100
    brdf_vray_mtl.reflect_dim_distance_falloff = 0
    brdf_vray_mtl.reflect_affect_alpha         = 0
    brdf_vray_mtl.anisotropy                   = 0
    brdf_vray_mtl.anisotropy_rotation          = 0
    brdf_vray_mtl.anisotropy_derivation        = 0
    brdf_vray_mtl.anisotropy_axis              = 2
    brdf_vray_mtl.refract                      = vray.AColor(0, 0, 0, 1)
    brdf_vray_mtl.refract_ior                  = 1.6
    brdf_vray_mtl.refract_glossiness           = 1
    brdf_vray_mtl.refract_subdivs              = 8
    brdf_vray_mtl.refract_trace                = 1
    brdf_vray_mtl.refract_depth                = 5
    brdf_vray_mtl.refract_exit_color_on        = 0
    brdf_vray_mtl.refract_exit_color           = vray.Color(0, 0, 0)
    brdf_vray_mtl.refract_affect_alpha         = 0
    brdf_vray_mtl.refract_affect_shadows       = 1
    brdf_vray_mtl.dispersion_on                = 0
    brdf_vray_mtl.dispersion                   = 50
    brdf_vray_mtl.fog_color                    = vray.Color(1, 1, 1)
    brdf_vray_mtl.fog_mult                     = 1
    brdf_vray_mtl.fog_bias                     = 0
    brdf_vray_mtl.fog_unit_scale_on            = 1
    brdf_vray_mtl.translucency                 = 0
    brdf_vray_mtl.translucency_color           = vray.AColor(1, 1, 1, 1)
    brdf_vray_mtl.translucency_light_mult      = 1
    brdf_vray_mtl.translucency_scatter_dir     = 1
    brdf_vray_mtl.translucency_scatter_coeff   = 0
    brdf_vray_mtl.translucency_thickness       = 1000
    brdf_vray_mtl.option_double_sided          = 1
    brdf_vray_mtl.option_reflect_on_back       = 0
    brdf_vray_mtl.option_glossy_rays_as_gi     = 1
    brdf_vray_mtl.option_cutoff                = 0.001
    brdf_vray_mtl.option_use_irradiance_map    = 1
    brdf_vray_mtl.option_energy_mode           = 0
    brdf_vray_mtl.option_fix_dark_edges        = 1
    brdf_vray_mtl.option_glossy_fresnel        = 1
    brdf_vray_mtl.option_use_roughness         = 0
    brdf_vray_mtl.use_environment_override     = 0
    brdf_vray_mtl.environment_priority         = 0
    plugins.append(brdf_vray_mtl)

    # MtlSingleBRDF
    mtl_single_brdf = renderer.classes.MtlSingleBRDF("HYPERSIM_MTL_SINGLE_BRDF_" + quad_id)
    mtl_single_brdf.brdf         = brdf_vray_mtl
    mtl_single_brdf.double_sided = 1
    mtl_single_brdf.scene_name   = vray.List()
    plugins.append(mtl_single_brdf)

    quad_corner_obj_00_vray = matrix( [ 0,                   0,                   0 ] ).T
    quad_corner_obj_01_vray = matrix( [ params["obj_len_x"], 0,                   0 ] ).T
    quad_corner_obj_10_vray = matrix( [ 0,                   params["obj_len_y"], 0 ] ).T
    quad_corner_obj_11_vray = matrix( [ params["obj_len_x"], params["obj_len_y"], 0 ] ).T

    # GeomStaticMesh
    geom_static_mesh = renderer.classes.GeomStaticMesh("HYPERSIM_GEOM_STATIC_MESH_" + quad_id)
    geom_static_mesh.vertices         = vray.List( [ vray.Vector( quad_corner_obj_00_vray[0], quad_corner_obj_00_vray[1], quad_corner_obj_00_vray[2] ),
                                                     vray.Vector( quad_corner_obj_01_vray[0], quad_corner_obj_01_vray[1], quad_corner_obj_01_vray[2] ),
                                                     vray.Vector( quad_corner_obj_10_vray[0], quad_corner_obj_10_vray[1], quad_corner_obj_10_vray[2] ),
                                                     vray.Vector( quad_corner_obj_11_vray[0], quad_corner_obj_11_vray[1], quad_corner_obj_11_vray[2] ) ] )
    geom_static_mesh.faces            = vray.List( [2,0,3,1,3,0] )
    geom_static_mesh.normals          = vray.List( [ vray.Vector(0, 0, 1),
                                                     vray.Vector(0, 0, 1),
                                                     vray.Vector(0, 0, 1),
                                                     vray.Vector(0, 0, 1) ] )
    geom_static_mesh.faceNormals      = vray.List( [2,0,3,1,3,0] )
    geom_static_mesh.map_channels     = vray.List( [ vray.List( [ 1,
                                                                  vray.List( [ vray.Vector(0, 0, 0), vray.Vector(1, 0, 0), vray.Vector(0, 0, 0), vray.Vector(1, 0, 0), vray.Vector(0, 0, 0), vray.Vector(1, 0, 0), vray.Vector(0, 1, 0), vray.Vector(1, 1, 0) ] ),
                                                                  vray.List( [6,4,7,5,7,4] ) ] ) ] )
    geom_static_mesh.edge_visibility  = vray.List( [45] )
    geom_static_mesh.smooth_derivs    = 0
    geom_static_mesh.dynamic_geometry = 0
    plugins.append(geom_static_mesh)

    transform = \
        vray.Transform(vray.Matrix(vray.Vector(params["rotation_world_from_obj_00"], params["rotation_world_from_obj_10"], params["rotation_world_from_obj_20"]),
                                   vray.Vector(params["rotation_world_from_obj_01"], params["rotation_world_from_obj_11"], params["rotation_world_from_obj_21"]),
                                   vray.Vector(params["rotation_world_from_obj_02"], params["rotation_world_from_obj_12"], params["rotation_world_from_obj_22"])),
                       vray.Vector(params["translation_world_from_obj_x"], params["translation_world_from_obj_y"], params["translation_world_from_obj_z"]))

    # Node
    node = renderer.classes.Node("HYPERSIM_NODE_" + quad_id)
    node.transform          = transform
    node.geometry           = geom_static_mesh
    node.material           = mtl_single_brdf
    node.nsamples           = 1
    node.visible            = 1
    node.primary_visibility = 1
    node.scene_name         = vray.List()
    plugins.append(node)

    plugins.reverse()

    return plugins



renderer = vray.VRayRenderer()
def log_msg(renderer, message, level, instant):
    print(str(instant) + " " + str(level) + " " + message)
renderer.setOnLogMessage(log_msg)
time.sleep(0.5)

plugin_export_list = []

for dfi in df.itertuples():

    params = df.loc[dfi.Index].copy()

    quad_id                       = "textured_quad_%04d" % dfi.Index
    in_image_file                 = params["image_file"]
    image_filename                = os.path.basename(in_image_file)
    out_image_file                = os.path.join(args.shared_asset_dir, image_filename)
    out_image_file_when_rendering = os_path_module_when_rendering.join(args.shared_asset_dir_when_rendering, image_filename)

    # copy image file to the shared asset folder
    if os.path.abspath(in_image_file) != os.path.abspath(out_image_file):
        shutil.copy(in_image_file, out_image_file)

    # modify quad params to refer to the image file in the shared asset folder
    params["image_file"] = out_image_file_when_rendering

    # generate plugins for quad
    plugins = generate_plugins_for_quad(quad_id, params)

    # add plugins to the global export list
    plugin_export_list = plugin_export_list + plugins

# save scene fragment
options = {"hexArrays" : False, "pluginExportList" : plugin_export_list}
renderer.export(fragment_file, options)
print("Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("Finished.")
