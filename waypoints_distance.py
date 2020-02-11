"""ROI-based distances.
"""

from __future__ import division, print_function, absolute_import
import numpy as np
import nibabel as nib
from nibabel.affines import apply_affine 
from scipy.spatial.distance import cdist
from sklearn.neighbors import KDTree

try:
    from joblib import Parallel, delayed, cpu_count
    joblib_available = True
except ImportError:
    joblib_available = False


def bundle2roi_distance(bundle, roi_mask, distance='euclidean'):
	"""Compute the minimum euclidean distance between a
	   set of streamlines and a ROI nifti mask.
	"""
	data = roi_mask.get_data()
	affine = roi_mask.affine
	roi_coords = np.array(np.where(data)).T
	x_roi_coords = apply_affine(affine, roi_coords)
	result=[]
	for sl in bundle:                                                                                  
		d = cdist(sl, x_roi_coords, distance)
		result.append(np.min(d)) 
	return result


def bundle2roi_distance_kdt(bundle, roi_mask, distance='euclidean'):
	"""Compute the minimum euclidean distance between a
	   set of streamlines and a ROI nifti mask.
	"""
	data = roi_mask.get_data()
	affine = roi_mask.affine
	roi_coords = np.array(np.where(data)).T
	x_roi_coords = apply_affine(affine, roi_coords)
	kdt = KDTree(x_roi_coords)
	result=[]
	for sl in bundle:                                                                                  
		d,i = kdt.query(sl, k=1)
		result.append(np.min(d)) 
	return result


def bundles_distances_roi(bundle, superset, roi1, roi2):

    roi1_dist = bundle2roi_distance(superset, roi1)
    roi2_dist = bundle2roi_distance(superset, roi2)
    roi_vector = np.add(roi1_dist, roi2_dist)
    roi_matrix = np.zeros((len(bundle), len(superset)))
    roi1_ex_dist = bundle2roi_distance(bundle, roi1)
    roi2_ex_dist = bundle2roi_distance(bundle, roi2)
    roi_ex_vector = np.add(roi1_ex_dist, roi2_ex_dist)
    #subtraction
    for i in range(len(bundle)):
    	for j in range(len(superset)):
    		roi_matrix[i,j] = np.abs(np.subtract(roi_ex_vector[i], roi_vector[j]))
    	
    return roi_matrix


def wrapper_bundle2roi_distance(bundle, roi, n_jobs=-1):
    
    if joblib_available and n_jobs != 1:
        if n_jobs is None or n_jobs == -1:
            n_jobs = cpu_count()      
    tmp = np.linspace(0, len(bundle), n_jobs + 1).astype(np.int)     
    chunks = zip(tmp[:-1], tmp[1:])
    roi_dist = np.hstack(Parallel(n_jobs=n_jobs)(delayed(bundle2roi_distance_kdt)(bundle[start:stop], roi) for start, stop in chunks))

    return roi_dist.flatten()


def bundles_distances_roi_fastest(bundle, superset, roi1, roi2):

    roi1_dist = wrapper_bundle2roi_distance(superset, roi1)
    roi2_dist = wrapper_bundle2roi_distance(superset, roi2)
    roi_vector = np.add(roi1_dist, roi2_dist)
    roi_matrix = np.zeros((len(bundle), len(superset)))
    roi1_ex_dist = wrapper_bundle2roi_distance(bundle, roi1)
    roi2_ex_dist = wrapper_bundle2roi_distance(bundle, roi2)
    roi_ex_vector = np.add(roi1_ex_dist, roi2_ex_dist)

    #subtraction
    for i in range(len(bundle)):
        for j in range(len(superset)):
            roi_matrix[i,j] = np.abs(np.subtract(roi_ex_vector[i], roi_vector[j]))

    return roi_matrix

