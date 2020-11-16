//
// For licensing see accompanying LICENSE.txt file.
// Copyright (C) 2020 Apple Inc. All Rights Reserved.
//

#include <assert.h>

#include <iostream>
#include <limits>
#include <string>

#include <args.hxx>

#include <armadillo>

#include <embree3/rtcore.h>
#include <embree3/rtcore_scene.h>
#include <embree3/rtcore_ray.h>



struct Vertex   { float x, y, z, a; };
struct Triangle { unsigned int v0, v1, v2; };



int main (int argc, const char** argv) {

    //
    // parse input arguments
    //

    args::ArgumentParser parser("generate_ray_intersections", "");

    args::HelpFlag               help                               (parser, "__DUMMY__",                      "Display this help menu",         {'h', "help"});
    args::ValueFlag<std::string> vertices_file_arg                  (parser, "VERTICES_FILE",                  "vertices_file",                  {"vertices_file"},                  args::Options::Required);
    args::ValueFlag<std::string> faces_file_arg                     (parser, "FACES_FILE",                     "faces_file",                     {"faces_file"},                     args::Options::Required);
    args::ValueFlag<std::string> ray_positions_file_arg             (parser, "RAY_POSITIONS_FILE",             "ray_positions_file",             {"ray_positions_file"},             args::Options::Required);
    args::ValueFlag<std::string> ray_directions_file_arg            (parser, "RAY_DIRECTIONS_FILE",            "ray_directions_file",            {"ray_directions_file"},            args::Options::Required);
    args::ValueFlag<std::string> output_ray_hit_data_float_file_arg (parser, "OUTPUT_RAY_HIT_DATA_FLOAT_FILE", "output_ray_hit_data_float_file", {"output_ray_hit_data_float_file"}, args::Options::Required);
    args::ValueFlag<std::string> output_ray_hit_data_int_file_arg   (parser, "OUTPUT_RAY_HIT_DATA_INT_FILE",   "output_ray_hit_data_int_file",   {"output_ray_hit_data_int_file"},   args::Options::Required);
    args::Flag                   silent_arg                         (parser, "__DUMMY__",                      "silent",                         {"silent"});

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

    auto vertices_file                  = args::get(vertices_file_arg);
    auto faces_file                     = args::get(faces_file_arg);
    auto ray_positions_file             = args::get(ray_positions_file_arg);
    auto ray_directions_file            = args::get(ray_directions_file_arg);
    auto output_ray_hit_data_float_file = args::get(output_ray_hit_data_float_file_arg);
    auto output_ray_hit_data_int_file   = args::get(output_ray_hit_data_int_file_arg);
    auto silent                         = args::get(silent_arg);

    arma::mat vertices, faces, ray_positions, ray_directions;

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_RAY_INTERSECTIONS] Begin..." << std::endl;
    }

    //
    // load input data
    //

    vertices.load(vertices_file, arma::hdf5_binary_trans);
    faces.load(faces_file, arma::hdf5_binary_trans);
    ray_positions.load(ray_positions_file, arma::hdf5_binary_trans);
    ray_directions.load(ray_directions_file, arma::hdf5_binary_trans);

    assert(vertices.n_cols == 3);
    assert(faces.n_cols == 3);
    assert(ray_positions.n_cols == 3);
    assert(ray_directions.n_cols == 3);
    assert(ray_positions.n_rows == ray_directions.n_rows);

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_RAY_INTERSECTIONS] Tracing " << ray_positions.n_rows << " rays..." << std::endl;
    }

    //
    // construct Embree data
    //

    assert(RTC_MAX_INSTANCE_LEVEL_COUNT == 1);

    auto rtc_device = rtcNewDevice(nullptr);
    assert(rtcGetDeviceError(nullptr) == RTC_ERROR_NONE);

    auto rtc_scene = rtcNewScene(rtc_device);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    auto rtc_triangle_mesh = rtcNewGeometry(rtc_device, RTC_GEOMETRY_TYPE_TRIANGLE);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    // set vertices
    auto rtc_vertices = (Vertex*) rtcSetNewGeometryBuffer(rtc_triangle_mesh, RTC_BUFFER_TYPE_VERTEX, 0, RTC_FORMAT_FLOAT3, sizeof(Vertex), vertices.n_rows);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    for (int i = 0; i < vertices.n_rows; i++) {
        rtc_vertices[i].x = vertices(i,0);
        rtc_vertices[i].y = vertices(i,1);
        rtc_vertices[i].z = vertices(i,2);
    }

    // set triangles
    auto rtc_triangles = (Triangle*) rtcSetNewGeometryBuffer(rtc_triangle_mesh, RTC_BUFFER_TYPE_INDEX, 0, RTC_FORMAT_UINT3, sizeof(Triangle), faces.n_rows);
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    for (int i = 0; i < faces.n_rows; i++) {
        rtc_triangles[i].v0 = faces(i,0);
        rtc_triangles[i].v1 = faces(i,1);
        rtc_triangles[i].v2 = faces(i,2);
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
    // perform raycasting
    //

    arma::mat ray_hit_data_float = arma::ones<arma::mat>(ray_positions.n_rows,4) * std::numeric_limits<float>::infinity();
    arma::imat ray_hit_data_int  = arma::ones<arma::imat>(ray_positions.n_rows,1) * -1;

    for (int i = 0; i < ray_positions.n_rows; i++)  {

        // initialize ray
        arma::vec ray_position             = ray_positions.row(i).t();
        arma::vec ray_direction_normalized = arma::normalise(ray_directions.row(i).t());

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
            arma::vec ray_hit_normal_normalized = arma::normalise(arma::vec({rtc_ray_hit.hit.Ng_x, rtc_ray_hit.hit.Ng_y, rtc_ray_hit.hit.Ng_z}));

            ray_hit_data_float(i, 0) = rtc_ray_hit.ray.tfar;
            ray_hit_data_float(i, 1) = ray_hit_normal_normalized(0);
            ray_hit_data_float(i, 2) = ray_hit_normal_normalized(1);
            ray_hit_data_float(i, 3) = ray_hit_normal_normalized(2);

            ray_hit_data_int(i, 0) = rtc_ray_hit.hit.primID;
        }
    }

    //
    // saving intersection distances
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_RAY_INTERSECTIONS] Saving intersection data..." << std::endl;
    }

    ray_hit_data_float.save(output_ray_hit_data_float_file, arma::hdf5_binary_trans);
    ray_hit_data_int.save(output_ray_hit_data_int_file, arma::hdf5_binary_trans);

    //
    // release Embree data
    //

    rtcReleaseScene(rtc_scene); rtc_scene = nullptr;
    assert(rtcGetDeviceError(rtc_device) == RTC_ERROR_NONE);

    rtcReleaseDevice(rtc_device); rtc_device = nullptr;
    assert(rtcGetDeviceError(nullptr) == RTC_ERROR_NONE);

    return 0;
}
