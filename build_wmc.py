import os
import sys
import json
import argparse
import numpy as np
import nibabel as nib
import scipy.io as sio
from matplotlib import cm
from json import encoder
from matplotlib import colors as mcolors

encoder.FLOAT_REPR = lambda o: format(o, '.2f') 


def build_wmc(tck_file, tractID_list):
    """
    Build the wmc structure.
    """
    print("building wmc structure")
    tractogram = nib.streamlines.load(tck_file)
    tractogram = tractogram.streamlines
    labels = np.zeros((len(tractogram),1))
    #os.makedirs('tracts')
    tractsfile = []
    names = np.full(tractID_list[-1],'NC',dtype=object)
    
    with open('tract_name_list.txt') as f:
    	tract_name_list = f.read().splitlines()

    np.random.seed(0)
    colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
    by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
             for name, color in colors.items())
    permuted_colors = np.random.permutation(by_hsv)

    for t, tractID in enumerate(tractID_list):
    	tract_name = tract_name_list[t]
    	idx_fname = 'estimated_idx_%s.npy' %tract_name		
    	idx_tract = np.load(idx_fname)
    	labels[idx_tract] = tractID

    	#build json file
    	filename = '%s.json' %tractID
    	tract = tractogram[idx_tract]
    	count = len(tract)
    	streamlines = np.zeros([count], dtype=object)
    	for e in range(count):
    		streamlines[e] = np.transpose(tract[e]).round(2)
    	#color=list(cm.nipy_spectral(t+10))[0:3]
    	color = list(permuted_colors[tractID][0])

    	print("sub-sampling for json")
    	if count < 1000:
    		max = count
    	else:
    		max = 1000
    	jsonfibers = np.reshape(streamlines[:max], [max,1]).tolist()
    	for i in range(max):
    		jsonfibers[i] = [jsonfibers[i][0].tolist()]

    	with open ('tracts/%s' %filename, 'w') as outfile:
    		jsonfile = {'name': tract_name, 'color': color, 'coords': jsonfibers}
    		json.dump(jsonfile, outfile)
    
    	splitname = tract_name.split('_')
    	fullname = splitname[-1].capitalize()+' '+' '.join(splitname[0:-1])  
    	tractsfile.append({"name": fullname, "color": color, "filename": filename})
    	names[tractID-1] = tract_name    	

    print("saving classification.mat")
    sio.savemat('classification.mat', { "classification": {"names": names, "index": labels }})

    with open ('tracts/tracts.json', 'w') as outfile:
    	json.dump(tractsfile, outfile, separators=(',', ': '), indent=4)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-tractogram', nargs='?', const=1, default='',
                        help='The tractogram file')
    args = parser.parse_args()

    with open('config.json') as f:
    	data = json.load(f)
    	tractID_list = np.array(eval(data["tractID_list"]), ndmin=1)
    
    build_wmc(args.tractogram, tractID_list)

    sys.exit()

