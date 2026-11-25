<h1 align="center">Classifyber</h1>

<p align="center">
  Segments white matter bundles in a target tractogram with Classifyber, a streamline-based linear classifier trained on example segmentations from other subjects.
</p>

<p align="center">
  <a href="https://github.com/brainlife/abcd-spec"><img src="https://img.shields.io/badge/ABCD_Spec-v1.1-green.svg" alt="ABCD Spec v1.1"></a>
  <a href="https://doi.org/10.25663/brainlife.app.228"><img src="https://img.shields.io/badge/Brainlife-brainlife.app.228-blue.svg" alt="Run on brainlife.io"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-see_LICENSE-lightgrey.svg" alt="License"></a>
</p>

## At a glance

<!-- brainlife-app:begin (generated from the App manifest; edit the manifest, not this block) -->

> **Segments white matter bundles in a target tractogram with Classifyber, a streamline-based linear classifier trained on example segmentations from other subjects.**

Runs both the training and test phases of Classifyber: for each requested bundle it learns a binary linear classifier from example subjects' segmented bundles (combining streamline geometry, connectivity and atlas features in MNI space) and applies it to the target subject's tractogram. Use it for automatic bundle segmentation when segmented examples are available; for the test phase only, use brainlife.app.265. The moving tractograms, segmentations and T1s must be given in the same subject order, and the code checks that subject IDs match.

| | |
|---|---|
| **Inputs** | `neuro/track/tck` ×2 · `neuro/anat/t1w` ×2 · `neuro/wmc` |
| **Outputs** | `neuro/wmc` |
| **Container** | `brainlife/dipy:0.16.0` |
| **Resources** | 16 CPUs · 40 GB memory · 12 h walltime |
| **Run it** | [doi.org/10.25663/brainlife.app.228](https://doi.org/10.25663/brainlife.app.228) |

#### Inputs

| Input | Datatype | Required | Description |
|---|---|---|---|
| `0` | `neuro/track/tck` | yes | Tractogram of static (target) subject |
| `1` | `neuro/anat/t1w` (acpc_aligned) | yes | T1 of static (target) subject |
| `2` | `neuro/wmc` | yes | Segmentations of moving (examples) subjects (they should be extracted from the tractogram provided) |
| `3` | `neuro/track/tck` | yes | Tractograms of moving (example) subjects |
| `4` | `neuro/anat/t1w` (acpc_aligned) | yes | Ts1 of moving (example) subjects |

#### Outputs

| Output | Datatype | Description |
|---|---|---|
| `output_wmc` | `neuro/wmc` | White matter classification (classification.mat plus per-tract JSON files) of the selected bundles in the target tractogram. |

<details>
<summary><b>Parameters</b> (1)</summary>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tractID_list` | string |  | ID list of the bundles of interest, separated by commas (refer to the README.md for the mapping) |

</details>

<!-- brainlife-app:end -->

## Running the App

### On brainlife.io

Open the App at [doi.org/10.25663/brainlife.app.228](https://doi.org/10.25663/brainlife.app.228), choose `neuro/track/tck`, `neuro/anat/t1w`, `neuro/wmc`, `neuro/track/tck`, `neuro/anat/t1w` from your project, set the parameters and press **Execute**. The results are saved to your project as `neuro/wmc`.

### Locally

You need [Singularity/Apptainer](https://apptainer.org/) (the App runs in `brainlife/dipy:0.16.0`), [`jq`](https://jqlang.github.io/jq/).

1. Clone this repository.
2. Create `config.json` with the paths to your inputs and the parameters:

   ```json
   {
       "tractogram_static": "/path/to/0/tractogram_static",
       "t1_static": "/path/to/1/t1_static",
       "segmentations": "/path/to/2/segmentations",
       "tracts": "/path/to/2/tracts",
       "tractograms_moving": "/path/to/3/tractograms_moving",
       "t1s_moving": "/path/to/4/t1s_moving",
       "tractID_list": ""
   }
   ```

3. Run `./main`.

## Troubleshooting

- **Inputs subject id incorrectly inserted. Check them again.**: Give the target tractogram and T1 of the same subject, and the example segmentations, tractograms and T1s in the same subject order.

## On [Brainlife.io](http://brainlife.io/)

You can submit this App online at https://doi.org/10.25663/brainlife.app.228 via the “Execute” tab.

Inputs: \
To perform the bundle segmentation, you need two key elements: (i) the tractogram of the (target) subject you want to extract the bundle from and (ii) the wmc segmentations of multiple (example) subjects you want to learn from. Moreover, you have to provide the anatomical T1s and the tractograms of the (example) subjects (which are used to compute bundle superset and internal conversions). WARNING: all the tractograms need to be already co-registered in the same anatomical space (you can use the App https://doi.org/10.25663/brainlife.app.202 to warp your .tck file to the MNI152 T1 space). 

Output: \
You will get the wmc segmentation of the bundle(s) of interest in the target subject. You can convert it in multiple .tck files with the App https://doi.org/10.25663/brainlife.app.251.

#### Branch 1.0:
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

## Citing

If you use this App, please cite it, the software it builds on and brainlife.io:

- Classifyber. brainlife.io App. [doi:10.25663/brainlife.app.228](https://doi.org/10.25663/brainlife.app.228)
- Berto G, Bullock D, Astolfi P, et al. Classifyber, a robust streamline-based linear classifier for white matter bundle segmentation. NeuroImage (2020). [doi:10.1016/j.neuroimage.2020.117402](https://doi.org/10.1016/j.neuroimage.2020.117402)
- Garyfallidis et al. Dipy, a library for the analysis of diffusion MRI data. *Frontiers in Neuroinformatics* 8 (2014). [doi:10.3389/fninf.2014.00008](https://doi.org/10.3389/fninf.2014.00008)
- Hayashi S, Caron BA, Heinsfeld AS, et al. brainlife.io: a decentralized and open-source cloud platform to support neuroscience research. *Nature Methods* 21:809–813 (2024). [doi:10.1038/s41592-024-02237-2](https://doi.org/10.1038/s41592-024-02237-2)
- Avesani P, McPherson B, Hayashi S, et al. The open diffusion data derivatives, brain data upcycling via integrated publishing of derivatives and reproducible open cloud services. *Scientific Data* 6:69 (2019). [doi:10.1038/s41597-019-0073-y](https://doi.org/10.1038/s41597-019-0073-y)

## Authors

- Giulia Bertò

**Contributors**

- Emanuele Olivetti

## Funding

[![Wellcome-226486/Z/22/Z](https://img.shields.io/badge/Wellcome-226486%2FZ%2F22%2FZ-purple.svg)](https://wellcome.org/)
[![NIH-NINDS-U24NS140384](https://img.shields.io/badge/NIH_NINDS-U24NS140384-green.svg)](https://reporter.nih.gov/project-details/11261037)
[![NIH-NINDS-UM1NS132207](https://img.shields.io/badge/NIH_NINDS-UM1NS132207-green.svg)](https://reporter.nih.gov/project-details/11411328)
[![NIH-NIBIB-R01EB029272](https://img.shields.io/badge/NIH_NIBIB-R01EB029272-green.svg)](https://reporter.nih.gov/project-details/10262925)
[![NIH-NIBIB-R01EB030896](https://img.shields.io/badge/NIH_NIBIB-R01EB030896-green.svg)](https://reporter.nih.gov/project-details/10428625)
[![NIH-NIMH-R01MH126699](https://img.shields.io/badge/NIH_NIMH-R01MH126699-green.svg)](https://reporter.nih.gov/project-details/10460628)
[![NIH-NIDCD-R01DC020088](https://img.shields.io/badge/NIH_NIDCD-R01DC020088-green.svg)](https://reporter.nih.gov/project-details/11140284)
[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-2203524](https://img.shields.io/badge/NSF_BCS-2203524-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2203524)
[![NSF-IIS-1636893](https://img.shields.io/badge/NSF_IIS-1636893-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-OAC-2148729](https://img.shields.io/badge/NSF_OAC-2148729-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2148729)
[![NSF-IIS-1912270](https://img.shields.io/badge/NSF_IIS-1912270-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1912270)
[![NSF-IIS-2148700](https://img.shields.io/badge/NSF_IIS-2148700-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2148700)
[![NSF-OAC-1916518](https://img.shields.io/badge/NSF_OAC-1916518-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1916518)

<sub>brainlife.io, which runs this App, is publicly funded by Wellcome, the U.S. National Institutes of Health and the U.S. National Science Foundation; acknowledging that support helps keep it running.</sub>

## License

See [LICENSE](LICENSE).
