from __future__ import print_function, division
import os
import time
import numpy as np
import nibabel as nib
from dipy.tracking.utils import length
from dipy.tracking.streamline import set_number_of_points
from dipy.tracking.distances import bundles_distances_mam, bundles_distances_mdf
from nibabel.affines import apply_affine 
from sklearn.neighbors import KDTree
from scipy.spatial.distance import cdist
from dissimilarity import compute_dissimilarity
from distances import parallel_distance_computation
from functools import partial


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


def resample_tract(tract, step_size):
    """Resample the tract with the given step size.
    """
    lengths=list(length(tract))
    tract_res = []
    for i, f in enumerate(tract):
    	if lengths[i]>step_size:
    		nb_res_points = np.int(np.ceil(lengths[i]/step_size))
    		tmp = set_number_of_points(f, nb_res_points)
    	else:	
    		tmp = f
    	tract_res.append(tmp)
    tract_res = nib.streamlines.array_sequence.ArraySequence(tract_res)
    return tract_res


def streamlines_idx(target_tract, kdt, prototypes, distance_func=bundles_distances_mam, nb_points=20, warning_threshold=1.0e-1):
    """Retrieve indexes of the streamlines of the target tract.
    """
    if distance_func==bundles_distances_mdf:
    	print("Resampling the tract with %s points" %nb_points)
    	target_tract = set_number_of_points(target_tract, nb_points)
    distance = partial(parallel_distance_computation, distance=distance_func)
    dm_target_tract = distance(target_tract, prototypes)
    D, I = kdt.query(dm_target_tract, k=1)
    if (D > warning_threshold).any():
        print("WARNING (streamlines_idx()): for %s streamlines D > 1.0e-1 !!" % (D > warning_threshold).sum())
    #print(D)
    target_tract_idx = I.squeeze()
    return target_tract_idx


def compute_superset(true_tract, kdt, prototypes, k=2000, distance_func=bundles_distances_mam, nb_points=20):
    """Compute a superset of the true target tract with k-NN.
    """
    if distance_func==bundles_distances_mdf:
    	#print("Resampling the tract with %s points" %nb_points)
    	true_tract = set_number_of_points(true_tract, nb_points)
    distance = partial(parallel_distance_computation, distance=distance_func)
    true_tract = np.array(true_tract, dtype=np.object)
    dm_true_tract = distance(true_tract, prototypes)
    D, I = kdt.query(dm_true_tract, k=k)
    superset_idx = np.unique(I.flat)
    return superset_idx


def compute_kdtree_and_dr_tractogram(tractogram, num_prototypes=40, 
									 distance_func=bundles_distances_mam, nb_points=20):
    """Compute the dissimilarity representation of the target tractogram and 
    build the kd-tree.
    """
    t0 = time.time()
    if distance_func==bundles_distances_mdf:
        print("Resampling the tractogram with %s points" %nb_points)
        tractogram = set_number_of_points(tractogram, nb_points)
    distance = partial(parallel_distance_computation, distance=distance_func)
    tractogram = np.array(tractogram, dtype=np.object)

    print("Computing dissimilarity matrices using %s prototypes..." % num_prototypes)
    dm_tractogram, prototype_idx = compute_dissimilarity(tractogram,
                                                         distance,
                                                         num_prototypes,
                                                         prototype_policy='sff',
                                                         verbose=False)
    prototypes = tractogram[prototype_idx]
    print("Building the KD-tree of tractogram.")
    kdt = KDTree(dm_tractogram)
    print("Time spent to compute the DR of the tractogram: %.2f seconds" %(time.time()-t0))
    return kdt, prototypes


def save_trk(streamlines, out_file, affine=np.zeros((4,4)), vox_sizes=np.array([0,0,0]), vox_order='LAS', dim=np.array([0,0,0])):
    """
    This function saves tracts in Trackvis '.trk' format.
    The default values for the parameters are the values for the HCP data.
    """
    if affine.any()==0:
        affine = np.array([[  -1.25,    0.  ,    0.  ,   90.  ],
                           [   0.  ,    1.25,    0.  , -126.  ],
                           [   0.  ,    0.  ,    1.25,  -72.  ],
                           [   0.  ,    0.  ,    0.  ,    1.  ]], 
                          dtype=np.float32)
    if (vox_sizes==[0,0,0]).all():
        vox_sizes = np.array([1.25, 1.25, 1.25], dtype=np.float32)   
    if (dim==[0,0,0]).all(): 
        dim = np.array([145, 174, 145], dtype=np.int16)
    if out_file.split('.')[-1] != 'trk':
        print("Format not supported.")

    # Create a new header with the correct affine 
    hdr = nib.streamlines.trk.TrkFile.create_empty_header()
    hdr['voxel_sizes'] = vox_sizes
    hdr['voxel_order'] = vox_order
    hdr['dimensions'] = dim
    hdr['voxel_to_rasmm'] = affine
    hdr['nb_streamlines'] = len(streamlines)

    t = nib.streamlines.tractogram.Tractogram(streamlines=streamlines, affine_to_rasmm=np.eye(4))
    nib.streamlines.save(t, out_file, header=hdr)

