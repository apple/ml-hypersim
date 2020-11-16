include ../../system_config.inc

default:
	mkdir -p ../../bin
	g++ main.cpp \
	-o ../../bin/generate_oriented_bounding_box \
	-std=c++11 -O3 \
	-I$(APPROX_MVBB_INCLUDE_DIR) \
	-I$(ARGS_INCLUDE_DIR) \
	-I$(ARMADILLO_INCLUDE_DIR) \
	-I/usr/local/include/eigen3 \
	-I$(HDF5_INCLUDE_DIR) \
	-L$(APPROX_MVBB_LIB_DIR) -lApproxMVBB \
	-L$(ARMADILLO_LIB_DIR) -larmadillo \
	-L$(HDF5_LIB_DIR) -lhdf5 \
	$(APPROX_MVBB_EXTRA_CPP_FLAGS) \
	$(ARMADILLO_EXTRA_CPP_FLAGS) -DARMA_NO_DEBUG
