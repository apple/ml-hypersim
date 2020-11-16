//
// For licensing see accompanying LICENSE.txt file.
// Copyright (C) 2020 Apple Inc. All Rights Reserved.
//

#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <string>

#include <args.hxx>

#include <armadillo>

#include <embree3/rtcore.h>
#include <embree3/rtcore_scene.h>
#include <embree3/rtcore_ray.h>

#include <octomap/octomap.h>
#include <octomap/OcTree.h>



struct Vertex   { float x, y, z, a; };
struct Triangle { unsigned int v0, v1, v2; };



int main (int argc, const char** argv) {

    //
    // parse input arguments
    //

    args::ArgumentParser parser("generate_camera_trajectory_random_walk", "");

    args::HelpFlag               help                                             (parser, "__DUMMY__",                                    "Display this help menu",                       {'h', "help"});
    args::ValueFlag<std::string> mesh_vertices_file_arg                           (parser, "MESH_VERTICES_FILE",                           "mesh_vertices_file",                           {"mesh_vertices_file"},                           args::Options::Required);
    args::ValueFlag<std::string> mesh_faces_vi_file_arg                           (parser, "MESH_FACES_VI_FILE",                           "mesh_faces_vi_file",                           {"mesh_faces_vi_file"},                           args::Options::Required);
    args::ValueFlag<std::string> start_camera_position_file_arg                   (parser, "START_CAMERA_POSITION_FILE",                   "start_camera_position_file",                   {"start_camera_position_file"},                   args::Options::Required);
    args::ValueFlag<std::string> start_camera_orientation_file_arg                (parser, "START_CAMERA_ORIENTATION_FILE",                "start_camera_position_file",                   {"start_camera_orientation_file"},                args::Options::Required);
    args::ValueFlag<std::string> camera_rays_file_arg                             (parser, "CAMERA_RAYS_FILE",                             "camera_rays_file",                             {"camera_rays_file"},                             args::Options::Required);
    args::ValueFlag<std::string> camera_rays_distances_to_center_file_arg         (parser, "CAMERA_RAYS_DISTANCES_TO_CENTER_FILE",         "camera_rays_distances_to_center_file",         {"camera_rays_distances_to_center_file"},         args::Options::Required);
    args::ValueFlag<std::string> octomap_file_arg                                 (parser, "OCTOMAP_FILE",                                 "octomap_file",                                 {"octomap_file"},                                 args::Options::Required);
    args::ValueFlag<std::string> octomap_free_space_min_file_arg                  (parser, "OCTOMAP_FREE_SPACE_MIN_FILE",                  "octomap_free_space_min_file",                  {"octomap_free_space_min_file"},                  args::Options::Required);
    args::ValueFlag<std::string> octomap_free_space_max_file_arg                  (parser, "OCTOMAP_FREE_SPACE_MAX_FILE",                  "octomap_free_space_max_file",                  {"octomap_free_space_max_file"},                  args::Options::Required);
    args::ValueFlag<int>         n_samples_random_walk_arg                        (parser, "N_SAMPLES_RANDOM_WALK",                        "n_samples_random_walk",                        {"n_samples_random_walk"},                        args::Options::Required);
    args::ValueFlag<int>         n_samples_octomap_query_arg                      (parser, "N_SAMPLES_OCTOMAP_QUERY",                      "n_samples_octomap_query",                      {"n_samples_octomap_query"},                      args::Options::Required);
    args::ValueFlag<int>         n_samples_camera_pose_candidates_arg             (parser, "N_CAMERA_POSE_CANDIDATES",                     "n_samples_camera_pose_candidates",             {"n_samples_camera_pose_candidates"},             args::Options::Required);
    args::ValueFlag<float>       n_voxel_size_arg                                 (parser, "N_VOXEL_SIZE",                                 "n_voxel_size",                                 {"n_voxel_size"},                                 args::Options::Required);
    args::ValueFlag<std::string> n_query_half_extent_relative_to_start_file_arg   (parser, "N_QUERY_HALF_EXTENT_RELATIVE_TO_START_FILE",   "n_query_half_extent_relative_to_start_file",   {"n_query_half_extent_relative_to_start_file"},   args::Options::Required);
    args::ValueFlag<std::string> n_query_half_extent_relative_to_current_file_arg (parser, "N_QUERY_HALF_EXTENT_RELATIVE_TO_CURRENT_FILE", "n_query_half_extent_relative_to_current_file", {"n_query_half_extent_relative_to_current_file"}, args::Options::Required);
    args::ValueFlag<std::string> output_camera_look_from_positions_file_arg       (parser, "OUTPUT_CAMERA_LOOK_FROM_POSITIONS_FILE",       "output_camera_look_from_positions_file",       {"output_camera_look_from_positions_file"},       args::Options::Required);
    args::ValueFlag<std::string> output_camera_look_at_positions_file_arg         (parser, "OUTPUT_CAMERA_LOOK_AT_POSITIONS_FILE",         "output_camera_look_at_positions_file",         {"output_camera_look_at_positions_file"},         args::Options::Required);
    args::ValueFlag<std::string> output_camera_orientations_file_arg              (parser, "OUTPUT_CAMERA_ORIENTATIONS_FILE",              "output_camera_orientations_file",              {"output_camera_orientations_file"},              args::Options::Required);
    args::ValueFlag<std::string> output_intersection_distances_file_arg           (parser, "OUTPUT_INTERSECTION_DISTANCES_FILE",           "output_intersection_distances_file",           {"output_intersection_distances_file"},           args::Options::Required);
    args::ValueFlag<std::string> output_prim_ids_file_arg                         (parser, "OUTPUT_PRIM_IDS_FILE",                         "output_prim_ids_file",                         {"output_prim_ids_file"},                         args::Options::Required);
    args::Flag                   silent_arg                                       (parser, "__DUMMY__",                                    "silent",                                       {"silent"});

    try {
        parser.ParseCLI(argc, argv);
    } catch (args::Completion e) {
        std::cout << parser;
        return 1;
    } catch (args::Help e) {
        std::cout << parser;
        return 1;
    } catch (args::ParseError e) {
        std::cout << parser;
        std::cout << std::endl << std::endl << std::endl << e.what() << std::endl << std::endl << std::endl;
        return 1;
    } catch (args::RequiredError e) {
        std::cout << parser;
        std::cout << std::endl << std::endl << std::endl << e.what() << std::endl << std::endl << std::endl;
        return 1;
    }

    auto mesh_vertices_file                           = args::get(mesh_vertices_file_arg);
    auto mesh_faces_vi_file                           = args::get(mesh_faces_vi_file_arg);
    auto start_camera_position_file                   = args::get(start_camera_position_file_arg);
    auto start_camera_orientation_file                = args::get(start_camera_orientation_file_arg);
    auto camera_rays_file                             = args::get(camera_rays_file_arg);
    auto camera_rays_distances_to_center_file         = args::get(camera_rays_distances_to_center_file_arg);
    auto octomap_file                                 = args::get(octomap_file_arg);
    auto octomap_free_space_min_file                  = args::get(octomap_free_space_min_file_arg);
    auto octomap_free_space_max_file                  = args::get(octomap_free_space_max_file_arg);
    auto n_samples_random_walk                        = args::get(n_samples_random_walk_arg);
    auto n_samples_octomap_query                      = args::get(n_samples_octomap_query_arg);
    auto n_samples_camera_pose_candidates             = args::get(n_samples_camera_pose_candidates_arg);
    auto n_voxel_size                                 = args::get(n_voxel_size_arg);
    auto n_query_half_extent_relative_to_start_file   = args::get(n_query_half_extent_relative_to_start_file_arg);
    auto n_query_half_extent_relative_to_current_file = args::get(n_query_half_extent_relative_to_current_file_arg);
    auto output_camera_look_from_positions_file       = args::get(output_camera_look_from_positions_file_arg);
    auto output_camera_look_at_positions_file         = args::get(output_camera_look_at_positions_file_arg);
    auto output_camera_orientations_file              = args::get(output_camera_orientations_file_arg);
    auto output_intersection_distances_file           = args::get(output_intersection_distances_file_arg);
    auto output_prim_ids_file                         = args::get(output_prim_ids_file_arg);
    auto silent                                       = args::get(silent_arg);

    arma::mat mesh_vertices, start_camera_orientation, camera_rays;
    arma::imat mesh_faces_vi;
    arma::vec start_camera_position, camera_rays_distances_to_center, octomap_free_space_min, octomap_free_space_max;
    arma::vec n_query_half_extent_relative_to_start, n_query_half_extent_relative_to_current;

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK] Begin..." << std::endl;
    }

    //
    // load input data
    //

    mesh_vertices.load(mesh_vertices_file, arma::hdf5_binary_trans);
    mesh_faces_vi.load(mesh_faces_vi_file, arma::hdf5_binary_trans);
    start_camera_position.load(start_camera_position_file, arma::hdf5_binary_trans);
    start_camera_orientation.load(start_camera_orientation_file, arma::hdf5_binary_trans);
    octomap_free_space_min.load(octomap_free_space_min_file, arma::hdf5_binary_trans);
    octomap_free_space_max.load(octomap_free_space_max_file, arma::hdf5_binary_trans);
    camera_rays.load(camera_rays_file, arma::hdf5_binary_trans);
    camera_rays_distances_to_center.load(camera_rays_distances_to_center_file, arma::hdf5_binary_trans);
    n_query_half_extent_relative_to_start.load(n_query_half_extent_relative_to_start_file, arma::hdf5_binary_trans);
    n_query_half_extent_relative_to_current.load(n_query_half_extent_relative_to_current_file, arma::hdf5_binary_trans);

    octomap::OcTree octree_octomap(octomap_file);

    assert(mesh_vertices.n_cols == 3);
    assert(mesh_faces_vi.n_cols == 3);
    assert(start_camera_position.n_rows == 3);
    assert(start_camera_orientation.n_rows == 3);
    assert(start_camera_orientation.n_cols == 3);
    assert(camera_rays.n_cols == 3);
    assert(camera_rays.n_rows == camera_rays_distances_to_center.n_rows);
    assert(n_query_half_extent_relative_to_start.n_rows == 3);
    assert(n_query_half_extent_relative_to_current.n_rows == 3);

    arma::arma_rng::set_seed(0);
    arma::mat V_cam = camera_rays.t();
    arma::uvec indices;

    //
    // construct Embree data
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK] Constructing Embree data..." << std::endl;
    }

    assert(RTC_MAX_INSTANCE_LEVEL_COUNT == 1);

    auto rtc_device = rtcNewDevice(nullptr);
    assert(rtcGetDeviceError(nullptr) == RTC_ERROR_NONE);

    auto rtc_scene = rtcNewScene(rtc_device);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    auto rtc_triangle_mesh = rtcNewGeometry(rtc_device, RTC_GEOMETRY_TYPE_TRIANGLE);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    // set vertices
    auto rtc_vertices = (Vertex*) rtcSetNewGeometryBuffer(rtc_triangle_mesh, RTC_BUFFER_TYPE_VERTEX, 0, RTC_FORMAT_FLOAT3, sizeof(Vertex), mesh_vertices.n_rows);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    for (int i = 0; i < mesh_vertices.n_rows; i++) {
        rtc_vertices[i].x = mesh_vertices(i,0);
        rtc_vertices[i].y = mesh_vertices(i,1);
        rtc_vertices[i].z = mesh_vertices(i,2);
    }

    // set triangles
    auto rtc_triangles = (Triangle*) rtcSetNewGeometryBuffer(rtc_triangle_mesh, RTC_BUFFER_TYPE_INDEX, 0, RTC_FORMAT_UINT3, sizeof(Triangle), mesh_faces_vi.n_rows);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    for (int i = 0; i < mesh_faces_vi.n_rows; i++) {
        rtc_triangles[i].v0 = mesh_faces_vi(i,0);
        rtc_triangles[i].v1 = mesh_faces_vi(i,1);
        rtc_triangles[i].v2 = mesh_faces_vi(i,2);
    }

    rtcCommitGeometry(rtc_triangle_mesh);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    unsigned int geomID = rtcAttachGeometry(rtc_scene, rtc_triangle_mesh);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    rtcReleaseGeometry(rtc_triangle_mesh);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    rtcCommitScene(rtc_scene);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    RTCIntersectContext rtc_intersect_context;
    rtcInitIntersectContext(&rtc_intersect_context);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);



    //
    // parameters
    //

    // when randomly sampling an up vector, perturb it according to these parameters
    auto n_camera_up_hint_noise_std_dev = 0.1;
    arma::vec n_camera_up_hint_nominal  = {0,0,1};

    // margin parameter for line-of-sight queries: point A must be closer than the scene geometry to point B,
    // along the ray from B to A, by a margin of eps percent, in order for A to be considered visible from B
    auto eps = 0.01;

    // when attempting to find the initial look-at position, sample the occupancy map slightly closer to the
    // initial look-from position than the point of mesh intersection, but at least delta units away from the
    // initial look-from position to avoid a degenerate (look-from, look-at) pair    
    auto delta = 0.0001;

    // constant term added to the view saliency score; as lamb goes to infinty, the distribution of view saliency
    // scores will approach a uniform distribution
    auto lamb = 0.0;



    //
    // arrays to hold preview images across the random walk, so we only have to save them in a single HDF5 file
    //

    arma::mat  intersection_distances = arma::ones<arma::mat>(n_samples_random_walk, V_cam.n_cols) * std::numeric_limits<float>::infinity();
    arma::imat prim_ids               = arma::ones<arma::imat>(n_samples_random_walk, V_cam.n_cols) * -1;



    //
    // start_camera_look_from_position
    //

    arma::vec start_camera_look_from_position = start_camera_position;



    //
    // start_camera_look_at_position
    //

    arma::mat start_camera_R_world_from_cam = start_camera_orientation;
    arma::vec start_camera_look_at_dir      = -start_camera_R_world_from_cam.col(2);

    auto intersection_distance = std::numeric_limits<float>::infinity();

    arma::vec ray_position = start_camera_look_from_position;
    arma::vec ray_direction_normalized = arma::normalise(start_camera_look_at_dir);

    RTCRayHit rtc_ray_hit;

    rtc_ray_hit.ray.org_x  = (float)ray_position(0);
    rtc_ray_hit.ray.org_y  = (float)ray_position(1);
    rtc_ray_hit.ray.org_z  = (float)ray_position(2);
    rtc_ray_hit.ray.dir_x  = (float)ray_direction_normalized(0);
    rtc_ray_hit.ray.dir_y  = (float)ray_direction_normalized(1);
    rtc_ray_hit.ray.dir_z  = (float)ray_direction_normalized(2);
    rtc_ray_hit.ray.tnear  = 0.0f;
    rtc_ray_hit.ray.tfar   = std::numeric_limits<float>::infinity();
    rtc_ray_hit.ray.time   = 0.0f;
    rtc_ray_hit.ray.mask   = 0;
    rtc_ray_hit.ray.id     = 0;
    rtc_ray_hit.ray.flags  = 0;

    rtc_ray_hit.hit.Ng_x      = std::numeric_limits<float>::infinity();
    rtc_ray_hit.hit.Ng_y      = std::numeric_limits<float>::infinity();
    rtc_ray_hit.hit.Ng_z      = std::numeric_limits<float>::infinity();
    rtc_ray_hit.hit.u         = std::numeric_limits<float>::infinity();
    rtc_ray_hit.hit.v         = std::numeric_limits<float>::infinity();
    rtc_ray_hit.hit.primID    = RTC_INVALID_GEOMETRY_ID;
    rtc_ray_hit.hit.geomID    = RTC_INVALID_GEOMETRY_ID;
    rtc_ray_hit.hit.instID[0] = RTC_INVALID_GEOMETRY_ID;

    // intersect ray with scene
    rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

    if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
        assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
        assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
    } else {
        assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
        assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
    }

    if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
        intersection_distance = rtc_ray_hit.ray.tfar;
    }

    // slack of 1.75*n_voxel_size guarantees that we're not in the same voxel as the intersection point
    intersection_distance = std::max(intersection_distance - 1.75*n_voxel_size, delta);

    arma::vec query_position = start_camera_look_from_position + intersection_distance*start_camera_look_at_dir;
    auto octomap_sample = -3;

    if (query_position.is_finite()) {
        auto node_octomap = octree_octomap.search(octomap::point3d(query_position(0), query_position(1), query_position(2)));
        if (node_octomap != nullptr) {
            if (node_octomap->getOccupancy() <= octree_octomap.getOccupancyThres()) {
                octomap_sample = 0;
            } else {
                octomap_sample = 1;
            }
        } else {
            octomap_sample = -1;
        }
    } else {
        octomap_sample = -2;
    }



    arma::vec start_camera_look_at_position;
    auto computed_intersection_distance_image = false;

    if (isfinite(intersection_distance) && octomap_sample == 0) {
        start_camera_look_at_position = start_camera_look_from_position + intersection_distance*start_camera_look_at_dir;
        computed_intersection_distance_image = false;

    } else {

        // try to find an unoccupied cell for the initial look-at position by shooting camera rays,
        // testing for intersections with the scene mesh, and testing the occupancy map cells slightly
        // before the intersections (when proceeding from the optical center of the camera to the
        // mesh intersection point); if no unoccupied cells can be found, try perturbing the camera
        // forwards along the camera's look-at vector slightly and trying again
        arma::vec camera_z_axis                     = start_camera_R_world_from_cam.col(2);
        auto camera_perturb_attempts                = 8;
        auto camera_perturb_length                  = 0.25*n_voxel_size;
        auto all_intersection_distances_at_infinity = false;
        auto encountered_unoccupied_cell            = false;

        arma::mat ray_directions_world, ray_positions_world;
        arma::vec intersection_distances_current;
        arma::ivec prim_ids_current, octomap_samples;

        for (int p = 0; p < camera_perturb_attempts; p++) {

            //
            // works around a bug where matrix-matrix multiplication causes non-deterministic behavior in Armadillo's random number generator
            //
            // arma::mat V_world = start_camera_R_world_from_cam*V_cam;
            arma::mat V_world = arma::ones<arma::mat>(start_camera_R_world_from_cam.n_rows, V_cam.n_cols) * std::numeric_limits<float>::infinity();
            for (int k = 0; k < V_cam.n_cols; k++) {
                V_world.col(k) = start_camera_R_world_from_cam*V_cam.col(k);
            }

            ray_directions_world           = V_world.t();
            ray_positions_world            = arma::repmat(start_camera_look_from_position.t() + p*camera_perturb_length*camera_z_axis.t(), ray_directions_world.n_rows, 1);
            intersection_distances_current = arma::ones<arma::vec>(camera_rays.n_rows) * std::numeric_limits<float>::infinity();
            prim_ids_current               = arma::ones<arma::ivec>(camera_rays.n_rows) * -1;

            // for each ray direction...
            for (int k = 0; k < ray_directions_world.n_rows; k++) {

                arma::vec ray_position             = ray_positions_world.row(k).t();
                arma::vec ray_direction_normalized = arma::normalise(ray_directions_world.row(k).t());

                RTCRayHit rtc_ray_hit;

                rtc_ray_hit.ray.org_x = (float)ray_position(0);
                rtc_ray_hit.ray.org_y = (float)ray_position(1);
                rtc_ray_hit.ray.org_z = (float)ray_position(2);
                rtc_ray_hit.ray.dir_x = (float)ray_direction_normalized(0);
                rtc_ray_hit.ray.dir_y = (float)ray_direction_normalized(1);
                rtc_ray_hit.ray.dir_z = (float)ray_direction_normalized(2);
                rtc_ray_hit.ray.tnear = 0.0f;
                rtc_ray_hit.ray.tfar  = std::numeric_limits<float>::infinity();
                rtc_ray_hit.ray.time  = 0.0f;
                rtc_ray_hit.ray.mask  = 0;
                rtc_ray_hit.ray.id    = 0;
                rtc_ray_hit.ray.flags = 0;

                rtc_ray_hit.hit.Ng_x      = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.Ng_y      = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.Ng_z      = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.u         = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.v         = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.primID    = RTC_INVALID_GEOMETRY_ID;
                rtc_ray_hit.hit.geomID    = RTC_INVALID_GEOMETRY_ID;
                rtc_ray_hit.hit.instID[0] = RTC_INVALID_GEOMETRY_ID;

                // intersect ray with scene
                rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

                if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                    assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
                } else {
                    assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
                }

                if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                    intersection_distances_current(k) = rtc_ray_hit.ray.tfar;
                    prim_ids_current(k)               = rtc_ray_hit.hit.primID;
                }
            }

            if (p == 0) {
                intersection_distances.row(0) = intersection_distances_current.t();
                prim_ids.row(0)               = prim_ids_current.t();
            }

            indices = arma::find_finite(intersection_distances_current);
            if (indices.n_rows == 0) {
                all_intersection_distances_at_infinity = true;
                break;
            }

            //
            // clip rays against octomap bounding box, see https://tavianator.com/fast-branchless-raybounding-box-intersections/
            //

            ray_directions_world = arma::normalise(ray_directions_world, 2, 1);
            arma::vec t_min      = arma::ones(ray_directions_world.n_rows)*-std::numeric_limits<float>::infinity();
            arma::vec t_max      = arma::ones(ray_directions_world.n_rows)*std::numeric_limits<float>::infinity();

            auto gamma = 0.000001; // slack parameter to test if a value is close to 0.0

            arma::vec t_x0 = (octomap_free_space_min(0) - ray_positions_world.col(0)) / ray_directions_world.col(0);
            arma::vec t_x1 = (octomap_free_space_max(0) - ray_positions_world.col(0)) / ray_directions_world.col(0);
            indices = arma::find(arma::abs(ray_directions_world.col(0)) > gamma);
            t_min.elem(indices) = arma::max(t_min.elem(indices), arma::min(t_x0.elem(indices), t_x1.elem(indices)));
            t_max.elem(indices) = arma::min(t_max.elem(indices), arma::max(t_x0.elem(indices), t_x1.elem(indices)));

            arma::vec t_y0 = (octomap_free_space_min(1) - ray_positions_world.col(1)) / ray_directions_world.col(1);
            arma::vec t_y1 = (octomap_free_space_max(1) - ray_positions_world.col(1)) / ray_directions_world.col(1);
            indices = arma::find(arma::abs(ray_directions_world.col(1)) > gamma);
            t_min.elem(indices) = arma::max(t_min.elem(indices), arma::min(t_y0.elem(indices), t_y1.elem(indices)));
            t_max.elem(indices) = arma::min(t_max.elem(indices), arma::max(t_y0.elem(indices), t_y1.elem(indices)));

            arma::vec t_z0 = (octomap_free_space_min(2) - ray_positions_world.col(2)) / ray_directions_world.col(2);
            arma::vec t_z1 = (octomap_free_space_max(2) - ray_positions_world.col(2)) / ray_directions_world.col(2);
            indices = arma::find(arma::abs(ray_directions_world.col(2)) > gamma);
            t_min.elem(indices) = arma::max(t_min.elem(indices), arma::min(t_z0.elem(indices), t_z1.elem(indices)));
            t_max.elem(indices) = arma::min(t_max.elem(indices), arma::max(t_z0.elem(indices), t_z1.elem(indices)));

            assert(arma::is_finite(t_min));
            assert(arma::is_finite(t_max));
            assert(arma::all(t_max > t_min)); // assert all rays intersect bounding box
            assert(arma::all(t_min < 0.5*1.75*n_voxel_size)); // assert all rays start from inside bounding box (with a bit of slack because bounding box min and max might be off by a half voxel)

            indices = arma::find_nonfinite(intersection_distances_current);
            t_max.elem(indices) = arma::ones<arma::vec>(indices.n_rows)*std::numeric_limits<float>::infinity();

            // slack of 1.75*n_voxel_size guarantees that we're not in the same voxel as the intersection point
            intersection_distances_current = arma::max(arma::min(intersection_distances_current, t_max) - 1.75*n_voxel_size, arma::ones<arma::vec>(intersection_distances_current.n_rows)*delta);

            arma::mat query_positions = arma::repmat(start_camera_look_from_position.t() + p*camera_perturb_length*camera_z_axis.t(), ray_directions_world.n_rows, 1) + ray_directions_world % arma::repmat(intersection_distances_current, 1, 3);

            octomap_samples = arma::ones<arma::ivec>(query_positions.n_rows) * -3;

            for (int k = 0; k < query_positions.n_rows; k++) {
                arma::vec query_position = query_positions.row(k).t();
                if (query_position.is_finite()) {
                    auto node_octomap = octree_octomap.search(octomap::point3d(query_position(0), query_position(1), query_position(2)));
                    if (node_octomap != nullptr) {
                        if (node_octomap->getOccupancy() <= octree_octomap.getOccupancyThres()) {
                            octomap_samples(k) = 0;
                        } else {
                            octomap_samples(k) = 1;
                        }
                    } else {
                        octomap_samples(k) = -1;
                    }
                } else {
                    octomap_samples(k) = -2;
                }
            }

            if (arma::any(octomap_samples == 0)) {
                encountered_unoccupied_cell = true;
                break;
            }
        }

        if (all_intersection_distances_at_infinity) {
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK] WARNING: CAMERA DOESN'T OBSERVE ANY PART OF THE SCENE. ALL INTERSECTION DISTANCES ARE AT INFINITY. GIVING UP." << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            return 1;
        }

        if (!encountered_unoccupied_cell) {
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK] WARNING: CAMERA DOESN'T OBSERVE ANY PART OF THE SCENE. ALL OBSERVED OCTOMAP SAMPLES ARE UNKNOWN OR OCCUPIED. GIVING UP." << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK]" << std::endl;
            return 1;
        }

        computed_intersection_distance_image = true;

        indices = arma::find_nonfinite(intersection_distances_current);
        camera_rays_distances_to_center.elem(indices) = arma::ones<arma::vec>(indices.n_rows)*std::numeric_limits<float>::infinity();
        indices = arma::find(octomap_samples != 0);
        camera_rays_distances_to_center.elem(indices) = arma::ones<arma::vec>(indices.n_rows)*std::numeric_limits<float>::infinity();

        indices = arma::find_finite(camera_rays_distances_to_center);
        assert(indices.n_rows != 0);

        indices = arma::sort_index(camera_rays_distances_to_center);
        auto selected_index = indices(0);
        arma::vec ray_direction_world = ray_directions_world.row(selected_index).t();
        auto intersection_distance = intersection_distances_current(selected_index);

        start_camera_look_at_position = start_camera_look_from_position + intersection_distance*ray_direction_world;
    }



    //
    // save preview image
    //

    if (!computed_intersection_distance_image) {

        //
        // works around a bug where matrix-matrix multiplication causes non-deterministic behavior in Armadillo's random number generator
        //
        // arma::mat V_world = start_camera_R_world_from_cam*V_cam;
        arma::mat V_world = arma::ones<arma::mat>(start_camera_R_world_from_cam.n_rows, V_cam.n_cols) * std::numeric_limits<float>::infinity();
        for (int k = 0; k < V_cam.n_cols; k++) {
            V_world.col(k) = start_camera_R_world_from_cam*V_cam.col(k);
        }

        arma::mat  ray_directions_world           = V_world.t();
        arma::mat  ray_positions_world            = arma::repmat(start_camera_look_from_position.t(), ray_directions_world.n_rows, 1);
        arma::vec  intersection_distances_current = arma::ones<arma::vec>(camera_rays.n_rows) * std::numeric_limits<float>::infinity();
        arma::ivec prim_ids_current               = arma::ones<arma::ivec>(camera_rays.n_rows) * -1;

        // for each ray direction...
        for (int k = 0; k < ray_directions_world.n_rows; k++) {

            arma::vec ray_position             = ray_positions_world.row(k).t();
            arma::vec ray_direction_normalized = arma::normalise(ray_directions_world.row(k).t());

            RTCRayHit rtc_ray_hit;

            rtc_ray_hit.ray.org_x = (float)ray_position(0);
            rtc_ray_hit.ray.org_y = (float)ray_position(1);
            rtc_ray_hit.ray.org_z = (float)ray_position(2);
            rtc_ray_hit.ray.dir_x = (float)ray_direction_normalized(0);
            rtc_ray_hit.ray.dir_y = (float)ray_direction_normalized(1);
            rtc_ray_hit.ray.dir_z = (float)ray_direction_normalized(2);
            rtc_ray_hit.ray.tnear = 0.0f;
            rtc_ray_hit.ray.tfar  = std::numeric_limits<float>::infinity();
            rtc_ray_hit.ray.time  = 0.0f;
            rtc_ray_hit.ray.mask  = 0;
            rtc_ray_hit.ray.id    = 0;
            rtc_ray_hit.ray.flags = 0;

            rtc_ray_hit.hit.Ng_x      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.Ng_y      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.Ng_z      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.u         = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.v         = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.primID    = RTC_INVALID_GEOMETRY_ID;
            rtc_ray_hit.hit.geomID    = RTC_INVALID_GEOMETRY_ID;
            rtc_ray_hit.hit.instID[0] = RTC_INVALID_GEOMETRY_ID;

            // intersect ray with scene
            rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

            if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
            } else {
                assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
            }

            if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                intersection_distances_current(k) = rtc_ray_hit.ray.tfar;
                prim_ids_current(k)               = rtc_ray_hit.hit.primID;
            }
        }

        intersection_distances.row(0) = intersection_distances_current.t();
        prim_ids.row(0)               = prim_ids_current.t();
    }



    //
    // camera_up_hints
    //

    arma::mat camera_up_hint_noise = arma::randn<arma::mat>(n_samples_random_walk,3) * n_camera_up_hint_noise_std_dev;
    arma::mat camera_up_hints      = arma::repmat(n_camera_up_hint_nominal.t(), camera_up_hint_noise.n_rows, 1) + camera_up_hint_noise;



    //
    // compute random walk
    //

    arma::vec current_camera_look_from_position = start_camera_look_from_position;
    arma::vec current_camera_look_at_position   = start_camera_look_at_position;
    arma::mat current_camera_orientation        = start_camera_R_world_from_cam;

    arma::mat random_walk_camera_look_from_positions = arma::ones<arma::mat>(n_samples_random_walk,3) * std::numeric_limits<float>::infinity();
    arma::mat random_walk_camera_look_at_positions   = arma::ones<arma::mat>(n_samples_random_walk,3) * std::numeric_limits<float>::infinity();
    arma::cube random_walk_camera_orientations       = arma::ones<arma::cube>(3,3,n_samples_random_walk) * std::numeric_limits<float>::infinity();

    random_walk_camera_look_from_positions.row(0) = current_camera_look_from_position.t();
    random_walk_camera_look_at_positions.row(0)   = current_camera_look_at_position.t();
    random_walk_camera_orientations.slice(0)      = current_camera_orientation.t();

    for (int i = 1; i < n_samples_random_walk; i++) {

        if (!silent) {
            std::cout << "[HYPERSIM: GENERATE_CAMERA_TRAJECTORY_RANDOM_WALK] i = " << i << std::endl;
        }

        arma::vec current_position, start_position, query_extent, current_to_query_distances, intersection_distances_current;
        arma::uvec indices;
        arma::ivec octomap_samples, prim_ids_current;
        arma::mat query_offsets, query_positions, current_to_query, query_ray_directions, query_ray_positions;

        //
        // look_from_position_candidates
        //

        current_position = current_camera_look_from_position;
        start_position   = start_camera_look_from_position;

        query_extent    = 2*n_query_half_extent_relative_to_current;
        query_offsets   = arma::randu<arma::mat>(n_samples_octomap_query, 3) % arma::repmat(query_extent.t(), n_samples_octomap_query, 1) - arma::repmat(n_query_half_extent_relative_to_current.t(), n_samples_octomap_query, 1);
        query_positions = arma::repmat(current_position.t(), n_samples_octomap_query, 1) + query_offsets;

        // filter according to global min and max boundaries
        indices = arma::find(arma::all(query_positions >= arma::repmat(start_position.t(), query_positions.n_rows, 1) - arma::repmat(n_query_half_extent_relative_to_start.t(), query_positions.n_rows, 1), 1));
        query_positions = query_positions.rows(indices);
        indices = arma::find(arma::all(query_positions <= arma::repmat(start_position.t(), query_positions.n_rows, 1) + arma::repmat(n_query_half_extent_relative_to_start.t(), query_positions.n_rows, 1), 1));
        query_positions = query_positions.rows(indices);
        assert(query_positions.n_rows > 0);

        // filter according to occupancy
        octomap_samples = arma::ones<arma::ivec>(query_positions.n_rows) * -3;

        for (int k = 0; k < query_positions.n_rows; k++) {
            arma::vec query_position = query_positions.row(k).t();
            if (query_position.is_finite()) {
                auto node_octomap = octree_octomap.search(octomap::point3d(query_position(0), query_position(1), query_position(2)));
                if (node_octomap != nullptr) {
                    if (node_octomap->getOccupancy() <= octree_octomap.getOccupancyThres()) {
                        octomap_samples(k) = 0;
                    } else {
                        octomap_samples(k) = 1;
                    }
                } else {
                    octomap_samples(k) = -1;
                }
            } else {
                octomap_samples(k) = -2;
            }
        }

        indices = arma::find(octomap_samples == 0);
        query_positions = query_positions.rows(indices);
        assert(query_positions.n_rows > 0);

        // filter according to line of sight
        current_to_query = query_positions - arma::repmat(current_position.t(), query_positions.n_rows, 1);

        current_to_query_distances = arma::ones<arma::vec>(current_to_query.n_rows) * std::numeric_limits<float>::infinity();
        for (int k = 0; k < current_to_query.n_rows; k++) {
            current_to_query_distances(k) = arma::norm(current_to_query.row(k));
        }

        query_ray_directions           = current_to_query;
        query_ray_positions            = arma::repmat(current_position.t(), query_ray_directions.n_rows, 1);
        intersection_distances_current = arma::ones<arma::vec>(query_ray_directions.n_rows) * std::numeric_limits<float>::infinity();
        prim_ids_current               = arma::ones<arma::ivec>(query_ray_directions.n_rows) * -1;

        // for each ray direction...
        for (int k = 0; k < query_ray_directions.n_rows; k++) {

            arma::vec ray_position             = query_ray_positions.row(k).t();
            arma::vec ray_direction_normalized = arma::normalise(query_ray_directions.row(k).t());

            RTCRayHit rtc_ray_hit;

            rtc_ray_hit.ray.org_x = (float)ray_position(0);
            rtc_ray_hit.ray.org_y = (float)ray_position(1);
            rtc_ray_hit.ray.org_z = (float)ray_position(2);
            rtc_ray_hit.ray.dir_x = (float)ray_direction_normalized(0);
            rtc_ray_hit.ray.dir_y = (float)ray_direction_normalized(1);
            rtc_ray_hit.ray.dir_z = (float)ray_direction_normalized(2);
            rtc_ray_hit.ray.tnear = 0.0f;
            rtc_ray_hit.ray.tfar  = std::numeric_limits<float>::infinity();
            rtc_ray_hit.ray.time  = 0.0f;
            rtc_ray_hit.ray.mask  = 0;
            rtc_ray_hit.ray.id    = 0;
            rtc_ray_hit.ray.flags = 0;

            rtc_ray_hit.hit.Ng_x      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.Ng_y      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.Ng_z      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.u         = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.v         = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.primID    = RTC_INVALID_GEOMETRY_ID;
            rtc_ray_hit.hit.geomID    = RTC_INVALID_GEOMETRY_ID;
            rtc_ray_hit.hit.instID[0] = RTC_INVALID_GEOMETRY_ID;

            // intersect ray with scene
            rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

            if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
            } else {
                assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
            }

            if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                intersection_distances_current(k) = rtc_ray_hit.ray.tfar;
                prim_ids_current(k)               = rtc_ray_hit.hit.primID;
            }
        }

        indices = arma::find((1.0-eps)*intersection_distances_current >= current_to_query_distances);
        query_positions = query_positions.rows(indices);
        assert(query_positions.n_rows > 0);

        arma::mat look_from_position_candidates = query_positions;



        //
        // look_at_position_candidates
        //

        current_position = current_camera_look_at_position;
        start_position   = start_camera_look_at_position;

        query_extent    = 2*n_query_half_extent_relative_to_current;
        query_offsets   = arma::randu<arma::mat>(n_samples_octomap_query, 3) % arma::repmat(query_extent.t(), n_samples_octomap_query, 1) - arma::repmat(n_query_half_extent_relative_to_current.t(), n_samples_octomap_query, 1);
        query_positions = arma::repmat(current_position.t(), n_samples_octomap_query, 1) + query_offsets;

        // filter according to global min and max boundaries
        indices = arma::find(arma::all(query_positions >= arma::repmat(start_position.t(), query_positions.n_rows, 1) - arma::repmat(n_query_half_extent_relative_to_start.t(), query_positions.n_rows, 1), 1));
        query_positions = query_positions.rows(indices);
        indices = arma::find(arma::all(query_positions <= arma::repmat(start_position.t(), query_positions.n_rows, 1) + arma::repmat(n_query_half_extent_relative_to_start.t(), query_positions.n_rows, 1), 1));
        query_positions = query_positions.rows(indices);
        assert(query_positions.n_rows > 0);

        // filter according to occupancy
        octomap_samples = arma::ones<arma::ivec>(query_positions.n_rows) * -3;

        for (int k = 0; k < query_positions.n_rows; k++) {
            arma::vec query_position = query_positions.row(k).t();
            if (query_position.is_finite()) {
                auto node_octomap = octree_octomap.search(octomap::point3d(query_position(0), query_position(1), query_position(2)));
                if (node_octomap != nullptr) {
                    if (node_octomap->getOccupancy() <= octree_octomap.getOccupancyThres()) {
                        octomap_samples(k) = 0;
                    } else {
                        octomap_samples(k) = 1;
                    }
                } else {
                    octomap_samples(k) = -1;
                }
            } else {
                octomap_samples(k) = -2;
            }
        }

        indices = arma::find(octomap_samples == 0);
        query_positions = query_positions.rows(indices);
        assert(query_positions.n_rows > 0);

        // filter according to line of sight
        current_to_query = query_positions - arma::repmat(current_position.t(), query_positions.n_rows, 1);

        current_to_query_distances = arma::ones<arma::vec>(current_to_query.n_rows) * std::numeric_limits<float>::infinity();
        for (int k = 0; k < current_to_query.n_rows; k++) {
            current_to_query_distances(k) = arma::norm(current_to_query.row(k));
        }

        query_ray_directions           = current_to_query;
        query_ray_positions            = arma::repmat(current_position.t(), query_ray_directions.n_rows, 1);
        intersection_distances_current = arma::ones<arma::vec>(query_ray_directions.n_rows) * std::numeric_limits<float>::infinity();
        prim_ids_current               = arma::ones<arma::ivec>(query_ray_directions.n_rows) * -1;

        // for each ray direction...
        for (int k = 0; k < query_ray_directions.n_rows; k++) {

            arma::vec ray_position             = query_ray_positions.row(k).t();
            arma::vec ray_direction_normalized = arma::normalise(query_ray_directions.row(k).t());

            RTCRayHit rtc_ray_hit;

            rtc_ray_hit.ray.org_x = (float)ray_position(0);
            rtc_ray_hit.ray.org_y = (float)ray_position(1);
            rtc_ray_hit.ray.org_z = (float)ray_position(2);
            rtc_ray_hit.ray.dir_x = (float)ray_direction_normalized(0);
            rtc_ray_hit.ray.dir_y = (float)ray_direction_normalized(1);
            rtc_ray_hit.ray.dir_z = (float)ray_direction_normalized(2);
            rtc_ray_hit.ray.tnear = 0.0f;
            rtc_ray_hit.ray.tfar  = std::numeric_limits<float>::infinity();
            rtc_ray_hit.ray.time  = 0.0f;
            rtc_ray_hit.ray.mask  = 0;
            rtc_ray_hit.ray.id    = 0;
            rtc_ray_hit.ray.flags = 0;

            rtc_ray_hit.hit.Ng_x      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.Ng_y      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.Ng_z      = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.u         = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.v         = std::numeric_limits<float>::infinity();
            rtc_ray_hit.hit.primID    = RTC_INVALID_GEOMETRY_ID;
            rtc_ray_hit.hit.geomID    = RTC_INVALID_GEOMETRY_ID;
            rtc_ray_hit.hit.instID[0] = RTC_INVALID_GEOMETRY_ID;

            // intersect ray with scene
            rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

            if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
            } else {
                assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
            }

            if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                intersection_distances_current(k) = rtc_ray_hit.ray.tfar;
                prim_ids_current(k)               = rtc_ray_hit.hit.primID;
            }
        }

        indices = arma::find((1.0-eps)*intersection_distances_current >= current_to_query_distances);
        query_positions = query_positions.rows(indices);
        assert(query_positions.n_rows > 0);

        arma::mat look_at_position_candidates = query_positions;



        //
        // raycast against triangle mesh for each camera pose candidate
        //

        indices = arma::randi<arma::uvec>(n_samples_camera_pose_candidates, arma::distr_param(0, look_from_position_candidates.n_rows - 1));
        look_from_position_candidates = look_from_position_candidates.rows(indices);

        indices = arma::randi<arma::uvec>(n_samples_camera_pose_candidates, arma::distr_param(0, look_at_position_candidates.n_rows - 1));
        look_at_position_candidates = look_at_position_candidates.rows(indices);
        arma::vec camera_up_hint = camera_up_hints.row(i).t();

        arma::cube camera_orientation_candidates     = arma::ones<arma::cube>(3,3,n_samples_camera_pose_candidates) * std::numeric_limits<float>::infinity();
        arma::mat  intersection_distances_candidates = arma::ones<arma::mat>(n_samples_camera_pose_candidates, V_cam.n_cols) * std::numeric_limits<float>::infinity();
        arma::imat prim_ids_candidates               = arma::ones<arma::imat>(n_samples_camera_pose_candidates, V_cam.n_cols) * -1;
        arma::vec  view_scores_candidates            = arma::ones<arma::vec>(n_samples_camera_pose_candidates) * std::numeric_limits<float>::infinity();

        for (int j = 0; j < n_samples_camera_pose_candidates; j++) {

            arma::vec camera_look_from_position = look_from_position_candidates.row(j).t();
            arma::vec camera_look_at_position   = look_at_position_candidates.row(j).t();
            arma::vec camera_look_at_dir        = arma::normalise(camera_look_at_position - camera_look_from_position);

            // The convention here is that the camera's positive x axis points right, the positive y
            // axis points up, and the positive z axis points away from where the camera is looking.
            arma::vec camera_z_axis = -arma::normalise(camera_look_at_dir);
            arma::vec camera_x_axis = -arma::normalise(arma::cross(camera_z_axis, camera_up_hint));
            arma::vec camera_y_axis = arma::normalise(arma::cross(camera_z_axis, camera_x_axis));

            arma::mat R_world_from_cam = arma::ones<arma::mat>(3,3) * std::numeric_limits<float>::infinity();
            R_world_from_cam.col(0) = camera_x_axis;
            R_world_from_cam.col(1) = camera_y_axis;
            R_world_from_cam.col(2) = camera_z_axis;

            //
            // works around a bug where matrix-matrix multiplication causes non-deterministic behavior in Armadillo's random number generator
            //
            // arma::mat V_world = R_world_from_cam*V_cam;
            arma::mat V_world = arma::ones<arma::mat>(R_world_from_cam.n_rows, V_cam.n_cols) * std::numeric_limits<float>::infinity();
            for (int k = 0; k < V_cam.n_cols; k++) {
                V_world.col(k) = R_world_from_cam*V_cam.col(k);
            }

            arma::mat ray_directions_world = V_world.t();
            arma::mat ray_positions_world  = arma::repmat(camera_look_from_position.t(), ray_directions_world.n_rows, 1);

            // for each ray direction...
            for (int k = 0; k < ray_directions_world.n_rows; k++) {

                arma::vec ray_position             = ray_positions_world.row(k).t();
                arma::vec ray_direction_normalized = arma::normalise(ray_directions_world.row(k).t());

                RTCRayHit rtc_ray_hit;

                rtc_ray_hit.ray.org_x = (float)ray_position(0);
                rtc_ray_hit.ray.org_y = (float)ray_position(1);
                rtc_ray_hit.ray.org_z = (float)ray_position(2);
                rtc_ray_hit.ray.dir_x = (float)ray_direction_normalized(0);
                rtc_ray_hit.ray.dir_y = (float)ray_direction_normalized(1);
                rtc_ray_hit.ray.dir_z = (float)ray_direction_normalized(2);
                rtc_ray_hit.ray.tnear = 0.0f;
                rtc_ray_hit.ray.tfar  = std::numeric_limits<float>::infinity();
                rtc_ray_hit.ray.time  = 0.0f;
                rtc_ray_hit.ray.mask  = 0;
                rtc_ray_hit.ray.id    = 0;
                rtc_ray_hit.ray.flags = 0;

                rtc_ray_hit.hit.Ng_x      = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.Ng_y      = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.Ng_z      = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.u         = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.v         = std::numeric_limits<float>::infinity();
                rtc_ray_hit.hit.primID    = RTC_INVALID_GEOMETRY_ID;
                rtc_ray_hit.hit.geomID    = RTC_INVALID_GEOMETRY_ID;
                rtc_ray_hit.hit.instID[0] = RTC_INVALID_GEOMETRY_ID;

                // intersect ray with scene
                rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

                if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                    assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
                } else {
                    assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
                }

                if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                    intersection_distances_candidates(j,k) = rtc_ray_hit.ray.tfar;
                    prim_ids_candidates(j,k)               = rtc_ray_hit.hit.primID;
                }
            }

            indices = arma::find(prim_ids_candidates.row(j) != -1);
            auto valid_fraction = (float)indices.n_rows / (float)ray_directions_world.n_rows;
            indices = arma::find_unique(prim_ids_candidates.row(j));
            auto num_unique_prims = indices.n_rows;

            view_scores_candidates(j)              = std::pow(valid_fraction,2)*num_unique_prims + lamb;
            camera_orientation_candidates.slice(j) = R_world_from_cam;
        }

        //
        // select a camera pose candidate with probability proportional to the view scores
        //

        arma::vec view_scores_candidates_normalized_cumsum = arma::cumsum(view_scores_candidates / arma::sum(view_scores_candidates));
        arma::vec uniform_vals = arma::randu<arma::vec>(1);
        indices = arma::find(view_scores_candidates_normalized_cumsum >= uniform_vals(0));
        auto selected_index = indices(0);

        // auto selected_index = arma::index_max(view_scores_candidates);



        //
        // save preview image
        //

        intersection_distances.row(i) = intersection_distances_candidates.row(selected_index);
        prim_ids.row(i)               = prim_ids_candidates.row(selected_index);



        //
        // append selected camera pose to random walk
        //

        current_camera_look_from_position = look_from_position_candidates.row(selected_index).t();
        current_camera_look_at_position   = look_at_position_candidates.row(selected_index).t();
        current_camera_orientation        = camera_orientation_candidates.slice(selected_index);

        random_walk_camera_look_from_positions.row(i) = current_camera_look_from_position.t();
        random_walk_camera_look_at_positions.row(i)   = current_camera_look_at_position.t();
        random_walk_camera_orientations.slice(i)      = current_camera_orientation.t();
    }



    random_walk_camera_look_from_positions.save(output_camera_look_from_positions_file, arma::hdf5_binary_trans);
    random_walk_camera_look_at_positions.save(output_camera_look_at_positions_file, arma::hdf5_binary_trans);
    random_walk_camera_orientations.save(output_camera_orientations_file, arma::hdf5_binary_trans);
    intersection_distances.save(output_intersection_distances_file, arma::hdf5_binary_trans);
    prim_ids.save(output_prim_ids_file, arma::hdf5_binary_trans);

    //
    // release Embree data
    //

    rtcReleaseScene(rtc_scene); rtc_scene = nullptr;
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    rtcReleaseDevice(rtc_device); rtc_device = nullptr;
    assert(rtcGetDeviceError(nullptr) == RTC_ERROR_NONE);

    return 0;
}
