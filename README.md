[![Run on Brainlife.io](https://img.shields.io/badge/Brainlife-bl.app.228-blue.svg)](https://doi.org/10.25663/brainlife.app.228)

# app-classifyber
This app implements Classifyber, a supervised streamline-based method that performs automatic bundle segmentation by learning from example bundles already segmented, and that is robust to a multitude of diverse settings, i.e. that can deal with different bundle sizes, tracking algorithms, and dMRI data qualities. Classifyber is based on binary linear classification, which simultaneously combines information from bundle geometries, connectivity patterns and atlases. 

![](graphical_abstract_classifyber.png)

### Authors
- Giulia Bertò (giulia.berto.4@gmail.com)

### Contributors
- Emanuele Olivetti (olivetti@fbk.eu)

### Funding 
[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-1636893](https://img.shields.io/badge/NSF_BCS-1636893-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-AOC-1916518](https://img.shields.io/badge/NSF_AOC-1916518-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1916518)

### Reference
["Classifyber, a robust streamline-based linear classifier for white matter bundle segmentation"](https://www.biorxiv.org/content/10.1101/2020.02.10.942714v1), Bertò, G., Bullock, D., Astolfi, P., Hayashi, S., Zigiotto, L., Annicchiarico, L., Corsini, F., De Benedictis, A., Sarubbo, S., Pestilli, F., Avesani, P., Olivetti, E. 

### Running the app
On [BrainLife.io](http://brainlife.io/) \
You can submit this App online at https://doi.org/10.25663/brainlife.app.228 via the “Execute” tab.

Inputs: \
To perform the bundle segmentation, you need two key elements: (i) the tractogram of the (target) subject you want to extract the bundle from and (ii) the wmc segmentations of multiple (example) subjects you want to learn from. Moreover, you have to provide the anatomical T1s and the tractograms of the (example) subjects (which are used to compute bundle superset and internal conversions). WARNING: all the tractograms need to be already co-registered in the same anatomical space.  

Output: \
You will get the wmc segmentation of the bundle(s) of interest in the target subject.

Branch 1.0: \
The wmc segmentation files you have to provide as examples should be obtained using the AFQ segmentation algorithm (https://doi.org/10.25663/brainlife.app.207) or the WMA segmentation algorithm (https://doi.org/10.25663/brainlife.app.188). 

In the first case, you can choose the bundle(s) to be segmented by providing the id(s) related to the AFQ segmentation as follows: \
1 - Left Thalamic Radiation \
2 - Right Thalamic Radiation \
3 - Left Corticospinal \
4 - Right Corticospinal \
5 - Left Cingulum Cingulate \
6 - Right Cingulum Cingulate \
7 - Left Cingulum Hippocampus \
8 - Right Cingulum Hippocampus \
9 - Callosum Forceps Major \
10 - Callosum Forceps Minor \
11 - Left IFOF \
12 - Right IFOF \
13 - Left ILF \
14 - Right ILF \
15 - Left SLF \
16 - Right SLF \
17 - Left Uncinate \
18 - Right Uncinate \
19 - Left Arcuate \
20 - Right Arcuate 

In the second case, you can choose the bundle(s) to be segmented by providing the id(s) related to the WMA segmentation as follows: \
38 - Left pArc \
39 - Right pArc \
40 - Left TP-SPL \
41 - Right TP-SPL \
42 - Left MdLF-SPL \
43 - Right MdLF-SPL \
44 - Left MdLF-Ang \
45 - Right MdLF-Ang 
