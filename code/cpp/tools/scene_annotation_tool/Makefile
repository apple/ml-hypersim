include ../../system_config.inc

default:
	mkdir -p ../../bin
	g++ main.cpp \
	-o ../../bin/scene_annotation_tool \
	-std=c++11 -O3 \
	-I$(ARGS_INCLUDE_DIR) \
	-I$(ARMADILLO_INCLUDE_DIR) \
	-I$(EMBREE_INCLUDE_DIR) \
	-I$(HDF5_INCLUDE_DIR) \
	-I$(ICON_FONT_CPP_HEADERS_INCLUDE_DIR) \
	-I$(LIBIGL_INCLUDE_DIR) \
	-I$(LIBIGL_EXTERNAL_DIR) \
	-I$(LIBIGL_EXTERNAL_DIR)/eigen \
	-I$(LIBIGL_EXTERNAL_DIR)/glad/include \
	-I$(LIBIGL_EXTERNAL_DIR)/glfw/include \
	-I$(LIBIGL_EXTERNAL_DIR)/imgui/examples \
	-I$(LIBIGL_EXTERNAL_DIR)/libigl-imgui \
	-I$(LIBIGL_EXTERNAL_DIR)/stb \
	-I$(LIBIGL_LIB_DIR)/stb_image \
	-L$(ARMADILLO_LIB_DIR) -larmadillo \
	-L$(EMBREE_LIB_DIR) -lembree3 \
	-L$(HDF5_LIB_DIR) -lhdf5 \
	-L$(LIBIGL_LIB_DIR) -ligl -ligl_stb_image -limgui -lglad -lglfw3 \
	$(ARMADILLO_EXTRA_CPP_FLAGS) -DARMA_NO_DEBUG \
	$(LIBIGL_EXTRA_CPP_FLAGS)
	cp $(FONT_AWESOME_DIR)/webfonts/fa-solid-900.ttf ../../bin
	cp semantic_label_descs.csv ../../bin
