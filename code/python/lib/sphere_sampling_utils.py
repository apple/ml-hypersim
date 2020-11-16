#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

def generate_evenly_distributed_samples_on_sphere(n_samples):
    
    # See http://blog.marmakoide.org/?p=1 for details
    golden_angle = pi * (3 - sqrt(5))
    theta = golden_angle * arange(n_samples)
    lat = linspace((1.0/n_samples) - 1, 1 - (1.0/n_samples), n_samples)
    radius = sqrt(1 - lat*lat)

    samples = ones((n_samples, 3))*np.inf
    samples[:,0] = radius * cos(theta)
    samples[:,1] = radius * sin(theta)
    samples[:,2] = lat

    return samples
