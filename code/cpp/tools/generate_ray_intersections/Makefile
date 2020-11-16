include ../../system_config.inc

default:
	mkdir -p ../../bin
	g++ main.cpp \
	-o ../../bin/generate_ray_intersections \
	-std=c++11 -O3 \
	-I$(ARGS_INCLUDE_DIR) \
	-I$(ARMADILLO_INCLUDE_DIR) \
	-I$(EMBREE_INCLUDE_DIR) \
	-I$(HDF5_INCLUDE_DIR) \
	-L$(ARMADILLO_LIB_DIR) -larmadillo \
	-L$(EMBREE_LIB_DIR) -lembree3 \
	-L$(HDF5_LIB_DIR) -lhdf5 \
	$(ARMADILLO_EXTRA_CPP_FLAGS) -DARMA_NO_DEBUG
