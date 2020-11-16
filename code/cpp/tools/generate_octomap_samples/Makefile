include ../../system_config.inc

default:
	mkdir -p ../../bin
	g++ main.cpp \
	-o ../../bin/generate_octomap_samples \
	-std=c++11 -O3 \
	-I$(ARGS_INCLUDE_DIR) \
	-I$(ARMADILLO_INCLUDE_DIR) \
	-I$(HDF5_INCLUDE_DIR) \
	-I$(OCTOMAP_INCLUDE_DIR) \
	-L$(ARMADILLO_LIB_DIR) -larmadillo \
	-L$(HDF5_LIB_DIR) -lhdf5 \
	-L$(OCTOMAP_LIB_DIR) -loctomath -loctomap \
	$(ARMADILLO_EXTRA_CPP_FLAGS) -DARMA_NO_DEBUG \
	$(OCTOMAP_EXTRA_CPP_FLAGS)
