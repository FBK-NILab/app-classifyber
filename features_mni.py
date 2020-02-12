"""Code to compute the feature matrix.
"""
from __future__ import print_function, division
import numpy as np
import nibabel as nib
import pickle
from dipy.tracking.distances import bundles_distances_mam, bundles_distances_mdf
from dipy.tracking.streamline import set_number_of_points
from distances import parallel_distance_computation
from functools import partial
from endpoints_distance import bundles_distances_endpoints_fastest
from waypoints_distance import wrapper_bundle2roi_distance, bundle2roi_distance
from utils import compute_kdtree_and_dr_tractogram, compute_superset

try:
    from joblib import Parallel, delayed, cpu_count
    joblib_available = True
except ImportError:
    joblib_available = False


## features settings 
dm = True
local_prototypes = True
endpoints = True
rois = True


## global configuration parameters
distance_func = bundles_distances_mdf
num_local_prototypes = 100
nb_points = 20


def compute_X_dm(superset, prototypes, distance_func=bundles_distances_mam, nb_points=20):
	"""Compute the global dissimilarity matrix.
	"""
	if distance_func==bundles_distances_mdf:
		print("Resampling the superset with %s points" %nb_points)
		superset = set_number_of_points(superset, nb_points)
	distance = partial(parallel_distance_computation, distance=distance_func)
	print("Computing dissimilarity matrix (%s x %s)..." %(len(superset), len(prototypes)))
	dm_superset = distance(superset, prototypes)
	
	return dm_superset


def compute_X_dm_local(superset, tract_name, distance_func=bundles_distances_mam, nb_points=20):
	"""Compute the local dissimilarity matrix.
	"""
	if distance_func==bundles_distances_mdf:
		print("Resampling the superset with %s points" %nb_points)
		superset = set_number_of_points(superset, nb_points)
	distance = partial(parallel_distance_computation, distance=distance_func)
	local_prot_fname = 'common_local_prototypes/%s_common_prototypes.npy' %tract_name
	local_prototypes = np.load(local_prot_fname)
	print("Computing dissimilarity matrix (%s x %s)..." %(len(superset), len(local_prototypes)))
	dm_local_superset = distance(superset, local_prototypes)
	
	return dm_local_superset


def compute_X_end(superset, prototypes):
	"""Compute the endpoint matrix.
	"""
	endpoint_matrix = bundles_distances_endpoints_fastest(superset, prototypes)
	endpoint_matrix = endpoint_matrix * 0.5
	return endpoint_matrix


def compute_X_roi(superset, tract_name):
	"""Compute a matrix with dimension (len(superset), 2) that contains 
	   the distances of each streamline of the superset with the 2 ROIs. 
	""" 
	superset = set_number_of_points(superset, nb_points) #to speed up the computational time
	print("Loading the two-waypoint ROIs of the target...")
	table_filename = 'ROIs_labels_dictionary.pickle'
	table = pickle.load(open(table_filename)) #python2
	roi1_lab = table[tract_name].items()[0][1] #python2
	roi2_lab = table[tract_name].items()[1][1] #python2
	#with open(table_filename, 'rb') as f: #python3
	#	u = pickle._Unpickler(f)
	#	u.encoding = 'latin1'
	#	table = u.load()
	#roi1_lab = table[tract_name]['label_ROI1'] #python3
	#roi2_lab = table[tract_name]['label_ROI2'] #python3
	d = pickle.load(open('IDs_tracts_dictionary.pickle')) #python2
	for i, n in d.items():
		if n == {tract_name}:
			tractID=eval(i)
	if tractID < 30:
		roi_dir = 'templates_mni125'
		roi1_filename = '%s/sub-MNI_var-AFQ_lab-%s_roi.nii.gz' %(roi_dir, roi1_lab)
		roi2_filename = '%s/sub-MNI_var-AFQ_lab-%s_roi.nii.gz' %(roi_dir, roi2_lab)
	else:
		roi_dir = 'templates_mni125_ICBM2009c'
		roi1_filename = '%s/%s.nii.gz' %(roi_dir, roi1_lab)
		roi2_filename = '%s/%s.nii.gz' %(roi_dir, roi2_lab)
	roi1 = nib.load(roi1_filename)
	roi2 = nib.load(roi2_filename)
	print("Computing superset to ROIs distances...")
	if joblib_available:
		roi1_dist = wrapper_bundle2roi_distance(superset, roi1)
		roi2_dist = wrapper_bundle2roi_distance(superset, roi2)
	else:
		roi1_dist = bundle2roi_distance(superset, roi1)
		roi2_dist = bundle2roi_distance(superset, roi2)
	X_roi = np.vstack((roi1_dist, roi2_dist))

	return X_roi.T


def compute_endpoints(bundle):
	endpoints = np.zeros((len(bundle),3)) 
	for i, st in enumerate(bundle):
		endpoints[i] = endpoint(st)
	return endpoints


def compute_feature_matrix(superset, tract_name, distance_func=distance_func, nb_points=nb_points):
	"""Compute the feature matrix.
	"""
	np.random.seed(0)
	feature_list = []

	if dm:
		common_prototypes = np.load('common_prototypes.npy')
		X_dm = compute_X_dm(superset, common_prototypes, distance_func=distance_func, nb_points=nb_points)
		feature_list.append(X_dm)
		print("----> Added dissimilarity matrix of size (%s, %s)" %(X_dm.shape))
		
	if local_prototypes:
		X_dm_local = compute_X_dm_local(superset, tract_name, distance_func=distance_func, nb_points=nb_points)
		feature_list.append(X_dm_local)
		print("----> Added local dissimilarity matrix of size (%s, %s)" %(X_dm_local.shape))

	if endpoints:
		common_prototypes = np.load('common_prototypes.npy')
		X_end = compute_X_end(superset, common_prototypes)
		feature_list.append(X_end)
		print("----> Added endpoint matrix of size (%s, %s)" %(X_end.shape))

	if rois:
		X_roi = compute_X_roi(superset, tract_name)
		feature_list.append(X_roi)
		print("----> Added ROI distance matrix of size (%s, %s)" %(X_roi.shape))

	#concatenation
	X_tmp = np.array([])
	for matrix in feature_list:
		X_tmp = np.hstack([X_tmp, matrix]) if X_tmp.size else matrix
	print("----> Size of final feature matrix: (%s, %s)" %(X_tmp.shape))

	return np.array(X_tmp, dtype=np.float32)

