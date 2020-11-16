from pylab import *

import vray

def _set_vray_user_params(renderer):

    # SettingsOutput
    settings_output = renderer.classes.SettingsOutput.getInstanceOrCreate()
    settings_output.img_width  = 1024
    settings_output.img_height = 768

    # SettingsImageSampler
    settings_image_sampler = renderer.classes.SettingsImageSampler.getInstances()[0]
    settings_image_sampler.type                   = 3 # sampler type == progressive (0 is fixed; 1 is bucket; 2 is deprecated; 3 is progressive)
    settings_image_sampler.min_shade_rate         = 6 # recommended by Vlado @ Chaos Group
    settings_image_sampler.progressive_minSubdivs = 1
    settings_image_sampler.progressive_maxSubdivs = 24    # recommended by Vlado @ Chaos Group
    settings_image_sampler.progressive_threshold  = 0.01  # recommended by Vlado @ Chaos Group for fast renders
    settings_image_sampler.progressive_maxTime    = 180

    # SettingsGI
    settings_gi = renderer.classes.SettingsGI.getInstances()[0]
    settings_gi.on               = 1
    settings_gi.primary_engine   = 0
    settings_gi.secondary_engine = 3

    # SettingsLightCache
    settings_light_cache = renderer.classes.SettingsLightCache.getInstances()[0]
    settings_light_cache.subdivs         = 500
    settings_light_cache.show_calc_phase = 1

    # SettingsIrradianceMap
    settings_irradiance_map = renderer.classes.SettingsIrradianceMap.getInstances()[0]
    settings_irradiance_map.min_rate        = -3
    settings_irradiance_map.max_rate        = -1
    settings_irradiance_map.subdivs         = 50
    settings_irradiance_map.show_calc_phase = 1
    settings_irradiance_map.multipass       = 1

    # SettingsDMCSampler
    settings_dmc_sampler = renderer.classes.SettingsDMCSampler.getInstances()[0]
    settings_dmc_sampler.subdivs_mult = 0 # recommended by Vlado @ Chaos Group

    # CameraPhysical
    camera_physical = renderer.classes.CameraPhysical.getInstanceOrCreate()

    # camera type
    camera_physical.type                   = 0        # camera type == still cam (0 is a still camera with a regular shutter; 1 is a cinematic camera with a circular shutter; 2 is a shutterless video camera with a CCD matrix)

    # camera intrinsics
    camera_physical.specify_fov            = 1        # specify fov == enabled (when enabled, fov is specified directly instead of film gate and focal length)
    camera_physical.fov                    = 45.0 * np.pi / 180.0 # fov x (radians)
    camera_physical.film_width             = 1        # film gate (mm, not used but can't be 0 or nan)
    # camera_physical.focal_length           = np.nan # focal length (mm, not used)
    camera_physical.zoom_factor            = 1.0      # zoom factor

    # focus distance
    camera_physical.specify_focus          = 1        # specify focus == enabled (when enabled, focus distance is different from the target distance)
    camera_physical.focus_distance         = 1000     # focus distance (units not specified in documentation)

    # target distance
    camera_physical.targeted               = 0        # targeted mode == not targeted
    # camera_physical.target_distance        = np.nan # target distance (units not specified in documentation, not used)

    # exposure settings
    camera_physical.exposure               = 1        # manual exposure == enabled (when enabled, the f-number, shutter speed, and film speed settings will affect the image brightness)
    camera_physical.f_number               = 2        # f-number
    camera_physical.shutter_speed          = 300      # shutter speed (s^-1)
    camera_physical.shutter_angle          = 180      # shutter angle (degrees)
    camera_physical.shutter_offset         = 0        # shutter offset (degrees)
    camera_physical.ISO                    = 400      # film speed (ISO)
    camera_physical.white_balance          = vray.Color(1, 1, 1) # allows additional modification of the image output

    # depth-of-field and motion blur
    camera_physical.use_dof                = 0        # depth-of-field == disabled
    camera_physical.use_moblur             = 0        # motion blur == disabled

    # bokeh effects
    camera_physical.blades_enable          = 0        # bokeh effects == disabled
    # camera_physical.blades_num             = np.nan # number of blades for bokeh effects
    # camera_physical.blades_rotation        = np.nan # blade rotation for bokeh effects (radians)
    # camera_physical.center_bias            = np.nan # bias shape for bokeh effects
    # camera_physical.anisotropy             = np.nan # anisotropy for bokeh effects
    camera_physical.bmpaperture_enable     = 0        # apeture shape == analytic (0 is analytic; 1 uses an image to control the aperture shape, as well as any dirt or scratches that may affect the bokeh effects)
    # camera_physical.bmpaperture_resolution = np.nan # resolution at which the apeture shape texture will be sampled when calculating the bokeh effects

    # undocumented
    camera_physical.horizontal_shift       = 0        # horizontal lens shift
    camera_physical.horizontal_offset      = 0        # horizontal offset
    camera_physical.latency                = 0        # ?
    camera_physical.lens_shift             = 0        # ?
    camera_physical.subdivs                = 1        # ?
    camera_physical.vertical_offset        = 0        # vertical offset

    # lens distortion
    camera_physical.distortion             = 0        # distortion amount
    camera_physical.distortion_type        = 0        # distortion type == quadratic
    camera_physical.lens_file              = ""       # vrlens file

    # SettingsMotionBlur
    settings_motion_blur = renderer.classes.SettingsMotionBlur.getInstanceOrCreate()
    settings_motion_blur.on                 = 0
    settings_motion_blur.geom_samples       = 2
    settings_motion_blur.low_samples        = 1
    settings_motion_blur.duration           = 0.5
    settings_motion_blur.subdivs            = 1
    settings_motion_blur.bias               = 0
    settings_motion_blur.shutter_efficiency = 1
    settings_motion_blur.interval_center    = 0.5
    settings_motion_blur.camera_motion_blur = 0

    # SettingsCamera
    settings_camera = renderer.classes.SettingsCamera.getInstanceOrCreate()
    # settings_camera.fov = np.nan # fov x (radians, not used)

    # SettingsCameraDof
    settings_camera_dof = renderer.classes.SettingsCameraDof.getInstanceOrCreate()
    settings_camera_dof.on          = 0
    settings_camera_dof.aperture    = 5
    settings_camera_dof.center_bias = 0
    settings_camera_dof.focal_dist  = 200
    settings_camera_dof.sides_on    = 0
    settings_camera_dof.sides_num   = 5
    settings_camera_dof.rotation    = 0
    settings_camera_dof.anisotropy  = 0
    settings_camera_dof.subdivs     = 1
    settings_camera_dof.aperture    = 5

    # FilterArea
    filter_area = renderer.classes.FilterArea.getInstanceOrCreate()
    filter_area.size = 1.42 # must be larger than a pixel diagonal, i.e., sqrt(2) == 1.414...

    retval = { "SettingsOutput"        : settings_output,
               "SettingsImageSampler"  : settings_image_sampler,
               "SettingsGI"            : settings_gi,
               "SettingsLightCache"    : settings_light_cache,
               "SettingsIrradianceMap" : settings_irradiance_map,
               "CameraPhysical"        : camera_physical,
               "SettingsMotionBlur"    : settings_motion_blur,
               "SettingsCamera"        : settings_camera,
               "SettingsCameraDof"     : settings_camera_dof,
               "FilterArea"            : filter_area }

    return retval
