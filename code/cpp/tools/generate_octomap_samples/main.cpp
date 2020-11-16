//
// For licensing see accompanying LICENSE.txt file.
// Copyright (C) 2020 Apple Inc. All Rights Reserved.
//

#include <cassert>
#include <iostream>
#include <string>

#include <args.hxx>

#include <armadillo>

#include <octomap/octomap.h>
#include <octomap/OcTree.h>



int main (int argc, const char** argv) {

    //
    // parse input arguments
    //

    args::ArgumentParser parser("generate_octomap_samples", "");

    args::HelpFlag               help                     (parser, "__DUMMY__",            "Display this help menu", {'h', "help"});
    args::ValueFlag<std::string> octomap_file_arg         (parser, "OCTOMAP_FILE",         "octomap_file",           {"octomap_file"},         args::Options::Required);
    args::ValueFlag<std::string> query_positions_file_arg (parser, "QUERY_POSITIONS_FILE", "query_positions_file",   {"query_positions_file"}, args::Options::Required);
    args::ValueFlag<std::string> output_file_arg          (parser, "OUTPUT_FILE",          "output_file",            {"output_file"},          args::Options::Required);
    args::Flag                   silent_arg               (parser, "__DUMMY__",            "silent",                 {"silent"});

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

    auto octomap_file         = args::get(octomap_file_arg);
    auto query_positions_file = args::get(query_positions_file_arg);
    auto output_file          = args::get(output_file_arg);
    auto silent               = args::get(silent_arg);

    arma::mat query_positions;

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP_SAMPLES] Begin..." << std::endl;
    }

    //
    // load input data
    //

    octomap::OcTree octree_octomap(octomap_file);
    query_positions.load(query_positions_file, arma::hdf5_binary_trans);

    assert(query_positions.n_cols == 3);

    //
    // perform octomap queries
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP_SAMPLES] Performing Octomap queries..." << std::endl;
    }

    arma::ivec occupancy_samples = arma::ones<arma::ivec>(query_positions.n_rows) * -3;

    for (int i = 0; i < query_positions.n_rows; i++) {
        arma::vec query_position = query_positions.row(i).t();
        if (query_position.is_finite()) {
            auto node_octomap = octree_octomap.search(octomap::point3d(query_positions(i,0), query_positions(i,1), query_positions(i,2)));
            if (node_octomap != nullptr) {
                if (node_octomap->getOccupancy() <= octree_octomap.getOccupancyThres()) {
                    occupancy_samples(i) = 0;
                } else {
                    occupancy_samples(i) = 1;
                }
            } else {
                occupancy_samples(i) = -1;
            }
        } else {
            occupancy_samples(i) = -2;
        }
    }

    //
    // save octomap
    //

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP_SAMPLES] Saving Octomap query results..." << std::endl;
    }

    occupancy_samples.save(output_file, arma::hdf5_binary_trans);

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_OCTOMAP_SAMPLES] Finished." << std::endl;
    }

    return 0;
}
