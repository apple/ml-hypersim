include ../../system_config.inc

default:
	mkdir -p ../../bin
	g++ main.cpp \
	-o ../../bin/generate_hdf5_from_exr \
	-std=c++11 -O3 \
	-I$(ARGS_INCLUDE_DIR) \
	-I$(ARMADILLO_INCLUDE_DIR) \
	-I$(HDF5_INCLUDE_DIR) \
	-I$(OPENEXR_INCLUDE_DIR) \
	-L$(ARMADILLO_LIB_DIR) -larmadillo \
	-L$(HDF5_LIB_DIR) -lhdf5 \
	-L$(OPENEXR_LIB_DIR) -lHalf -lIex -lIlmImf \
	$(ARMADILLO_EXTRA_CPP_FLAGS) -DARMA_NO_DEBUG
