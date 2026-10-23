# Data Loader

The data loading step ensures all possbile ways of passing raw data are coerced into in-memory SpikeInterface objects.

It should exist as a convenience function rather than as a fixed step in the pipeline, as its output may be passed to any of [raw data metrics](implementation.md#raw-data-quality-metrics), [artefact detection](implementation.md#artifact-detection), [artefact curation](implementation.md#artifact-curation), [preprocessing](implementation.md#preprocessing), or the [full pipeline](../steps/overview.md#pipeline-steps). As such, no information related to data loading (e.g. file paths) is encoded in the {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`.


It essentially takes SpikeInterface recordings, or paths to raw data, and ensures they are loaded SpikeInterface recordings with probes attached. If recordings are concatenated, this is detected and concatenation times flagged.

**INPUTS:**

- A {ref}`RAW_DATA_PATH <definitions-raw-data-path>`, {ref}`RAW_DATA_PATH_SESSION_LIST <definitions-raw-data-path-session-list>`, {ref}`SPIKEINTERFACE_REC <definitions-spikeinterface-rec>`, or {ref}`SPIKEINTERFACE_REC_SESSION_LIST <definitions-spikeinterface-rec-session-list>`.
- (optional) a `bool` flag for producing a {ref}`DEBUGGING_REC <definitions-debugging-rec>`
- (optional) a `STREAM_NAME` in case the AP stream cannot be automatically detected.
- (optional) a {ref}`PROBE <outputs-probe>` to set on all loaded recordings in case it cannot be automatically loaded.
- (optional) a `split_by_shank` option.

**OUTPUTS:**

- a {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>`.

**OPERATIONS:**

- Load a {ref}`RAW_DATA_PATH <definitions-raw-data-path>` or {ref}`RAW_DATA_PATH_SESSION_LIST <definitions-raw-data-path-session-list>` to {ref}`SPIKEINTERFACE_REC <definitions-spikeinterface-rec>` or {ref}`SPIKEINTERFACE_REC_SESSION_LIST <definitions-spikeinterface-rec-session-list>`, respectively.  
- (optional) time slice the recordings to produce a {ref}`DEBUGGING_REC <definitions-debugging-rec>`.
- Automatically determine the AP stream, otherwise use `STREAM_NAME`. 
- Set a passed `PROBE` on the recordings, if passed and they are not automatically detected.

**CHECKS:**

- Error if no probe found in the loaded or passed recordings and `PROBE` is not passed.
- Error if cannot determine AP stream and no `STREAM_NAME` provided.
- Error if sessions do not have the same probe, sampling rate, data type etc. Do a confidence check on the session times if `time_vector` is set.
