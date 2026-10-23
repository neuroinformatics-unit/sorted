# Definitions

(definitions-raw-data-path)=
## `RAW_DATA_PATH`
A filepath to any raw data files or folders that can be loaded by SpikeInterface (e.g. SpikeGLX, Open Ephys, SpikeInterface folder).

(definitions-spikeinterface-rec)=
## `SPIKEINTERFACE_REC`
An in-memory SpikeInterface [`Recording`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.BaseRecording) object.

If split by shank, the `SPIKEINTERFACE_REC` may be a dictionary where the keys are shank name and values are recording for that shank e.g. `recording=[{"0": Recording1, "1": Recording2}, {"0": Recording3, "1": Recording4}]`

(definitions-raw-data-path-session-list)=
## `RAW_DATA_PATH_SESSION_LIST`
A Python list of `RAW_DATA_PATH`.

(definitions-spikeinterface-rec-session-list)=
## `SPIKEINTERFACE_REC_SESSION_LIST`
A Python list of `SPIKEINTERFACE_REC`.

(definitions-debugging-rec)=
## `DEBUGGING_REC`
A `SPIKEINTERFACE_REC` that has been cut down to allow the pipeline to run quickly.

The default time to cut a recording down to is 30 seconds, based on the Allen pipeline (as of 02/09/2026).

(definitions-data-loader-output-recordings)=
## `DATA_LOADER_OUTPUT_RECORDINGS`
The data returned by the data loader. It may be a {ref}`SPIKEINTERFACE_REC <definitions-spikeinterface-rec>`, a {ref}`SPIKEINTERFACE_REC_SESSION_LIST <definitions-spikeinterface-rec-session-list>`, a {ref}`DEBUGGING_REC <definitions-debugging-rec>` or list thereof.

(definitions-preprocessed-output-recordings)=
## `PREPROCESSED_OUTPUT_RECORDINGS`
Takes the form `DATA_LOADER_OUTPUT_RECORDINGS` but the recordings are the final output of the preprocessing step.

(definitions-sorting)=
## `SORTING`
A SpikeInterface [`BaseSorting`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.BaseSorting) object.

(definitions-sorting-analyzer)=
## `SORTING_ANALYZER`
A SpikeInterface [`SortingAnalyzer`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.SortingAnalyzer) object.

(definitions-sorter-report)=
## `SORTER_REPORT`
The report produced for the SpikeInterface sorting result.

(definitions-postprocessing-plots)=
## `POSTPROCESSING_PLOTS`
The collection of plots generated during postprocessing.

**TODO: fill in** (for the most part these will )

(definitions-template-plots)=
### `TEMPLATE_PLOTS`
(definitions-waveform-plots)=
### `WAVEFORM_PLOTS`
(definitions-cluster-plots)=
### `CLUSTER_PLOTS`
(definitions-unit-location-plots)=
### `UNIT_LOCATION_PLOTS`
(definitions-autocorrelogram-plots)=
### `AUTOCORRELOGRAM_PLOTS`
(definitions-crosscorrelogram-plots)=
### `CROSSCORRELOGRAM_PLOTS`
(definitions-firing-rate-plots)=
### `FIRING_RATE_PLOTS`
(definitions-quality-metric-plots)=
### `QUALITY_METRIC_PLOTS`