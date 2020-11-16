//
// For licensing see accompanying LICENSE.txt file.
// Copyright (C) 2020 Apple Inc. All Rights Reserved.
//

#include <cassert>
#include <iostream>
#include <string>

#include <ApproxMVBB/ComputeApproxMVBB.hpp>

#include <args.hxx>

#include <armadillo>



int main (int argc, const char** argv) {

    //
    // parse input arguments
    //

    args::ArgumentParser parser("generate_oriented_bounding_box", "");

    args::HelpFlag               help                                     (parser, "__DUMMY__",                            "Display this help menu",               {'h', "help"});
    args::ValueFlag<std::string> points_file_arg                          (parser, "POINTS_FILE",                          "points_file",                          {"points_file"},                          args::Options::Required);
    args::ValueFlag<double>      n_epsilon_arg                            (parser, "N_EPSILON",                            "n_epsilon",                            {"n_epsilon"},                            args::Options::Required);
    args::ValueFlag<int>         n_point_samples_arg                      (parser, "N_POINT_SAMPLES",                      "n_point_samples",                      {"n_point_samples"},                      args::Options::Required);
    args::ValueFlag<int>         n_grid_size_arg                          (parser, "N_GRID_SIZE",                          "n_grid_size",                          {"n_grid_size"},                          args::Options::Required);
    args::ValueFlag<int>         n_diam_opt_loops_arg                     (parser, "N_DIAM_OPT_LOOPS",                     "n_diam_opt_loops",                     {"n_diam_opt_loops"},                     args::Options::Required);
    args::ValueFlag<int>         n_grid_search_opt_loops_arg              (parser, "N_GRID_SEARCH_OPT_LOOPS",              "n_grid_search_opt_loops",              {"n_grid_search_opt_loops"},              args::Options::Required);
    args::ValueFlag<std::string> output_bounding_box_center_file_arg      (parser, "OUTPUT_BOUNDING_BOX_CENTER_FILE",      "output_bounding_box_center_file",      {"output_bounding_box_center_file"},      args::Options::Required);
    args::ValueFlag<std::string> output_bounding_box_extent_file_arg      (parser, "OUTPUT_BOUNDING_BOX_EXTENT_FILE",      "output_bounding_box_extent_file",      {"output_bounding_box_extent_file"},      args::Options::Required);
    args::ValueFlag<std::string> output_bounding_box_orientation_file_arg (parser, "OUTPUT_BOUNDING_BOX_ORIENTATION_FILE", "output_bounding_box_orientation_file", {"output_bounding_box_orientation_file"}, args::Options::Required);
    args::Flag                   silent_arg                               (parser, "__DUMMY__",                            "silent",                               {"silent"});

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

    auto points_file                          = args::get(points_file_arg);
    auto n_epsilon                            = args::get(n_epsilon_arg);
    auto n_point_samples                      = args::get(n_point_samples_arg);
    auto n_grid_size                          = args::get(n_grid_size_arg);
    auto n_diam_opt_loops                     = args::get(n_diam_opt_loops_arg);
    auto n_grid_search_opt_loops              = args::get(n_grid_search_opt_loops_arg);
    auto output_bounding_box_center_file      = args::get(output_bounding_box_center_file_arg);
    auto output_bounding_box_extent_file      = args::get(output_bounding_box_extent_file_arg);
    auto output_bounding_box_orientation_file = args::get(output_bounding_box_orientation_file_arg);
    auto silent                               = args::get(silent_arg);

    arma::mat points;

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_ORIENTED_BOUNDING_BOXES] Begin..." << std::endl;
    }

    //
    // load input data
    //

    points.load(points_file, arma::hdf5_binary_trans);

    assert(points.n_cols == 2 || points.n_cols == 3);



    //
    // compute bounding box
    //

    arma::vec bounding_box_center_world, bounding_box_extent_world;
    arma::mat bounding_box_R_world_from_obj;

    if (points.n_cols == 2) {

        // Note that ApproxMVBB assumes that each point is a column, which is different to our convention in Hypersim, so we transpose here.
        ApproxMVBB::Matrix2Dyn points_amvbb(2, points.n_rows);
        for (int i = 0; i < points.n_rows; i++) {
            points_amvbb.col(i) << points(i,0), points(i,1);
        }

        // see https://github.com/gabyx/ApproxMVBB for details 
        ApproxMVBB::MinAreaRectangle amvbb_min_area_rectangle(points_amvbb);
        amvbb_min_area_rectangle.compute();
        auto rect = amvbb_min_area_rectangle.getMinRectangle();

        auto rect_center = rect.m_p + 0.5*rect.m_u*rect.m_uL + 0.5*rect.m_v*rect.m_vL;

        arma::vec bounding_box_extent_obj_({rect.m_uL, rect.m_vL});
        arma::mat bounding_box_R_world_from_obj_({
            {rect.m_u(0), rect.m_v(0)},
            {rect.m_u(1), rect.m_v(1)}});

        bounding_box_center_world = {rect_center(0), rect_center(1)};

        // Our convention is as follows: We set the x-axis to be the longest axis. We set the positive direction
        // of the x-axis to be the direction that points roughly towards the center of mass of the points. We set
        // the y-axis to be the positive x-axis rotated by positive 90 degrees.

        arma::vec points_mean_world = arma::mean(points, 0);
        arma::vec points_bbcenter_to_mean = points_mean_world - bounding_box_center_world;

        arma::uvec sorted_axes = sort_index(bounding_box_extent_obj_, "descend");
        arma::vec axis_0 = bounding_box_R_world_from_obj_.col(sorted_axes(0));
        auto axis_0_length = bounding_box_extent_obj_(sorted_axes(0));
        if (arma::dot(axis_0, points_bbcenter_to_mean) < 0) {
            axis_0 = -axis_0;
        }

        arma::mat R({
            {0, -1},
            {1,  0}});
        arma::vec axis_1 = R*axis_0; // positive rotation by 90 degrees
        auto axis_1_length = bounding_box_extent_obj_(sorted_axes(1));

        bounding_box_extent_world = {axis_0_length, axis_1_length};
        bounding_box_R_world_from_obj = {
            {axis_0(0), axis_1(0)},
            {axis_0(1), axis_1(1)}};
    }

    if (points.n_cols == 3) {

        // Note that ApproxMVBB assumes that each point is a column, which is different to our convention in Hypersim, so we transpose here.
        ApproxMVBB::Matrix3Dyn points_amvbb(3, points.n_rows);
        for (int i = 0; i < points.n_rows; i++) {
            points_amvbb.col(i) << points(i,0), points(i,1), points(i,2);
        }

        // suppress overly verbose output
        auto std_cout_rdbuf = std::cout.rdbuf();
        std::ostringstream std_ostringstream;
        if (silent) {
            std::cout.rdbuf(std_ostringstream.rdbuf());
        }

        // see https://github.com/gabyx/ApproxMVBB for details 
        ApproxMVBB::OOBB oobb = ApproxMVBB::approximateMVBB(points_amvbb, n_epsilon, n_point_samples, n_grid_size, n_diam_opt_loops, n_grid_search_opt_loops);

        if (silent) {
            std::cout.rdbuf(std_cout_rdbuf);
        }

        // make all points inside the OOBB, see https://github.com/gabyx/ApproxMVBB for details
        ApproxMVBB::Matrix33 A_KI = oobb.m_q_KI.matrix().transpose();
        for(int i = 0; i < points_amvbb.cols(); i++) {
            oobb.unite(A_KI*points_amvbb.col(i));
        }

        arma::vec bounding_box_center_obj_({oobb.center()(0), oobb.center()(1), oobb.center()(2)});
        arma::vec bounding_box_extent_obj_({oobb.extent()(0), oobb.extent()(1), oobb.extent()(2)});
        arma::mat bounding_box_R_world_from_obj_({
            {oobb.m_q_KI.matrix()(0,0), oobb.m_q_KI.matrix()(0,1), oobb.m_q_KI.matrix()(0,2)},
            {oobb.m_q_KI.matrix()(1,0), oobb.m_q_KI.matrix()(1,1), oobb.m_q_KI.matrix()(1,2)},
            {oobb.m_q_KI.matrix()(2,0), oobb.m_q_KI.matrix()(2,1), oobb.m_q_KI.matrix()(2,2)}});

        bounding_box_center_world = bounding_box_R_world_from_obj_*bounding_box_center_obj_; 

        // Our convention is as follows: We set the x-axis to be the longest axis. We set the positive direction
        // of the x-axis to be the direction that points roughly towards the center of mass of the points. We set
        // the y-axis to be the 2nd longest axis, and we set the positive direction of the y-axis to be the
        // direction that points roughly towards the center of mass of the points. We set the positive z-axis to
        // be x cross y.

        arma::vec points_mean_world = arma::mean(points, 0);
        arma::vec points_bbcenter_to_mean = points_mean_world - bounding_box_center_world;

        arma::uvec sorted_axes = sort_index(bounding_box_extent_obj_, "descend");
        arma::vec axis_0 = bounding_box_R_world_from_obj_.col(sorted_axes(0));
        auto axis_0_length = bounding_box_extent_obj_(sorted_axes(0));
        if (arma::dot(axis_0, points_bbcenter_to_mean) < 0) {
            axis_0 = -axis_0;
        }
        arma::vec axis_1 = bounding_box_R_world_from_obj_.col(sorted_axes(1));
        auto axis_1_length = bounding_box_extent_obj_(sorted_axes(1));
        if (arma::dot(axis_1, points_bbcenter_to_mean) < 0) {
            axis_1 = -axis_1;
        }

        arma::vec axis_2 = arma::cross(axis_0, axis_1);
        auto axis_2_length = bounding_box_extent_obj_(sorted_axes(2));

        bounding_box_extent_world = {axis_0_length, axis_1_length, axis_2_length};
        bounding_box_R_world_from_obj = {
            {axis_0(0), axis_1(0), axis_2(0)},
            {axis_0(1), axis_1(1), axis_2(1)},
            {axis_0(2), axis_1(2), axis_2(2)}};
    }



    //
    // save bounding box
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_ORIENTED_BOUNDING_BOXES] Saving bounding box results..." << std::endl;
    }

    bounding_box_center_world.save(output_bounding_box_center_file, arma::hdf5_binary_trans);
    bounding_box_extent_world.save(output_bounding_box_extent_file, arma::hdf5_binary_trans);
    bounding_box_R_world_from_obj.save(output_bounding_box_orientation_file, arma::hdf5_binary_trans);

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_ORIENTED_BOUNDING_BOXES] Finished." << std::endl;
    }

    return 0;
}
