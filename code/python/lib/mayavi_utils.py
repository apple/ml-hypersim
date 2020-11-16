#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import mayavi.mlab

def points3d_color_by_scalar(positions, scalars, sizes=None, mode="sphere", scale_factor=1.0, colormap="jet", opacity=1.0):

    assert scalars is not None

    num_pts = positions.shape[0]

    S = c_[ones(num_pts), zeros(num_pts), zeros(num_pts)]

    if sizes is not None:
        S = S*sizes[:,newaxis]

    pts = mayavi.mlab.quiver3d(positions[:,0], positions[:,1], positions[:,2], S[:,0], S[:,1], S[:,2], scalars=scalars, mode=mode, scale_factor=scale_factor, colormap=colormap, opacity=opacity)
    pts.glyph.color_mode = "color_by_scalar"
    pts.glyph.glyph_source.glyph_source.center = [0,0,0]

def points3d_color_by_rgb_value(positions, colors, sizes=None, mode="sphere", scale_factor=1.0, colormap="jet", opacity=1.0):

    assert colors is not None
    assert all(colors >= 0.0) and all(colors <= 1.0)
    assert colors.shape[1] == 3 or colors.shape[1] == 4

    num_pts = positions.shape[0]

    S = c_[ones(num_pts), zeros(num_pts), zeros(num_pts)]

    if sizes is not None:
        S = S*sizes[:,newaxis]

    scalars = arange(num_pts)

    if colors.shape[1] == 3:
        colors_cmap = (c_[colors, ones(num_pts)]*255).astype(int32)
    if colors.shape[1] == 4:
        colors_cmap = (colors*255).astype(int32)

    pts = mayavi.mlab.quiver3d(positions[:,0], positions[:,1], positions[:,2], S[:,0], S[:,1], S[:,2], scalars=scalars, mode=mode, scale_factor=scale_factor, opacity=opacity)
    pts.glyph.color_mode = "color_by_scalar"
    pts.glyph.glyph_source.glyph_source.center = [0,0,0]
    pts.module_manager.scalar_lut_manager.lut.table = colors_cmap
    mayavi.mlab.draw()
