from pylab import *

import argparse
import fnmatch
import inspect
import os
import pandas as pd
import scipy.linalg
import vray

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--out_file", required=True)
parser.add_argument("--scene_names")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)

import path_utils
path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_CAMERA_PARAMETERS_METADATA] Begin...")



df_camera_parameters_columns = [
    "scene_name",
    "settings_output_img_height",
    "settings_output_img_width",
    "settings_units_info_meters_scale",
    "use_camera_physical",
    "camera_physical_anisotropy",
    "camera_physical_blades_enable",
    "camera_physical_blades_num",
    "camera_physical_blades_rotation",
    "camera_physical_bmpaperture_affects_exposure",
    "camera_physical_bmpaperture_enable",
    "camera_physical_bmpaperture_resolution",
    "camera_physical_bmpaperture_tex",
    "camera_physical_center_bias",
    "camera_physical_distortion",
    "camera_physical_distortion_tex",
    "camera_physical_distortion_type",
    "camera_physical_dof_display_threshold",
    "camera_physical_dont_affect_settings",
    "camera_physical_enable_thin_lens_equation",
    "camera_physical_exposure",
    "camera_physical_f_number",
    "camera_physical_film_width",
    "camera_physical_focal_length",
    "camera_physical_focus_distance",
    "camera_physical_fov",
    "camera_physical_horizontal_offset",
    "camera_physical_horizontal_shift",
    "camera_physical_ISO",
    "camera_physical_latency",
    "camera_physical_lens_file",
    "camera_physical_lens_shift",
    "camera_physical_optical_vignetting",
    "camera_physical_rolling_shutter_duration",
    "camera_physical_rolling_shutter_mode",
    "camera_physical_shutter_angle",
    "camera_physical_shutter_offset",
    "camera_physical_shutter_speed",
    "camera_physical_specify_focus",
    "camera_physical_specify_fov",
    "camera_physical_subdivs",
    "camera_physical_target_distance",
    "camera_physical_targeted",
    "camera_physical_type",
    "camera_physical_use_dof",
    "camera_physical_use_moblur",
    "camera_physical_vertical_offset",
    "camera_physical_vignetting",
    "camera_physical_white_balance",
    "camera_physical_zoom_factor",
    "settings_camera_auto_corrections_mode",
    "settings_camera_auto_exposure",
    "settings_camera_auto_exposure_compensation",
    "settings_camera_auto_fit",
    "settings_camera_auto_white_balance",
    "settings_camera_curve",
    "settings_camera_dist",
    "settings_camera_dont_affect_settings",
    "settings_camera_fov",
    "settings_camera_height",
    "settings_camera_image_planes",
    "settings_camera_type",
    "M_cam_from_uv_00", "M_cam_from_uv_01", "M_cam_from_uv_02",
    "M_cam_from_uv_10", "M_cam_from_uv_11", "M_cam_from_uv_12",
    "M_cam_from_uv_20", "M_cam_from_uv_21", "M_cam_from_uv_22",
    "M_proj_00", "M_proj_01", "M_proj_02", "M_proj_03",
    "M_proj_10", "M_proj_11", "M_proj_12", "M_proj_13",
    "M_proj_20", "M_proj_21", "M_proj_22", "M_proj_23",
    "M_proj_30", "M_proj_31", "M_proj_32", "M_proj_33" ]

df_camera_parameters = pd.DataFrame(columns=df_camera_parameters_columns)

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



for s in scenes:

    #
    # We load the vrscene precisely as it has been exported from 3ds Max,
    # before it has been modified by the Hypersim pipeline in any way. This
    # is done as a matter of convenience, so that this script can be run
    # after running the bare minimum part of the Hypersim pipeline.
    #

    scene_name           = s["name"]
    scene_file           = os.path.join(args.dataset_dir, "scenes", scene_name, "_asset_export", "scene.vrscene")
    vray_user_params_dir = args.dataset_dir

    renderer = vray.VRayRenderer()
    def log_msg(renderer, message, level, instant):
        print(str(instant) + " " + str(level) + " " + message)
    renderer.setOnLogMessage(log_msg)
    renderer.load(scene_file)
    time.sleep(0.5)

    #
    # We must execute the _set_vray_user_params(...) function
    # because this user code might modify camera parameters.
    #

    path_utils.add_path_to_sys_path(vray_user_params_dir, mode="relative_to_cwd", frame=inspect.currentframe())
    import _vray_user_params

    camera_params = _vray_user_params._set_vray_user_params(renderer)



    camera_physicals      = renderer.classes.CameraPhysical.getInstances()
    settings_camera       = renderer.classes.SettingsCamera.getInstances()[0]
    settings_output       = renderer.classes.SettingsOutput.getInstances()[0]
    settings_units_info   = renderer.classes.SettingsUnitsInfo.getInstances()[0]

    use_camera_physical = len(camera_physicals) > 0



    # parameters from vrscene file
    width_pixels          = settings_output.img_width
    height_pixels         = settings_output.img_height
    meters_per_asset_unit = settings_units_info.meters_scale



    if use_camera_physical:

        camera_physical = camera_physicals[0]

        # parameters from CameraPhysical
        film_width        = camera_physical.film_width
        focus_distance    = camera_physical.focus_distance
        fov_x             = camera_physical.fov
        horizontal_offset = camera_physical.horizontal_offset
        horizontal_shift  = camera_physical.horizontal_shift
        lens_shift        = camera_physical.lens_shift
        specify_focus     = camera_physical.specify_focus
        target_distance   = camera_physical.target_distance
        vertical_offset   = camera_physical.vertical_offset
        zoom              = camera_physical.zoom_factor

        # derived parameters
        fov_y = 2.0 * np.arctan(height_pixels * np.tan(fov_x/2.0) / width_pixels)

        if specify_focus:
            lens_params_focus_distance = focus_distance
        else:
            lens_params_focus_distance = target_distance

        lens_params_film_width = film_width*(1.0/meters_per_asset_unit)*0.001
        lens_params_zoom       = zoom



        #
        # Binary search for the aperture distance that matches specified FOV.
        #

        #
        # In this function, we adopt the convention that the horizontal extent of
        # the frustum goes from rx=-0.5 to rx=0.5 to match the V-Ray implementation
        # as closely as possible. We could modify this function to match our
        # conventions (where the horizontal extent of the the frustum goes from
        # u=-1.0 to u=1.0), but there is no need, so we leave this function as-is.
        #

        def compute_ray_camera_space(rx, ry, zval): 

            rx += horizontal_offset
            ry += vertical_offset

            k  = -lens_params_focus_distance/zval
            px = rx*lens_params_film_width*k/lens_params_zoom
            py = ry*lens_params_film_width*k/lens_params_zoom
            pz = lens_params_focus_distance

            shiftkx = np.sqrt(1.0 + horizontal_shift**2.0)
            shiftk  = np.sqrt(1.0 + lens_shift**2.0)

            px_ = px/shiftkx
            py_ = py/shiftk
            pz_ = pz + ((py_*lens_shift) + (px_*horizontal_shift))

            r = np.array([px_, py_, -pz_])
            return r

        lens_params_aperture_dist_min  = 0.0001
        lens_params_aperture_dist_max  = 500.0
        lens_params_aperture_dist_curr = (lens_params_aperture_dist_min+lens_params_aperture_dist_max)/2.0

        ray_l = compute_ray_camera_space(-0.5, 0.0, lens_params_aperture_dist_curr)
        ray_r = compute_ray_camera_space( 0.5, 0.0, lens_params_aperture_dist_curr)

        # This code does not exactly calculate the angle between ray_l
        # and ray_r, but it's used by V-Ray to compute aperture distance,
        # and we want to match V-Ray's behavior exactly.

        ray_l_                  = ray_l / ray_l[2]
        ray_r_                  = ray_r / ray_r[2]
        width                   = ray_r_[0] - ray_l_[0]
        fov_x_aperture_dist_est = np.arctan(0.5*width)*2.0

        num_steps = 100
        eps       = 1e-9

        for i in range(num_steps):    
            if abs(fov_x_aperture_dist_est - fov_x) < eps:
                break
                
            if fov_x_aperture_dist_est < fov_x:
                lens_params_aperture_dist_max  = lens_params_aperture_dist_curr
                lens_params_aperture_dist_curr = (lens_params_aperture_dist_min+lens_params_aperture_dist_max)/2.0
            else:
                lens_params_aperture_dist_min  = lens_params_aperture_dist_curr
                lens_params_aperture_dist_curr = (lens_params_aperture_dist_min+lens_params_aperture_dist_max)/2.0

            ray_l = compute_ray_camera_space(-0.5, 0.0, lens_params_aperture_dist_curr)
            ray_r = compute_ray_camera_space( 0.5, 0.0, lens_params_aperture_dist_curr)

            # This code does not exactly calculate the angle between ray_l
            # and ray_r, but it's used by V-Ray to compute aperture distance,
            # and we want to match V-Ray's behavior exactly.

            ray_l_                  = ray_l / ray_l[2]
            ray_r_                  = ray_r / ray_r[2]
            width                   = ray_r_[0] - ray_l_[0]
            fov_x_aperture_dist_est = np.arctan(0.5*width)*2.0

        lens_params_aperture_dist = lens_params_aperture_dist_curr



        #
        # Construct matrix to map points to camera-space from uv-space, ignore all camera parameters for now.
        #

        M_cam_from_uv_canonical = np.matrix([[np.tan(fov_x/2.0), 0.0,               0.0],
                                             [0.0,               np.tan(fov_y/2.0), 0.0],
                                             [0.0,               0.0,               -1.0]])

        eps = 0.0001
        assert abs(np.linalg.det(M_cam_from_uv_canonical)) > eps

        # print(M_cam_from_uv_canonical)
        # print()



        #
        # Construct matrix to map points to camera-space from uv-space, take camera parameters into account here.
        #

        zval    = lens_params_aperture_dist
        k       = -lens_params_focus_distance/zval
        shiftkx = np.sqrt(1.0 + horizontal_shift**2.0)
        shiftk  = np.sqrt(1.0 + lens_shift**2.0)

        k_x   = lens_params_film_width*k*(1.0/lens_params_zoom)*(1.0/shiftkx)
        k_x_u = -0.5*k_x
        k_x_v = 0.0
        k_x_c = horizontal_offset*k_x

        k_y   = lens_params_film_width*k*(1.0/lens_params_zoom)*(1.0/shiftk)
        k_y_u = 0.0
        k_y_v = -0.5*k_y*(height_pixels/width_pixels)
        k_y_c = vertical_offset*k_y

        k_z_u = -horizontal_shift*k_x_u
        k_z_v = -lens_shift*k_y_v
        k_z_c = -lens_params_focus_distance - lens_shift*k_y_c - horizontal_shift*k_x_c

        M_cam_from_uv_transformed = np.matrix([[k_x_u, k_x_v, k_x_c],
                                               [k_y_u, k_y_v, k_y_c],
                                               [k_z_u, k_z_v, k_z_c]])

        eps = 0.0001
        assert abs(np.linalg.det(M_cam_from_uv_transformed)) > eps

        # print(M_cam_from_uv_transformed)
        # print()



        #
        # The scale of M_cam_from_uv_transformed is arbitrary, but we would prefer to define
        # it in a way that is as convenient as possible in OpenGL applications. So we solve
        # for the scale parameter k that minimizes the following expression:
        #
        # np.linalg.norm(np.identity(3) - M_cam_from_uv_canonical*(k*M_cam_from_uv_transformed).I)**2.0
        #
        # By rescaling in this way, we will eventually obtain a modified projection matrix
        # that is (roughly speaking) as similar as possible to the usual OpenGL projection
        # matrix, so it can be used in OpenGL applications without needing to drastically
        # alter the near and far clipping planes.
        #
        # Note that our strategy is not exactly equivalent to minimizing the difference
        # between the usual OpenGL projection matrix and our modified projection matrix. But
        # it is more mathematically convenient, and produces very similar results empirically.
        #

        # expression we would like to minimize
        k = 1.0
        norm_squared = np.linalg.norm(np.identity(3) - M_cam_from_uv_canonical*(k*M_cam_from_uv_transformed).I)**2.0
        # print(norm_squared)
        # print()

        # we can express as a scalar quadratic in k_inv
        k_inv = 1.0/k
        A = np.identity(3)
        B = (M_cam_from_uv_canonical*M_cam_from_uv_transformed.I).A
        a = np.sum(B*B)
        b = -2.0*np.sum(A*B)
        c = np.sum(A*A)
        norm_squared = a*k_inv**2.0 + b*k_inv + c
        # print(norm_squared)
        # print()

        # analytic optimal solution for k_inv
        k_inv_opt = -b/(2.0*a)

        # analytic optimal solution for k
        k_opt = 1.0/k_inv_opt

        # print(k_opt)
        # print()

        # optimal norm squared value
        norm_squared_opt = np.linalg.norm(np.identity(3) - M_cam_from_uv_canonical*(k_opt*M_cam_from_uv_transformed).I)**2

        # print(norm_squared_opt)
        # print()

        M_cam_from_uv_transformed_scaled = k_opt*M_cam_from_uv_transformed

        # print(M_cam_from_uv_transformed_scaled)
        # print()

        M_cam_from_uv_ = M_cam_from_uv_transformed_scaled



        #
        # Construct a standard OpenGL projection matrix, ignore V-Ray camera parameters for now.
        #

        near = 1.0
        far  = 1000.0
            
        # construct projection matrix
        f_h    = np.tan(fov_y/2.0)*near
        f_w    = f_h*width_pixels/height_pixels
        left   = -f_w
        right  = f_w
        bottom = -f_h
        top    = f_h

        M_proj      = matrix(zeros((4,4)))
        M_proj[0,0] = (2.0*near)/(right - left)
        M_proj[1,1] = (2.0*near)/(top - bottom)
        M_proj[0,2] = (right + left)/(right - left)
        M_proj[1,2] = (top + bottom)/(top - bottom)
        M_proj[2,2] = -(far + near)/(far - near)
        M_proj[3,2] = -1.0
        M_proj[2,3] = -(2.0*far*near)/(far - near)

        # print(M_proj)
        # print()



        #
        # Construct modified projection matrix that takes V-Ray camera parameters into account.
        #

        M_canonical_from_transformed  = M_cam_from_uv_canonical*(M_cam_from_uv_transformed_scaled).I
        M_canonical_from_transformed_ = scipy.linalg.block_diag(M_canonical_from_transformed, 1)
        M_proj_transformed            = M_proj*M_canonical_from_transformed_

        # print(M_proj_transformed)
        # print()

        M_proj_ = M_proj_transformed



    else:

        # parameters from SettingsCamera
        fov_x = settings_camera.fov

        # derived parameters
        fov_y = 2.0 * np.arctan(height_pixels * np.tan(fov_x/2.0) / width_pixels)

        #
        # Construct matrix to map points to camera-space from uv-space, ignore all camera parameters for now.
        #

        M_cam_from_uv_canonical = np.matrix([[np.tan(fov_x/2.0), 0.0,               0.0],
                                             [0.0,               np.tan(fov_y/2.0), 0.0],
                                             [0.0,               0.0,               -1.0]])

        eps = 0.0001
        assert abs(np.linalg.det(M_cam_from_uv_canonical)) > eps

        # print(M_cam_from_uv_canonical)
        # print()

        M_cam_from_uv_ = M_cam_from_uv_canonical

        #
        # Construct a standard OpenGL projection matrix.
        #

        near = 1.0
        far  = 1000.0
            
        # construct projection matrix
        f_h    = np.tan(fov_y/2.0)*near
        f_w    = f_h*width_pixels/height_pixels
        left   = -f_w
        right  = f_w
        bottom = -f_h
        top    = f_h

        M_proj      = matrix(zeros((4,4)))
        M_proj[0,0] = (2.0*near)/(right - left)
        M_proj[1,1] = (2.0*near)/(top - bottom)
        M_proj[0,2] = (right + left)/(right - left)
        M_proj[1,2] = (top + bottom)/(top - bottom)
        M_proj[2,2] = -(far + near)/(far - near)
        M_proj[3,2] = -1.0
        M_proj[2,3] = -(2.0*far*near)/(far - near)

        M_proj_ = M_proj



    df_camera_parameters_ = pd.DataFrame(
        columns=df_camera_parameters_columns,
        data={
            "scene_name"                                   : [ scene_name ],
            "settings_output_img_height"                   : [ settings_output.img_height ],
            "settings_output_img_width"                    : [ settings_output.img_width ],
            "settings_units_info_meters_scale"             : [ settings_units_info.meters_scale ],
            "use_camera_physical"                          : [ use_camera_physical ],
            "camera_physical_anisotropy"                   : [ camera_physical.anisotropy                   if use_camera_physical else None ],
            "camera_physical_blades_enable"                : [ camera_physical.blades_enable                if use_camera_physical else None ],
            "camera_physical_blades_num"                   : [ camera_physical.blades_num                   if use_camera_physical else None ],
            "camera_physical_blades_rotation"              : [ camera_physical.blades_rotation              if use_camera_physical else None ],
            "camera_physical_bmpaperture_affects_exposure" : [ camera_physical.bmpaperture_affects_exposure if use_camera_physical else None ],
            "camera_physical_bmpaperture_enable"           : [ camera_physical.bmpaperture_enable           if use_camera_physical else None ],
            "camera_physical_bmpaperture_resolution"       : [ camera_physical.bmpaperture_resolution       if use_camera_physical else None ],
            "camera_physical_bmpaperture_tex"              : [ camera_physical.bmpaperture_tex              if use_camera_physical else None ],
            "camera_physical_center_bias"                  : [ camera_physical.center_bias                  if use_camera_physical else None ],
            "camera_physical_distortion"                   : [ camera_physical.distortion                   if use_camera_physical else None ],
            "camera_physical_distortion_tex"               : [ camera_physical.distortion_tex               if use_camera_physical else None ],
            "camera_physical_distortion_type"              : [ camera_physical.distortion_type              if use_camera_physical else None ],
            "camera_physical_dof_display_threshold"        : [ camera_physical.dof_display_threshold        if use_camera_physical else None ],
            "camera_physical_dont_affect_settings"         : [ camera_physical.dont_affect_settings         if use_camera_physical else None ],
            "camera_physical_enable_thin_lens_equation"    : [ camera_physical.enable_thin_lens_equation    if use_camera_physical else None ],
            "camera_physical_exposure"                     : [ camera_physical.exposure                     if use_camera_physical else None ],
            "camera_physical_f_number"                     : [ camera_physical.f_number                     if use_camera_physical else None ],
            "camera_physical_film_width"                   : [ camera_physical.film_width                   if use_camera_physical else None ],
            "camera_physical_focal_length"                 : [ camera_physical.focal_length                 if use_camera_physical else None ],
            "camera_physical_focus_distance"               : [ camera_physical.focus_distance               if use_camera_physical else None ],
            "camera_physical_fov"                          : [ camera_physical.fov                          if use_camera_physical else None ],
            "camera_physical_horizontal_offset"            : [ camera_physical.horizontal_offset            if use_camera_physical else None ],
            "camera_physical_horizontal_shift"             : [ camera_physical.horizontal_shift             if use_camera_physical else None ],
            "camera_physical_ISO"                          : [ camera_physical.ISO                          if use_camera_physical else None ],
            "camera_physical_latency"                      : [ camera_physical.latency                      if use_camera_physical else None ],
            "camera_physical_lens_file"                    : [ camera_physical.lens_file                    if use_camera_physical else None ],
            "camera_physical_lens_shift"                   : [ camera_physical.lens_shift                   if use_camera_physical else None ],
            "camera_physical_optical_vignetting"           : [ camera_physical.optical_vignetting           if use_camera_physical else None ],
            "camera_physical_rolling_shutter_duration"     : [ camera_physical.rolling_shutter_duration     if use_camera_physical else None ],
            "camera_physical_rolling_shutter_mode"         : [ camera_physical.rolling_shutter_mode         if use_camera_physical else None ],
            "camera_physical_shutter_angle"                : [ camera_physical.shutter_angle                if use_camera_physical else None ],
            "camera_physical_shutter_offset"               : [ camera_physical.shutter_offset               if use_camera_physical else None ],
            "camera_physical_shutter_speed"                : [ camera_physical.shutter_speed                if use_camera_physical else None ],
            "camera_physical_specify_focus"                : [ camera_physical.specify_focus                if use_camera_physical else None ],
            "camera_physical_specify_fov"                  : [ camera_physical.specify_fov                  if use_camera_physical else None ],
            "camera_physical_subdivs"                      : [ camera_physical.subdivs                      if use_camera_physical else None ],
            "camera_physical_target_distance"              : [ camera_physical.target_distance              if use_camera_physical else None ],
            "camera_physical_targeted"                     : [ camera_physical.targeted                     if use_camera_physical else None ],
            "camera_physical_type"                         : [ camera_physical.type                         if use_camera_physical else None ],
            "camera_physical_use_dof"                      : [ camera_physical.use_dof                      if use_camera_physical else None ],
            "camera_physical_use_moblur"                   : [ camera_physical.use_moblur                   if use_camera_physical else None ],
            "camera_physical_vertical_offset"              : [ camera_physical.vertical_offset              if use_camera_physical else None ],
            "camera_physical_vignetting"                   : [ camera_physical.vignetting                   if use_camera_physical else None ],
            "camera_physical_white_balance"                : [ camera_physical.white_balance                if use_camera_physical else None ],
            "camera_physical_zoom_factor"                  : [ camera_physical.zoom_factor                  if use_camera_physical else None ],
            "settings_camera_auto_corrections_mode"        : [ settings_camera.auto_corrections_mode ],
            "settings_camera_auto_exposure"                : [ settings_camera.auto_exposure ],
            "settings_camera_auto_exposure_compensation"   : [ settings_camera.auto_exposure_compensation ],
            "settings_camera_auto_fit"                     : [ settings_camera.auto_fit ],
            "settings_camera_auto_white_balance"           : [ settings_camera.auto_white_balance ],
            "settings_camera_curve"                        : [ settings_camera.curve ],
            "settings_camera_dist"                         : [ settings_camera.dist ],
            "settings_camera_dont_affect_settings"         : [ settings_camera.dont_affect_settings ],
            "settings_camera_fov"                          : [ settings_camera.fov ],
            "settings_camera_height"                       : [ settings_camera.height ],
            "settings_camera_image_planes"                 : [ settings_camera.image_planes ],
            "settings_camera_type"                         : [ settings_camera.type ],
            "M_cam_from_uv_00"                             : [ M_cam_from_uv_[0,0] ],
            "M_cam_from_uv_01"                             : [ M_cam_from_uv_[0,1] ],
            "M_cam_from_uv_02"                             : [ M_cam_from_uv_[0,2] ],
            "M_cam_from_uv_10"                             : [ M_cam_from_uv_[1,0] ],
            "M_cam_from_uv_11"                             : [ M_cam_from_uv_[1,1] ],
            "M_cam_from_uv_12"                             : [ M_cam_from_uv_[1,2] ],
            "M_cam_from_uv_20"                             : [ M_cam_from_uv_[2,0] ],
            "M_cam_from_uv_21"                             : [ M_cam_from_uv_[2,1] ],
            "M_cam_from_uv_22"                             : [ M_cam_from_uv_[2,2] ],
            "M_proj_00"                                    : [ M_proj_[0,0] ],
            "M_proj_01"                                    : [ M_proj_[0,1] ],
            "M_proj_02"                                    : [ M_proj_[0,2] ],
            "M_proj_03"                                    : [ M_proj_[0,3] ],
            "M_proj_10"                                    : [ M_proj_[1,0] ],
            "M_proj_11"                                    : [ M_proj_[1,1] ],
            "M_proj_12"                                    : [ M_proj_[1,2] ],
            "M_proj_13"                                    : [ M_proj_[1,3] ],
            "M_proj_20"                                    : [ M_proj_[2,0] ],
            "M_proj_21"                                    : [ M_proj_[2,1] ],
            "M_proj_22"                                    : [ M_proj_[2,2] ],
            "M_proj_23"                                    : [ M_proj_[2,3] ],
            "M_proj_30"                                    : [ M_proj_[3,0] ],
            "M_proj_31"                                    : [ M_proj_[3,1] ],
            "M_proj_32"                                    : [ M_proj_[3,2] ],
            "M_proj_33"                                    : [ M_proj_[3,3] ] })

    df_camera_parameters = df_camera_parameters.append(df_camera_parameters_)

    df_camera_parameters.to_csv(args.out_file, index=False)



print("[HYPERSIM: DATASET_GENERATE_CAMERA_PARAMETERS_METADATA] Finished.")
