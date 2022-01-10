//
// For licensing see accompanying LICENSE.txt file.
// Copyright (C) 2020 Apple Inc. All Rights Reserved.
//

#include <cassert>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <args.hxx>

#include <armadillo>

#include <embree3/rtcore.h>
#include <embree3/rtcore_scene.h>
#include <embree3/rtcore_ray.h>

#include <IconsFontAwesome5.h>

#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/imgui/ImGuiMenu.h>
#include <igl/opengl/glfw/imgui/ImGuiHelpers.h>
#include <igl/png/writePNG.h>

#include <imgui/imgui.h>
#include <imgui/imgui_internal.h>



// structs
struct Vertex   { float x, y, z, a; };
struct Triangle { unsigned int v0, v1, v2; };

struct segmentation_state {
    arma::ivec mesh_objects_sii, mesh_objects_si;
    Eigen::MatrixXd C_semantic_instance_colors, C_semantic_colors;
};

std::streambuf* g_suppress_stdout_helper_streambuf = nullptr;
std::ostringstream g_suppress_stdout_helper_ss;
struct suppress_stdout_helper {
    suppress_stdout_helper(bool suppress) {
        if (suppress) {
            g_suppress_stdout_helper_streambuf = std::cout.rdbuf();
            std::cout.rdbuf(g_suppress_stdout_helper_ss.rdbuf());
        } else {
            std::cout.rdbuf(g_suppress_stdout_helper_streambuf);
        }
    }
};

// tool state
void initialize_tool_state();
void initialize_tool_state_deferred();

// top-level functions that correspond to UI actions
void load_scene(std::string scene_dir);
void unload_scene();
void load_segmentation(std::string segmentation_dir, bool can_undo);
void unload_segmentation();
int create_new_semantic_instance_segmentation_id();
void save_segmentation(std::string segmentation_dir);
void undo();
void redo();
void reset_camera_lookat_position();
bool remove_vertices_and_faces(bool prefer_remove_small_vertices, bool prefer_remove_distant_vertices, bool remove_orphaned_vertices);
void reset_vertices_and_faces();

// embree state
void initialize_embree_state();
void terminate_embree_state();

// segmentation state
void initialize_segmentation_state(segmentation_state& segmentation_state);
void initialize_derived_segmentation_state(segmentation_state& segmentation_state);
void update_derived_segmentation_state();
void update_derived_segmentation_state(std::set<int>& selected_mesh_object_ids);
void update_derived_segmentation_state_for_face(int f);

// viewer state
void set_viewer_mesh();
void clear_viewer_mesh();
void set_viewer_mesh_colors();

// TODO: replace with a cleaner solution for open directoy dialog and interaction with the filesystem
std::string open_directory_dialog();
bool filesystem_exists(std::string file);

// string helper functions
void _string_ltrim(std::string &s);
void _string_rtrim(std::string &s);
void _string_trim(std::string &s);
std::string string_ltrim(std::string s);
std::string string_rtrim(std::string s);
std::string string_trim(std::string s);

// callbacks
void draw_custom_window();
bool mouse_down(igl::opengl::glfw::Viewer& viewer, int button, int modifier);
bool mouse_up(igl::opengl::glfw::Viewer& viewer, int button, int modifier);
bool mouse_move(igl::opengl::glfw::Viewer& viewer, int mouse_x, int mouse_y);
bool mouse_scroll(igl::opengl::glfw::Viewer& viewer, float delta);
bool key_down(igl::opengl::glfw::Viewer& viewer, unsigned char key, int modifier);
bool key_up(igl::opengl::glfw::Viewer& viewer, unsigned char key, int modifier);
bool key_pressed(igl::opengl::glfw::Viewer& viewer, unsigned char key, int modifier);
bool pre_draw(igl::opengl::glfw::Viewer& viewer);
bool post_draw(igl::opengl::glfw::Viewer& viewer);

// viewer
suppress_stdout_helper g_suppress_stdout_helper_suppress(true);
igl::opengl::glfw::Viewer g_viewer;
suppress_stdout_helper g_suppress_stdout_helper_restore(false);

// embree state
RTCDevice g_rtc_device = nullptr;
RTCScene g_rtc_scene = nullptr;
RTCIntersectContext g_rtc_intersect_context;

// mesh state
arma::mat g_vertices_orig, g_vertices_curr;
arma::imat g_faces_vi_orig, g_faces_vi_curr;
arma::ivec g_faces_oi_orig, g_faces_oi_curr;
Eigen::MatrixXd g_C_specular;
std::vector<std::string> g_mesh_objects;

// segmentation state
segmentation_state g_segmentation_state_curr, g_segmentation_state_prev;

// command-line state
std::string g_cmd_semantic_descs_csv_file = "semantic_label_descs.csv";
std::string g_cmd_scene_dir               = "";
std::string g_cmd_camera_name             = "";
int         g_cmd_frame_id                = -1;
int         g_cmd_fov_x_degrees           = 120;
int         g_cmd_width_pixels            = 1440;
int         g_cmd_height_pixels           = 985;

// tool state
std::mt19937 g_rng;
std::map<int, std::tuple<std::string, arma::ivec>> g_semantic_instance_descs;
std::map<int, std::tuple<std::string, arma::ivec>> g_semantic_descs;

bool g_mouse_rotation             = false;
bool g_mouse_translation          = false;
bool g_mouse_drawing              = false;
bool g_mouse_drawing_create       = false;
bool g_mouse_drawing_key_modifier = false;

int g_mouse_curr_x         = -1;
int g_mouse_curr_y         = -1;
int g_mouse_prev_x         = -1;
int g_mouse_prev_y         = -1;
int g_mouse_ignore_counter = 0; 

std::vector<arma::ivec> g_mouse_drawing_positions;

enum TOOL { TOOL_PEN, TOOL_LINE, TOOL_RECTANGLE, TOOL_EYEDROPPER };
enum SEGMENTATION_LAYER { SEGMENTATION_LAYER_SEMANTIC_INSTANCE, SEGMENTATION_LAYER_SEMANTIC };
enum PREFER_SELECT_FACES_BY_MODE { PREFER_SELECT_FACES_BY_MODE_OBJECT_MESH_ID, PREFER_SELECT_FACES_BY_MODE_SEMANTIC_INSTANCE_ID, PREFER_SELECT_FACES_BY_MODE_SEMANTIC_ID };

bool        g_scene_loaded          = false;
std::string g_scene_dir             = "";
bool        g_decimate_mesh_on_load = false;

TOOL g_tool                                                    = TOOL_RECTANGLE;
bool g_erase_mode                                              = false;
bool g_assign_unique_semantic_instance_ids_to_each_mesh_object = false;

bool g_can_undo = false;
bool g_can_redo = false;

SEGMENTATION_LAYER          g_segmentation_layer          = SEGMENTATION_LAYER_SEMANTIC;
PREFER_SELECT_FACES_BY_MODE g_prefer_select_faces_by_mode = PREFER_SELECT_FACES_BY_MODE_OBJECT_MESH_ID;

bool g_select_only_null_semantic_instance_id  = false;
bool g_select_only_valid_semantic_instance_id = false;
bool g_select_only_null_semantic_id           = false;
bool g_select_only_valid_semantic_id          = false;

bool g_updated_collapse_state_segmentation = true;

int  g_semantic_instance_counter    = -1;
bool g_updated_semantic_instance_id = false;

int g_semantic_instance_id = -1;
int g_semantic_id          = -1;

float g_navigation_sensitivity = 1.0f; // sensitivity parameter for mouse and keyboard navigation through a scene

// parameters to control mesh decimation
int   g_max_num_vertices               = 15000000;
int   g_max_num_faces                  = 1500000;
int   g_max_num_iters                  = 20;    // since we're selecting triangle faces for removal without replacement, we need to apply an iterative algorithm; give up after g_max_num_iters
float g_face_score_area_half_life      = 1.0f;  // as the area of a triangle grows by g_face_score_area_half_life units, selecting it for removal is half as likely
float g_face_score_distance_half_life  = 50.0f; // as the distance from the camera to a triangle grows by g_face_score_distance_half_life units, selecting it for removal is half as likely
bool  g_prefer_remove_small_vertices   = true;
bool  g_prefer_remove_distant_vertices = false;
bool  g_remove_orphaned_vertices       = true;



int main(int argc, const char** argv) {

    assert(filesystem_exists("fa-solid-900.ttf"));

    //
    // parse input arguments
    //

    args::ArgumentParser parser("scene_annotation_tool", "");

    args::HelpFlag               help                          (parser, "__DUMMY__",                 "Display this help menu",    {'h', "help"});
    args::ValueFlag<std::string> semantic_label_descs_file_arg (parser, "SEMANTIC_LABEL_DESCS_FILE", "semantic_label_descs_file", {"semantic_label_descs_file"});
    args::ValueFlag<std::string> scene_dir_arg                 (parser, "SCENE_DIR",                 "scene_dir",                 {"scene_dir"});
    args::ValueFlag<std::string> camera_name_arg               (parser, "CAMERA_NAME",               "camera_name",               {"camera_name"});
    args::ValueFlag<int>         frame_id_arg                  (parser, "FRAME_ID",                  "frame_id",                  {"frame_id"});
    args::ValueFlag<int>         fov_x_degrees_arg             (parser, "FOV_X_DEGREES",             "fov_x_degrees",             {"fov_x_degrees"});
    args::ValueFlag<int>         width_pixels_arg              (parser, "WIDTH_PIXELS",              "width_pixels",              {"width_pixels"});
    args::ValueFlag<int>         height_pixels_arg             (parser, "HEIGHT_PIXELS",             "height_pixels",             {"height_pixels"});

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

    auto semantic_label_descs_file = args::get(semantic_label_descs_file_arg);
    auto scene_dir                 = args::get(scene_dir_arg);
    auto camera_name               = args::get(camera_name_arg);
    auto frame_id                  = args::get(frame_id_arg);
    auto fov_x_degrees             = args::get(fov_x_degrees_arg);
    auto width_pixels              = args::get(width_pixels_arg);
    auto height_pixels             = args::get(height_pixels_arg);

    if (semantic_label_descs_file != "") {
        g_cmd_semantic_descs_csv_file = semantic_label_descs_file;
    }

    assert(filesystem_exists(g_cmd_semantic_descs_csv_file));

    if (scene_dir != "") {
        g_cmd_scene_dir     = scene_dir;
        g_cmd_camera_name   = camera_name;
        g_cmd_frame_id      = frame_id;

        if (fov_x_degrees > 0) {
            g_cmd_fov_x_degrees = fov_x_degrees;
        }

        if (width_pixels > 0) {
            g_cmd_width_pixels  = width_pixels;
        }

        if (height_pixels > 0) {
            g_cmd_height_pixels = height_pixels;
        }

        assert(g_cmd_camera_name != "");
        assert(g_cmd_frame_id >= 0);
    }

    assert(g_cmd_fov_x_degrees > 0);
    assert(g_cmd_width_pixels > 0);
    assert(g_cmd_height_pixels > 0);

    // global embree data
    assert(RTC_MAX_INSTANCE_LEVEL_COUNT == 1);
    g_rtc_device = rtcNewDevice(nullptr);
    assert(rtcGetDeviceError(nullptr) == RTC_ERROR_NONE);

    // global viewer data
    g_viewer.callback_mouse_down   = &mouse_down;
    g_viewer.callback_mouse_up     = &mouse_up;
    g_viewer.callback_mouse_move   = &mouse_move;
    g_viewer.callback_mouse_scroll = &mouse_scroll;
    g_viewer.callback_key_down     = &key_down;
    g_viewer.callback_key_up       = &key_up;
    g_viewer.callback_key_pressed  = &key_pressed;
    g_viewer.callback_pre_draw     = &pre_draw;
    g_viewer.callback_post_draw    = &post_draw;

    igl::opengl::glfw::imgui::ImGuiMenu menu;
    g_viewer.plugins.push_back(&menu);

    menu.callback_draw_viewer_window = [&]() {};
    menu.callback_draw_viewer_menu   = [&]() {};
    menu.callback_draw_custom_window = &draw_custom_window;

    initialize_tool_state();

    g_viewer.launch(true, false, "Hypersim Scene Annotation Tool", g_cmd_width_pixels, g_cmd_height_pixels);

    if (g_scene_loaded) {
        unload_scene();
    }
}



void initialize_tool_state() {

    g_rtc_scene = nullptr;

    g_rng = std::mt19937(0);
    g_semantic_instance_descs = {};
    g_semantic_instance_counter = 0;
    g_semantic_instance_id = create_new_semantic_instance_segmentation_id();
    g_updated_semantic_instance_id = true;

    //
    // load semantic labels from csv file
    // 
    // NYU40 labels can be obtained here:
    // https://github.com/shelhamer/fcn.berkeleyvision.org/blob/master/data/nyud/classes.txt
    // https://github.com/ScanNet/ScanNet/blob/master/BenchmarkScripts/util.py
    //
    // cityscapes labels can be obtained here:
    // https://github.com/mcordts/cityscapesScripts/blob/master/cityscapesscripts/helpers/labels.py
    //
    
    assert(filesystem_exists(g_cmd_semantic_descs_csv_file));

    std::ifstream fs(g_cmd_semantic_descs_csv_file);
    std::string line;
    std::getline(fs, line); // get csv header
    assert(fs);
    while (std::getline(fs, line)) {
        std::istringstream ss(line);
        std::string token;
        std::getline(ss, token, ','); assert(ss); auto semantic_id      = std::stoi(token);
        std::getline(ss, token, ','); assert(ss); auto semantic_name    = string_trim(token);
        std::getline(ss, token, ','); assert(ss); auto semantic_color_r = std::stoi(token);
        std::getline(ss, token, ','); assert(ss); auto semantic_color_g = std::stoi(token);
        std::getline(ss, token, ','); assert(ss); auto semantic_color_b = std::stoi(token);

        if (semantic_id <= 0) {
            std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] ERROR: SEMANTIC LABEL IDs -1 AND 0 ARE RESERVED FOR INTERNAL USE, AND ARE NOT ALLOWED IN " << g_cmd_semantic_descs_csv_file << "..." << std::endl;
            assert(false);
        }

        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Adding semantic label: " << semantic_id << ", " << semantic_name << ", " << semantic_color_r << ", " << semantic_color_g << ", " << semantic_color_b << std::endl;
        g_semantic_descs.insert({semantic_id, {semantic_name, {semantic_color_r,semantic_color_g,semantic_color_b}}});
    }

    if (g_semantic_descs.size() == 0) {
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] ERROR: " << g_cmd_semantic_descs_csv_file << " MUST CONTAIN AT LEAST ONE ENTRY..." << std::endl;
        assert(false);
    }

    g_semantic_id = 1;

    g_mouse_rotation             = false;
    g_mouse_translation          = false;
    g_mouse_drawing              = false;
    g_mouse_drawing_create       = false;
    g_mouse_drawing_key_modifier = false;

    g_mouse_curr_x         = 0;
    g_mouse_curr_y         = 0;
    g_mouse_prev_x         = 0;
    g_mouse_prev_y         = 0;
    g_mouse_ignore_counter = 0;

    g_mouse_drawing_positions = std::vector<arma::ivec>();

    g_scene_loaded = false;
    g_scene_dir    = "";

    g_tool                                                    = TOOL_RECTANGLE;
    g_erase_mode                                              = false;
    g_assign_unique_semantic_instance_ids_to_each_mesh_object = false;

    g_can_undo = false;
    g_can_redo = false;

    g_segmentation_layer          = SEGMENTATION_LAYER_SEMANTIC;
    g_prefer_select_faces_by_mode = PREFER_SELECT_FACES_BY_MODE_OBJECT_MESH_ID;

    g_select_only_null_semantic_instance_id  = true;
    g_select_only_valid_semantic_instance_id = false;
    g_select_only_null_semantic_id           = true;
    g_select_only_valid_semantic_id          = false;

    g_updated_collapse_state_segmentation = true;

    g_navigation_sensitivity = 1.0f;

    g_max_num_vertices               = 15000000;
    g_max_num_faces                  = 1500000;
    g_face_score_area_half_life      = 1.0f;
    g_face_score_distance_half_life  = 50.0f;
    g_prefer_remove_small_vertices   = true;
    g_prefer_remove_distant_vertices = false;
    g_remove_orphaned_vertices       = true;

    g_viewer.core().camera_view_angle = 60.0;
    g_viewer.core().camera_dnear      = 1.0;
    g_viewer.core().camera_dfar       = 10000.0;

    g_viewer.data().show_lines = false;
}

void initialize_tool_state_deferred() {

    // need to do this ImGui initialization step after the menu viewer plugin is already initialized
    float x_scale, y_scale;
    GLFWwindow* window = glfwGetCurrentContext();
    glfwGetWindowContentScale(window, &x_scale, &y_scale);
    auto hidpi_scaling = 0.5 * (x_scale + y_scale);

    ImGuiIO& io = ImGui::GetIO();
    ImFontConfig config;
    config.MergeMode = true;
    config.GlyphMinAdvanceX = 13.0f; // Use if you want to make the icon monospaced
    static const ImWchar icon_ranges[] = { ICON_MIN_FA, ICON_MAX_FA, 0 };
    io.Fonts->AddFontFromFileTTF(FONT_ICON_FILE_NAME_FAS, 13.0f*hidpi_scaling, &config, icon_ranges);

    ImGui_ImplOpenGL3_DestroyDeviceObjects();
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    // load scene if we're in screenshot mode, need to do this after viewer is initialized or else the mesh doesn't get loaded
    if (g_cmd_scene_dir != "") {
        auto dir = g_cmd_scene_dir + "/_detail/mesh"; // TODO: use portable paths
        assert(filesystem_exists(dir));
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Selected folder appears to be a top-level Hypersim scene folder, attempting to load meshes from " + dir + "/_detail/mesh..." << std::endl;
        load_scene(dir);

        arma::mat camera_positions;
        arma::cube camera_orientations;

        // TODO: use portable paths
        auto camera_positions_file    = g_cmd_scene_dir + "/_detail/" + g_cmd_camera_name + "/camera_keyframe_positions.hdf5";
        auto camera_orientations_file = g_cmd_scene_dir + "/_detail/" + g_cmd_camera_name + "/camera_keyframe_orientations.hdf5";

        camera_positions.load(camera_positions_file, arma::hdf5_binary_trans);
        camera_orientations.load(camera_orientations_file, arma::hdf5_binary_trans);

        arma::vec camera_position    = camera_positions.row(g_cmd_frame_id).t();
        arma::mat camera_orientation = camera_orientations.slice(g_cmd_frame_id);

        arma::vec camera_look_at_dir = -camera_orientation.col(2);
        arma::vec camera_up_dir      = camera_orientation.col(1);
        arma::vec camera_look_at_pos = camera_position + camera_look_at_dir;

        Eigen::Vector3f camera_position_, camera_look_at_pos_, camera_up_dir_;

        camera_position_    << camera_position(0),    camera_position(1),    camera_position(2);
        camera_look_at_pos_ << camera_look_at_pos(0), camera_look_at_pos(1), camera_look_at_pos(2);
        camera_up_dir_      << camera_up_dir(0),      camera_up_dir(1),      camera_up_dir(2);

        g_viewer.core().camera_eye    = camera_position_;
        g_viewer.core().camera_center = camera_look_at_pos_;

        g_viewer.core().view = Eigen::Matrix4f::Identity();
        g_viewer.core().proj = Eigen::Matrix4f::Identity();
        g_viewer.core().norm = Eigen::Matrix4f::Identity();

        igl::look_at( g_viewer.core().camera_eye, g_viewer.core().camera_center, camera_up_dir_, g_viewer.core().view);
        g_viewer.core().norm = g_viewer.core().view.inverse().transpose();

        // HACK: we should use the per-scene projection matrix defined in contrib/mikeroberts3000 because this matrix will be incorrect for some scenes
        auto fov_x = g_cmd_fov_x_degrees*(igl::PI/180.0);
        auto fov_y = 2.0*std::atan(g_cmd_height_pixels * tan(fov_x/2.0) / g_cmd_width_pixels);

        float fH = std::tan(fov_y/2.0) * g_viewer.core().camera_dnear;
        float fW = fH * (double)g_cmd_width_pixels/(double)g_cmd_height_pixels;
        igl::frustum(-fW, fW, -fH, fH, g_viewer.core().camera_dnear, g_viewer.core().camera_dfar, g_viewer.core().proj);

        g_viewer.data().show_lines = true;

        Eigen::Matrix<unsigned char,Eigen::Dynamic,Eigen::Dynamic> R(2*g_cmd_width_pixels,2*g_cmd_height_pixels);
        Eigen::Matrix<unsigned char,Eigen::Dynamic,Eigen::Dynamic> G(2*g_cmd_width_pixels,2*g_cmd_height_pixels);
        Eigen::Matrix<unsigned char,Eigen::Dynamic,Eigen::Dynamic> B(2*g_cmd_width_pixels,2*g_cmd_height_pixels);
        Eigen::Matrix<unsigned char,Eigen::Dynamic,Eigen::Dynamic> A(2*g_cmd_width_pixels,2*g_cmd_height_pixels);
        g_viewer.core().draw_buffer(g_viewer.data(),false,R,G,B,A);

        auto png_file = g_cmd_scene_dir + "/_detail/mesh/screenshot.png";
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Saving screenshot at " << png_file << "..." << std::endl;
        igl::png::writePNG(R,G,B,A,png_file);

        GLFWwindow* window = glfwGetCurrentContext();
        glfwSetWindowShouldClose(window, GL_TRUE);

        g_updated_collapse_state_segmentation = true;
    }
}

void load_scene(std::string scene_dir) {

    if (g_scene_loaded) {
        unload_scene();
    }

    // TODO: use portable paths
    auto vertices_file                           = scene_dir + "/mesh_vertices.hdf5";
    auto faces_vi_file                           = scene_dir + "/mesh_faces_vi.hdf5";
    auto faces_oi_file                           = scene_dir + "/mesh_faces_oi.hdf5";
    auto mesh_objects_file                       = scene_dir + "/metadata_objects.csv";
    auto metadata_scene_annotation_tool_log_file = scene_dir + "/metadata_scene_annotation_tool.log";

    if (!filesystem_exists(vertices_file) || !filesystem_exists(faces_vi_file) || !filesystem_exists(faces_oi_file) || !filesystem_exists(mesh_objects_file)) {
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Can't find mesh files in " + scene_dir + "..." << std::endl;
        return;
    }

    //
    // load input data
    //

    g_vertices_orig.load(vertices_file, arma::hdf5_binary_trans);
    g_faces_vi_orig.load(faces_vi_file, arma::hdf5_binary_trans);
    g_faces_oi_orig.load(faces_oi_file, arma::hdf5_binary_trans);

    assert(g_vertices_orig.n_cols == 3);
    assert(g_faces_vi_orig.n_cols == 3);
    assert(g_faces_vi_orig.n_rows == g_faces_oi_orig.n_elem);

    assert(arma::all(arma::vectorise(g_faces_vi_orig) >= 0));
    assert(arma::all(arma::vectorise(g_faces_vi_orig) < g_vertices_orig.n_rows));

    g_vertices_curr = g_vertices_orig;
    g_faces_vi_curr = g_faces_vi_orig;
    g_faces_oi_curr = g_faces_oi_orig;

    std::ifstream fs(mesh_objects_file);
    std::string line;
    std::getline(fs, line); // get csv header
    assert(fs);
    while (std::getline(fs, line)) {
        g_mesh_objects.push_back(line);
    }

    assert(arma::all(g_faces_oi_orig >= 0));
    assert(arma::all(g_faces_oi_orig < g_mesh_objects.size()));

    // create descs
    g_rng = std::mt19937(0);
    g_semantic_instance_descs = {};
    g_semantic_instance_counter = 0;
    g_semantic_instance_id = create_new_semantic_instance_segmentation_id();
    g_updated_semantic_instance_id = true;

    //
    // initialize Embree state, segmentation state, viewer state
    //

    initialize_segmentation_state(g_segmentation_state_prev);
    initialize_segmentation_state(g_segmentation_state_curr);

    auto initialized_embree_segmentation_viewer_state = false;

    if (g_decimate_mesh_on_load) {
        auto prefer_remove_small_vertices   = true;
        auto prefer_remove_distant_vertices = false;
        auto remove_orphaned_vertices       = true;
        initialized_embree_segmentation_viewer_state = remove_vertices_and_faces(prefer_remove_small_vertices, prefer_remove_distant_vertices, remove_orphaned_vertices);
    }

    if (!initialized_embree_segmentation_viewer_state) {
        initialize_embree_state();

        initialize_derived_segmentation_state(g_segmentation_state_prev);
        initialize_derived_segmentation_state(g_segmentation_state_curr);
        update_derived_segmentation_state();

        clear_viewer_mesh();
        set_viewer_mesh();
        set_viewer_mesh_colors();        
    }

    //
    // roughly fit view to scene extent
    //

    int width_window, height_window;
    glfwGetFramebufferSize(g_viewer.window, &width_window, &height_window);

    // min, max, mean along columns then transpose to column vectors
    arma::vec vertices_min = arma::min(g_vertices_curr, 0).t();
    arma::vec vertices_max = arma::max(g_vertices_curr, 0).t();
    arma::vec vertices_mean = arma::mean(g_vertices_curr, 0).t();
    arma::vec vertices_half_extent = (vertices_max - vertices_min) / 2.0;
    arma::vec vertices_center = vertices_min + vertices_half_extent;
    auto vertices_half_extent_max = arma::max(vertices_half_extent);

    auto k = 0.8; // mesh should occupy this fraction of fov
    auto fov_y = g_viewer.core().camera_view_angle * (igl::PI/180.0);
    auto fov_x = 2.0 * std::atan(width_window * std::tan(fov_y/2) / height_window);
    auto fov   = k*std::min(fov_x, fov_y);
    auto d     = vertices_half_extent_max / std::tan(fov/2.0);

    arma::vec look_at_dir = arma::vec({-1,-1,-1}) / arma::norm(arma::vec({-1,-1,-1}));
    arma::vec eye         = vertices_center - d*look_at_dir;

    // g_viewer.core().camera_center << vertices_center(0), vertices_center(1), vertices_center(2);
    // g_viewer.core().camera_eye << eye(0), eye(1), eye(2);

    // use mean vertex position in case there are lots of low-polygon objects that are far away from the interesting part of the scene
    g_viewer.core().camera_center << vertices_mean(0), vertices_mean(1), vertices_mean(2);
    g_viewer.core().camera_eye << eye(0), eye(1), eye(2);
    g_viewer.core().camera_dfar = 2.0*d;

    //
    // initialize tool state
    //

    g_scene_dir    = scene_dir;
    g_scene_loaded = true;

    g_semantic_id = 1;

    g_tool                                                    = TOOL_RECTANGLE;
    g_erase_mode                                              = false;
    g_assign_unique_semantic_instance_ids_to_each_mesh_object = false;

    g_can_undo = false;
    g_can_redo = false;

    g_segmentation_layer          = SEGMENTATION_LAYER_SEMANTIC;
    g_prefer_select_faces_by_mode = PREFER_SELECT_FACES_BY_MODE_OBJECT_MESH_ID;

    g_select_only_null_semantic_instance_id  = true;
    g_select_only_valid_semantic_instance_id = false;
    g_select_only_null_semantic_id           = true;
    g_select_only_valid_semantic_id          = false;

    // g_navigation_sensitivity = 1.0f;

    // g_max_num_vertices               = 15000000;
    // g_max_num_faces                  = 1500000;
    // g_face_score_area_half_life      = 1.0f;
    // g_face_score_distance_half_life  = 50.0f;
    // g_prefer_remove_small_vertices   = true;
    // g_prefer_remove_distant_vertices = false;
    // g_remove_orphaned_vertices       = true;

    // g_viewer.core().camera_view_angle = 60.0;
    // g_viewer.core().camera_dnear      = 1.0;
    // g_viewer.core().camera_dfar       = 10000.0;

    g_viewer.data().show_lines = false;

    //
    // update log
    //

    std::ofstream ofs;
    std::time_t time = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    ofs.open(metadata_scene_annotation_tool_log_file, std::ios::out | std::ios::app);
    ofs << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Loaded scene:   " << std::ctime(&time);
    ofs.close();

    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Loaded scene from " + scene_dir + "..." << std::endl;
}

void unload_scene() {

    // TODO: use portable paths
    auto metadata_scene_annotation_tool_log_file = g_scene_dir + "/metadata_scene_annotation_tool.log";

    // update log
    std::ofstream ofs;
    std::time_t time = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    ofs.open(metadata_scene_annotation_tool_log_file, std::ios::out | std::ios::app);
    ofs << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Unloaded scene: " << std::ctime(&time);
    ofs.close();

    g_scene_loaded = false;

    g_segmentation_state_curr = segmentation_state();
    g_segmentation_state_prev = segmentation_state();

    g_semantic_instance_descs = {};
    g_semantic_instance_counter = -1;

    clear_viewer_mesh();

    terminate_embree_state();

    g_mesh_objects.clear();

    g_vertices_orig = arma::vec();
    g_faces_vi_orig = arma::imat();
    g_faces_oi_orig = arma::ivec();

    g_vertices_curr = g_vertices_orig;
    g_faces_vi_curr = g_faces_vi_orig;
    g_faces_oi_curr = g_faces_oi_orig;    
}

void load_segmentation(std::string segmentation_dir, bool can_undo) {

    // TODO: use portable paths
    auto mesh_objects_sii_file = segmentation_dir + "/mesh_objects_sii.hdf5";
    auto mesh_objects_si_file  = segmentation_dir + "/mesh_objects_si.hdf5";

    if (!filesystem_exists(mesh_objects_sii_file) || !filesystem_exists(mesh_objects_si_file)) {
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Can't find segmentation files in " + segmentation_dir + "..." << std::endl;
        return;
    }

    // load segmentation data
    arma::ivec tmp_mesh_objects_sii, tmp_mesh_objects_si;
    tmp_mesh_objects_sii.load(mesh_objects_sii_file, arma::hdf5_binary_trans);
    tmp_mesh_objects_si.load(mesh_objects_si_file, arma::hdf5_binary_trans);

    if (tmp_mesh_objects_sii.n_rows != g_mesh_objects.size() || tmp_mesh_objects_si.n_rows != g_mesh_objects.size()) {
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Segmentation data doesn't match loaded scene..." << std::endl;
        return;
    }

    // create descs
    g_rng = std::mt19937(0);
    g_semantic_instance_descs = {};
    g_semantic_instance_counter = 0;
    g_semantic_instance_id = create_new_semantic_instance_segmentation_id();
    g_updated_semantic_instance_id = true;

    auto max_sii = arma::max(tmp_mesh_objects_sii);
    for (int i = 2; i <= max_sii; i++) {
        g_semantic_instance_id = create_new_semantic_instance_segmentation_id();
        g_updated_semantic_instance_id = true;
    }

    // save previous segmentation state
    g_segmentation_state_prev = g_segmentation_state_curr;
    g_can_undo                = can_undo;
    g_can_redo                = false;

    // update current segmentation state
    g_segmentation_state_curr.mesh_objects_sii = tmp_mesh_objects_sii;
    g_segmentation_state_curr.mesh_objects_si = tmp_mesh_objects_si;
    update_derived_segmentation_state();

    // update viewer
    set_viewer_mesh_colors();

    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Loaded segmentation from " + segmentation_dir + "..." << std::endl;
    return;    
}

void unload_segmentation() {

    // create descs
    g_rng = std::mt19937(0);
    g_semantic_instance_descs = {};
    g_semantic_instance_counter = 0;
    g_semantic_instance_id = create_new_semantic_instance_segmentation_id();
    g_updated_semantic_instance_id = true;

    // save previous segmentation state
    g_segmentation_state_prev = g_segmentation_state_curr;
    g_can_undo                = true;
    g_can_redo                = false;

    // update current segmentation state
    initialize_segmentation_state(g_segmentation_state_curr);
    initialize_derived_segmentation_state(g_segmentation_state_curr);

    // update viewer
    set_viewer_mesh_colors();
}

void save_segmentation(std::string segmentation_dir) {

    if (!filesystem_exists(segmentation_dir)) {
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Can't find " + segmentation_dir + "..." << std::endl;
        return;
    }

    // TODO: use portable paths
    auto mesh_objects_sii_file                  = segmentation_dir + "/mesh_objects_sii.hdf5";
    auto mesh_objects_si_file                   = segmentation_dir + "/mesh_objects_si.hdf5";
    auto metadata_semantic_instance_colors_file = segmentation_dir + "/metadata_semantic_instance_colors.hdf5";
    auto metadata_semantic_colors_file          = segmentation_dir + "/metadata_semantic_colors.hdf5";

    arma::imat semantic_instance_colors = arma::ones<arma::imat>(g_semantic_instance_descs.size()+1,3) * -1;
    arma::imat semantic_colors          = arma::ones<arma::imat>(g_semantic_descs.size()+1,3) * -1;

    for (int i = 1; i <= g_semantic_instance_descs.size(); i++) {
        semantic_instance_colors.row(i) = std::get<1>(g_semantic_instance_descs.at(i));
    }

    for (int i = 1; i <= g_semantic_descs.size(); i++) {
        semantic_colors.row(i) = std::get<1>(g_semantic_descs.at(i));
    }

    g_segmentation_state_curr.mesh_objects_sii.save(mesh_objects_sii_file, arma::hdf5_binary_trans);
    g_segmentation_state_curr.mesh_objects_si.save(mesh_objects_si_file, arma::hdf5_binary_trans);
    semantic_instance_colors.save(metadata_semantic_instance_colors_file, arma::hdf5_binary_trans);
    semantic_colors.save(metadata_semantic_colors_file, arma::hdf5_binary_trans);

    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Saved segmentation to " + segmentation_dir + "..." << std::endl;    
}

int create_new_semantic_instance_segmentation_id() {

    g_semantic_instance_counter++;
    std::stringstream ss; ss << "instance_id_" << g_semantic_instance_counter;

    if (g_semantic_instance_descs.size() == 0) {
        float h,r,g,b;
        std::uniform_real_distribution<> uniform_real_distribution(0.0, 1.0);
        h = uniform_real_distribution(g_rng);
        ImGui::ColorConvertHSVtoRGB(h,0.8,1.0,r,g,b);
        g_semantic_instance_descs.insert({g_semantic_instance_counter, {ss.str(), {(int)(r*255),(int)(g*255),(int)(b*255)}}});
    } else {
        auto eps = 45.0*(igl::PI/180.0); // new hue needs to be at least this far from the old hue
        float h,r,g,b,h_prev,s_prev,v_prev;
        arma::ivec rgb_prev = std::get<1>(g_semantic_instance_descs.rbegin()->second);
        ImGui::ColorConvertRGBtoHSV(rgb_prev(0)/255.0f, rgb_prev(1)/255.0f, rgb_prev(2)/255.0f, h_prev, s_prev, v_prev);
        auto close = true;
        while (close) {
            std::uniform_real_distribution<> uniform_real_distribution(0.0, 1.0);
            h           = uniform_real_distribution(g_rng);
            arma::vec a = {std::cos(h*2*igl::PI),      std::sin(h*2*igl::PI)};
            arma::vec b = {std::cos(h_prev*2*igl::PI), std::sin(h_prev*2*igl::PI)};
            auto omega  = std::acos(std::min(std::max(arma::dot(a, b), -1.0), 1.0));
            close       = omega < eps;
        }
        ImGui::ColorConvertHSVtoRGB(h,1.0,0.8,r,g,b);
        g_semantic_instance_descs.insert({g_semantic_instance_counter, {ss.str(), {(int)(r*255),(int)(g*255),(int)(b*255)}}});
    }

    return g_semantic_instance_counter;
}

void undo() {
    segmentation_state tmp    = g_segmentation_state_curr;
    g_segmentation_state_curr = g_segmentation_state_prev;
    g_segmentation_state_prev = tmp;
    g_can_undo                = false;
    g_can_redo                = true;
    set_viewer_mesh_colors();
}

void redo() {
    segmentation_state tmp    = g_segmentation_state_curr;
    g_segmentation_state_curr = g_segmentation_state_prev;
    g_segmentation_state_prev = tmp;
    g_can_undo                = true;
    g_can_redo                = false;
    set_viewer_mesh_colors();
}

void reset_camera_lookat_position() {
    Eigen::Vector3f camera_look_at_dir = (g_viewer.core().camera_center - g_viewer.core().camera_eye) / (g_viewer.core().camera_center - g_viewer.core().camera_eye).norm();
    auto delta = 5.0; // TODO: convert to metric
    g_viewer.core().camera_center = g_viewer.core().camera_eye + delta*camera_look_at_dir;
}

bool remove_vertices_and_faces(bool prefer_remove_small_vertices, bool prefer_remove_distant_vertices, bool remove_orphaned_vertices) {

    assert(g_vertices_orig.n_cols == 3);
    assert(g_faces_vi_orig.n_cols == 3);
    assert(g_faces_vi_orig.n_rows == g_faces_oi_orig.n_elem);

    assert(arma::all(arma::vectorise(g_faces_vi_orig) >= 0));
    assert(arma::all(arma::vectorise(g_faces_vi_orig) < g_vertices_orig.n_rows));

    assert(arma::all(g_faces_oi_orig >= 0));
    assert(arma::all(g_faces_oi_orig < g_mesh_objects.size()));

    int num_vertices, num_faces;

    arma::mat  vertices                      = g_vertices_orig;
    arma::umat faces_vi                      = arma::conv_to<arma::umat>::from(g_faces_vi_orig);
    arma::ivec faces_oi                      = g_faces_oi_orig;
    auto       max_num_faces                 = g_max_num_faces;
    auto       max_num_vertices              = g_max_num_vertices;
    auto       face_score_area_half_life     = g_face_score_area_half_life;
    auto       face_score_distance_half_life = g_face_score_distance_half_life;
    arma::vec  camera_position               = { g_viewer.core().camera_eye(0), g_viewer.core().camera_eye(1), g_viewer.core().camera_eye(2) };

    num_vertices = vertices.n_rows;
    num_faces    = faces_vi.n_rows;

    if (num_vertices <= max_num_vertices && num_faces <= max_num_faces) {
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Vertices and faces are within user-specified budgets, so there is no need to remove mesh data..." << std::endl;
        return false;
    }

    // Compute face areas.
    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Computing face areas and distances..." << std::endl;
    arma::mat faces_v0 = vertices.rows(faces_vi.col(0));
    arma::mat faces_v1 = vertices.rows(faces_vi.col(1));
    arma::mat faces_v2 = vertices.rows(faces_vi.col(2));

    arma::mat face_edges_01 = faces_v1 - faces_v0;
    arma::mat face_edges_02 = faces_v2 - faces_v0;

    arma::vec face_areas = arma::ones<arma::vec>(num_faces) * std::numeric_limits<float>::infinity();
    for (int fi = 0; fi < num_faces; fi++) {
        face_areas(fi) = 0.5*arma::norm(arma::cross(face_edges_01.row(fi), face_edges_02.row(fi)));
    }

    arma::vec face_distances = arma::ones<arma::vec>(num_faces) * std::numeric_limits<float>::infinity();
    arma::vec vertex_distances = arma::ones<arma::vec>(3) * std::numeric_limits<float>::infinity();
    for (int fi = 0; fi < num_faces; fi++) {
        vertex_distances(0) = arma::norm(camera_position - faces_v0.row(fi));
        vertex_distances(1) = arma::norm(camera_position - faces_v1.row(fi));
        vertex_distances(2) = arma::norm(camera_position - faces_v2.row(fi));
        face_distances(fi) = arma::min(vertex_distances);
    }

    arma::vec face_scores_area     = arma::ones<arma::vec>(num_faces);
    arma::vec face_scores_distance = arma::ones<arma::vec>(num_faces);

    // Compute area score as an exponentially decaying function of face area.
    if (prefer_remove_small_vertices) {
        face_scores_area = arma::exp2(-face_areas/face_score_area_half_life);
    }

    // Compute distance score as an exponentially growing function of distance.
    if (prefer_remove_distant_vertices) {
        face_scores_distance = arma::exp2(face_distances/face_score_distance_half_life);
    }

    // Compute final face score as the product of the area score and the distance score.
    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Computing face scores..." << std::endl;
    arma::vec face_scores = face_scores_area % face_scores_distance; // % operator is element-wise multiplication

    //
    // Remove vertices (selected)
    //

    if (num_vertices > max_num_vertices) {

        auto num_vertices_to_remove = num_vertices - max_num_vertices;
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Removing " << num_vertices_to_remove << " vertices..." << std::endl;

        // Construct a list of faces that refer to each vertex. Iterate over the faces,
        // and for each vertex of each face, add the face to a per-vertex list.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Constructing list of faces that refer to each vertex..." << std::endl;
        std::vector<std::vector<int>> vertices_fi_;
        for (int vi = 0; vi < num_vertices; vi++) {
            vertices_fi_.push_back({});
        }
        for (int fi = 0; fi < num_faces; fi++) {
            arma::uvec vi = faces_vi.row(fi).t();
            arma::uvec vi_unique = arma::unique(vi);
            for (int vii = 0; vii < vi_unique.n_elem; vii++) {
                vertices_fi_.at(vi_unique(vii)).push_back(fi);
            }
        }

        // Convert to list of arma::uvec for more convenient indexing.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Converting to list of arma::uvec for more convenient indexing..." << std::endl;    
        std::vector<arma::uvec> vertices_fi;
        for (int vi = 0; vi < num_vertices; vi++) {
            auto fi_ = vertices_fi_.at(vi);
            arma::uvec fi = arma::ones<arma::uvec>(fi_.size());
            for (int fii = 0; fii < fi_.size(); fii++) {
                fi(fii) = fi_.at(fii);
            }
            vertices_fi.push_back(fi);
        }

        // Compute vertex scores. For each vertex, compute the vertex score as the minimum face
        // score among faces that refer to the vertex. This approach favors removing vertices that
        // only belong to faces with high scores, because a single face with a low score will give
        // the vertex a low score.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Computing vertex scores..." << std::endl;    
        arma::vec vertex_scores = arma::zeros<arma::vec>(num_vertices);
        for (int vi = 0; vi < num_vertices; vi++) {
            arma::uvec fi = vertices_fi.at(vi);
            assert(arma::all(fi == arma::sort(fi)));
            assert(arma::all(fi == arma::unique(fi)));
            auto num_faces_vi = fi.n_elem;
            if (num_faces_vi != 0) {
                vertex_scores(vi) = arma::min(face_scores.elem(fi));
            }
        }

        // Select vertices to remove.
        arma::vec selection_scores = vertex_scores;
        auto num_elements_to_select = num_vertices_to_remove;

        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Selecting elements to remove..." << std::endl;
        arma::arma_rng::set_seed(0);
        std::vector<int> selected_elements_;

        for (int i = 0; i < g_max_num_iters; i++) {

            auto num_elements_to_select_curr = num_elements_to_select - selected_elements_.size();

            std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Remaining elements to select: " << num_elements_to_select_curr << std::endl;

            // Since we are choosing without replacement, we need to re-normalize during each iteration.
            arma::vec selection_scores_normalized_cumsum = arma::cumsum(selection_scores) / arma::sum(selection_scores);
            arma::vec sorted_uniform_vals = arma::sort(arma::randu<arma::vec>(num_elements_to_select_curr), "ascend");
            arma::uvec selected_elements_curr = arma::zeros<arma::uvec>(num_elements_to_select_curr);

            int ci = 0;
            for (int ui = 0; ui < num_elements_to_select_curr; ui++) {
                while (selection_scores_normalized_cumsum(ci) <= sorted_uniform_vals(ui)) {
                    ci++;
                }
                selected_elements_curr(ui) = ci;
            }
            arma::uvec selected_elements_curr_unique = arma::unique(selected_elements_curr);
            for (int si = 0; si < selected_elements_curr_unique.n_elem; si++) {
                selected_elements_.push_back(selected_elements_curr_unique(si));
            }

            // Since we are choosing without replacement, we need to modify the vertex scores to not repeatedly select the same vertex.
            selection_scores.elem(selected_elements_curr_unique).zeros();

            if (selected_elements_.size() == num_elements_to_select) {
                break;
            }
        }

        if (selected_elements_.size() < num_elements_to_select) {
            std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Scores are too sharply peaked. Couldn't select enough elements in the maximum number of iterations. Giving up......" << std::endl;
            return false;
        }

        assert(selected_elements_.size() == num_elements_to_select);

        // Convert to arma::uvec for more convenient indexing.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Converting selected elements to arma::uvec for more convenient indexing..." << std::endl;    
        arma::uvec selected_elements = arma::zeros<arma::uvec>(selected_elements_.size());
        for (int si = 0; si < selected_elements_.size(); si++) {
            selected_elements(si) = selected_elements_.at(si);
        }

        std::vector<int> vertices_to_remove_selected_ = selected_elements_;
        arma::uvec vertices_to_remove_selected = selected_elements;

        // Mark all orphaned and selected vertices for removal.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Marking all selected vertices for removal..." << std::endl;    
        arma::uvec vertices_to_keep_mask = arma::ones<arma::uvec>(num_vertices);
        vertices_to_keep_mask.elem(vertices_to_remove_selected).zeros();
        arma::uvec vertices_to_keep = arma::find(vertices_to_keep_mask == 1);
        arma::uvec vertices_to_remove_mask = vertices_to_keep_mask == 0;
        arma::uvec vertices_to_remove = arma::find(vertices_to_remove_mask == 1);

        // Mark all faces for removal that refer to a vertex marked for removal.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Marking all faces for removal that refer to a vertex marked for removal..." << std::endl;    
        arma::uvec faces_to_keep_mask = arma::ones<arma::uvec>(num_faces);
        for (auto vi : vertices_to_remove_selected_) {
            faces_to_keep_mask.elem(vertices_fi.at(vi)).zeros();
        }
        arma::uvec faces_to_keep = arma::find(faces_to_keep_mask == 1);
        arma::uvec faces_to_remove_mask = faces_to_keep_mask == 0;
        arma::uvec faces_to_remove = arma::find(faces_to_remove_mask == 1);

        // Remove vertices and compact the result into a new densely packed array.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Removing " << vertices_to_remove.n_elem << " vertices and compacting the result into a new densely packed array..." << std::endl;    
        arma::mat vertices_compact = vertices.rows(vertices_to_keep);

        // Remove faces and compact the results into a new densely packed array.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Removing " << faces_to_remove.n_elem << " faces and compacting the results into new densely packed arrays..." << std::endl;    
        arma::umat faces_vi_compact = faces_vi.rows(faces_to_keep);
        arma::ivec faces_oi_compact = faces_oi.elem(faces_to_keep);
        arma::vec face_scores_compact = face_scores.elem(faces_to_keep);

        // Adjust faces to account for the newly compacted vertex array.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Adjusting faces to account for the newly compacted vertex array..." << std::endl;
        arma::uvec vertices_to_remove_mask_cumsum = arma::cumsum(vertices_to_remove_mask);
        arma::umat faces_vi_compact_adjusted = arma::reshape(arma::vectorise(faces_vi_compact) - vertices_to_remove_mask_cumsum.elem(arma::vectorise(faces_vi_compact)), faces_vi_compact.n_rows, 3);

        // Set output data
        vertices = vertices_compact;
        faces_vi = faces_vi_compact_adjusted;
        faces_oi = faces_oi_compact;
        face_scores = face_scores_compact;

        num_vertices = vertices.n_rows;
        num_faces = faces_vi.n_rows;
    }

    //
    // Remove faces (selected)
    //

    if (num_faces > max_num_faces) {

        auto num_faces_to_remove = num_faces - max_num_faces;
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Removing " << num_faces_to_remove << " faces..." << std::endl;

        // Select faces to remove.
        arma::vec selection_scores = face_scores;
        auto num_elements_to_select = num_faces_to_remove;

        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Selecting elements to remove..." << std::endl;
        arma::arma_rng::set_seed(0);
        std::vector<int> selected_elements_;

        for (int i = 0; i < g_max_num_iters; i++) {

            auto num_elements_to_select_curr = num_elements_to_select - selected_elements_.size();

            std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Remaining elements to select: " << num_elements_to_select_curr << std::endl;

            // Since we are choosing without replacement, we need to re-normalize during each iteration.
            arma::vec selection_scores_normalized_cumsum = arma::cumsum(selection_scores) / arma::sum(selection_scores);
            arma::vec sorted_uniform_vals = arma::sort(arma::randu<arma::vec>(num_elements_to_select_curr), "ascend");
            arma::uvec selected_elements_curr = arma::zeros<arma::uvec>(num_elements_to_select_curr);

            int ci = 0;
            for (int ui = 0; ui < num_elements_to_select_curr; ui++) {
                while (selection_scores_normalized_cumsum(ci) <= sorted_uniform_vals(ui)) {
                    ci++;
                }
                selected_elements_curr(ui) = ci;
            }
            arma::uvec selected_elements_curr_unique = arma::unique(selected_elements_curr);
            for (int si = 0; si < selected_elements_curr_unique.n_elem; si++) {
                selected_elements_.push_back(selected_elements_curr_unique(si));
            }

            // Since we are choosing without replacement, we need to modify the vertex scores to not repeatedly select the same vertex.
            selection_scores.elem(selected_elements_curr_unique).zeros();

            if (selected_elements_.size() == num_elements_to_select) {
                break;
            }
        }

        if (selected_elements_.size() < num_elements_to_select) {
            std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Scores are too sharply peaked. Couldn't select enough elements in the maximum number of iterations. Giving up..." << std::endl;
            return false;
        }

        assert(selected_elements_.size() == num_elements_to_select);

        // Convert to arma::uvec for more convenient indexing.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Converting selected elements to arma::uvec for more convenient indexing..." << std::endl;    
        arma::uvec selected_elements = arma::zeros<arma::uvec>(selected_elements_.size());
        for (int si = 0; si < selected_elements_.size(); si++) {
            selected_elements(si) = selected_elements_.at(si);
        }

        std::vector<int> faces_to_remove_selected_ = selected_elements_;
        arma::uvec faces_to_remove_selected = selected_elements;

        // Mark all selected faces for removal.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Marking selected faces for removal..." << std::endl;    
        arma::uvec faces_to_keep_mask = arma::ones<arma::uvec>(num_faces);
        faces_to_keep_mask.elem(faces_to_remove_selected).zeros();
        arma::uvec faces_to_keep = arma::find(faces_to_keep_mask == 1);
        arma::uvec faces_to_remove_mask = faces_to_keep_mask == 0;
        arma::uvec faces_to_remove = arma::find(faces_to_remove_mask == 1);

        // Remove faces and compact the results into a new densely packed array.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Removing " << faces_to_remove.n_elem << " faces and compacting the results into new densely packed arrays..." << std::endl;    
        arma::umat faces_vi_compact = faces_vi.rows(faces_to_keep);
        arma::ivec faces_oi_compact = faces_oi.elem(faces_to_keep);
        arma::vec face_scores_compact = face_scores.elem(faces_to_keep);

        // Set output data
        faces_vi = faces_vi_compact;
        faces_oi = faces_oi_compact;
        face_scores = face_scores_compact;

        num_faces = faces_vi.n_rows;
    }

    //
    // Remove vertices (orphaned)
    //

    if (remove_orphaned_vertices) {

        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Removing orphaned vertices..." << std::endl;

        // Construct a list of faces that refer to each vertex. Iterate over the faces,
        // and for each vertex of each face, add the face to a per-vertex list.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Constructing list of faces that refer to each vertex..." << std::endl;
        std::vector<std::vector<int>> vertices_fi_;
        for (int vi = 0; vi < num_vertices; vi++) {
            vertices_fi_.push_back({});
        }
        for (int fi = 0; fi < num_faces; fi++) {
            arma::uvec vi = faces_vi.row(fi).t();
            arma::uvec vi_unique = arma::unique(vi);
            for (int vii = 0; vii < vi_unique.n_elem; vii++) {
                vertices_fi_.at(vi_unique(vii)).push_back(fi);
            }
        }

        // Convert to list of arma::uvec for more convenient indexing.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Converting to list of arma::uvec for more convenient indexing..." << std::endl;    
        std::vector<arma::uvec> vertices_fi;
        for (int vi = 0; vi < num_vertices; vi++) {
            auto fi_ = vertices_fi_.at(vi);
            arma::uvec fi = arma::ones<arma::uvec>(fi_.size());
            for (int fii = 0; fii < fi_.size(); fii++) {
                fi(fii) = fi_.at(fii);
            }
            vertices_fi.push_back(fi);
        }

        // Construct a list of orphaned vertices. An "orphaned" vertex, i.e., a vertex that
        // is not belong to any face, can be removed without further consideration.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Constructing list of orphaned vertices..." << std::endl;    
        std::vector<int> vertices_to_remove_orphaned_;
        for (int vi = 0; vi < num_vertices; vi++) {
            arma::uvec fi = vertices_fi.at(vi);
            assert(arma::all(fi == arma::sort(fi)));
            assert(arma::all(fi == arma::unique(fi)));
            auto num_faces_vi = fi.n_elem;
            if (num_faces_vi == 0) {
                vertices_to_remove_orphaned_.push_back(vi);
            }
        }

        // Convert to arma::uvec for more convenient indexing.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Converting orphaned vertices to arma::uvec for more convenient indexing..." << std::endl;    
        arma::uvec vertices_to_remove_orphaned = arma::zeros<arma::uvec>(vertices_to_remove_orphaned_.size());
        for (int i = 0; i < vertices_to_remove_orphaned_.size(); i++) {
            vertices_to_remove_orphaned(i) = vertices_to_remove_orphaned_.at(i);
        }

        // Mark all orphaned vertices for removal.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Marking all orphaned vertices for removal..." << std::endl;    
        arma::uvec vertices_to_keep_mask = arma::ones<arma::uvec>(num_vertices);
        vertices_to_keep_mask.elem(vertices_to_remove_orphaned).zeros();
        arma::uvec vertices_to_keep = arma::find(vertices_to_keep_mask == 1);
        arma::uvec vertices_to_remove_mask = vertices_to_keep_mask == 0;
        arma::uvec vertices_to_remove = arma::find(vertices_to_remove_mask == 1);

        // Remove vertices and compact the result into a new densely packed array.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Removing " << vertices_to_remove.n_elem << " vertices and compacting the result into a new densely packed array..." << std::endl;    
        arma::mat vertices_compact = vertices.rows(vertices_to_keep);

        // Adjust faces to account for the newly compacted vertex array.
        std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Adjusting faces to account for the newly compacted vertex array..." << std::endl;
        arma::uvec vertices_to_remove_mask_cumsum = arma::cumsum(vertices_to_remove_mask);
        arma::umat faces_vi_adjusted = arma::reshape(arma::vectorise(faces_vi) - vertices_to_remove_mask_cumsum.elem(arma::vectorise(faces_vi)), faces_vi.n_rows, 3);

        // Set output data
        vertices = vertices_compact;
        faces_vi = faces_vi_adjusted;

        num_vertices = vertices.n_rows;
    }

    // Convert to final output format.
    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Converting to final output format..." << std::endl;    
    g_vertices_curr = vertices;
    g_faces_vi_curr = arma::conv_to<arma::imat>::from(faces_vi);
    g_faces_oi_curr = arma::conv_to<arma::ivec>::from(faces_oi);

    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Updating viewer state..." << std::endl;

    initialize_embree_state();

    initialize_derived_segmentation_state(g_segmentation_state_prev);
    initialize_derived_segmentation_state(g_segmentation_state_curr);
    update_derived_segmentation_state();

    clear_viewer_mesh();
    set_viewer_mesh();
    set_viewer_mesh_colors();

    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Finished." << std::endl;

    return true;
}

void reset_vertices_and_faces() {

    // Convert to final output format.
    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Resetting vertices and faces..." << std::endl;    
    g_vertices_curr = g_vertices_orig;
    g_faces_vi_curr = g_faces_vi_orig;
    g_faces_oi_curr = g_faces_oi_orig;

    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Updating viewer state..." << std::endl;

    initialize_embree_state();

    initialize_derived_segmentation_state(g_segmentation_state_prev);
    initialize_derived_segmentation_state(g_segmentation_state_curr);
    update_derived_segmentation_state();

    clear_viewer_mesh();
    set_viewer_mesh();
    set_viewer_mesh_colors();

    std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Finished." << std::endl;    
}

void initialize_embree_state() {

    if (g_rtc_scene != nullptr) {
        terminate_embree_state();
    }

    g_rtc_scene = rtcNewScene(g_rtc_device);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    auto rtc_triangle_mesh = rtcNewGeometry(g_rtc_device, RTC_GEOMETRY_TYPE_TRIANGLE);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    // set vertices
    auto rtc_vertices = (Vertex*) rtcSetNewGeometryBuffer(rtc_triangle_mesh, RTC_BUFFER_TYPE_VERTEX, 0, RTC_FORMAT_FLOAT3, sizeof(Vertex), g_vertices_curr.n_rows);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    for (int i = 0; i < g_vertices_curr.n_rows; i++) {
        rtc_vertices[i].x = g_vertices_curr(i,0);
        rtc_vertices[i].y = g_vertices_curr(i,1);
        rtc_vertices[i].z = g_vertices_curr(i,2);
    }

    // set triangles
    auto rtc_triangles = (Triangle*) rtcSetNewGeometryBuffer(rtc_triangle_mesh, RTC_BUFFER_TYPE_INDEX, 0, RTC_FORMAT_UINT3, sizeof(Triangle), g_faces_vi_curr.n_rows);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    for (int i = 0; i < g_faces_vi_curr.n_rows; i++) {
        rtc_triangles[i].v0 = g_faces_vi_curr(i,0);
        rtc_triangles[i].v1 = g_faces_vi_curr(i,1);
        rtc_triangles[i].v2 = g_faces_vi_curr(i,2);
    }

    rtcCommitGeometry(rtc_triangle_mesh);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    unsigned int geomID = rtcAttachGeometry(g_rtc_scene, rtc_triangle_mesh);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    rtcReleaseGeometry(rtc_triangle_mesh);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    rtcCommitScene(g_rtc_scene);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);

    rtcInitIntersectContext(&g_rtc_intersect_context);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);
}

void terminate_embree_state() {
    rtcReleaseScene(g_rtc_scene);
    assert(rtcGetDeviceError(g_rtc_device) == RTC_ERROR_NONE);
    g_rtc_scene = nullptr;
}

void initialize_segmentation_state(segmentation_state& segmentation_state) {
    segmentation_state.mesh_objects_sii = arma::ones<arma::ivec>(g_mesh_objects.size()) * -1;
    segmentation_state.mesh_objects_si  = arma::ones<arma::ivec>(g_mesh_objects.size()) * -1;
}

void initialize_derived_segmentation_state(segmentation_state& segmentation_state) {
    segmentation_state.C_semantic_instance_colors = Eigen::MatrixXd::Constant(g_vertices_curr.n_rows, 3, 1.0);
    segmentation_state.C_semantic_colors          = Eigen::MatrixXd::Constant(g_vertices_curr.n_rows, 3, 1.0);
}

void update_derived_segmentation_state() {
    for (int f = 0; f < g_faces_vi_curr.n_rows; f++) {
        update_derived_segmentation_state_for_face(f);
    }
}

void update_derived_segmentation_state(std::set<int>& selected_mesh_object_ids) {
    // extract selected faces
    std::set<int> selected_face_ids;
    for (auto m : selected_mesh_object_ids) {
        arma::uvec indices;
        indices = arma::find(g_faces_oi_curr == m);
        for (auto i : indices) {
            selected_face_ids.insert(i);
        }
    }
    // update derived per-face colors
    for (auto f : selected_face_ids) {
        update_derived_segmentation_state_for_face(f);
    }
}

void update_derived_segmentation_state_for_face(int f) {

    arma::vec semantic_color, semantic_instance_color;
    auto semantic_instance_id = g_segmentation_state_curr.mesh_objects_sii(g_faces_oi_curr(f));
    auto semantic_id          = g_segmentation_state_curr.mesh_objects_si(g_faces_oi_curr(f));

    // semantic instance color
    if (semantic_instance_id == -1) {
        if (semantic_id == -1) {
            semantic_instance_color = {1.0, 1.0, 1.0};
        } else {
            semantic_instance_color = {0.3, 0.3, 0.3};
        }
    } else {
        arma::ivec color_       = std::get<1>(g_semantic_instance_descs.at(semantic_instance_id));
        semantic_instance_color = {color_(0) / 255.0, color_(1) / 255.0, color_(2) / 255.0};
    }

    g_segmentation_state_curr.C_semantic_instance_colors.row(g_faces_vi_curr(f,0)) << semantic_instance_color(0), semantic_instance_color(1), semantic_instance_color(2);
    g_segmentation_state_curr.C_semantic_instance_colors.row(g_faces_vi_curr(f,1)) << semantic_instance_color(0), semantic_instance_color(1), semantic_instance_color(2);
    g_segmentation_state_curr.C_semantic_instance_colors.row(g_faces_vi_curr(f,2)) << semantic_instance_color(0), semantic_instance_color(1), semantic_instance_color(2);

    // semantic color
    if (semantic_id == -1) {
        if (semantic_instance_id == -1) {
            semantic_color = {1.0, 1.0, 1.0};
        } else {
            semantic_color = {0.3, 0.3, 0.3};
        }
    } else {
        arma::ivec color_ = std::get<1>(g_semantic_descs.at(semantic_id));
        semantic_color    = {color_(0) / 255.0, color_(1) / 255.0, color_(2) / 255.0};
    }

    g_segmentation_state_curr.C_semantic_colors.row(g_faces_vi_curr(f,0)) << semantic_color(0), semantic_color(1), semantic_color(2);
    g_segmentation_state_curr.C_semantic_colors.row(g_faces_vi_curr(f,1)) << semantic_color(0), semantic_color(1), semantic_color(2);
    g_segmentation_state_curr.C_semantic_colors.row(g_faces_vi_curr(f,2)) << semantic_color(0), semantic_color(1), semantic_color(2);
}

void set_viewer_mesh() {
    g_C_specular = Eigen::MatrixXd::Zero(g_vertices_curr.n_rows, 4);
    for (int i = 0; i < g_vertices_curr.n_rows; i++) {
        g_C_specular.row(i) << 0,0,0,1;
    }

    Eigen::MatrixXd V = Eigen::MatrixXd::Zero(g_vertices_curr.n_rows, 3);
    Eigen::MatrixXi F = Eigen::MatrixXi::Zero(g_faces_vi_curr.n_rows, 3);

    for (int i = 0; i < g_vertices_curr.n_rows; i++) {
        V.row(i) << g_vertices_curr(i,0), g_vertices_curr(i,1), g_vertices_curr(i,2);
    }

    for (int i = 0; i < g_faces_vi_curr.n_rows; i++) {
        F.row(i) << g_faces_vi_curr(i,0), g_faces_vi_curr(i,1), g_faces_vi_curr(i,2);
    }

    g_viewer.data().set_mesh(V, F);
}

void clear_viewer_mesh() {
    auto show_lines = g_viewer.data().show_lines;    
    g_viewer.data().clear();
    g_C_specular = Eigen::MatrixXd::Zero(0, 4);
    g_viewer.data().show_lines = show_lines;
}

void set_viewer_mesh_colors() {
    // update g_viewer.data().V_material_diffuse
    if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {
        g_viewer.data().set_colors(g_segmentation_state_curr.C_semantic_instance_colors);
    }
    if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC) {
        g_viewer.data().set_colors(g_segmentation_state_curr.C_semantic_colors);
    }

    // reset ambient with custom scaling factor
    auto k_ambient = 0.2;
    Eigen::MatrixXd C_ambient = k_ambient*g_viewer.data().V_material_diffuse;
    C_ambient.col(3) = g_viewer.data().V_material_diffuse.col(3);
    g_viewer.data().V_material_ambient = C_ambient;

    // reset diffuse with custom scaling factor
    auto k_diffuse = 0.8;
    Eigen::MatrixXd C_diffuse = k_diffuse*g_viewer.data().V_material_diffuse;
    C_diffuse.col(3) = g_viewer.data().V_material_diffuse.col(3);
    g_viewer.data().V_material_diffuse = C_diffuse;

    // reset specular
    g_viewer.data().V_material_specular = g_C_specular;

    // force update of OpenGL buffers
    g_viewer.data().dirty |= igl::opengl::MeshGL::DIRTY_AMBIENT | igl::opengl::MeshGL::DIRTY_DIFFUSE | igl::opengl::MeshGL::DIRTY_SPECULAR;
}

std::string open_directory_dialog() {

    // HACK: only works on mac
    const int FILE_DIALOG_MAX_BUFFER = 4096;
    char buffer[FILE_DIALOG_MAX_BUFFER];
    FILE * output = popen(
        "osascript -e \""
        "   tell application \\\"System Events\\\"\n"
        "           activate\n"
        "           set existing_folder to choose folder\n"
        "   end tell\n"
        "   set existing_file_path to (POSIX path of (existing_folder))\n"
        "\" 2>/dev/null | tr -d '\n' ","r");

    while (fgets(buffer, FILE_DIALOG_MAX_BUFFER, output) != NULL) {}
    if (!filesystem_exists(buffer)) {
        return "";
    } else {
        return buffer;
    }
}

bool filesystem_exists(std::string file) {
    std::ifstream ifs(file.c_str());
    return ifs.good();
}

void _string_ltrim(std::string &s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](int ch) {
        return !std::isspace(ch);
    }));
}
void _string_rtrim(std::string &s) {
    s.erase(std::find_if(s.rbegin(), s.rend(), [](int ch) {
        return !std::isspace(ch);
    }).base(), s.end());
}
void _string_trim(std::string &s) {
    _string_ltrim(s);
    _string_rtrim(s);
}
std::string string_ltrim(std::string s) {
    _string_ltrim(s);
    return s;
}
std::string string_rtrim(std::string s) {
    _string_rtrim(s);
    return s;
}
std::string string_trim(std::string s) {
    _string_trim(s);
    return s;
}

void draw_custom_window() {

    auto indent_width = 6.0;

    ImGui::SetNextWindowPos(ImVec2(10, 10), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(300, 880), ImGuiCond_FirstUseEver);
    ImGui::Begin("Hypersim Scene Annotation Tool", nullptr, 0);
    ImGui::PushStyleVar(ImGuiStyleVar_IndentSpacing, indent_width);

    auto content_region_available_width = ImGui::GetContentRegionAvailWidth();
    auto button_not_centered_offset = 0.0;

    if (ImGui::Button(ICON_FA_FOLDER_OPEN " Load scene...", ImVec2(content_region_available_width/2.0 - ImGui::GetStyle().ItemSpacing.x/2.0 - button_not_centered_offset, 0.0f))) {
        auto dir = open_directory_dialog();
        g_mouse_ignore_counter = 2; // ignore the next 2 mouse move events because the mouse locations will be buggy
        if (filesystem_exists(dir)) {
            if (filesystem_exists(dir + "/_detail/mesh")) { // TODO: use portable paths
                std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Selected folder appears to be a top-level Hypersim scene folder, attempting to load meshes from " + dir + "/_detail/mesh..." << std::endl;
                dir = dir + "/_detail/mesh"; // TODO: use portable paths
            }
            load_scene(dir);
            g_updated_collapse_state_segmentation = true;
        }
    }

    ImGui::SameLine();

    if (!g_scene_loaded) {
        ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
        ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
    }

    if (ImGui::Button(ICON_FA_FOLDER_OPEN " Load segmentation...", ImVec2(content_region_available_width/2.0 - ImGui::GetStyle().ItemSpacing.x/2.0 + button_not_centered_offset, 0.0f))) {
        auto dir = open_directory_dialog();
        g_mouse_ignore_counter = 2; // ignore the next 2 mouse move events because the mouse locations will be buggy
        if (filesystem_exists(dir)) {
            if (filesystem_exists(dir + "/_detail/mesh")) { // TODO: use portable paths
                std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Selected folder appears to be a top-level Hypersim scene folder, attempting to load segmentation from " + dir + "/_detail/mesh..." << std::endl;
                dir = dir + "/_detail/mesh"; // TODO: use portable paths
            }
            load_segmentation(dir, true); // dir, can undo
        }
    }

    if (ImGui::Button(ICON_FA_SAVE " Save segmentation", ImVec2(content_region_available_width/2.0 - ImGui::GetStyle().ItemSpacing.x/2.0 - button_not_centered_offset, 0.0f))) {
        save_segmentation(g_scene_dir);
    }

    ImGui::SameLine();

    if (ImGui::Button(ICON_FA_SAVE " Save segmentation as...", ImVec2(content_region_available_width/2.0 - ImGui::GetStyle().ItemSpacing.x/2.0 + button_not_centered_offset, 0.0f))) {
        auto dir = open_directory_dialog();
        g_mouse_ignore_counter = 2; // ignore the next 2 mouse move events because the mouse locations will be buggy
        if (filesystem_exists(dir)) {
            if (filesystem_exists(dir + "/_detail/mesh")) { // TODO: use portable paths
                std::cout << "[HYPERSIM: SCENE_ANNOTATION_TOOL] Selected folder appears to be a top-level Hypersim scene folder, attempting to save segmentation to " + dir + "/_detail/mesh..." << std::endl;
                dir = dir + "/_detail/mesh"; // TODO: use portable paths
            }
            save_segmentation(dir);
        }
    }

    if (!g_scene_loaded) {
        ImGui::PopItemFlag();
        ImGui::PopStyleVar();
    }

    ImGui::Checkbox(ICON_FA_TRASH " Decimate mesh immediately after loading", &g_decimate_mesh_on_load);

    ImGui::Separator();

    if (ImGui::BeginTabBar("imgui_tab_bar", ImGuiTabBarFlags_None)) {

        //
        // Segmentation
        //

        if (ImGui::BeginTabItem("Segmentation Editor")) {

            if (!g_scene_loaded) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }

            ImGui::Indent();

            TOOL tool_curr;
            std::string label_curr;
            bool tool_curr_selected;

            tool_curr          = TOOL_PEN;
            label_curr         = ICON_FA_PEN " Pen";
            tool_curr_selected = g_tool == tool_curr;
            if (tool_curr_selected) ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(15.0f/255.0f, 135.0f/255.0f, 250.0f/255.0f, 255.0f/255.0f));
            if (ImGui::Button(label_curr.c_str())) g_tool = tool_curr; ImGui::SameLine();
            if (tool_curr_selected) ImGui::PopStyleColor();

            tool_curr          = TOOL_LINE;
            label_curr         = ICON_FA_RULER " Line";
            tool_curr_selected = g_tool == tool_curr;
            if (tool_curr_selected) ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(15.0f/255.0f, 135.0f/255.0f, 250.0f/255.0f, 255.0f/255.0f));
            if (ImGui::Button(label_curr.c_str())) g_tool = tool_curr; ImGui::SameLine();
            if (tool_curr_selected) ImGui::PopStyleColor();

            tool_curr          = TOOL_RECTANGLE;
            label_curr         = ICON_FA_RULER_COMBINED " Rectangle";
            tool_curr_selected = g_tool == tool_curr;
            if (tool_curr_selected) ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(15.0f/255.0f, 135.0f/255.0f, 250.0f/255.0f, 255.0f/255.0f));
            if (ImGui::Button(label_curr.c_str())) g_tool = tool_curr; ImGui::SameLine();
            if (tool_curr_selected) ImGui::PopStyleColor();

            tool_curr          = TOOL_EYEDROPPER;
            label_curr         = ICON_FA_EYE_DROPPER " Eyedropper";
            tool_curr_selected = g_tool == tool_curr;
            if (tool_curr_selected) ImGui::PushStyleColor(ImGuiCol_Button, ImVec4(15.0f/255.0f, 135.0f/255.0f, 250.0f/255.0f, 255.0f/255.0f));
            if (ImGui::Button(label_curr.c_str())) g_tool = tool_curr;
            if (tool_curr_selected) ImGui::PopStyleColor();

            auto content_region_available_width                              = ImGui::GetContentRegionAvailWidth();
            auto can_undo                                                    = g_can_undo;
            auto can_redo                                                    = g_can_redo;
            auto can_erase                                                   = g_tool != TOOL_EYEDROPPER;
            auto can_assign_unique_semantic_instance_ids_to_each_mesh_object = g_tool != TOOL_EYEDROPPER && g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE;

            if (g_scene_loaded && !can_erase) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            if (ImGui::Checkbox(ICON_FA_ERASER " Erase", &g_erase_mode)) {
                g_assign_unique_semantic_instance_ids_to_each_mesh_object = false;
            }
            if (g_scene_loaded && !can_erase) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            if (g_scene_loaded && !can_assign_unique_semantic_instance_ids_to_each_mesh_object) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            if (ImGui::Checkbox(ICON_FA_RAINBOW " Assign unique semantic instance IDs", &g_assign_unique_semantic_instance_ids_to_each_mesh_object)) {
                g_erase_mode = false;
            }
            if (g_scene_loaded && !can_assign_unique_semantic_instance_ids_to_each_mesh_object) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            if (g_scene_loaded && !can_undo) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            if (ImGui::Button(ICON_FA_UNDO " Undo", ImVec2((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0), 0.0f))) {
                undo();
            }
            if (g_scene_loaded && !can_undo) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            ImGui::SameLine();

            if (g_scene_loaded && !can_redo) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            if (ImGui::Button(ICON_FA_REDO " Redo", ImVec2((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0), 0.0f))) {
                redo();
            }
            if (g_scene_loaded && !can_redo) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            if (ImGui::Button(ICON_FA_CAMERA " Reset camera look-at position", ImVec2(content_region_available_width - indent_width, 0.0f))) {
                reset_camera_lookat_position();
            }

            if (ImGui::Button(ICON_FA_TRASH " Decimate mesh", ImVec2((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0), 0.0f))) {
                remove_vertices_and_faces(g_prefer_remove_small_vertices, g_prefer_remove_distant_vertices, g_remove_orphaned_vertices);
            }
            ImGui::SameLine();
            if (ImGui::Button(ICON_FA_TRASH_RESTORE " Restore mesh", ImVec2((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0), 0.0f))) {
                reset_vertices_and_faces();
            }

            ImGui::Separator();

            if (ImGui::RadioButton("Edit semantic instance segmentation layer", (int*)&g_segmentation_layer, (int)SEGMENTATION_LAYER_SEMANTIC_INSTANCE)) {
                set_viewer_mesh_colors();
                g_updated_collapse_state_segmentation = true;
            }
            if (ImGui::RadioButton("Edit semantic segmentation layer", (int*)&g_segmentation_layer, (int)SEGMENTATION_LAYER_SEMANTIC)) {
                set_viewer_mesh_colors();
                g_updated_collapse_state_segmentation = true;
            }

            ImGui::Separator();

            auto can_edit_selection_logic = g_tool != TOOL_EYEDROPPER;

            if (!can_edit_selection_logic) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            ImGui::RadioButton("Prefer to select faces by mesh object ID",       (int*)&g_prefer_select_faces_by_mode, PREFER_SELECT_FACES_BY_MODE_OBJECT_MESH_ID);
            ImGui::RadioButton("Prefer to select faces by semantic instance ID", (int*)&g_prefer_select_faces_by_mode, PREFER_SELECT_FACES_BY_MODE_SEMANTIC_INSTANCE_ID);
            ImGui::RadioButton("Prefer to select faces by semantic ID",          (int*)&g_prefer_select_faces_by_mode, PREFER_SELECT_FACES_BY_MODE_SEMANTIC_ID);
            if (!can_edit_selection_logic) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            ImGui::Separator();

            if (!can_edit_selection_logic) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            if (ImGui::Checkbox("Only select faces with no semantic instance ID", &g_select_only_null_semantic_instance_id)) {
                g_select_only_valid_semantic_instance_id = false;
            }
            if (ImGui::Checkbox("Only select faces with valid semantic instance ID", &g_select_only_valid_semantic_instance_id)) {
                g_select_only_null_semantic_instance_id = false;
            }
            if (ImGui::Checkbox("Only select faces with no semantic ID", &g_select_only_null_semantic_id)) {            
                g_select_only_valid_semantic_id = false;
            }
            if (ImGui::Checkbox("Only select faces with valid semantic ID", &g_select_only_valid_semantic_id)) {
                g_select_only_null_semantic_id = false;
            }
            if (!can_edit_selection_logic) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            //
            // Semantic Instance Segmentation IDs
            //

            if (g_updated_collapse_state_segmentation) {
                ImGui::SetNextTreeNodeOpen(g_scene_loaded && g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE);
            }
            if (g_scene_loaded && g_segmentation_layer != SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            if (ImGui::CollapsingHeader("Semantic Instance Segmentation IDs", ImGuiTreeNodeFlags_DefaultOpen)) {

                ImGui::Indent();

                if (ImGui::Button(ICON_FA_PLUS_SQUARE " Create new semantic instance ID", ImVec2(ImGui::GetContentRegionAvailWidth() - indent_width, 0.0f))) {
                    g_semantic_instance_id         = create_new_semantic_instance_segmentation_id();
                    g_updated_semantic_instance_id = true;
                }

                // Create child region so it will have its own scroll bar
                ImGui::BeginChild("imgui_semantic_instance_child", ImVec2(ImGui::GetContentRegionAvailWidth() - indent_width, 100), false, 0);
                ImGui::Columns(2, "imgui_semantic_instance_columns", false);  // count, id, border
                for (auto d : g_semantic_instance_descs) {
                    std::string selectable_name     = "##_selectable_" + std::get<0>(d.second);
                    int         selectable_val      = d.first;
                    bool        selectable_selected = g_semantic_instance_id == d.first;
                    std::string color_button_name   = "##_color_" + std::get<0>(d.second);
                    ImVec4      color_button_color  = ImVec4(std::get<1>(d.second)(0) / 255.0f, std::get<1>(d.second)(1) / 255.0f, std::get<1>(d.second)(2) / 255.0f, 1.0f);
                    std::string text_label          = std::get<0>(d.second);

                    if (ImGui::Selectable(selectable_name.c_str(), selectable_selected)) {
                        g_semantic_instance_id = selectable_val;
                    }
                    ImGui::SameLine();
                    ImGui::ColorButton(color_button_name.c_str(), color_button_color, ImGuiColorEditFlags_NoAlpha | ImGuiColorEditFlags_NoPicker | ImGuiColorEditFlags_NoTooltip, ImVec2(12,12));
                    ImGui::SameLine();
                    ImGui::TextUnformatted(text_label.c_str());
                    ImGui::NextColumn();
                    if (g_updated_semantic_instance_id && selectable_val == g_semantic_instance_id) {
                        ImGui::SetScrollHereY();
                        g_updated_semantic_instance_id = false;
                    }
                }
                ImGui::Columns(1);
                ImGui::EndChild();

                ImGui::Unindent();
            }
            if (g_scene_loaded && g_segmentation_layer != SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            //
            // Semantic Segmentation IDs
            //

            if (g_updated_collapse_state_segmentation) {
                ImGui::SetNextTreeNodeOpen(g_scene_loaded && g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC);
            }
            if (g_scene_loaded && g_segmentation_layer != SEGMENTATION_LAYER_SEMANTIC) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            if (ImGui::CollapsingHeader("Semantic Segmentation IDs", ImGuiTreeNodeFlags_DefaultOpen)) {

                ImGui::Indent();

                // Create child region to match Semantic Instance IDs region above (338 is the height in pixels required by all the NYU40 labels)
                ImGui::BeginChild("imgui_semantic_child", ImVec2(ImGui::GetContentRegionAvailWidth() - indent_width, 338), false, 0);
                ImGui::Columns(2, "imgui_semantic_columns", false);  // count, id, border
                for (auto d : g_semantic_descs) {
                    std::string selectable_name     = "##_selectable_" + std::get<0>(d.second);
                    int         selectable_val      = d.first;
                    bool        selectable_selected = g_semantic_id == d.first;
                    std::string color_button_name   = "##_color_" + std::get<0>(d.second);
                    ImVec4      color_button_color  = ImVec4(std::get<1>(d.second)(0) / 255.0f, std::get<1>(d.second)(1) / 255.0f, std::get<1>(d.second)(2) / 255.0f, 1.0f);
                    std::string text_label          = std::get<0>(d.second);

                    if (ImGui::Selectable(selectable_name.c_str(), selectable_selected)) {
                        g_semantic_id = selectable_val;
                    }
                    ImGui::SameLine();
                    ImGui::ColorButton(color_button_name.c_str(), color_button_color, ImGuiColorEditFlags_NoAlpha | ImGuiColorEditFlags_NoPicker | ImGuiColorEditFlags_NoTooltip, ImVec2(12,12));
                    ImGui::SameLine();
                    ImGui::TextUnformatted(text_label.c_str());
                    ImGui::NextColumn();
                }
                ImGui::Columns(1);
                ImGui::EndChild();

                ImGui::Unindent();
            }
            if (g_scene_loaded && g_segmentation_layer != SEGMENTATION_LAYER_SEMANTIC) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            if (g_updated_collapse_state_segmentation) {
                g_updated_collapse_state_segmentation = false;
            }

            ImGui::Unindent();

            if (!g_scene_loaded) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            ImGui::EndTabItem();
        }

        // //
        // // Camera Poses
        // //

        // if (ImGui::BeginTabItem("Camera Pose Editor")) {
        //     ImGui::EndTabItem();
        // }

        //
        // Viewer Options
        //

        if (ImGui::BeginTabItem("Viewer Options")) {

            if (!g_scene_loaded) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }

            ImGui::Indent();

            auto content_region_available_width = ImGui::GetContentRegionAvailWidth();

            ImGui::BeginChild("imgui_viewer_child_camera", ImVec2(ImGui::GetContentRegionAvailWidth() - indent_width, 32), false, 0); // 32 is height required for camera text
            ImGui::Columns(2, "imgui_viewer_columns_camera", false);  // count, id, border

            ImGui::Text("Camera look-from pos."); ImGui::NextColumn(); ImGui::Text("[%0.1f  %0.1f  %0.1f]", g_viewer.core().camera_eye(0),    g_viewer.core().camera_eye(1),    g_viewer.core().camera_eye(2));    ImGui::NextColumn();
            ImGui::Text("Camera look-at pos.");  ImGui::NextColumn(); ImGui::Text("[%0.1f  %0.1f  %0.1f]", g_viewer.core().camera_center(0), g_viewer.core().camera_center(1), g_viewer.core().camera_center(2)); ImGui::NextColumn();

            ImGui::Columns(1);
            ImGui::EndChild();

            if (ImGui::Button(ICON_FA_CAMERA " Reset camera look-at position", ImVec2(content_region_available_width - indent_width, 0.0f))) {
                reset_camera_lookat_position();
            }

            ImGui::PushItemWidth(content_region_available_width-indent_width);
            ImGui::DragFloat("##_sensitivity", &g_navigation_sensitivity, 0.1, 0.1f, 10.0f, "Navigation sensitivity = %.1f");
            ImGui::PopItemWidth();

            ImGui::PushItemWidth((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0));
            ImGui::DragFloat("##_near_plane", &g_viewer.core().camera_dnear, 0.1f,   0.1f,   100.0f,    "Near plane = %.1f");
            ImGui::SameLine();
            ImGui::DragFloat("##_far_plane",  &g_viewer.core().camera_dfar,  100.0f, 100.0f, 100000.0f, "Far plane = %.1f");
            ImGui::PopItemWidth();

            ImGui::Separator();

            ImGui::BeginChild("imgui_viewer_child_mesh", ImVec2(ImGui::GetContentRegionAvailWidth() - indent_width, 64), false, 0); // 64 is height required for mesh text
            ImGui::Columns(4, "imgui_viewer_columns_mesh", false);  // count, id, border

            ImGui::Text("Orig. verts."); ImGui::NextColumn(); ImGui::Text("%d",         (int)g_vertices_orig.n_rows);                        ImGui::NextColumn(); ImGui::Text("Orig. faces");  ImGui::NextColumn(); ImGui::Text("%d",         (int)g_faces_vi_orig.n_rows);                        ImGui::NextColumn();
            ImGui::Text("");             ImGui::NextColumn(); ImGui::Text("(%0.1f MB)", (float)(4*3*g_vertices_orig.n_rows)/(float)1000000); ImGui::NextColumn(); ImGui::Text("");             ImGui::NextColumn(); ImGui::Text("(%0.1f MB)", (float)(4*4*g_faces_vi_orig.n_rows)/(float)1000000); ImGui::NextColumn();
            ImGui::Text("Curr. verts."); ImGui::NextColumn(); ImGui::Text("%d",         (int)g_vertices_curr.n_rows);                        ImGui::NextColumn(); ImGui::Text("Curr. faces");  ImGui::NextColumn(); ImGui::Text("%d",         (int)g_faces_vi_curr.n_rows);                        ImGui::NextColumn();
            ImGui::Text("");             ImGui::NextColumn(); ImGui::Text("(%0.1f MB)", (float)(4*3*g_vertices_curr.n_rows)/(float)1000000); ImGui::NextColumn(); ImGui::Text("");             ImGui::NextColumn(); ImGui::Text("(%0.1f MB)", (float)(4*4*g_faces_vi_curr.n_rows)/(float)1000000); ImGui::NextColumn();

            ImGui::Columns(1);
            ImGui::EndChild();

            if (ImGui::Button(ICON_FA_TRASH " Decimate mesh", ImVec2((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0), 0.0f))) {
                remove_vertices_and_faces(g_prefer_remove_small_vertices, g_prefer_remove_distant_vertices, g_remove_orphaned_vertices);
            }
            ImGui::SameLine();
            if (ImGui::Button(ICON_FA_TRASH_RESTORE " Restore mesh", ImVec2((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0), 0.0f))) {
                reset_vertices_and_faces();
            }

           ImGui::PushItemWidth((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0));
            ImGui::DragInt("##_max_num_vertices", &g_max_num_vertices, 10000, 100000, 100000000, "Max. verts. = %d");
            ImGui::PopItemWidth();

            ImGui::SameLine();

            ImGui::PushItemWidth((content_region_available_width-indent_width)/2.0 - (ImGui::GetStyle().ItemSpacing.x/2.0));
            ImGui::DragInt("##_max_num_faces", &g_max_num_faces, 10000, 100000, 10000000, "Max. faces = %d");
            ImGui::PopItemWidth();

            ImGui::PushItemWidth(content_region_available_width-indent_width);
            ImGui::DragInt("##_max_num_iters", &g_max_num_iters, 1, 1, 100, "Maximum decimation iterations = %d");
            ImGui::PopItemWidth();

            if (g_scene_loaded && !g_prefer_remove_small_vertices) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            ImGui::PushItemWidth(content_region_available_width-indent_width);
            ImGui::DragFloat("##_face_score_area_half_life", &g_face_score_area_half_life, 0.01f, 0.01f, 10.0f, "Half-life with respect to face area = %.2f");
            ImGui::PopItemWidth();
            if (g_scene_loaded && !g_prefer_remove_small_vertices) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            if (g_scene_loaded && !g_prefer_remove_distant_vertices) {
                ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);
                ImGui::PushStyleVar(ImGuiStyleVar_Alpha, ImGui::GetStyle().Alpha * 0.5f);
            }
            ImGui::PushItemWidth(content_region_available_width-indent_width);
            ImGui::DragFloat("##_face_score_distance_half_life", &g_face_score_distance_half_life, 1.0f, 1.0f, 1000.0f, "Half-life with respect to camera distance = %.1f");
            ImGui::PopItemWidth();
            if (g_scene_loaded && !g_prefer_remove_distant_vertices) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            ImGui::Separator();

            ImGui::Checkbox("Prefer to decimate small faces and vertices", &g_prefer_remove_small_vertices);
            ImGui::Checkbox("Prefer to decimate distant faces and vertices", &g_prefer_remove_distant_vertices);
            ImGui::Checkbox("Remove orphaned vertices", &g_remove_orphaned_vertices);

            ImGui::Separator();

            ImGui::Checkbox("Show wireframe overlay", (bool*)(&g_viewer.data().show_lines));

            if (!g_scene_loaded) {
                ImGui::PopItemFlag();
                ImGui::PopStyleVar();
            }

            static bool show_imgui_demo_window = false;
            ImGui::Checkbox("Show ImGui demo window", &show_imgui_demo_window);
            if (show_imgui_demo_window) {
                ImGui::ShowDemoWindow();
            }

            ImGui::Unindent();

            ImGui::EndTabItem();
        }

        ImGui::EndTabBar();
    }

    ImGui::PopStyleVar();
    ImGui::End();

    if (g_scene_loaded) {

        float x_scale, y_scale;
        GLFWwindow* window = glfwGetCurrentContext();
        glfwGetWindowContentScale(window, &x_scale, &y_scale);

        ImU32 color;
        if (g_erase_mode || (g_assign_unique_semantic_instance_ids_to_each_mesh_object && (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE))) {
            ImVec4 color_ = ImVec4(1.0f, 1.0f, 1.0f, 0.5f);
            color = ImColor(color_);
        } else {
            if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {
                auto desc = g_semantic_instance_descs.at(g_semantic_instance_id);
                ImVec4 color_ = ImVec4(std::get<1>(desc)(0) / 255.0f, std::get<1>(desc)(1) / 255.0f, std::get<1>(desc)(2) / 255.0f, 0.5f);
                color = ImColor(color_);
            }
            if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC) {
                auto desc = g_semantic_descs.at(g_semantic_id);
                ImVec4 color_ = ImVec4(std::get<1>(desc)(0) / 255.0f, std::get<1>(desc)(1) / 255.0f, std::get<1>(desc)(2) / 255.0f, 0.5f);
                color = ImColor(color_);
            }
        }

        if (g_tool == TOOL_PEN) {
            if (g_mouse_drawing_positions.size() > 0) {
                for (arma::ivec p : g_mouse_drawing_positions) {
                    ImGui::GetBackgroundDrawList()->AddCircleFilled(ImVec2(p(0)/x_scale, p(1)/y_scale), 2, color, 20); // screen pos, size, color, num_edges
                }
                for (int i = 0; i < g_mouse_drawing_positions.size() - 1; i++) {
                    arma::ivec p0 = g_mouse_drawing_positions.at(i);
                    arma::ivec p1 = g_mouse_drawing_positions.at(i+1);
                    ImGui::GetBackgroundDrawList()->AddLine(ImVec2(p0(0)/x_scale, p0(1)/y_scale), ImVec2(p1(0)/x_scale, p1(1)/y_scale), color, 4); // screen pos 0, screen pos 1, color, width
                }
            }
        }
        if (g_tool == TOOL_LINE) {
            if (g_mouse_drawing_positions.size() > 0) {
                arma::ivec p0 = g_mouse_drawing_positions.front();
                arma::ivec p1 = g_mouse_drawing_positions.back();
                ImGui::GetBackgroundDrawList()->AddCircleFilled(ImVec2(p0(0)/x_scale, p0(1)/y_scale), 2, color, 20); // screen pos, size, color, num_edges
                ImGui::GetBackgroundDrawList()->AddCircleFilled(ImVec2(p1(0)/x_scale, p1(1)/y_scale), 2, color, 20); // screen pos, size, color, num_edges
                ImGui::GetBackgroundDrawList()->AddLine(ImVec2(p0(0)/x_scale, p0(1)/y_scale), ImVec2(p1(0)/x_scale, p1(1)/y_scale), color, 4); // screen pos 0, screen pos 1, color, width
            }
        }
        if (g_tool == TOOL_RECTANGLE) {
            if (g_mouse_drawing_positions.size() > 0) {
                arma::ivec p0 = g_mouse_drawing_positions.front();
                arma::ivec p1 = g_mouse_drawing_positions.back();
                ImDrawCornerFlags corners_none = 0;
                ImGui::GetBackgroundDrawList()->AddRectFilled(ImVec2(p0(0)/x_scale, p0(1)/y_scale), ImVec2(p1(0)/x_scale, p1(1)/y_scale), color, 4, corners_none); // screen pos 0, screen pos 1, color, ?, corner flags
            }
        }
    }
}

bool mouse_down(igl::opengl::glfw::Viewer& viewer, int button, int modifier) {

    auto mouse_button = (igl::opengl::glfw::Viewer::MouseButton)button;

    if (g_scene_loaded) {
        switch (mouse_button) {
            case igl::opengl::glfw::Viewer::MouseButton::Left:
                if (g_mouse_drawing_key_modifier) {
                    g_mouse_rotation       = false;
                    g_mouse_translation    = false;
                    g_mouse_drawing        = true;
                    g_mouse_drawing_create = false;
                } else {
                    g_mouse_rotation       = true;
                    g_mouse_translation    = false;
                    g_mouse_drawing        = false;
                    g_mouse_drawing_create = false;
                }
                break;

            case igl::opengl::glfw::Viewer::MouseButton::Right:
                if (g_mouse_drawing_key_modifier) {
                    g_mouse_rotation       = false;
                    g_mouse_translation    = false;
                    g_mouse_drawing        = false;
                    g_mouse_drawing_create = true;
                } else {
                    g_mouse_rotation       = false;
                    g_mouse_translation    = true;
                    g_mouse_drawing        = false;
                    g_mouse_drawing_create = false;
                }
                break;

            default:
                g_mouse_rotation       = false;
                g_mouse_translation    = false;
                g_mouse_drawing        = false;
                g_mouse_drawing_create = false;
        }
    }

    int width_window, height_window;
    glfwGetFramebufferSize(viewer.window, &width_window, &height_window);

    if (g_mouse_rotation || g_mouse_translation || g_mouse_drawing) {
        g_mouse_prev_x = viewer.current_mouse_x;
        g_mouse_prev_y = viewer.current_mouse_y;
        g_mouse_curr_x = viewer.current_mouse_x;
        g_mouse_curr_y = viewer.current_mouse_y;
    }

    if (g_mouse_drawing) {
        if (viewer.current_mouse_x >= 0 && viewer.current_mouse_x < width_window && viewer.current_mouse_y >= 0 && viewer.current_mouse_y < height_window) {
            g_mouse_drawing_positions.push_back({viewer.current_mouse_x, viewer.current_mouse_y});
        }
    }

    return true;
}

bool mouse_up(igl::opengl::glfw::Viewer& viewer, int button, int modifier) {

    if (g_mouse_drawing_create) {
        if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {
            g_semantic_instance_id = create_new_semantic_instance_segmentation_id();
            g_updated_semantic_instance_id = true;
        }
    }

    if (g_mouse_drawing) {

        if (g_mouse_drawing_positions.size() == 0) {
            g_mouse_rotation       = false;
            g_mouse_translation    = false;
            g_mouse_drawing        = false;
            g_mouse_drawing_create = false;

            return true;
        }

        //
        // raycasting setup
        //

        int width_window, height_window;
        glfwGetFramebufferSize(viewer.window, &width_window, &height_window);

        arma::vec camera_look_from_position = { viewer.core().camera_eye(0),    viewer.core().camera_eye(1),    viewer.core().camera_eye(2) };
        arma::vec camera_look_at_position   = { viewer.core().camera_center(0), viewer.core().camera_center(1), viewer.core().camera_center(2) };
        arma::vec camera_look_at_dir        = arma::normalise(camera_look_at_position - camera_look_from_position);
        arma::vec camera_up_hint            = { 0, 0, 1 };

        // The convention here is that the camera's positive x axis points right, the positive y
        // axis points up, and the positive z axis points away from where the camera is looking.
        arma::vec camera_z_axis = -arma::normalise(camera_look_at_dir);
        arma::vec camera_x_axis = -arma::normalise(arma::cross(camera_z_axis, camera_up_hint));
        arma::vec camera_y_axis = arma::normalise(arma::cross(camera_z_axis, camera_x_axis));

        arma::mat R_world_from_cam = arma::ones<arma::mat>(3,3) * std::numeric_limits<float>::infinity();
        R_world_from_cam.col(0)    = camera_x_axis;
        R_world_from_cam.col(1)    = camera_y_axis;
        R_world_from_cam.col(2)    = camera_z_axis;

        auto fov_y = viewer.core().camera_view_angle * (igl::PI/180.0);
        auto fov_x = 2.0 * std::atan(width_window * std::tan(fov_y/2.0) / height_window);

        auto uv_min  = -1.0;
        auto uv_max  = 1.0;
        auto half_du = 0.5 * (uv_max - uv_min) / width_window;
        auto half_dv = 0.5 * (uv_max - uv_min) / height_window;
        arma::vec u  = arma::linspace(uv_min+half_du, uv_max-half_du, width_window);
        arma::vec v  = arma::reverse(arma::linspace(uv_min+half_dv, uv_max-half_dv, height_window));

        //
        // eyedropper is a special case because it doesn't actually do any drawing
        //

        if (g_tool == TOOL_EYEDROPPER) {

            arma::ivec p = g_mouse_drawing_positions.back();
            auto s_x     = p(0);
            auto s_y     = p(1);
            auto u_      = u(s_x);
            auto v_      = v(s_y);

            arma::vec ray_cam   = { u_*std::tan(fov_x/2.0), v_*std::tan(fov_y/2.0), -1.0 };
            arma::vec ray_world = arma::normalise(R_world_from_cam*ray_cam);

            // initialize ray
            arma::vec ray_position = camera_look_from_position;
            arma::vec ray_direction_normalized = ray_world;

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
            rtcIntersect1(g_rtc_scene, &g_rtc_intersect_context, &rtc_ray_hit);

            if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
            } else {
                assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
            }

            if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                auto face_id = rtc_ray_hit.hit.primID;

                if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {
                    if (g_segmentation_state_curr.mesh_objects_sii(g_faces_oi_curr(face_id)) != -1) {
                        g_semantic_instance_id = g_segmentation_state_curr.mesh_objects_sii(g_faces_oi_curr(face_id));
                        g_updated_semantic_instance_id = true;
                    }
                }
                if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC) {
                    if (g_segmentation_state_curr.mesh_objects_si(g_faces_oi_curr(face_id)) != -1) {
                        g_semantic_id = g_segmentation_state_curr.mesh_objects_si(g_faces_oi_curr(face_id));
                    }
                }
            }
        }

        //
        // for the pen and line tools, approximately rasterize lines by oversampling, rather than implementing an exact rasterization algorithm like DDA
        //

        std::set<std::pair<int,int>> covered_pixels;

        if (g_tool == TOOL_PEN) {

            if (g_mouse_drawing_positions.size() == 1) {
                arma::ivec p = g_mouse_drawing_positions.at(0);
                covered_pixels.insert({p(0), p(1)});
            } else {

                auto k = 4; // number of samples per unit of screen space distance

                for (int i = 0; i < g_mouse_drawing_positions.size() - 1; i++) {
                    arma::ivec p0    = g_mouse_drawing_positions.at(i);
                    arma::ivec p1    = g_mouse_drawing_positions.at(i+1);
                    arma::vec p0_    = arma::conv_to<arma::vec>::from(p0);
                    arma::vec p1_    = arma::conv_to<arma::vec>::from(p1);
                    auto num_samples = (int)(k*arma::norm(p1_ - p0_) + 1);
                    arma::vec x_vals = arma::linspace(p0_(0), p1_(0), num_samples);
                    arma::vec y_vals = arma::linspace(p0_(1), p1_(1), num_samples);

                    for (int j = 0; j < num_samples; j++) {
                        arma::ivec p = {(int)x_vals(j), (int)y_vals(j)};
                        covered_pixels.insert({p(0), p(1)});
                    }
                }
            }
        }

        if (g_tool == TOOL_LINE) {

            if (g_mouse_drawing_positions.size() == 1) {
                arma::ivec p = g_mouse_drawing_positions.at(0);
                covered_pixels.insert({p(0), p(1)});
            } else {

                auto k = 4; // number of samples per unit of screen space distance

                arma::ivec p0    = g_mouse_drawing_positions.front();
                arma::ivec p1    = g_mouse_drawing_positions.back();
                arma::vec p0_    = arma::conv_to<arma::vec>::from(p0);
                arma::vec p1_    = arma::conv_to<arma::vec>::from(p1);
                auto num_samples = (int)(k*arma::norm(p1_ - p0_) + 1);
                arma::vec x_vals = arma::linspace(p0_(0), p1_(0), num_samples);
                arma::vec y_vals = arma::linspace(p0_(1), p1_(1), num_samples);

                for (int j = 0; j < num_samples; j++) {
                    arma::ivec p = {(int)x_vals(j), (int)y_vals(j)};
                    covered_pixels.insert({p(0), p(1)});
                }
            }
        }

        if (g_tool == TOOL_RECTANGLE) {

            if (g_mouse_drawing_positions.size() == 1) {
                arma::ivec p = g_mouse_drawing_positions.at(0);
                covered_pixels.insert({p(0), p(1)});
            } else {
                arma::ivec p0 = g_mouse_drawing_positions.front();
                arma::ivec p1 = g_mouse_drawing_positions.back();
                auto x_min    = std::min(p0(0), p1(0));
                auto y_min    = std::min(p0(1), p1(1));
                auto x_max    = std::max(p0(0), p1(0));
                auto y_max    = std::max(p0(1), p1(1));

                for (int y = y_min; y <= y_max; y++) {
                    for (int x = x_min; x <= x_max; x++) {
                        covered_pixels.insert({x, y});
                    }
                }
            }
        }

        g_mouse_drawing_positions.clear();

        if (g_tool == TOOL_PEN || g_tool == TOOL_LINE || g_tool == TOOL_RECTANGLE) {

            //
            // perform raycasting for each covered pixel
            //

            std::set<int> covered_face_ids;
            for (auto p : covered_pixels) {

                auto s_x   = p.first;
                auto s_y   = p.second;
                auto u_    = u(s_x);
                auto v_    = v(s_y);

                arma::vec ray_cam   = { u_*std::tan(fov_x/2.0), v_*std::tan(fov_y/2.0), -1.0 };
                arma::vec ray_world = arma::normalise(R_world_from_cam*ray_cam);

                // initialize ray
                arma::vec ray_position = camera_look_from_position;
                arma::vec ray_direction_normalized = ray_world;

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
                rtcIntersect1(g_rtc_scene, &g_rtc_intersect_context, &rtc_ray_hit);

                if (rtc_ray_hit.ray.tfar < std::numeric_limits<float>::infinity()) {
                    assert(rtc_ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID);
                } else {
                    assert(rtc_ray_hit.hit.primID == RTC_INVALID_GEOMETRY_ID);
                    assert(rtc_ray_hit.hit.geomID == RTC_INVALID_GEOMETRY_ID);
                }

                if (rtc_ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID) {
                    auto face_id = rtc_ray_hit.hit.primID;
                    covered_face_ids.insert(face_id);
                }
            }

            //
            // perform selection logic for each covered face
            //

            std::set<int> selected_mesh_object_ids;

            for (auto f : covered_face_ids) {

                auto select_face = true;

                if (g_select_only_null_semantic_instance_id && g_segmentation_state_curr.mesh_objects_sii(g_faces_oi_curr(f)) != -1) {
                    select_face = false;
                }
                if (g_select_only_valid_semantic_instance_id && g_segmentation_state_curr.mesh_objects_sii(g_faces_oi_curr(f)) == -1) {
                    select_face = false;
                }
                if (g_select_only_null_semantic_id && g_segmentation_state_curr.mesh_objects_si(g_faces_oi_curr(f)) != -1) {
                    select_face = false;
                }
                if (g_select_only_valid_semantic_id && g_segmentation_state_curr.mesh_objects_si(g_faces_oi_curr(f)) == -1) {
                    select_face = false;
                }

                if (select_face) {
                    if (g_prefer_select_faces_by_mode == PREFER_SELECT_FACES_BY_MODE_OBJECT_MESH_ID) {
                        selected_mesh_object_ids.insert(g_faces_oi_curr(f));
                    }

                    if (g_prefer_select_faces_by_mode == PREFER_SELECT_FACES_BY_MODE_SEMANTIC_INSTANCE_ID) {
                        if (g_segmentation_state_curr.mesh_objects_sii(g_faces_oi_curr(f)) == -1) {
                            selected_mesh_object_ids.insert(g_faces_oi_curr(f));
                        } else {
                            arma::uvec indices = arma::find(g_segmentation_state_curr.mesh_objects_sii == g_segmentation_state_curr.mesh_objects_sii(g_faces_oi_curr(f)));
                            for (auto i : indices) {
                                selected_mesh_object_ids.insert(i);
                            }
                        }
                    }

                    if (g_prefer_select_faces_by_mode == PREFER_SELECT_FACES_BY_MODE_SEMANTIC_ID) {
                        if (g_segmentation_state_curr.mesh_objects_si(g_faces_oi_curr(f)) == -1) {
                            selected_mesh_object_ids.insert(g_faces_oi_curr(f));
                        } else {
                            arma::uvec indices = arma::find(g_segmentation_state_curr.mesh_objects_si == g_segmentation_state_curr.mesh_objects_si(g_faces_oi_curr(f)));
                            for (auto i : indices) {
                                selected_mesh_object_ids.insert(i);
                            }
                        }
                    }
                }
            }

            //
            // save segmentation state
            //

            g_segmentation_state_prev = g_segmentation_state_curr;
            g_can_undo                = true;
            g_can_redo                = false;

            //
            // update segmentation state
            //

            auto updated_segmentation_state = false;
            for (auto m : selected_mesh_object_ids) {
                updated_segmentation_state = true;
                if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {                    
                    int layer_index_val;
                    if (g_erase_mode) {
                        layer_index_val = -1;
                    } else {
                        if (g_assign_unique_semantic_instance_ids_to_each_mesh_object) {
                            g_semantic_instance_id         = create_new_semantic_instance_segmentation_id();
                            g_updated_semantic_instance_id = true;
                        }
                        layer_index_val = g_semantic_instance_id;
                    }
                    g_segmentation_state_curr.mesh_objects_sii(m) = layer_index_val;
                }

                if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC) {
                    int layer_index_val;
                    if (g_erase_mode) {
                        layer_index_val = -1;
                    } else {
                        layer_index_val = g_semantic_id;
                    }
                    g_segmentation_state_curr.mesh_objects_si(m) = layer_index_val;
                }                
            }

            if (updated_segmentation_state) {
                update_derived_segmentation_state(selected_mesh_object_ids);
                set_viewer_mesh_colors();
            }
        }
    }

    g_mouse_rotation       = false;
    g_mouse_translation    = false;
    g_mouse_drawing        = false;
    g_mouse_drawing_create = false;

    return true;
}

bool mouse_move(igl::opengl::glfw::Viewer& viewer, int mouse_x, int mouse_y) {

    int width_window, height_window;
    glfwGetFramebufferSize(viewer.window, &width_window, &height_window);

    if (g_mouse_rotation || g_mouse_translation || g_mouse_drawing) {
        g_mouse_prev_x = g_mouse_curr_x;
        g_mouse_prev_y = g_mouse_curr_y;
        g_mouse_curr_x = mouse_x;
        g_mouse_curr_y = mouse_y;
        if (g_mouse_ignore_counter > 0) {
            g_mouse_ignore_counter--;
        }
    }

    if (g_mouse_prev_x >= 0 && g_mouse_prev_x < width_window && g_mouse_prev_y >= 0 && g_mouse_prev_y < height_window &&
        g_mouse_curr_x >= 0 && g_mouse_curr_x < width_window && g_mouse_curr_y >= 0 && g_mouse_curr_y < height_window &&
        g_mouse_ignore_counter == 0) {

        if (g_mouse_rotation) {

            auto p_x_curr = ((2.0*g_mouse_curr_x) / width_window)  - 1.0;
            auto p_x_prev = ((2.0*g_mouse_prev_x) / width_window)  - 1.0;
            auto p_y_curr = ((2.0*g_mouse_curr_y) / height_window) - 1.0;
            auto p_y_prev = ((2.0*g_mouse_prev_y) / height_window) - 1.0;

            Eigen::Vector3f camera_eye_curr_;
            Eigen::Vector3f camera_rotation_axis_;
            Eigen::Vector3f camera_eye_next_;

            // horizontal rotation
            auto theta_curr  = std::acos(std::min(std::max(p_x_curr,-1.0),1.0));
            auto theta_prev  = std::acos(std::min(std::max(p_x_prev,-1.0),1.0));
            auto theta_delta = theta_curr - theta_prev;

            camera_eye_curr_      = viewer.core().camera_eye - viewer.core().camera_center;
            camera_rotation_axis_ = Eigen::Vector3f::UnitZ();
            camera_eye_next_      = Eigen::AngleAxisf(theta_delta, camera_rotation_axis_).toRotationMatrix()*camera_eye_curr_;
            viewer.core().camera_eye = viewer.core().camera_center + camera_eye_next_;

            // vertical rotation
            camera_eye_curr_ = viewer.core().camera_eye - viewer.core().camera_center;
            Eigen::Vector3f camera_eye_curr_norm = camera_eye_curr_ / camera_eye_curr_.norm();
            auto gamma = std::acos(std::min(std::max(camera_eye_curr_norm.dot(Eigen::Vector3f::UnitZ()),-1.0f),1.0f)); // angle between center-to-eye and up

            auto alpha_curr  = std::acos(std::min(std::max(p_y_curr,-1.0),1.0));
            auto alpha_prev  = std::acos(std::min(std::max(p_y_prev,-1.0),1.0));
            auto alpha_delta = alpha_curr - alpha_prev;

            auto eps = 1.0*(igl::PI/180.0); // maintain minimum angle between center-to-eye and poles
            auto alpha_delta_ = 0.0;

            if (alpha_delta < 0.0) {
                alpha_delta_ = std::min(std::max(alpha_delta, eps-gamma), 0.0); // always keep eye least eps away from north pole, most of the time this term is alpha_delta
            }
            if (alpha_delta > 0.0) {
                alpha_delta_ = std::min(std::max(alpha_delta, 0.0), igl::PI-gamma-eps); // always keep eye at least eps away from south pole, most of the time this term is alpha_delta
            }

            camera_rotation_axis_ = camera_eye_curr_.cross(Eigen::Vector3f::UnitZ()) / camera_eye_curr_.cross(Eigen::Vector3f::UnitZ()).norm();
            camera_eye_next_      = Eigen::AngleAxisf(-alpha_delta_, camera_rotation_axis_).toRotationMatrix()*camera_eye_curr_;
            viewer.core().camera_eye = viewer.core().camera_center + camera_eye_next_;
        }

        if (g_mouse_translation) {

            Eigen::Vector3f camera_look_at_dir;
            Eigen::Vector3f camera_right_dir;
            Eigen::Vector3f camera_up_dir;
            float camera_look_at_dist;

            auto fov_y = viewer.core().camera_view_angle * (igl::PI/180.0);
            auto fov_x = 2.0 * std::atan(width_window * std::tan(fov_y/2.0) / height_window);

            // horizontal translation
            camera_look_at_dir  = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            camera_right_dir    = camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()) / camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()).norm();
            camera_look_at_dist = (viewer.core().camera_center - viewer.core().camera_eye).norm();

            auto mouse_delta_x = g_mouse_curr_x - g_mouse_prev_x;
            auto delta_x       = -(mouse_delta_x / (width_window/2.0))*std::tan(fov_x/2.0)*camera_look_at_dist;
            auto delta_x_      = delta_x;

            viewer.core().camera_eye    = viewer.core().camera_eye    + delta_x_*camera_right_dir;
            viewer.core().camera_center = viewer.core().camera_center + delta_x_*camera_right_dir;

            // vertical translation
            camera_look_at_dir  = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            camera_right_dir    = camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()) / camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()).norm();
            camera_up_dir       = -(camera_look_at_dir.cross(camera_right_dir) / camera_look_at_dir.cross(camera_right_dir).norm());
            camera_look_at_dist = (viewer.core().camera_center - viewer.core().camera_eye).norm();

            auto mouse_delta_y = g_mouse_curr_y - g_mouse_prev_y;
            auto delta_y       = (mouse_delta_y / (height_window/2.0))*std::tan(fov_y/2.0)*camera_look_at_dist;
            auto delta_y_      = delta_y;

            viewer.core().camera_eye    = viewer.core().camera_eye    + delta_y_*camera_up_dir;
            viewer.core().camera_center = viewer.core().camera_center + delta_y_*camera_up_dir;
        }

        if (g_mouse_drawing) {
            if (mouse_x >= 0 && mouse_x < width_window && mouse_y >= 0 && mouse_y < height_window) {
                g_mouse_drawing_positions.push_back({mouse_x, mouse_y});
            }
        }
    }

    return true;
}

bool mouse_scroll(igl::opengl::glfw::Viewer& viewer, float delta) {

    if (!g_mouse_drawing) {
        Eigen::Vector3f camera_look_at_dir = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
        float camera_look_at_dist          = (viewer.core().camera_center - viewer.core().camera_eye).norm();

        // TODO: convert to metric
        auto eps = 10.0f; // maintain minimum distance to camera center
        auto delta_ = 0.0;

        if (delta < 0.0) {
            delta_ = delta*g_navigation_sensitivity;
        }
        if (delta > 0.0) {
            delta_ = std::min(std::max(delta*g_navigation_sensitivity, 0.0f), camera_look_at_dist-eps); // always keep center at least eps away from eye, most of the time this term is delta*g_navigation_sensitivity
        }

        viewer.core().camera_eye = viewer.core().camera_eye + delta_*camera_look_at_dir;
    }

    return true;
}

bool key_down(igl::opengl::glfw::Viewer& viewer, unsigned char key, int modifier) {

    GLFWwindow* window = glfwGetCurrentContext();
    glfwSetWindowShouldClose(window, GL_FALSE);

    if (modifier == 1) { // modifier == SHIFT
        g_mouse_drawing_key_modifier = true;
    }

    switch (key) {
        case 'Z':
        case 'z':
            if (modifier == 8) { // modifier == COMMAND
                if (g_can_undo) {
                    undo();
                }
            }
            if (modifier == 9) { // modifier == COMMAND+SHIFT
                if (g_can_redo) {
                    redo();
                }
            }
            break;

        case ' ':
            if (g_segmentation_layer == SEGMENTATION_LAYER_SEMANTIC_INSTANCE) {
                g_semantic_instance_id         = create_new_semantic_instance_segmentation_id();
                g_updated_semantic_instance_id = true;
            }
            break;
    }

    return true;
}

bool key_up(igl::opengl::glfw::Viewer& viewer, unsigned char key, int modifier) {
    g_mouse_drawing_key_modifier = false;
    return true;
}

bool key_pressed(igl::opengl::glfw::Viewer& viewer, unsigned char key, int modifier) {

    switch(key) {
        case 'W':
        case 'w':
        {
            Eigen::Vector3f camera_look_at_dir = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            float camera_look_at_dist          = (viewer.core().camera_center - viewer.core().camera_eye).norm();

            // TODO: convert to metric
            auto delta  = 5.0f*g_navigation_sensitivity;
            auto eps  = 10.0f;
            auto delta_ = std::min(std::max(eps-camera_look_at_dist+delta, 0.0f), delta); // always keep center at least eps away from eye, most of the time this term is 0

            viewer.core().camera_eye = viewer.core().camera_eye + delta*camera_look_at_dir;
            viewer.core().camera_center = viewer.core().camera_center + delta_*camera_look_at_dir;
            break;
        }

        case 'S':
        case 's':
        {
            Eigen::Vector3f camera_look_at_dir = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            float camera_look_at_dist          = (viewer.core().camera_center - viewer.core().camera_eye).norm();

            // TODO: convert to metric
            auto delta = -5.0*g_navigation_sensitivity;

            viewer.core().camera_eye = viewer.core().camera_eye + delta*camera_look_at_dir;
            break;
        }

        case 'A':
        case 'a':
        {
            Eigen::Vector3f camera_look_at_dir = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            Eigen::Vector3f camera_right_dir   = camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()) / camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()).norm();

            // TODO: convert to metric
            auto delta = -5.0*g_navigation_sensitivity;

            viewer.core().camera_eye    = viewer.core().camera_eye    + delta*camera_right_dir;
            viewer.core().camera_center = viewer.core().camera_center + delta*camera_right_dir;
            break;
        }

        case 'D':
        case 'd':
        {
            Eigen::Vector3f camera_look_at_dir = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            Eigen::Vector3f camera_right_dir   = camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()) / camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()).norm();

            // TODO: convert to metric
            auto delta = 5.0*g_navigation_sensitivity;

            viewer.core().camera_eye    = viewer.core().camera_eye    + delta*camera_right_dir;
            viewer.core().camera_center = viewer.core().camera_center + delta*camera_right_dir;
            break;
        }

        case 'R':
        case 'r':
        {
            Eigen::Vector3f camera_look_at_dir = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            Eigen::Vector3f camera_right_dir   = camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()) / camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()).norm();
            Eigen::Vector3f camera_up_dir      = -(camera_look_at_dir.cross(camera_right_dir) / camera_look_at_dir.cross(camera_right_dir).norm());

            // TODO: convert to metric
            auto delta = 5.0*g_navigation_sensitivity;

            viewer.core().camera_eye    = viewer.core().camera_eye    + delta*camera_up_dir;
            viewer.core().camera_center = viewer.core().camera_center + delta*camera_up_dir;
            break;
        }

        case 'F':
        case 'f':
        {
            Eigen::Vector3f camera_look_at_dir = (viewer.core().camera_center - viewer.core().camera_eye) / (viewer.core().camera_center - viewer.core().camera_eye).norm();
            Eigen::Vector3f camera_right_dir   = camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()) / camera_look_at_dir.cross(Eigen::Vector3f::UnitZ()).norm();
            Eigen::Vector3f camera_up_dir      = -(camera_look_at_dir.cross(camera_right_dir) / camera_look_at_dir.cross(camera_right_dir).norm());

            // TODO: convert to metric
            auto delta = -5.0*g_navigation_sensitivity;

            viewer.core().camera_eye    = viewer.core().camera_eye    + delta*camera_up_dir;
            viewer.core().camera_center = viewer.core().camera_center + delta*camera_up_dir;
            break;
        }
    }

    return true;
}

bool pre_draw(igl::opengl::glfw::Viewer& viewer) {

    static bool once = false;
    if (!once) {
        once = true;
        initialize_tool_state_deferred();
    }

    viewer.core().view = Eigen::Matrix4f::Identity();
    viewer.core().proj = Eigen::Matrix4f::Identity();
    viewer.core().norm = Eigen::Matrix4f::Identity();

    igl::look_at( viewer.core().camera_eye, viewer.core().camera_center, Eigen::Vector3f::UnitZ().eval(), viewer.core().view);
    viewer.core().norm = viewer.core().view.inverse().transpose();

    float width  = viewer.core().viewport(2);
    float height = viewer.core().viewport(3);
    float fH = tan(viewer.core().camera_view_angle / 360.0 * igl::PI) * viewer.core().camera_dnear;
    float fW = fH * (double)width/(double)height;
    igl::frustum(-fW, fW, -fH, fH, viewer.core().camera_dnear, viewer.core().camera_dfar, viewer.core().proj);

    for (auto& core : viewer.core_list) {
        for (auto& mesh : viewer.data_list) {
            if (mesh.is_visible & core.id) {
                core.draw(mesh, false);
            }
        }
    }

    for (auto& core : viewer.core_list) {
        for (auto& mesh : viewer.data_list) {
            mesh.is_visible = false;
        }
    }

    return false;
}

bool post_draw(igl::opengl::glfw::Viewer& viewer) {

    for (auto& core : viewer.core_list) {
        for (auto& mesh : viewer.data_list) {
            mesh.is_visible = true;
        }
    }

    return false;
}
