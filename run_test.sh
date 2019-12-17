
















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
