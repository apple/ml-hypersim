#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import inspect
import os
import time
import vray

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config



current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
vrscene_file             = os.path.abspath(os.path.join(current_source_file_path, "..", "..", "..", "examples", "00_empty_scene", "empty.vrscene"))



# create renderer
renderer = vray.VRayRenderer()

# create logging callback 
def log_msg(renderer, message, level, instant):
    global fail_message
    if message.startswith("Failed"):
        fail_message = message

fail_message = None
renderer.setOnLogMessage(log_msg)
renderer.load(vrscene_file)
time.sleep(0.5)
renderer.close()

if fail_message is not None:
    print("\n[HYPERSIM: CHECK_VRAY_APPSDK_INSTALL] The V-Ray AppSDK is not configured correctly on your system: " + fail_message + "\n")
    exit(-1)
else:
    current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cwd = os.getcwd()
    os.chdir(current_source_file_path)

    cmd = _system_config.python_bin + " _check_vray_appsdk_install.py"
    retval = os.system(cmd)
    assert retval == 0

    os.chdir(cwd)

    print("\n[HYPERSIM: CHECK_VRAY_APPSDK_INSTALL] The V-Ray AppSDK is configured correctly on your system.\n")
