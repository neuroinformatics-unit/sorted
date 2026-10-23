# Pipeline Steps

The [Data loader](data-loader.md) is separate from the pipeline steps and returns a {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>` that can be passed to this pipeline.

## Raw data quality metrics

This step computes IBL's quality metrics on raw recordings.

The metrics and detect-bad-channels results are written to the `RAW_DATA_METRICS_DIR` in the {ref}`OUTPUT_PATH <outputs-output-path>`.

**Inputs**

- {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>`
- a {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`
- a {ref}`OUTPUT_PATH <outputs-output-path>`

**Outputs**

Outputs are saved to `RAW_DATA_METRICS_DIR`

- {ref}`RAW_DATA_QUALITY_METRICS <outputs-raw-data-quality-metrics>` and {ref}`RAW_DATA_QUALITY_PLOTS <outputs-raw-data-quality-plots>` 

- TODO: discuss {ref}`CONCAT_POINTS_QUALITY_METRICS <roadmap-concat-points-quality-metrics>` and {ref}`CONCAT_POINTS_QUALITY_METRICS_PLOTS <roadmap-concat-points-quality-metrics-plots>`
- {ref}`CONCAT_REC_TIMES <outputs-concat-rec-times>` if concatenated recordings are detected.

**OPERATIONS**:

- Compute raw-data quality metrics using the configured settings.
- Generate quality-assessment plots from the computed metrics.
- Save the metrics and plots to `RAW_DATA_METRICS_DIR`.
- Determine if recordings are concatenated. Quality metrics across concatenation points are a {ref}`roadmap TODO <roadmap-concat-points-quality-metrics>`.

**CHECKS**:

- Confirm that the input data can be resolved to an AP recording suitable for metric computation.
- Warn when probe-specific metric settings are used on recordings with substantially different channel counts or geometry.


(implementation-detect-bad-channels)=
## Detect bad channels
This (optional) step uses IBL's bad-channel detection algorithm to detect bad channels. The bad-channel information is used to
remove bad channels before artefact detection, and remove or interpolate bad channels during preprocessing.

Detect bad channels after high-pass filtering at 300 Hz. This is because bandpass filtering removes the high frequencies used for noisy-channel detection.


**Inputs**

- {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>`
- a {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`
- a {ref}`OUTPUT_PATH <outputs-output-path>`

**Outputs**

- {ref}`BAD_CHANNEL_DETECTION_OUTPUTS <outputs-bad-channel-detection-outputs>`, containing channel IDs and labels.
- TODO: discuss {ref}`BAD_CHANNEL_DETECTION_METRICS <roadmap-detect-bad-channels-metrics>` and {ref}`BAD_CHANNEL_DETECTION_PLOTS <roadmap-detect-bad-channels-plots>`


**OPERATIONS**:

- High-pass filter the data, as required by the detect-bad-channels method.
- Detect bad channels and assign labels using the configured thresholds.
- Save the channel IDs and labels to the bad-channel output directory.
- TODO: discuss saving quality metrics and associated plots; see {ref}`Roadmap <roadmap-detect-bad-channels-metrics>`.

**CHECKS**:

- This algorithm was developed for Neuropixels probes. Different settings should be recommended for probes with lower channel counts.
- No preprocessing should have been applied to the recording so far. 
- If too many are out mention adjusting threshold as this is a known issue. Or maybe we bandpass but with a very high cutoff. Ask Alessio for a few examples of this issue.


## Artifact detection

This (optional) step can detect two types of artifact:

- saturation artifacts, detected before preprocessing
- other artifacts detected after high-pass filtering (e.g. envelope).

see [`detect_and_remove_artifacts()`](https://spikeinterface.readthedocs.io/en/latest/api.html#spikeinterface.preprocessing.detect_and_remove_artifacts) for details.

These detected periods are used in [Preprocessing](#preprocessing) to zero or otherwise remove the periods. 

**Inputs**

- a {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>`
- a {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`
- a {ref}`OUTPUT_PATH <outputs-output-path>`

**Outputs**

- an {ref}`ARTEFACT_PERIODS_CSV <outputs-artefact-periods-csv>`, saved to `ARTIFACT_DETECTION_DIR`
- {ref}`ARTEFACT_DETECTION_PLOTS <outputs-artefact-detection-plots>`

**OPERATIONS**:

- Load the recording from the passed {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>`.
- Detect saturation artifacts before preprocessing.
- Detect other configured artifact classes after the required filtering steps. Use the filtering step from the passed `PIPELINE_CONFIG`.
- Save detected periods to `ARTIFACT_DETECTION_DIR` as {ref}`ARTEFACT_PERIODS_CSV <outputs-artefact-periods-csv>`.

**CHECKS**:

- Confirm that artifact detection settings match the recording type and sampling rate.
- Warn when no artifact class can be evaluated because the required filtered view of the recording is unavailable.

## Artifact curation

This (optional) stepprovides the user with the option to curate the automatically detected artifacts. This step is not automated, and typically more hands-on and requires a dedicated walkthrough in the documentation. It will entail the user loading their data into viewephys (applying the preprocessing beforehand as desired).

**Inputs**

- a {ref}`RAW_DATA_PATH <definitions-raw-data-path>` or {ref}`SPIKEINTERFACE_REC <definitions-spikeinterface-rec>`
- an {ref}`ARTEFACT_PERIODS_CSV <outputs-artefact-periods-csv>`
- a {ref}`OUTPUT_PATH <outputs-output-path>`

**Outputs**

- an {ref}`ARTEFACT_PERIODS_CURATED_CSV <outputs-artefact-periods-curated-csv>`, saved to `ARTIFACT_DETECTION_DIR`

**OPERATIONS**:

- Load the automatically detected artifact periods alongside the recording in a manual curation tool.
- Review, add, remove, or adjust artifact intervals.
- Save the curated artifact intervals back to `ARTIFACT_DETECTION_DIR`.

**CHECKS**:

- Confirm that the curated intervals refer to the same recording and time base as the detected intervals.
- Preserve the original automatically detected artifact file so manual curation remains auditable.

## Preprocessing

Preprocesses recordings, supporting: 

- Bad channel removal or interpolation (interpolation after filtering).
- Phase shift correction.
- TEMPORAL_FILTER steps 
- Artifact period filling with zeros, noise, or another configured strategy.
- - COMMON_REFERENCE steps
- Motion correction.
- Inter-session alignment
- Session concatenation
- Whitening.

This can get quite complicated if we have both multiple shanks and sessions, when 
this step concatenates across sessions. It should check that all passed shanks are available for all sessions (should they be concatenated). It will also need to handle taking the intersection of good channels, in this case.


**Inputs**

-   {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>`
- a {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`
- a {ref}`OUTPUT_PATH <outputs-output-path>`
- a `concatenate_sessions` flag. If `True`, sessions will be concatenated after preprocessing.

*Loaded from disk:*

- (optional) {ref}`ARTEFACT_PERIODS_CSV <outputs-artefact-periods-csv>` or {ref}`ARTEFACT_PERIODS_CURATED_CSV <outputs-artefact-periods-curated-csv>`
- (optional) {ref}`BAD_CHANNEL_DETECTION_OUTPUTS <outputs-bad-channel-detection-outputs>`

:::{warning}
Event periods and bad channel labels must match the organization of the passed recordings, which may be organized on disk [per shank and per session](on-disk-structure.md) when required.
:::

**Outputs**

- {ref}`PREPROCESSED_OUTPUT_RECORDINGS <definitions-preprocessed-output-recordings>`.
- {ref}`PREPROCESS_STEP_PLOTS <outputs-preprocess-step-plots>`
- {ref}`MOTION_CORRECTION_PLOTS <outputs-motion-correction-plots>`
- {ref}`INTER_SESSION_ALIGNMENT_PLOTS <outputs-session-concatenation-plots>`
- {ref}`SESSION_CONCATENATION_PLOTS <outputs-session-concatenation-plots>`

**OPERATIONS**:

- Load the recording from the passed {ref}`DATA_LOADER_OUTPUT_RECORDINGS <definitions-data-loader-output-recordings>`.
- Apply the configured preprocessing steps in sequence.
- for artefact removal, bad channel removal / interpolation the user can input where to do this on the config file. However, we should warn or error if is not done in the correct place (e.g. bad channel interpolate before filtering).
- Return or save the preprocessed recording in `PREPROCESSING_DIR`, depending on configuration.
- If the user requests, perform inter-session alignment on multiple sessions before (optionally) concatenating. If sessions are concatenated, update the recording attribute to indicate this and write appropriate metadata. Ensure the same set of channels across sessions when concatenating (detect bad channels). Use the intersection of available channels.
- Need to remove bad channels at the start, but interpolate after filtering.

**CHECKS**:

- Warn when recordings intended for multi-session processing do not share compatible channel sets or sampling rates. 
- per-shank and per-session organisation must be consistent on disk and match passed recordings.
- Apply phase-shift correction only when the probe supports it.
- Do not re-run whitening or motion correction in the sorter if already run through SpikeInterface preprocessing.
- Warn when high-density-specific methods, such as motion correction or detect-bad-channels methods, are used on 32- or 64-channel recordings.

## Spike sorting

The spike sorting step, made very simple thanks to SpikeInterface:

**Inputs**

- a {ref}`SPIKEINTERFACE_REC <definitions-spikeinterface-rec>` or {ref}`SPIKEINTERFACE_REC_SESSION_LIST <definitions-spikeinterface-rec-session-list>`,
  OR a {ref}`OUTPUT_PATH <outputs-output-path>` containing a `PREPROCESSING_DIR` with saved recording.
- a {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`
- a {ref}`OUTPUT_PATH <outputs-output-path>` containing a `PREPROCESSING_DIR`. This is used to store outputs and cross-check the metadata of the passed recording to the on-disk project.

**Outputs**

- a {ref}`SORTING <definitions-sorting>` and other sorting metadata.
- {ref}`SORTER_REPORT <definitions-sorter-report>`, corresponding to the SpikeInterface sorting report.

**OPERATIONS**:

- Load the preprocessed recording from memory or from the preprocessing output directory.
- Run the configured sorter on the prepared recording.
- Save the resulting sorting and associated metadata to `SORTING_DIR`.

**CHECKS**:

- Confirm that the passed recording matches any saved preprocessing metadata in the project.
- Avoid rerunning preprocessing-dependent steps in the sorter when they were already applied upstream.

## Postprocessing

Postprocessing computes unit quality metrics used for curation.

**Inputs**

- a {ref}`SPIKEINTERFACE_REC <definitions-spikeinterface-rec>` or {ref}`SPIKEINTERFACE_REC_SESSION_LIST <definitions-spikeinterface-rec-session-list>`,
  OR a {ref}`OUTPUT_PATH <outputs-output-path>` containing a `PREPROCESSING_DIR` with saved recording.
- a {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`
- a {ref}`OUTPUT_PATH <outputs-output-path>`

**Outputs**

- a {ref}`SORTING_ANALYZER <definitions-sorting-analyzer>` saved to disk as well as:
  - {ref}`POSTPROCESSING_PLOTS <definitions-postprocessing-plots>`
  - {ref}`QUALITY_METRICS_CSV <outputs-quality-metrics-csv>` and other metadata.

**OPERATIONS**:

- Load the sorting output together with the matching recording.
- Compute the configured postprocessing extensions and quality metrics.
- Save the resulting analyzer, plots, metrics, and metadata to `POSTPROCESSING_DIR`.

**CHECKS**:

- Must ensure the passed recording is the same recording used for sorting.
- Confirm that all required postprocessing extensions are computed before downstream curation methods rely on them.

## Curation

The curation step computes labels and merges automatically (e.g. with Bombcell, UnitRefine, SlaY) and applies them to the sorting analyzer, creating a new final sorting analyzer which services as the output of the pipeline.

**Inputs**

- a {ref}`OUTPUT_PATH <outputs-output-path>` containing a `POSTPROCESSING_DIR` with a saved {ref}`SORTING_ANALYZER <definitions-sorting-analyzer>`
- a {ref}`PIPELINE_CONFIG <outputs-pipeline-config>`

**Outputs**

- a {ref}`SORTING_ANALYZER <definitions-sorting-analyzer>` and associated metadata.

**OPERATIONS**:

- Load the postprocessing analyzer from the project.
- Apply configured automatic labeling, merge, and removal rules.
- Recompute any dependent analyzer extensions required after accepted merges.
- Save the final curated analyzer and metadata to `CURATION_DIR`.
