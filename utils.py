from __future__ import print_function
import os
import time
import numpy as np
import nibabel as nib
#from dipy.viz import fvtk
from nibabel.streamlines import load, save
from dipy.tracking.utils import length
from dipy.tracking.streamline import set_number_of_points
from dipy.tracking.distances import bundles_distances_mam, bundles_distances_mdf
from nibabel.affines import apply_affine 
from sklearn.neighbors import KDTree
#from scipy.spatial import cKDTree as KDTree
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


def streamlines_idx(target_tract, kdt, prototypes, distance_func=bundles_distances_mam, nb_points=20, warning_threshold=1.0e-0):
    """Retrieve indexes of the streamlines of the target tract.
    """
    if distance_func==bundles_distances_mdf:
    	print("Resampling the tract with %s points" %nb_points)
    	target_tract = set_number_of_points(target_tract, nb_points)
    distance = partial(parallel_distance_computation, distance=distance_func)
    dm_target_tract = distance(target_tract, prototypes)
    D, I = kdt.query(dm_target_tract, k=1)
    if (D > warning_threshold).any():
        print("WARNING (streamlines_idx()): for %s streamlines D > 1.0e-4 !!" % (D > warning_threshold).sum())
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


def NN(true_tract, kdt, prototypes, k=2000, distance_func=bundles_distances_mam, nb_points=20):
    """Compute the k-NN.
    """
    if distance_func==bundles_distances_mdf:
    	#print("Resampling the tract with %s points" %nb_points)
    	true_tract = set_number_of_points(true_tract, nb_points)
    distance = partial(parallel_distance_computation, distance=distance_func)
    true_tract = np.array(true_tract, dtype=np.object)
    dm_true_tract = distance(true_tract, prototypes)
    D, I = kdt.query(dm_true_tract, k=k)
    return D[0], I[0]


def NN_radius(true_tract, kdt, prototypes, r=10, distance_func=bundles_distances_mam, nb_points=20):
    """Compute the k-NN.
    """
    if distance_func==bundles_distances_mdf:
    	#print("Resampling the tract with %s points" %nb_points)
    	true_tract = set_number_of_points(true_tract, nb_points)
    distance = partial(parallel_distance_computation, distance=distance_func)
    true_tract = np.array(true_tract, dtype=np.object)
    dm_true_tract = distance(true_tract, prototypes)
    I = kdt.query_radius(dm_true_tract, r=r)
    I = np.sort(I[0])
    return I


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
    print("Time spent to compute the DR of the tractogram: %s seconds" %(time.time()-t0))
    return kdt, prototypes


def save_tract(tract, t1_filename, out_filename):
	"""Save a tract (voxel sizes and dimension are stored in the t1 file).
	"""
	extension = os.path.splitext(out_filename)[1]
	t1 = nib.load(t1_filename)
	aff_vox_to_ras = t1.affine
	header = t1.header
	dimensions = header.get_data_shape()
	voxel_sizes = header.get_zooms()
	
	if extension == '.trk':
		hdr = nib.streamlines.trk.TrkFile.create_empty_header()
		hdr['voxel_sizes'] = voxel_sizes
		hdr['dimensions'] = dimensions
		hdr['voxel_order'] = 'LAS'
		hdr['voxel_to_rasmm'] = aff_vox_to_ras 
	elif extension == '.tck':
		hdr = nib.streamlines.tck.TckFile.create_empty_header()
		hdr['voxel_sizes'] = voxel_sizes
		hdr['dimensions'] = dimensions
	else:
		print("%s format not supported." % extension)

	t = nib.streamlines.tractogram.Tractogram(tract, affine_to_rasmm=np.eye(4))
	nib.streamlines.save(t, out_filename, header=hdr)
	print("Bundle saved in %s" % out_filename)


def save_bundle(estimated_bundle_idx, static_tractogram, out_filename):
	"""Save a tract (voxel sizes and dimension are stored in the tractogram file).
	"""
	extension = os.path.splitext(out_filename)[1]
	static_tractogram = nib.streamlines.load(static_tractogram)
	aff_vox_to_ras = static_tractogram.affine
	voxel_sizes = static_tractogram.header['voxel_sizes']
	dimensions = static_tractogram.header['dimensions']
	static_tractogram = static_tractogram.streamlines
	estimated_bundle = static_tractogram[estimated_bundle_idx]
	
	if extension == '.trk':
		hdr = nib.streamlines.trk.TrkFile.create_empty_header()
		hdr['voxel_sizes'] = voxel_sizes
		hdr['dimensions'] = dimensions
		hdr['voxel_order'] = 'LAS'
		hdr['voxel_to_rasmm'] = aff_vox_to_ras 
	elif extension == '.tck':
		hdr = nib.streamlines.tck.TckFile.create_empty_header()
		hdr['voxel_sizes'] = voxel_sizes
		hdr['dimensions'] = dimensions
	else:
		print("%s format not supported." % extension)

	t = nib.streamlines.tractogram.Tractogram(estimated_bundle, affine_to_rasmm=np.eye(4))
	nib.streamlines.save(t, out_filename, header=hdr)
	print("Bundle saved in %s" % out_filename)	


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


def show_both_bundles(bundles, colors=None, show=True, fname=None):
    """Show two bundles
    """
    ren = fvtk.ren()
    ren.SetBackground(1., 1, 1)
    colors=[fvtk.colors.blue, fvtk.colors.red]
    for (i, bundle) in enumerate(bundles):
        color = colors[i]
        lines = fvtk.streamtube(bundle, color, linewidth=0.3)
        lines.RotateX(-90)
        lines.RotateZ(90)
        fvtk.add(ren, lines)
    if show:
        fvtk.show(ren)
    if fname is not None:
        sleep(1)
        fvtk.record(ren, n_frames=1, out_path=fname, size=(1500,1000))
        fvtk.show(ren)


def show_tracts(estimated_target_tract, target_tract, fname=None):
	"""Visualization of the tracts.
	"""
	ren = fvtk.ren()
	fvtk.add(ren, fvtk.line(estimated_target_tract, fvtk.colors.green,
                            linewidth=1, opacity=0.3))
	fvtk.add(ren, fvtk.line(target_tract, fvtk.colors.white,
                                linewidth=1, opacity=0.3))
	if fname is not None:
		fvtk.record(ren, n_frames=1, out_path=fname, size=(1500,1000))
		fvtk.show(ren)   
	else:
		fvtk.show(ren)
		fvtk.clear(ren)


def show_tract(target_tract, linewidth=1, fname=None):
	"""Visualization of a tract.
	"""
	ren = fvtk.ren()
	fvtk.add(ren, fvtk.line(target_tract, fvtk.colors.red,
                            linewidth=linewidth, opacity=0.5))     
	if fname is not None:
		fvtk.record(ren, n_frames=1, out_path=fname, size=(1500,1000))
		fvtk.show(ren)   
	else:
		fvtk.show(ren)
		fvtk.clear(ren) 		
