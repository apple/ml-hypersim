#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

import os, sys, inspect

def add_path_to_sys_path(path, mode, frame):
    assert mode == "unchanged" or mode == "relative_to_cwd" or mode == "relative_to_current_source_dir"
    if mode == "unchanged":
        if path not in sys.path:
            sys.path.insert(0,path)
    if mode == "relative_to_cwd":
        realpath = os.path.realpath(os.path.abspath(path))
        if realpath not in sys.path:
            sys.path.insert(0,realpath)
    if mode == "relative_to_current_source_dir":
        realpath = os.path.realpath(os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(frame)),path)))
        if realpath not in sys.path:
            sys.path.insert(0,realpath)

def get_current_source_file_path(frame):
    return os.path.realpath(os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(frame)))))
