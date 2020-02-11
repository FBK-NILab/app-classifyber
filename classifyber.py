#!/usr/bin/env python

""" Classification of multiple bundles from multiple examples.
"""
from __future__ import print_function, division
import os
import sys
import argparse
import numpy as np
import time
import ntpath
import nibabel as nib
import pickle
from utils import compute_kdtree_and_dr_tractogram, compute_superset, streamlines_idx, save_trk
from dipy.tracking.distances import bundles_distances_mam, bundles_distances_mdf
from dipy.tracking.streamline import set_number_of_points
from collections import OrderedDict
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from features_mni import compute_feature_matrix


#global configuration parameters
num_prototypes = 100
distance_func = bundles_distances_mdf
nb_points = 20
cw = {0:1, 1:3}
max_iter = 1000


def compute_X_y_train(subjID, tract_name, moving_tractogram_fname, example_fname):
	"""Compute X_train and y_train.
	"""
	moving_tractogram = nib.streamlines.load(moving_tractogram_fname)
	moving_tractogram = moving_tractogram.streamlines 
	print("Compute kdt and prototypes of %s" %moving_tractogram_fname)
	kdt, prototypes = compute_kdtree_and_dr_tractogram(moving_tractogram, num_prototypes=num_prototypes, 
									 					distance_func=distance_func, nb_points=nb_points)
	tract = nib.streamlines.load(example_fname)
	tract = tract.streamlines
	print("Computing the superset of %s" %example_fname)
	superset_idx = compute_superset(tract, kdt, prototypes, k=2000, distance_func=distance_func, nb_points=nb_points)
	superset = moving_tractogram[superset_idx]
	exID = ntpath.basename(moving_tractogram_fname)[4:10]

	print("Computing X_train.")
	X_train = compute_feature_matrix(superset, exID, subjID, tract_name, distance_func=distance_func, nb_points=nb_points)
 	
	print("Computing y_train.")
	y_train = np.zeros(len(superset))
	tract_idx = streamlines_idx(tract, kdt, prototypes, distance_func=distance_func, nb_points=nb_points)
	correspondent_idx = np.array([np.where(superset_idx==idx) for idx in tract_idx])
	y_train[correspondent_idx] = 1

	return X_train, y_train


def compute_union_superset_idx(kdt, prototypes, ex_dir_tract, distance_func=bundles_distances_mam, nb_points=20): 
	"""Compute a superset in a subject starting from the tracts of other subjects.
	"""
	union_superset_idx = []
	examples = os.listdir(ex_dir_tract)
	examples.sort()
	ne = len(examples)
	th = np.min([ne, 10]) #maximum 10 subjects

	for i in range(th):
		example_fname = '%s/%s' %(ex_dir_tract, examples[i])
		tract = nib.streamlines.load(example_fname)
		tract = tract.streamlines
		superset_idx_test = compute_superset(tract, kdt, prototypes, k=2000, distance_func=distance_func, nb_points=nb_points)
		union_superset_idx = np.concatenate((union_superset_idx, superset_idx_test))
	print("Total size superset: %s" %len(union_superset_idx))
	union_superset_idx = list(OrderedDict.fromkeys(union_superset_idx)) #removes duplicates
	union_superset_idx = np.array(union_superset_idx, dtype=int)
	print("Size reducted superset: %s" %len(union_superset_idx))

	return union_superset_idx


def classifyber(moving_tractograms_dir, static_tractogram_fname, ex_dir_tract):
	"""Code for classification from multiple examples.
	"""
	subjID = ntpath.basename(static_tractogram_fname)[4:10]
	tract_name = ntpath.basename(ex_dir_tract)
	moving_tractograms = os.listdir(moving_tractograms_dir)
	moving_tractograms.sort()
	examples = os.listdir(ex_dir_tract)
	examples.sort()

	nt = len(moving_tractograms)
	ne = len(examples)
	assert(nt == ne)

	X_train = np.array([])
	y_train = np.array([])
	
	print("Computing training set using %i examples." %ne)
	for i in range(nt):
		moving_tractogram_fname = '%s/%s' %(moving_tractograms_dir, moving_tractograms[i])
		example_fname = '%s/%s' %(ex_dir_tract, examples[i])
		X_tmp, y_tmp = compute_X_y_train(subjID, tract_name, moving_tractogram_fname, example_fname)
		X_train = np.vstack([X_train, X_tmp]) if X_train.size else X_tmp
		y_train = np.hstack([y_train, y_tmp]) if y_train.size else y_tmp
		print(X_train.shape)

	print("Computing X_test.")
	static_tractogram = nib.streamlines.load(static_tractogram_fname)
	static_tractogram = static_tractogram.streamlines
	print("Compute kdt and prototypes of %s" %static_tractogram_fname)
	kdt, prototypes = compute_kdtree_and_dr_tractogram(static_tractogram, num_prototypes=num_prototypes, 
														distance_func=distance_func, nb_points=nb_points)
	print("Computing the test superset...")
	union_superset_idx = compute_union_superset_idx(kdt, prototypes, ex_dir_tract, distance_func=distance_func, nb_points=nb_points)
	static_superset = static_tractogram[union_superset_idx] 
	X_test = compute_feature_matrix(static_superset, subjID, subjID, tract_name, distance_func=distance_func, nb_points=nb_points)
	del kdt, static_superset

	print("Normalize X_train and X_test.")	
	scaler = StandardScaler()
	scaler.fit(X_train)
	X_train = scaler.transform(X_train)
	X_test = scaler.transform(X_test)

	print("Classification.")
	clf = LogisticRegression(class_weight=cw, random_state=42, solver='sag', max_iter=max_iter)

	t0=time.time()
	clf.fit(X_train, y_train)
	print("---->Time to fit X_train of size (%s, %s) = %.2f seconds" %(X_train.shape[0], X_train.shape[1], time.time()-t0))
	t1=time.time()
	y_pred = clf.predict(X_test)
	y_pred_proba = clf.predict_proba(X_test)
	print("---->Time to predict X_test of size (%s, %s) = %.2f seconds" %(X_test.shape[0], X_test.shape[1], time.time()-t1))
	estimated_tract_idx = np.where(y_pred>0)[0]
	estimated_tract = static_tractogram[union_superset_idx[estimated_tract_idx]] 
	np.save('estimated_idx_%s.npy' %tract_name, union_superset_idx[estimated_tract_idx])

	return estimated_tract	



if __name__ == '__main__':

	np.random.seed(0) 

	parser = argparse.ArgumentParser()
	parser.add_argument('-moving_dir', nargs='?', const=1, default='',
	                    help='The moving tractograms directory')
	parser.add_argument('-static', nargs='?',  const=1, default='',
	                    help='The static tractogram filename')
	parser.add_argument('-ex_dir', nargs='?',  const=1, default='',
	                    help='The examples (moving) bundle directory')
	parser.add_argument('-list', nargs='?',  const=1, default='',
	                    help='The tract name list file .txt')
	parser.add_argument('-out_dir', nargs='?',  const=1, default='default',
	                    help='The output directory')                   
	args = parser.parse_args()

	t0=time.time()

	with open(args.list) as f:
		tract_name_list = f.read().splitlines()

	for tract_name in tract_name_list:
		t1=time.time()
		print("Classification of tract: %s" %tract_name)
		ex_dir_tract = '%s/%s' %(args.ex_dir, tract_name)
		estimated_tract = classifyber(args.moving_dir, args.static, ex_dir_tract)
		print("Time to compute classification of tract %s = %i minutes" %(tract_name, (time.time()-t1)/60))
		out_fname = '%s/%s.trk' %(args.out_dir, tract_name)
		save_trk(estimated_tract, out_fname)
		print("Tract saved in %s" %out_fname)

	print("Total time elapsed for the classification of all the tracts = %i minutes" %((time.time()-t0)/60))
	sys.exit()

