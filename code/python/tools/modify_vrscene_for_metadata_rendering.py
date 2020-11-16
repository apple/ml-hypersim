#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import time
import vray

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_file", required=True)
parser.add_argument("--generate_images_for_geometry_metadata", action="store_true")
parser.add_argument("--generate_images_for_compositing", action="store_true")
parser.add_argument("--generate_images_for_denoising", action="store_true")
parser.add_argument("--reduce_image_quality")
args = parser.parse_args()

assert os.path.exists(args.in_file)



print("[HYPERSIM: MODIFY_VRSCENE_FOR_METADATA_RENDERING] Begin...")



output_dir = os.path.dirname(args.out_file)
if output_dir == "":
    output_dir = "."

if not os.path.exists(output_dir): os.makedirs(output_dir)



renderer = vray.VRayRenderer()
def log_msg(renderer, message, level, instant):
    print(str(instant) + " " + str(level) + " " + message)
renderer.setOnLogMessage(log_msg)
renderer.load(args.in_file)
time.sleep(0.5)



# SettingsEXR
settings_exr = renderer.classes.SettingsEXR.getInstanceOrCreate()
settings_exr.bits_per_channel  = 32 # set 32-bits-per-channel for EXR images
settings_exr.write_integer_ids = 1  # write integer object IDs



if args.generate_images_for_geometry_metadata:

    # VRayPosition
    tex_sampler_position = renderer.classes.TexSampler("HYPERSIM_TEX_SAMPLER_POSITION")

    tex_vector_to_color_position = renderer.classes.TexVectorToColor("HYPERSIM_TEX_VECTOR_TO_COLOR_POSITION")
    tex_vector_to_color_position.input = tex_sampler_position.getName() + "::point"

    render_channel_extra_tex_position = renderer.classes.RenderChannelExtraTex("HYPERSIM_RENDER_CHANNEL_EXTRA_TEX_POSITION")
    render_channel_extra_tex_position.name                 = "VRayPosition"
    render_channel_extra_tex_position.consider_for_aa      = 0
    render_channel_extra_tex_position.affect_matte_objects = 1
    render_channel_extra_tex_position.texmap               = tex_vector_to_color_position.getName()
    render_channel_extra_tex_position.filtering            = 0
    render_channel_extra_tex_position.force_32_bit_output  = 1

    # VRayNormal
    tex_sampler_normal = renderer.classes.TexSampler("HYPERSIM_TEX_SAMPLER_NORMAL")

    tex_vector_to_color_normal = renderer.classes.TexVectorToColor("HYPERSIM_TEX_VECTOR_TO_COLOR_NORMAL")
    tex_vector_to_color_normal.input = tex_sampler_normal.getName() + "::normal"

    render_channel_extra_tex_normal = renderer.classes.RenderChannelExtraTex("HYPERSIM_RENDER_CHANNEL_EXTRA_TEX_NORMAL")
    render_channel_extra_tex_normal.name                 = "VRayNormal"
    render_channel_extra_tex_normal.consider_for_aa      = 0
    render_channel_extra_tex_normal.affect_matte_objects = 1
    render_channel_extra_tex_normal.texmap               = tex_vector_to_color_normal.getName()
    render_channel_extra_tex_normal.filtering            = 0
    render_channel_extra_tex_normal.force_32_bit_output  = 1

    # VRayNormalBump
    tex_sampler_normal_bump = renderer.classes.TexSampler("HYPERSIM_TEX_SAMPLER_NORMAL_BUMP")

    tex_vector_to_color_normal_bump = renderer.classes.TexVectorToColor("HYPERSIM_TEX_VECTOR_TO_COLOR_NORMAL_BUMP")
    tex_vector_to_color_normal_bump.input = tex_sampler_normal_bump.getName() + "::bumpNormal"

    render_channel_extra_tex_normal_bump = renderer.classes.RenderChannelExtraTex("HYPERSIM_RENDER_CHANNEL_EXTRA_TEX_NORMAL_BUMP")
    render_channel_extra_tex_normal_bump.name                 = "VRayNormalBump"
    render_channel_extra_tex_normal_bump.consider_for_aa      = 0
    render_channel_extra_tex_normal_bump.affect_matte_objects = 1
    render_channel_extra_tex_normal_bump.texmap               = tex_vector_to_color_normal_bump.getName()
    render_channel_extra_tex_normal_bump.filtering            = 0
    render_channel_extra_tex_normal_bump.force_32_bit_output  = 1

    # VRayTexCoord
    tex_sampler_tex_coord = renderer.classes.TexSampler("HYPERSIM_TEX_SAMPLER_TEX_COORD")
    tex_sampler_tex_coord.uv_index=1;

    tex_vector_to_color_tex_coord = renderer.classes.TexVectorToColor("HYPERSIM_TEX_VECTOR_TO_COLOR_TEX_COORD")
    tex_vector_to_color_tex_coord.input = tex_sampler_tex_coord.getName() + "::uvCoord"

    render_channel_extra_tex_tex_coord = renderer.classes.RenderChannelExtraTex("HYPERSIM_RENDER_CHANNEL_EXTRA_TEX_TEX_COORD")
    render_channel_extra_tex_tex_coord.name                 = "VRayTexCoord"
    render_channel_extra_tex_tex_coord.consider_for_aa      = 0
    render_channel_extra_tex_tex_coord.affect_matte_objects = 1
    render_channel_extra_tex_tex_coord.texmap               = tex_vector_to_color_tex_coord.getName()
    render_channel_extra_tex_tex_coord.filtering            = 0
    render_channel_extra_tex_tex_coord.force_32_bit_output  = 1

    # # VRayRenderID
    # render_channel_render_id = renderer.classes.RenderChannelRenderID("HYPERSIM_RENDER_CHANNEL_RENDER_ID")
    # render_channel_render_id.enableDeepOutput = 1
    # render_channel_render_id.name             = "VRayRenderID"

    # VRayRenderEntityID
    render_channel_render_entity_id = renderer.classes.RenderChannelNodeID("HYPERSIM_RENDER_CHANNEL_RENDER_ENTITY_ID")
    render_channel_render_entity_id.enableDeepOutput = 1
    render_channel_render_entity_id.name             = "VRayRenderEntityID"



if args.generate_images_for_compositing:

    # SettingsColorMapping
    settings_color_mapping = renderer.classes.SettingsColorMapping.getInstances()[0]
    settings_color_mapping.type              = 0 # set color mapping type to "linear multiply"
    settings_color_mapping.affect_background = 1
    settings_color_mapping.dark_mult         = 1.0 # recommended by Vlado @ Chaos Group
    settings_color_mapping.bright_mult       = 1.0 # recommended by Vlado @ Chaos Group
    # settings_color_mapping.gamma             = 2.2 # not used
    settings_color_mapping.subpixel_mapping  = 0
    settings_color_mapping.clamp_output      = 0 # don't clamp the rendering output
    # settings_color_mapping.clamp_level       = 1 # not used
    settings_color_mapping.adaptation_only   = 2 # only color mapping is applied (recommended by Vlado @ Chaos Group)
    settings_color_mapping.linearWorkflow    = 0 # configures a setting for legacy scenes that we don't need, so turn off

    # SettingsVFB
    settings_vfb = renderer.classes.SettingsVFB.getInstances()[0]
    settings_vfb.cc_settings  = -1 # overwrite cached VFB settings
    settings_vfb.display_srgb = 0  # don't apply gamma correction when saving 8-bits-per-channel images

    # BRDFVRayMtl
    for b in renderer.classes.BRDFVRayMtl.getInstances():
        b.reflect_affect_alpha = 0 # recommended by Vlado @ Chaos Group

    # MtlWrapper
    for m in renderer.classes.MtlWrapper.getInstances():
        m.matte_surface = 0 # recommended by Vlado @ Chaos Group

    # VRayAtmosphere
    render_channel_color_atmosphere = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_ATMOSPHERE")
    render_channel_color_atmosphere.enableDeepOutput              = 1
    render_channel_color_atmosphere.name                          = "VRayAtmosphere"
    render_channel_color_atmosphere.alias                         = 100
    render_channel_color_atmosphere.color_mapping                 = 1
    render_channel_color_atmosphere.filtering                     = 1
    render_channel_color_atmosphere.denoise                       = 0

    # VRayBackground
    render_channel_color_background = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_BACKGROUND")
    render_channel_color_background.enableDeepOutput              = 1
    render_channel_color_background.name                          = "VRayBackground"
    render_channel_color_background.alias                         = 124
    render_channel_color_background.color_mapping                 = 1
    render_channel_color_background.filtering                     = 1
    render_channel_color_background.denoise                       = 0

    # VRayCaustics
    render_channel_color_caustics = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_CAUSTICS")
    render_channel_color_caustics.enableDeepOutput                = 1
    render_channel_color_caustics.name                            = "VRayCaustics"
    render_channel_color_caustics.alias                           = 109
    render_channel_color_caustics.color_mapping                   = 1
    render_channel_color_caustics.filtering                       = 1
    render_channel_color_caustics.denoise                         = 0

    # VRayDiffuseFilter
    render_channel_color_diffuse_filter = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_DIFFUSE_FILTER")
    render_channel_color_diffuse_filter.enableDeepOutput          = 1
    render_channel_color_diffuse_filter.name                      = "VRayDiffuseFilter"
    render_channel_color_diffuse_filter.alias                     = 101
    render_channel_color_diffuse_filter.color_mapping             = 0
    render_channel_color_diffuse_filter.filtering                 = 1
    render_channel_color_diffuse_filter.denoise                   = 0

    # VRayGlobalIllumination
    render_channel_color_global_illumination = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_GLOBAL_ILLUMINATION")
    render_channel_color_global_illumination.enableDeepOutput     = 1
    render_channel_color_global_illumination.name                 = "VRayGlobalIllumination"
    render_channel_color_global_illumination.alias                = 108
    render_channel_color_global_illumination.color_mapping        = 1
    render_channel_color_global_illumination.filtering            = 1
    render_channel_color_global_illumination.denoise              = 0

    # VRayLighting
    render_channel_color_global_illumination = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_LIGHTING")
    render_channel_color_global_illumination.enableDeepOutput     = 1
    render_channel_color_global_illumination.name                 = "VRayLighting"
    render_channel_color_global_illumination.alias                = 107
    render_channel_color_global_illumination.color_mapping        = 1
    render_channel_color_global_illumination.filtering            = 1
    render_channel_color_global_illumination.denoise              = 0

    # # VRayRawGlobalIllumination
    # render_channel_color_raw_global_illumination = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_RAW_GLOBAL_ILLUMINATION")
    # render_channel_color_raw_global_illumination.enableDeepOutput = 1
    # render_channel_color_raw_global_illumination.name             = "VRayRawGlobalIllumination"
    # render_channel_color_raw_global_illumination.alias            = 110
    # render_channel_color_raw_global_illumination.color_mapping    = 1
    # render_channel_color_raw_global_illumination.filtering        = 1
    # render_channel_color_raw_global_illumination.denoise          = 0

    # # VRayRawLighting
    # render_channel_color_raw_lighting = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_RAW_LIGHTING")
    # render_channel_color_raw_lighting.enableDeepOutput            = 1
    # render_channel_color_raw_lighting.name                        = "VRayRawLighting"
    # render_channel_color_raw_lighting.alias                       = 111
    # render_channel_color_raw_lighting.color_mapping               = 1
    # render_channel_color_raw_lighting.filtering                   = 1
    # render_channel_color_raw_lighting.denoise                     = 0

    # # VRayRawReflection
    # render_channel_color_raw_reflection = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_RAW_REFLECTION")
    # render_channel_color_raw_reflection.enableDeepOutput          = 1
    # render_channel_color_raw_reflection.name                      = "VRayRawReflection"
    # render_channel_color_raw_reflection.alias                     = 119
    # render_channel_color_raw_reflection.color_mapping             = 1
    # render_channel_color_raw_reflection.filtering                 = 1
    # render_channel_color_raw_reflection.denoise                   = 0

    # # VRayRawRefraction
    # render_channel_color_raw_refraction = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_RAW_REFRACTION")
    # render_channel_color_raw_refraction.enableDeepOutput          = 1
    # render_channel_color_raw_refraction.name                      = "VRayRawRefraction"
    # render_channel_color_raw_refraction.alias                     = 121
    # render_channel_color_raw_refraction.color_mapping             = 1
    # render_channel_color_raw_refraction.filtering                 = 1
    # render_channel_color_raw_refraction.denoise                   = 0

    # VRayRawTotalLighting
    render_channel_color_raw_total_lighting = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_RAW_TOTAL_LIGHTING")
    render_channel_color_raw_total_lighting.enableDeepOutput      = 1
    render_channel_color_raw_total_lighting.name                  = "VRayRawTotalLighting"
    render_channel_color_raw_total_lighting.alias                 = 130
    render_channel_color_raw_total_lighting.color_mapping         = 1
    render_channel_color_raw_total_lighting.filtering             = 1
    render_channel_color_raw_total_lighting.denoise               = 0

    # VRayReflection
    render_channel_color_reflection = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_REFLECTION")
    render_channel_color_reflection.enableDeepOutput              = 1
    render_channel_color_reflection.name                          = "VRayReflection"
    render_channel_color_reflection.alias                         = 102
    render_channel_color_reflection.color_mapping                 = 1
    render_channel_color_reflection.filtering                     = 1
    render_channel_color_reflection.denoise                       = 0

    # # VRayReflectionFilter
    # render_channel_color_reflection_filter = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_REFLECTION_FILTER")
    # render_channel_color_reflection_filter.enableDeepOutput       = 1
    # render_channel_color_reflection_filter.name                   = "VRayReflectionFilter"
    # render_channel_color_reflection_filter.alias                  = 118
    # render_channel_color_reflection_filter.color_mapping          = 0
    # render_channel_color_reflection_filter.filtering              = 1
    # render_channel_color_reflection_filter.denoise                = 0

    # VRayRefraction
    render_channel_color_refraction = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_REFRACTION")
    render_channel_color_refraction.enableDeepOutput              = 1
    render_channel_color_refraction.name                          = "VRayRefraction"
    render_channel_color_refraction.alias                         = 103
    render_channel_color_refraction.color_mapping                 = 1
    render_channel_color_refraction.filtering                     = 1
    render_channel_color_refraction.denoise                       = 0

    # # VRayRefractionFilter
    # render_channel_color_refraction_filter = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_REFRACTION_FILTER")
    # render_channel_color_refraction_filter.enableDeepOutput       = 1
    # render_channel_color_refraction_filter.name                   = "VRayRefractionFilter"
    # render_channel_color_refraction_filter.alias                  = 120
    # render_channel_color_refraction_filter.color_mapping          = 0
    # render_channel_color_refraction_filter.filtering              = 1
    # render_channel_color_refraction_filter.denoise                = 0

    # VRaySelfIllumination
    render_channel_color_self_illumination = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_SELF_ILLUMINATION")
    render_channel_color_self_illumination.enableDeepOutput       = 1
    render_channel_color_self_illumination.name                   = "VRaySelfIllumination"
    render_channel_color_self_illumination.alias                  = 104
    render_channel_color_self_illumination.color_mapping          = 1
    render_channel_color_self_illumination.filtering              = 1
    render_channel_color_self_illumination.denoise                = 0

    # VRaySpecular
    render_channel_color_specular = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_SPECULAR")
    render_channel_color_specular.enableDeepOutput                = 1
    render_channel_color_specular.name                            = "VRaySpecular"
    render_channel_color_specular.alias                           = 106
    render_channel_color_specular.color_mapping                   = 1
    render_channel_color_specular.filtering                       = 1
    render_channel_color_specular.denoise                         = 0

    # VRaySSS2
    render_channel_color_sss2 = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_SSS2")
    render_channel_color_sss2.enableDeepOutput                    = 1
    render_channel_color_sss2.name                                = "VRaySSS2"
    render_channel_color_sss2.alias                               = 133
    render_channel_color_sss2.color_mapping                       = 1
    render_channel_color_sss2.filtering                           = 1
    render_channel_color_sss2.denoise                             = 0

    # VRayTotalLighting
    render_channel_color_total_lighting = renderer.classes.RenderChannelColor("HYPERSIM_RENDER_CHANNEL_COLOR_TOTAL_LIGHTING")
    render_channel_color_total_lighting.enableDeepOutput          = 1
    render_channel_color_total_lighting.name                      = "VRayTotalLighting"
    render_channel_color_total_lighting.alias                     = 129
    render_channel_color_total_lighting.color_mapping             = 1
    render_channel_color_total_lighting.filtering                 = 1
    render_channel_color_total_lighting.denoise                   = 0



if args.generate_images_for_denoising:

    render_channel_denoiser = renderer.classes.RenderChannelDenoiser.getInstanceOrCreate()

    render_channel_denoiser.enableDeepOutput = 1
    render_channel_denoiser.enabled          = 1
    render_channel_denoiser.name             = "VRayDenoiser"
    render_channel_denoiser.engine           = 0
    render_channel_denoiser.mode             = 0
    render_channel_denoiser.type             = 0
    render_channel_denoiser.preset           = 1
    render_channel_denoiser.strength         = 1
    render_channel_denoiser.radius           = 10
    render_channel_denoiser.use_gpu          = 0



renderer.export(args.out_file)
print("[HYPERSIM: MODIFY_VRSCENE_FOR_METADATA_RENDERING] Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: MODIFY_VRSCENE_FOR_METADATA_RENDERING] Finished.")
