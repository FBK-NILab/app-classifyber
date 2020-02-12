""" Classification of multiple bundles from multiple examples.
"""
import os
import sys
import argparse
import os.path
import numpy as np
import time
import ntpath
import nibabel as nib
import pickle
import json
from utils import compute_kdtree_and_dr_tractogram, compute_superset, save_trk
from dipy.tracking.distances import bundles_distances_mam, bundles_distances_mdf
from features_mni import compute_feature_matrix


def tract_predict(src_dir, superset, tract_name, distance_func=bundles_distances_mam, nb_points=20):
	"""Code for predict the tract.
	"""
	print("Computing X_test.") 
	X_test = compute_feature_matrix(superset, tract_name, distance_func=distance_func, nb_points=nb_points)
	
	print("Normalize X_test.")	
	scaler_fname = '%s/scaler_%s' %(src_dir, tract_name)
	scaler = pickle.load(open(scaler_fname))
	X_test = scaler.transform(X_test)
	
	print("Prediction.")
	t0=time.time()
	clf_fname = '%s/clf_%s' %(src_dir, tract_name)
	clf = pickle.load(open(clf_fname))
	y_pred = clf.predict(X_test)
	print("---->Time to predict X_test of size (%s, %s) = %.2f seconds" %(X_test.shape[0], X_test.shape[1], time.time()-t0)) 

	return y_pred


def test_multiple_examples(tractogram_fname, src_dir, tract_name_list, out_dir):
	"""Code for testing.
	"""
	num_prototypes = 100
	distance_func = bundles_distances_mdf
	nb_points = 20

	tractogram = nib.streamlines.load(tractogram_fname)
	tractogram = tractogram.streamlines

	print("Compute kdt and prototypes...")
	kdt, prototypes = compute_kdtree_and_dr_tractogram(tractogram, num_prototypes=num_prototypes, 
									 				   distance_func=distance_func, nb_points=nb_points)
		
	for tract_name in tract_name_list:
		t1=time.time()
		print("Computing the test superset...")
		example_fname = 'templates_tracts/%s.trk' %tract_name
		tract = nib.streamlines.load(example_fname).streamlines
		superset_idx_test = compute_superset(tract, kdt, prototypes, k=10000, distance_func=distance_func, nb_points=nb_points)
		superset = tractogram[superset_idx_test]
		y_pred = tract_predict(src_dir, superset, tract_name, distance_func=distance_func, nb_points=nb_points)
		estimated_tract_idx = np.where(y_pred>0)[0]
		estimated_tract = tractogram[superset_idx_test[estimated_tract_idx]]
		print("Time to compute classification of tract %s = %.2f seconds" %(tract_name, time.time()-t1))
		np.save('estimated_idx_%s.npy' %tract_name, estimated_tract_idx)
		out_fname = '%s/%s.trk' %(out_dir, tract_name)
		save_trk(estimated_tract, out_fname)
		print("Tract saved in %s" %out_fname)



if __name__ == '__main__':

	np.random.seed(0) 

	parser = argparse.ArgumentParser()
	parser.add_argument('-static', nargs='?',  const=1, default='',
	                    help='The static tractogram filename')
	parser.add_argument('-src_dir', nargs='?',  const=1, default='',
	                    help='The training results directory')
	parser.add_argument('-out_dir', nargs='?',  const=1, default='default',
	                    help='The output directory')                   
	args = parser.parse_args()

	t0=time.time()

	with open('config.json') as f:
		data = json.load(f)
		tractID_list = np.array(eval(data["tractID_list"]), ndmin=1)
	table = pickle.load(open('IDs_tracts_dictionary.pickle'))
	tract_name_list = []
	f = open("tract_name_list.txt","a")
	for i in tractID_list:
		tract_name = list(table[str(i)])[0]
		tract_name_list.append(tract_name)
		f.write(tract_name+'\n')
	f.close()

	print("----> Segmenting...")
	test_multiple_examples(args.static, args.src_dir, tract_name_list, args.out_dir)
	print("Total time elapsed = %i minutes" %((time.time()-t0)/60))

	sys.exit()

