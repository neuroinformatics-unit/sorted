# Electrophysiology pipeline plan

This document plans a high-level specification that defines the pipeline steps (and their inputs and outputs) to create a modern spike-sorting pipeline. The requirements of each step and proposed implementation are discussed. This documentation is not written for users but instead as guidelines for developers.

At a high level, the pipeline needs to be:

- **Modular**: the full pipeline can run from one command, but users can also run the pipeline up to any arbitrary step and stop for troubleshooting, parameter selection, and manual review.
- **Protective**: the implementation should check for common invalid or poor-practice choices and warn or fail before users create misleading outputs.

The [Allen AIND pipeline](https://github.com/AllenNeuralDynamics/aind-ephys-pipeline) already provides a detailed spike sorting pipeline run through Nextflow. This work aims to follow it as closely as possible, while extended it for raw data quality and artefact detection and curation, as well as implement in a Python API that can be run locally. 

The pipeline is designed for Python with steps run through [SpikeInterface](https://github.com/SpikeInterface/spikeinterface), with GUI-related review and curation handled in [viewephys](https://github.com/int-brain-lab/viewephys) for raw data and preprocessing, or [spikeinterface-gui](https://github.com/SpikeInterface/spikeinterface-gui) for sorting outputs.
Note that not all proposed functionality currently exists in these tools. Please see the [Roadmap](../specification/roadmap.md) for details.

## Pipeline steps

The proposed pipeline steps are shown below:

1. [Data loading](../specification/data-loader.md)
2. [Raw data quality metrics](../specification/implementation.md#raw-data-quality-metrics)
3. {ref}`Detect bad channels <pipeline-steps-detect-bad-channels>`
4. [Artifact detection](../specification/implementation.md#artifact-detection)
5. [Artifact curation](../specification/implementation.md#artifact-curation)
6. [Preprocessing](../specification/implementation.md#preprocessing)
7. [Spike sorting](../specification/implementation.md#spike-sorting)
8. [Postprocessing](../specification/implementation.md#postprocessing)
9. [Curation](../specification/implementation.md#curation)

See [Pipeline Steps](../specification/implementation.md) for full details on each step. The image below details how the steps interact, with thick green lines tracing the full automated pipeline, whereas thin lines trace additional possible data flows, including NWB conversion links from preprocessing, spike sorting, postprocessing, and curation.

![Pipeline flow showing pipeline steps and NWB conversion links.](../_static/images/spec/overview.png)





