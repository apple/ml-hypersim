//
// For licensing see accompanying LICENSE.txt file.
// Copyright (C) 2020 Apple Inc. All Rights Reserved.
//

#include <algorithm>
#include <cassert>
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

    args::ArgumentParser parser("generate_octomap", "");

    args::HelpFlag               help                            (parser, "__DUMMY__",                   "Display this help menu",      {'h', "help"});
    args::ValueFlag<std::string> mesh_vertices_file_arg          (parser, "MESH_VERTICES_FILE",          "mesh_vertices",               {"mesh_vertices_file"},          args::Options::Required);
    args::ValueFlag<std::string> mesh_faces_vi_file_arg          (parser, "MESH_FACES_VI_FILE",          "mesh_faces_vi_file",          {"mesh_faces_vi_file"},          args::Options::Required);
    args::ValueFlag<std::string> start_camera_positions_file_arg (parser, "START_CAMERA_POSITIONS_FILE", "start_camera_positions_file", {"start_camera_positions_file"}, args::Options::Required);
    args::ValueFlag<std::string> ray_directions_file_arg         (parser, "RAY_DIRECTIONS_FILE",         "ray_directions_file",         {"ray_directions_file"},         args::Options::Required);
    args::ValueFlag<std::string> ray_neighbor_indices_file_arg   (parser, "RAY_NEIGHBOR_INDICES_FILE",   "ray_neighbor_indices_file",   {"ray_neighbor_indices_file"},   args::Options::Required);
    args::ValueFlag<std::string> octomap_min_file_arg            (parser, "OCTOMAP_MIN_FILE",            "octomap_min_file",            {"octomap_min_file"},            args::Options::Required);
    args::ValueFlag<std::string> octomap_max_file_arg            (parser, "OCTOMAP_MAX_FILE",            "octomap_max_file",            {"octomap_max_file"},            args::Options::Required);
    args::ValueFlag<int>         n_iters_arg                     (parser, "N_ITERS",                     "n_iters",                     {"n_iters"},                     args::Options::Required);
    args::ValueFlag<float>       n_voxel_size_arg                (parser, "N_VOXEL_SIZE",                "n_voxel_size",                {"n_voxel_size"},                args::Options::Required);
    args::ValueFlag<std::string> octomap_file_arg                (parser, "OCTOMAP_FILE",                "octomap_file",                {"octomap_file"},                args::Options::Required);
    args::ValueFlag<std::string> free_space_min_file_arg         (parser, "FREE_SPACE_MIN_FILE",         "free_space_min_file",         {"free_space_min_file"},         args::Options::Required);
    args::ValueFlag<std::string> free_space_max_file_arg         (parser, "FREE_SPACE_MAX_FILE",         "free_space_max_file",         {"free_space_max_file"},         args::Options::Required);
    args::Flag                   silent_arg                      (parser, "__DUMMY__",                   "silent",                      {"silent"});

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

    auto mesh_vertices_file          = args::get(mesh_vertices_file_arg);
    auto mesh_faces_vi_file          = args::get(mesh_faces_vi_file_arg);
    auto start_camera_positions_file = args::get(start_camera_positions_file_arg);
    auto ray_directions_file         = args::get(ray_directions_file_arg);
    auto ray_neighbor_indices_file   = args::get(ray_neighbor_indices_file_arg);
    auto octomap_min_file            = args::get(octomap_min_file_arg);
    auto octomap_max_file            = args::get(octomap_max_file_arg);
    auto n_iters                     = args::get(n_iters_arg);
    auto n_voxel_size                = args::get(n_voxel_size_arg);
    auto octomap_file                = args::get(octomap_file_arg);
    auto free_space_min_file         = args::get(free_space_min_file_arg);
    auto free_space_max_file         = args::get(free_space_max_file_arg);
    auto silent                      = args::get(silent_arg);

    arma::mat mesh_vertices, start_camera_positions, ray_directions;
    arma::imat mesh_faces_vi;
    arma::umat ray_neighbor_indices;
    arma::vec octomap_min, octomap_max;

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Begin..." << std::endl;
    }

    //
    // load input data
    //

    mesh_vertices.load(mesh_vertices_file, arma::hdf5_binary_trans);
    mesh_faces_vi.load(mesh_faces_vi_file, arma::hdf5_binary_trans);
    start_camera_positions.load(start_camera_positions_file, arma::hdf5_binary_trans);
    ray_directions.load(ray_directions_file, arma::hdf5_binary_trans);
    ray_neighbor_indices.load(ray_neighbor_indices_file, arma::hdf5_binary_trans);
    octomap_min.load(octomap_min_file, arma::hdf5_binary_trans);
    octomap_max.load(octomap_max_file, arma::hdf5_binary_trans);

    assert(mesh_vertices.n_cols == 3);
    assert(mesh_faces_vi.n_cols == 3);
    assert(start_camera_positions.n_cols == 3);
    assert(ray_directions.n_cols == 3);
    assert(ray_neighbor_indices.n_rows == ray_directions.n_rows);
    assert(octomap_min.n_rows == 3);
    assert(octomap_max.n_rows == 3);

    arma::uvec ray_neighbor_indices_vec = arma::vectorise(ray_neighbor_indices);

    if (!silent) {
        octomap_min.raw_print(std::cout, "octomap_min = ");
        octomap_max.raw_print(std::cout, "octomap_max = ");
    }

    //
    // construct Embree data
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Constructing Embree data..." << std::endl;
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
    // sample mesh
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Generating mesh samples..." << std::endl;
    }

    octomap::OcTree octree_octomap(n_voxel_size);
    octomap::point3d octomap_min_octomap(octomap_min(0), octomap_min(1), octomap_min(2));
    octomap::point3d octomap_max_octomap(octomap_max(0), octomap_max(1), octomap_max(2));
    octree_octomap.setBBXMin(octomap_min_octomap);
    octree_octomap.setBBXMax(octomap_max_octomap);

    octomap::KeySet occupied_cells_octomap;

    for (int i = 0; i < mesh_faces_vi.n_rows; i++) {

        arma::vec v_0 = mesh_vertices.row(mesh_faces_vi(i,0)).t();
        arma::vec v_1 = mesh_vertices.row(mesh_faces_vi(i,1)).t();
        arma::vec v_2 = mesh_vertices.row(mesh_faces_vi(i,2)).t();

        // if v_0 or v_1 or v_2 is inside our bounding box, then sample face
        if ((arma::all(v_0 >= octomap_min) && arma::all(v_0 <= octomap_max)) ||
            (arma::all(v_1 >= octomap_min) && arma::all(v_1 <= octomap_max)) ||
            (arma::all(v_2 >= octomap_min) && arma::all(v_2 <= octomap_max))) {

            octomap::point3d v_0_octomap(v_0(0), v_0(1), v_0(2));
            octomap::point3d v_1_octomap(v_1(0), v_1(1), v_1(2));
            octomap::point3d v_2_octomap(v_2(0), v_2(1), v_2(2));
            octomap::OcTreeKey v_0_key_octomap, v_1_key_octomap, v_2_key_octomap;
            bool key_valid;
            key_valid = octree_octomap.coordToKeyChecked(v_0_octomap, v_0_key_octomap);
            assert(key_valid);
            key_valid = octree_octomap.coordToKeyChecked(v_1_octomap, v_1_key_octomap);
            assert(key_valid);
            key_valid = octree_octomap.coordToKeyChecked(v_2_octomap, v_2_key_octomap);
            assert(key_valid);

            if ((v_0_key_octomap == v_1_key_octomap) && (v_1_key_octomap == v_2_key_octomap)) {
                // if v_0 and v_1 and v_2 are all in the same octomap cell, then add v_0 to samples
                occupied_cells_octomap.insert(v_0_key_octomap);
            } else {

                // otherwise we need to generate samples over the face
                arma::vec p_c  = (v_0+v_1+v_2)/3.0;

                arma::vec d_c0 = v_0 - p_c;
                arma::vec d_c1 = v_1 - p_c;

                arma::vec tangent_space_x = arma::normalise(d_c0);
                arma::vec tangent_space_z = arma::normalise(arma::cross(d_c0, d_c1));
                arma::vec tangent_space_y = arma::normalise(arma::cross(tangent_space_z, tangent_space_x));

                arma::mat R_world_from_tangent = arma::join_rows(arma::join_rows(tangent_space_x, tangent_space_y), tangent_space_z);
                arma::vec t_world_from_tangent = p_c;

                arma::mat R_tangent_from_world = R_world_from_tangent.t();
                arma::vec t_tangent_from_world = -t_world_from_tangent;

                arma::vec v_0_tangent = R_tangent_from_world*(v_0 + t_tangent_from_world);
                arma::vec v_1_tangent = R_tangent_from_world*(v_1 + t_tangent_from_world);
                arma::vec v_2_tangent = R_tangent_from_world*(v_2 + t_tangent_from_world);

                arma::mat verts_tangent = arma::join_cols(arma::join_cols(v_0_tangent.t(), v_1_tangent.t()), v_2_tangent.t());

                arma::vec verts_tangent_min = arma::min(verts_tangent, 0).t();
                arma::vec verts_tangent_max = arma::max(verts_tangent, 0).t();

                auto grid_spacing = 0.25*n_voxel_size; // generate grid of points in tangent space with this much space between points
                auto eps = 0.001*n_voxel_size;         // make the grid extend slightly beyond the min and max extent of each face

                auto verts_tangent_min_x          = verts_tangent_min(0) - eps;
                auto verts_tangent_max_x          = verts_tangent_max(0) + eps;
                arma::vec grid_x_neg_conservative = arma::reverse(arma::regspace(0, -grid_spacing, verts_tangent_min_x));
                arma::vec grid_x_pos_conservative = arma::regspace(0, grid_spacing, verts_tangent_max_x);
                arma::vec grid_x_neg              = arma::join_cols(arma::vec({grid_x_neg_conservative(0) - grid_spacing}), grid_x_neg_conservative);
                arma::vec grid_x_pos              = arma::join_cols(grid_x_pos_conservative, arma::vec({grid_x_pos_conservative.tail(1) + grid_spacing}));
                arma::vec grid_x                  = arma::join_cols(grid_x_neg.head(grid_x_neg.n_elem - 1), grid_x_pos);

                auto verts_tangent_min_y          = verts_tangent_min(1) - eps;
                auto verts_tangent_max_y          = verts_tangent_max(1) + eps;
                arma::vec grid_y_neg_conservative = arma::reverse(arma::regspace(0, -grid_spacing, verts_tangent_min_y));
                arma::vec grid_y_pos_conservative = arma::regspace(0, grid_spacing, verts_tangent_max_y);
                arma::vec grid_y_neg              = arma::join_cols(arma::vec({grid_y_neg_conservative(0) - grid_spacing}), grid_y_neg_conservative);
                arma::vec grid_y_pos              = arma::join_cols(grid_y_pos_conservative, arma::vec({grid_y_pos_conservative.tail(1) + grid_spacing}));
                arma::vec grid_y                  = arma::join_cols(grid_y_neg.head(grid_y_neg.n_elem - 1), grid_y_pos);

                // precompute these values outside the for loop to compute barycentric coordinates
                // see https://gamedev.stackexchange.com/questions/23743/whats-the-most-efficient-way-to-find-barycentric-coordinates
                arma::vec a_ = v_0_tangent;
                arma::vec b_ = v_1_tangent;
                arma::vec c_ = v_2_tangent;
                arma::vec v_0_ = b_ - a_;
                arma::vec v_1_ = c_ - a_;
                auto d_00_     = arma::dot(v_0_, v_0_);
                auto d_01_     = arma::dot(v_0_, v_1_);
                auto d_11_     = arma::dot(v_1_, v_1_);

                for (auto y_tangent : grid_y) {
                    for (auto x_tangent : grid_x) {

                        arma::vec p_tangent({x_tangent, y_tangent, 0});
                        arma::vec p = R_world_from_tangent*p_tangent + t_world_from_tangent;

                        // if sample point is inside our bounding box 
                        if (arma::all(p >= octomap_min) && arma::all(p <= octomap_max)) {

                            // compute barycentric coordinates for sample point
                            arma::vec p_   = p_tangent;
                            arma::vec v_2_ = p_ - a_;

                            auto d_20_  = arma::dot(v_2_, v_0_);
                            auto d_21_  = arma::dot(v_2_, v_1_);
                            auto denom_ = d_00_ * d_11_ - d_01_ * d_01_;
                            auto v_     = (d_11_ * d_20_ - d_01_ * d_21_) / denom_;
                            auto w_     = (d_00_ * d_21_ - d_01_ * d_20_) / denom_;
                            auto u_     = 1.0 - v_ - w_;

                            // if sample point is inside the current face, then add it to our octomap
                            if (u_ > 0 && v_ > 0 && w_ > 0) {
                                octomap::point3d p_octomap(p(0), p(1), p(2));
                                octomap::OcTreeKey p_key_octomap;
                                auto key_valid = octree_octomap.coordToKeyChecked(p_octomap, p_key_octomap);
                                assert(key_valid);
                                occupied_cells_octomap.insert(p_key_octomap);
                            }
                        }
                    }
                }

                // due to numerical issues with very small triangles, the triangle center is not guaranteed
                // to be added in the loop above, so add it here explicitly
                if (arma::all(p_c >= octomap_min) && arma::all(p_c <= octomap_max)) {
                    octomap::point3d p_c_octomap(p_c(0), p_c(1), p_c(2));
                    octomap::OcTreeKey p_c_key_octomap;
                    auto key_valid = octree_octomap.coordToKeyChecked(p_c_octomap, p_c_key_octomap);
                    assert(key_valid);
                    occupied_cells_octomap.insert(p_c_key_octomap);
                }
            }
        }
    }

    //
    // pre-fill octomap with known occupied space from the mesh samples
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Updating Octomap..." << std::endl;
    }

    for (auto it : occupied_cells_octomap) {
        auto occupied  = true;
        auto lazy_eval = true;
        octree_octomap.updateNode(it, occupied, lazy_eval);
    }

    octree_octomap.updateInnerOccupancy();



    // if (!silent) {
    //     std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Writing Octomap..." << std::endl;
    // }

    // octree_octomap.writeBinary(octomap_file);



    //
    // perform space carving
    //

    arma::arma_rng::set_seed(0);
    std::cout.precision(20);
    std::cout.setf(std::ios::fixed);

    arma::vec free_space_min({std::numeric_limits<float>::infinity(), std::numeric_limits<float>::infinity(), std::numeric_limits<float>::infinity()});
    arma::vec free_space_max({-std::numeric_limits<float>::infinity(), -std::numeric_limits<float>::infinity(), -std::numeric_limits<float>::infinity()});

    auto n_max_ray_length      = arma::norm(octomap_max - octomap_min);
    auto n_ray_sample_step     = 0.25*n_voxel_size; // we may need to perturb our starting position so it is not in occupied space; use this step size when perturbing
    auto encountered_free_cell = false;

    if (!silent) {
        free_space_min.raw_print(std::cout, "free_space_min = ");
        free_space_max.raw_print(std::cout, "free_space_max = ");
    }

    // for all starting camera positions...
    for (int i = 0; i < start_camera_positions.n_rows; i++) {

        if (!silent) {
            std::cout << "[HYPERSIM: GENERATE_OCTOMAP] i = " << i << std::endl;
            start_camera_positions.row(i).raw_print(std::cout, "start_camera_positions[i] = ");
        }



        //
        // attempt to perturb the starting camera position in case it is in an occupied cell
        //

        if (!silent) {
            std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Verifying start_camera_position[i]..." << std::endl;
        }

        arma::vec camera_position = start_camera_positions.row(i).t();
        arma::vec intersection_distances = arma::ones<arma::vec>(ray_directions.n_rows) * std::numeric_limits<float>::infinity();

        // for each ray direction...
        for (int k = 0; k < ray_directions.n_rows; k++) {

            arma::vec ray_direction_normalized = arma::normalise(ray_directions.row(k).t());

            RTCRayHit rtc_ray_hit;

            rtc_ray_hit.ray.org_x = (float)camera_position(0);
            rtc_ray_hit.ray.org_y = (float)camera_position(1);
            rtc_ray_hit.ray.org_z = (float)camera_position(2);
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

            rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

            if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
            } else {
                assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
            }

            if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                auto intersection_distance = rtc_ray_hit.ray.tfar;
                intersection_distances(k) = intersection_distance;
            }
        }

        arma::vec intersection_distances_neighbors_vec = intersection_distances.elem(ray_neighbor_indices_vec);
        arma::mat intersection_distances_neighbors     = arma::reshape(intersection_distances_neighbors_vec, ray_neighbor_indices.n_rows, ray_neighbor_indices.n_cols);
        arma::vec intersection_distances_min           = arma::min(intersection_distances_neighbors, 1); // perform min-pooling operation
        intersection_distances                         = intersection_distances_min;
        arma::uvec intersection_distances_argsort      = sort_index(intersection_distances, "descend");
        auto encountered_unknown_or_free_cell          = false;
        auto num_perturbation_attempts                 = 0;
        auto num_perturbation_directions               = 0;

        // for each ray direction...
        for (int k = 0; k < intersection_distances_argsort.n_rows; k++) {

            auto max_ray_length                             = std::min(intersection_distances(intersection_distances_argsort(k)),n_max_ray_length);
            arma::vec ray_direction_normalized              = arma::normalise(ray_directions.row(intersection_distances_argsort(k)).t());
            arma::vec query_position                        = camera_position;
            auto current_ray_length                         = 0.0;
            auto attempted_to_perturb_for_current_direction = false;

            // use a conservative sampling approach here instead of computing the exact set of voxels intersected by the ray;
            // we could also use an exact approach (as we do later in this source file), but it seems wasteful because we
            // probably don't need to do much perturbing to find an unknown or free voxel
            while (current_ray_length < max_ray_length && !encountered_unknown_or_free_cell) {

                if (!(arma::all(query_position >= octomap_min) && arma::all(query_position <= octomap_max))) {
                    break;
                }

                octomap::point3d query_position_octomap(query_position(0), query_position(1), query_position(2));
                auto node_octomap = octree_octomap.search(query_position_octomap);

                if (node_octomap == nullptr) {
                    camera_position                  = query_position;
                    encountered_unknown_or_free_cell = true;
                    break;
                } else if (node_octomap->getOccupancy() <= octree_octomap.getOccupancyThres()) {
                    camera_position                  = query_position;
                    encountered_unknown_or_free_cell = true;
                    break;
                }

                current_ray_length += n_ray_sample_step;
                query_position = camera_position + current_ray_length*ray_direction_normalized;
                num_perturbation_attempts += 1;
                if (!attempted_to_perturb_for_current_direction) {
                    attempted_to_perturb_for_current_direction = true;
                    num_perturbation_directions += 1;
                }
            }

            if (encountered_unknown_or_free_cell) {
                break;
            }
        }

        if (encountered_unknown_or_free_cell) {
            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Finished verifying start_camera_position[i]." << std::endl;
                camera_position.raw_print(std::cout, "camera_position = ");
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Attempted " << num_perturbation_attempts << " perturbations along " << num_perturbation_directions << " distinct directions..." << std::endl;
            }
        } else {
            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP]" << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP]" << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP]" << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] WARNING: COULD NOT VERIFY start_camera_position[i], GIVING UP." << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Attempted " << num_perturbation_attempts << " perturbations along " << num_perturbation_directions << " distinct directions..." << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP]" << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP]" << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP]" << std::endl;
            }
            continue;
        }

        //
        // at this point, the camera position is guaranteed to be in free or unknown space...
        //



        // for all iterations...
        for (int j = 0; j < n_iters; j++) {

            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] j = " << j << std::endl;
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Performing space carving along rays..." << std::endl;
            }

            // sanity check the camera position prior to space carving
            auto node = octree_octomap.search(octomap::point3d(camera_position(0), camera_position(1), camera_position(2)));
            if (node != nullptr) {
                // if the camera position is in known space, then it must be unoccupied
                assert(node->getOccupancy() <= octree_octomap.getOccupancyThres());
            }

            //
            // raycast against triangle mesh
            //

            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Raycasting against triangle mesh..." << std::endl;
            }

            octomap::KeySet occupied_cells_octomap_current;
            arma::vec intersection_distances = arma::ones<arma::vec>(ray_directions.n_rows) * std::numeric_limits<float>::infinity();

            // for each ray direction...
            for (int k = 0; k < ray_directions.n_rows; k++) {

                arma::vec ray_direction_normalized = arma::normalise(ray_directions.row(k).t());

                RTCRayHit rtc_ray_hit;

                rtc_ray_hit.ray.org_x = (float)camera_position(0);
                rtc_ray_hit.ray.org_y = (float)camera_position(1);
                rtc_ray_hit.ray.org_z = (float)camera_position(2);
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

                rtcIntersect1(rtc_scene, &rtc_intersect_context, &rtc_ray_hit);

                if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                    assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
                } else {
                    assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
                }

                if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                    auto intersection_distance = rtc_ray_hit.ray.tfar;
                    arma::vec intersection_position = camera_position + intersection_distance*ray_direction_normalized;
                    intersection_distances(k) = intersection_distance;
                }
            }

            //
            // raycast against octomap
            //

            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Raycasting against Octomap..." << std::endl;
            }

            octomap::KeySet free_cells_octomap;
            octomap::KeyRay key_rays_octomap;

            // for each ray direction...
            for (int k = 0; k < ray_directions.n_rows; k++) {

                auto ray_length                    = std::min(intersection_distances(k),n_max_ray_length);
                arma::vec ray_direction_normalized = arma::normalise(ray_directions.row(k).t());
                arma::vec query_position           = camera_position;
                arma::vec end_position             = query_position + ray_length*ray_direction_normalized;
                octomap::point3d query_position_octomap(query_position(0), query_position(1), query_position(2));
                octomap::point3d end_position_octomap(end_position(0), end_position(1), end_position(2));

                // compute the exact set of voxels intersected by ray
                key_rays_octomap.reset();
                auto success = octree_octomap.computeRayKeys(query_position_octomap, end_position_octomap, key_rays_octomap);
                assert(success);

                for(auto it : key_rays_octomap) {

                    if (!octree_octomap.inBBX(it)) {
                        break;
                    }

                    auto node_octomap = octree_octomap.search(it);
                    if (node_octomap == nullptr) {
                        // if we encounter unknown space, then mark it as free because we're somewhere along a ray that starts in free space and hasn't encountered surface geometry yet
                        free_cells_octomap.insert(it);
                        auto key_position_octomap = octree_octomap.keyToCoord(it);
                        arma::vec key_position({ key_position_octomap.x(), key_position_octomap.y(), key_position_octomap.z() });
                        free_space_max = arma::max(free_space_max, key_position);
                        free_space_min = arma::min(free_space_min, key_position);
                        encountered_free_cell = true;
                    } else {
                        if (node_octomap->getOccupancy() > octree_octomap.getOccupancyThres()) {
                            // if we encounter occupied space, then terminate space carving for this ray
                            break;
                        }
                    }
                }
            }

            // make sure that we have found at least one free cell, since we sample within the free space to choose the next camera position
            assert(encountered_free_cell);

            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Updating Octomap..." << std::endl;
            }

            for (auto it : free_cells_octomap) {
                auto occupied  = false;
                auto lazy_eval = true;
                octree_octomap.updateNode(it, occupied, lazy_eval);
            }

            octree_octomap.updateInnerOccupancy();

            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Finding free camera position..." << std::endl;
                free_space_min.raw_print(std::cout, "free_space_min = ");
                free_space_max.raw_print(std::cout, "free_space_max = ");
            }

            bool query_position_valid = false;
            while (!query_position_valid) {

                arma::vec free_space_extent = free_space_max - free_space_min;
                arma::vec query_position     = arma::randu<arma::vec>(3) % free_space_extent + free_space_min;

                auto node_octomap = octree_octomap.search(octomap::point3d(query_position(0), query_position(1), query_position(2)));
                if (node_octomap != nullptr) {
                    if (node_octomap->getOccupancy() <= octree_octomap.getOccupancyThres()) {
                        query_position_valid = true;
                        camera_position = query_position;

                        if (!silent) {
                            camera_position.raw_print(std::cout, "camera_position = ");
                        }
                    }
                }
            }
        }
    }

    //
    // save octomap
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Writing Octomap..." << std::endl;
    }

    free_space_min.save(free_space_min_file, arma::hdf5_binary_trans);
    free_space_max.save(free_space_max_file, arma::hdf5_binary_trans);

    octree_octomap.writeBinary(octomap_file);

    //
    // release Embree data
    //

    rtcReleaseScene(rtc_scene); rtc_scene = nullptr;
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    rtcReleaseDevice(rtc_device); rtc_device = nullptr;
    assert(rtcGetDeviceError(nullptr) == RTC_ERROR_NONE);

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP] Finished." << std::endl;
    }

    return 0;
}
