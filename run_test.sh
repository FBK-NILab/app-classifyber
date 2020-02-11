#!/bin/bash

subjID=`jq -r '._inputs[0].meta.subject' config.json`
static=`jq -r '.tractogram_static' config.json`
t1_static=`jq -r '.t1_static' config.json`

echo "Check the inputs subject id"
if [ ! $subjID == `jq -r '._inputs[1].meta.subject' config.json` ]; then
echo "Inputs subject id incorrectly inserted. Check them again."
	exit 1
fi

echo "Tractogram conversion to trk"
if [[ $static == *.tck ]];then
	echo "Input in tck format. Convert it to trk."
	cp $static ./tractogram_static.tck
	python tck2trk.py $t1_static tractogram_static.tck -f
	cp tractogram_static.trk $subjID'_track.trk'
else
	echo "Tractogram already in .trk format"
	cp $static $subjID'_track.trk'
fi

echo "Running Classifyber (only test)"
mkdir -p tracts_trks
python test_classifyber.py \
		-src_dir 'results_training' \
		-static $subjID'_track.trk' \
		-out_dir 'tracts_trks'

if [ -z "$(ls -A -- "tracts_trks")" ]; then    
	echo "Segmentation failed."
	exit 1
else    
	echo "Segmentation done."
fi

echo "Building the wmc structure"
mkdir -p tracts
python build_wmc.py -tractogram $static

if [ -f 'classification.mat' ]; then 
    echo "WMC structure created."
else 
	echo "WMC structure missing."
	exit 1
fi

