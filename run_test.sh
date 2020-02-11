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
	cp $static ./tractogram_static.tck;
	python tck2trk.py $t1_static tractogram_static.tck -f;
	cp tractogram_static.trk $subjID'_track.trk';
else
	echo "Tractogram already in .trk format"
	cp $static $subjID'_track.trk';
fi














tractID_list=`jq -r '.tractID_list' config.json`
arr=()
arr+=(${tractID_list})
tractID=${arr[0]//[,\"]}

if [[ $tractID < 30 ]]; then #afq
	echo "Coregistering ROIs on the target subject space"
	./mni_roi_registration.sh ${subjID} ${t1_static} AFQ
else #wmaSeg
	echo "Extracting endROIs of the minor tracts"
	mkdir aligned_ROIs;
	fsDir=`jq -r '.fsDir' config.json`
	python extract_endrois_minor.py -region 'parietal' -fsDir ${fsDir} -t1 ${t1_static} -out_dir aligned_ROIs
	python extract_endrois_minor.py -region 'temporal' -fsDir ${fsDir} -t1 ${t1_static} -out_dir aligned_ROIs
	python extract_endrois_minor.py -region 'LatTemp' -fsDir ${fsDir} -t1 ${t1_static} -out_dir aligned_ROIs
fi


echo "Running Classifyber (only test)"
mkdir tracts_trks;
singularity exec -e docker://brainlife/dipy:0.16.0 python test_classifyber.py \
			-src_dir 'results-training' \
			-sub_list 'subject_21_ids_test_tractseg-2.txt' \
			-tract_list ${tractID_list} \
			-out_dir ${output_directory}
