from pylab import *

import vray

def _set_vray_user_params(renderer):

    # SettingsOutput
    settings_output = renderer.classes.SettingsOutput.getInstanceOrCreate()
    settings_output.img_width  = 1024
    settings_output.img_height = 768

    # SettingsCamera
    settings_camera = renderer.classes.SettingsCamera.getInstanceOrCreate()
    settings_camera.type = 0      # set type to pinhole
    settings_camera.fov  = pi/3.0 # set fov_x to pi/3 to match DIODE dataset

    # SettingsCameraDof
    settings_camera_dof = renderer.classes.SettingsCameraDof.getInstanceOrCreate()
    settings_camera_dof.on = 0 # turn off depth of field

    # SettingsImageSampler
    settings_image_sampler = renderer.classes.SettingsImageSampler.getInstanceOrCreate()
    settings_image_sampler.type                   = 3 # sampler type == progressive (0 is fixed; 1 is bucket; 2 is deprecated; 3 is progressive)
    settings_image_sampler.min_shade_rate         = 6 # recommended by Vlado @ Chaos Group
    settings_image_sampler.progressive_minSubdivs = 1
    settings_image_sampler.progressive_maxSubdivs = 24    # recommended by Vlado @ Chaos Group
    settings_image_sampler.progressive_threshold  = 0.01  # recommended by Vlado @ Chaos Group for fast renders
    settings_image_sampler.progressive_maxTime    = 5

    # SettingsGI
    settings_gi = renderer.classes.SettingsGI.getInstanceOrCreate()
    settings_gi.on               = 1
    settings_gi.primary_engine   = 0
    settings_gi.secondary_engine = 3

    # SettingsLightCache
    settings_light_cache = renderer.classes.SettingsLightCache.getInstanceOrCreate()
    settings_light_cache.subdivs         = 500
    settings_light_cache.show_calc_phase = 1

    # SettingsIrradianceMap
    settings_irradiance_map = renderer.classes.SettingsIrradianceMap.getInstanceOrCreate()
    settings_irradiance_map.min_rate        = -3
    settings_irradiance_map.max_rate        = -1
    settings_irradiance_map.subdivs         = 50
    settings_irradiance_map.show_calc_phase = 1
    settings_irradiance_map.multipass       = 1

    # SettingsDMCSampler
    settings_dmc_sampler = renderer.classes.SettingsDMCSampler.getInstanceOrCreate()
    settings_dmc_sampler.subdivs_mult = 0 # recommended by Vlado @ Chaos Group

    # SettingsEnvironment
    settings_environment = renderer.classes.SettingsEnvironment.getInstanceOrCreate()

    # we set the background color to be brighter than (1,1,1), so it will still
    # be white after color mapping. we choose to set it to (4,4,4) arbitrarily.
    settings_environment.bg_color              = vray.Color(4,4,4)
    settings_environment.gi_color              = vray.Color(4,4,4)
    settings_environment.reflect_color         = vray.Color(4,4,4)
    settings_environment.refract_color         = vray.Color(4,4,4)
    settings_environment.secondary_matte_color = vray.Color(4,4,4)

    if isinstance(settings_environment.bg_tex,              vray.AColor): settings_environment.bg_tex              = vray.AColor(4,4,4,1)
    if isinstance(settings_environment.gi_tex,              vray.AColor): settings_environment.gi_tex              = vray.AColor(4,4,4,1)
    if isinstance(settings_environment.reflect_tex,         vray.AColor): settings_environment.reflect_tex         = vray.AColor(4,4,4,1)
    if isinstance(settings_environment.refract_tex,         vray.AColor): settings_environment.refract_tex         = vray.AColor(4,4,4,1)
    if isinstance(settings_environment.secondary_matte_tex, vray.AColor): settings_environment.secondary_matte_tex = vray.AColor(4,4,4,1)

    # RenderView
    render_view = renderer.classes.RenderView.getInstanceOrCreate()
    render_view.orthographic = False

    # CameraPhysical
    camera_physicals = renderer.classes.CameraPhysical.getInstances()
    for c in camera_physicals:
        c.specify_fov     = 1
        c.fov             = pi/3.0 # set fov_x to pi/3 to match DIODE dataset
        c.use_dof         = 0      # turn off depth of field
        c.use_moblur      = 0      # turn off motion blur
        c.blades_enable   = 0      # turn off bokeh
        c.distortion_type = 0      # distortion type == quadratic
        c.distortion      = 0.0    # distortion amount

    retval = { "SettingsOutput"        : settings_output,
               "SettingsCamera"        : settings_camera,
               "SettingsCameraDof"     : settings_camera_dof,
               "SettingsImageSampler"  : settings_image_sampler,
               "SettingsGI"            : settings_gi,
               "SettingsLightCache"    : settings_light_cache,
               "SettingsIrradianceMap" : settings_irradiance_map,
               "SettingsDMCSampler"    : settings_dmc_sampler,
               "SettingsEnvironment"   : settings_environment,
               "RenderView"            : render_view,
               "CameraPhysical"        : camera_physicals }

    return retval
