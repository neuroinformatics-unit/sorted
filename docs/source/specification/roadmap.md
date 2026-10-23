# Roadmap

There are a number of missing steps:

- Raw data quality metrics is not in SpikeInterface
- Inter-session alignment is not merged yet
- Artefact curation is not in viewephys

The plan is:

1) port Raw data quality metrics to SpikeInterface
2) merge inter-session alignment
3) develop the pipeline (excluding artefact curation) in Python. Use SpikeInterface wherever possible. For some things (e.g. html visualisations) we may need to first develop outside of SpikeInterface and port if useful.
4) develop the slurm runner
5) document
6) advertise internally
7) develop the web app
8) advertise wider
9) add artefact curation and other visualisation helpers (e.g. driftplots, detected spike times) to viewephys.

## TODO: discuss bad-channel detection metrics and plots

Discuss the SpikeInterface changes needed to expose the per-channel metrics and generate these plots before adding them to the pipeline outputs.

(roadmap-detect-bad-channels-metrics)=
### `BAD_CHANNEL_DETECTION_METRICS`
The scores for each channel on the IBL's three metrics used for bad channel detection. Also RMS for each channel.

(roadmap-detect-bad-channels-plots)=
### `BAD_CHANNEL_DETECTION_PLOTS`
Plots of `BAD_CHANNEL_DETECTION_METRICS` as shown in figure 4 of the [IBL white paper.](https://figshare.com/articles/online_resource/Spike_sorting_pipeline_for_the_International_Brain_Laboratory/19705522?file=49783080).

## TODO: discuss concatenation-point quality metrics and plots

Discuss which metrics and plots are useful across concatenation boundaries, and the SpikeInterface changes needed to support them.

(roadmap-concat-points-quality-metrics)=
### `CONCAT_POINTS_QUALITY_METRICS`
This is hypothetical set of quality metrics that check RMS and other QA across the concatenation points of recordings,

(roadmap-concat-points-quality-metrics-plots)=
### `CONCAT_POINTS_QUALITY_METRICS_PLOTS`
Plots of preprocessed data at the concatenation point of recordings. Possibly plots of `CONCAT_POINTS_QUALITY_METRICS`.
