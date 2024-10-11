//
// For licensing see accompanying LICENSE.txt file.
// Copyright (C) 2020 Apple Inc. All Rights Reserved.
//

#include <algorithm>
#include <cassert>
#include <iostream>
#include <string>

#include <args.hxx>

#include <armadillo>

#include <OpenEXR/half.h>
#include <OpenEXR/IexBaseExc.h>
#include <OpenEXR/ImathBox.h>
#include <OpenEXR/ImathMatrix.h>
#include <OpenEXR/ImathVec.h>
#include <OpenEXR/ImfArray.h>
#include <OpenEXR/ImfAttribute.h>
#include <OpenEXR/ImfChannelList.h>
#include <OpenEXR/ImfCompression.h>
#include <OpenEXR/ImfFrameBuffer.h>
#include <OpenEXR/ImfInputFile.h>
#include <OpenEXR/ImfLineOrder.h>



int main (int argc, const char** argv) {

    //
    // parse input arguments
    //

    args::ArgumentParser parser("generate_hdf5_from_exr", "");

    args::HelpFlag                   help                           (parser, "__DUMMY__",                  "Display this help menu",     {"h", "help"});
    args::ValueFlag<std::string>     input_file_arg                 (parser, "INPUT_FILE",                 "input_file",                 {"input_file"},  args::Options::Required);
    args::ValueFlag<std::string>     output_file_arg                (parser, "OUTPUT_FILE",                "output_file",                {"output_file"}, args::Options::Required);
    args::ValueFlagList<std::string> output_channels_allow_list_arg (parser, "OUTPUT_CHANNELS_ALLOW_LIST", "output_channels_allow_list", {"o", "output_channels_allow_list"});
    args::Flag                       silent_arg                     (parser, "__DUMMY__",                  "silent",                     {"silent"});

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

    auto input_file                 = args::get(input_file_arg);
    auto output_file                = args::get(output_file_arg);
    auto output_channels_allow_list = args::get(output_channels_allow_list_arg);
    auto silent                     = args::get(silent_arg);

    auto use_output_channels_allow_list = !output_channels_allow_list.empty();
    auto output_file_header_csv         = output_file + ".header.csv";
    auto output_file_channels_csv       = output_file + ".channels.csv";

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_HDF5_FROM_EXR] Begin..." << std::endl;
    }

    //
    // load input data
    //

    try {

        Imf::InputFile input_file_exr(input_file.c_str());
        auto header = input_file_exr.header();

        std::ofstream output_file_header_csv_ofstream, output_file_channels_csv_ofstream;

        output_file_header_csv_ofstream.open(output_file_header_csv);
        output_file_header_csv_ofstream.precision(20);
        output_file_header_csv_ofstream.setf(std::ios::fixed);
        output_file_header_csv_ofstream << "header_attribute_name,header_attribute_type,header_attribute_value" << std::endl;

        output_file_channels_csv_ofstream.open(output_file_channels_csv);
        output_file_channels_csv_ofstream.precision(20);
        output_file_channels_csv_ofstream.setf(std::ios::fixed);
        output_file_channels_csv_ofstream << "channel_name,channel_type" << std::endl;

        // print header information
        if (!silent) {
            std::cout << "[HYPERSIM: GENERATE_HDF5_FROM_EXR] Extracting header information..." << std::endl;
        }

        for (auto i = header.begin(); i != header.end(); i++) {

            // C types
            if (i.attribute().typeName() == std::string("float")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<float>*>(&(i.attribute()));
                assert(ti != nullptr);
                output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << ti->value() << std::endl;
            } else if (i.attribute().typeName() == std::string("int")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<int>*>(&(i.attribute()));
                assert(ti != nullptr);
                output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << ti->value() << std::endl;
            // std types
            } else if (i.attribute().typeName() == std::string("string")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<Imf::string>*>(&(i.attribute()));
                assert(ti != nullptr);
                output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << ti->value() << std::endl;

            // Imath types
            } else if (i.attribute().typeName() == std::string("v2f")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<Imath::V2f>*>(&(i.attribute()));
                assert(ti != nullptr);
                auto v = ti->value();
                output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << ",";
                output_file_header_csv_ofstream << v[0] << " " << v[1] << std::endl;
            } else if (i.attribute().typeName() == std::string("m44f")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<Imath::M44f>*>(&(i.attribute()));
                assert(ti != nullptr);
                auto m = ti->value();
                output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << ",";
                output_file_header_csv_ofstream << m[0][0] << " " << m[0][1] << " " << m[0][2] << " " << m[0][3] << " ";
                output_file_header_csv_ofstream << m[1][0] << " " << m[1][1] << " " << m[1][2] << " " << m[1][3] << " ";
                output_file_header_csv_ofstream << m[2][0] << " " << m[2][1] << " " << m[2][2] << " " << m[2][3] << " ";
                output_file_header_csv_ofstream << m[3][0] << " " << m[3][1] << " " << m[3][2] << " " << m[3][3] << std::endl;
            } else if (i.attribute().typeName() == std::string("box2i")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<Imath::Box2i>*>(&(i.attribute()));
                assert(ti != nullptr);
                auto b = ti->value();
                output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << ",";
                output_file_header_csv_ofstream << b.min[0] << " " << b.min[1] << " ";
                output_file_header_csv_ofstream << b.max[0] << " " << b.max[1] << std::endl;

            // Imf types
            } else if (i.attribute().typeName() == std::string("chlist")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<Imf::ChannelList>*>(&(i.attribute()));
                assert(ti != nullptr);
                auto channels = ti->value();
                output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName();
                auto sep = ",";
                for (auto cli = channels.begin(); cli != channels.end(); cli++) {
                    switch (cli.channel().type) {
                        case Imf::UINT:
                            output_file_header_csv_ofstream   << sep << cli.name() << " " << "Imf::UINT";
                            output_file_channels_csv_ofstream <<        cli.name() << "," << "Imf::UINT" << std::endl;
                            sep = " ";
                            break;
                        case Imf::HALF:
                            output_file_header_csv_ofstream   << sep << cli.name() << " " << "Imf::HALF";
                            output_file_channels_csv_ofstream <<        cli.name() << "," << "Imf::HALF" << std::endl;
                            sep = " ";
                            break;
                        case Imf::FLOAT:
                            output_file_header_csv_ofstream   << sep << cli.name() << " " << "Imf::FLOAT";
                            output_file_channels_csv_ofstream <<        cli.name() << "," << "Imf::FLOAT" << std::endl;
                            sep = " ";
                            break;
                        default:
                            assert(false);
                            break;
                    }
                }
                output_file_header_csv_ofstream << std::endl;
            } else if (i.attribute().typeName() == std::string("compression")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<Imf::Compression>*>(&(i.attribute()));
                assert(ti != nullptr);
                switch (ti->value()) {
                    case Imf::NO_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::NO_COMPRESSION" << std::endl;
                        break;
                    case Imf::RLE_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::RLE_COMPRESSION" << std::endl;
                        break;
                    case Imf::ZIPS_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::ZIPS_COMPRESSION" << std::endl;
                        break;
                    case Imf::ZIP_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::ZIP_COMPRESSION" << std::endl;
                        break;
                    case Imf::PIZ_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::PIZ_COMPRESSION" << std::endl;
                        break;
                    case Imf::PXR24_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::PXR24_COMPRESSION" << std::endl;
                        break;
                    case Imf::B44_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::B44_COMPRESSION" << std::endl;
                        break;
                    case Imf::B44A_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::B44A_COMPRESSION" << std::endl;
                        break;
                    case Imf::DWAA_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::DWAA_COMPRESSION" << std::endl;
                        break;
                    case Imf::DWAB_COMPRESSION:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::DWAB_COMPRESSION" << std::endl;
                        break;
                    default:
                        assert(false);
                        break;
                }
            } else if (i.attribute().typeName() == std::string("lineOrder")) {
                auto ti = dynamic_cast<Imf::TypedAttribute<Imf::LineOrder>*>(&(i.attribute()));
                assert(ti != nullptr);
                switch (ti->value()) {
                    case Imf::INCREASING_Y:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::INCREASING_Y" << std::endl;
                        break;
                    case Imf::DECREASING_Y:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::DECREASING_Y" << std::endl;
                        break;
                    case Imf::RANDOM_Y:
                        output_file_header_csv_ofstream << i.name() << "," << i.attribute().typeName() << "," << "Imf::RANDOM_Y" << std::endl;
                        break;
                    default:
                        assert(false);
                        break;
                }

            // unknown type
            } else {
                std::cout << "[HYPERSIM: GENERATE_HDF5_FROM_EXR] WARNING: Couldn't parse header attribute: " << i.name() << " " << i.attribute().typeName() << std::endl;                
            }
        }

        output_file_header_csv_ofstream.close();
        output_file_channels_csv_ofstream.close();

        auto dw = header.dataWindow();
        auto width  = dw.max.x - dw.min.x + 1;
        auto height = dw.max.y - dw.min.y + 1;
        
        auto channels = header.channels();

        for (auto cli = channels.begin(); cli != channels.end(); cli++) {

            if (use_output_channels_allow_list && std::find(output_channels_allow_list.begin(), output_channels_allow_list.end(), std::string(cli.name())) == output_channels_allow_list.end()) {
                if (!silent) {
                    std::cout << "[HYPERSIM: GENERATE_HDF5_FROM_EXR] Skipping channel " << cli.name() << "..." << std::endl;
                }
                continue;
            }

            auto output_channel_file_name = output_file + "." + cli.name() + ".hdf5";
            if (!silent) {
                std::cout << "[HYPERSIM: GENERATE_HDF5_FROM_EXR] Writing output file " << output_channel_file_name << "..." << std::endl;
            }

            switch (cli.channel().type) {
                case Imf::UINT:
                    {
                        Imf::Array2D<unsigned int> pixels;
                        arma::umat pixels_ = arma::ones<arma::umat>(height, width) * 987654321;

                        pixels.resizeErase(height, width);
                        Imf::FrameBuffer frameBuffer;
                        frameBuffer.insert(
                            cli.name(),
                            Imf::Slice(
                                Imf::UINT,                                            // type
                                (char*)(&pixels[0][0] - dw.min.x - dw.min.y * width), // base
                                sizeof(pixels[0][0]) * 1,                             // xStride
                                sizeof(pixels[0][0]) * width,                         // yStride
                                1,                                                    // xSampling
                                1,                                                    // ySampling
                                123456789));                                          // fillValue
                        input_file_exr.setFrameBuffer(frameBuffer);
                        input_file_exr.readPixels(dw.min.y, dw.max.y);

                        for (unsigned int y = 0; y < height; y++)
                            for (unsigned int x = 0; x < width; x++)
                                pixels_(y,x) = pixels[y][x];

                        pixels_.save(output_channel_file_name, arma::hdf5_binary_trans);
                        break;
                    }

                case Imf::HALF:
                    {
                        Imf::Array2D<half> pixels;
                        arma::mat pixels_ = arma::ones<arma::mat>(height, width) * 987654321.0f;

                        pixels.resizeErase(height, width);
                        Imf::FrameBuffer frameBuffer;
                        frameBuffer.insert(
                            cli.name(),
                            Imf::Slice(
                                Imf::HALF,                                            // type
                                (char*)(&pixels[0][0] - dw.min.x - dw.min.y * width), // base
                                sizeof(pixels[0][0]) * 1,                             // xStride
                                sizeof(pixels[0][0]) * width,                         // yStride
                                1,                                                    // xSampling
                                1,                                                    // ySampling
                                123456789.0f));                                       // fillValue
                        input_file_exr.setFrameBuffer(frameBuffer);
                        input_file_exr.readPixels(dw.min.y, dw.max.y);

                        for (unsigned int y = 0; y < height; y++)
                            for (unsigned int x = 0; x < width; x++)
                                pixels_(y,x) = pixels[y][x];

                        pixels_.save(output_channel_file_name, arma::hdf5_binary_trans);
                        break;
                    }

                case Imf::FLOAT:
                    {
                        Imf::Array2D<float> pixels;
                        arma::mat pixels_ = arma::ones<arma::mat>(height, width) * 987654321.0f;

                        pixels.resizeErase(height, width);
                        Imf::FrameBuffer frameBuffer;
                        frameBuffer.insert(
                            cli.name(),
                            Imf::Slice(
                                Imf::FLOAT,                                           // type
                                (char*)(&pixels[0][0] - dw.min.x - dw.min.y * width), // base
                                sizeof(pixels[0][0]) * 1,                             // xStride
                                sizeof(pixels[0][0]) * width,                         // yStride
                                1,                                                    // xSampling
                                1,                                                    // ySampling
                                123456789.0f));                                       // fillValue
                        input_file_exr.setFrameBuffer(frameBuffer);
                        input_file_exr.readPixels(dw.min.y, dw.max.y);

                        for (unsigned int y = 0; y < height; y++)
                            for (unsigned int x = 0; x < width; x++)
                                pixels_(y,x) = pixels[y][x];

                        pixels_.save(output_channel_file_name, arma::hdf5_binary_trans);
                        break;
                    }

                default:
                    assert(false);
                    break;
            }
        }
    } catch(Iex::BaseExc & e) {
        std::cout << e.what() << std::endl;
    }

    if (!silent) {
        std::cout << "[HYPERSIM: GENERATE_HDF5_FROM_EXR] Finished." << std::endl;
    }
}
