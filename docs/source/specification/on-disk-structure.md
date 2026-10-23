# Project Structure

The pipeline stores outputs in a project directory so that each step can be run independently and downstream steps can discover and validate earlier outputs.

The planned output directory has the following structure:

:::{note}
## Output layout

```text
output/
├── raw_data_metrics/
│   ├── raw_data_quality_metrics.csv
│   ├── raw_data_quality_plots/
│   │   └── ...
│   ├── bad_channel_ids.csv
│   └── bad_channel_labels.csv
├── artifact_detection/
│   └── event_periods.csv              # or event_periods_curated.csv
├── preprocessing/
│   ├── metadata.*
│   ├── preprocessing_plots/
│   └── recording/                     # optional, depending on PIPELINE_CONFIG
├── sorting/
│   ├── sorting/
│   └── metadata.*
├── postprocessing/
│   ├── sorting_analyzer/
│   ├── quality_metrics.csv
│   ├── postprocessing_plots/
│   │   └── *.png
│   └── metadata.*
└── curation/
    ├── sorting_analyzer/
    ├── curation_decisions.*
    └── metadata.*
```

`*`
: Storage format has not yet been specified.

**Optional outputs**
: Created only when enabled in the [`PIPELINE_CONFIG`](config.md). Artifact detection may pause for manual curation and produce `event_periods_curated.csv`.
:::

## Raw data metrics with sessions and shanks

For two sessions with four shanks each, the raw data metrics directory is organized as follows:

```text
raw_data_metrics/
├── session_1/
│   ├── shank_1/
│   │   ├── raw_data_quality_metrics.csv
│   │   └── raw_data_quality_plots/
│   │       └── ...
│   ├── shank_2/
│   │   ├── raw_data_quality_metrics.csv
│   │   └── raw_data_quality_plots/
│   │       └── ...
│   ├── shank_3/
│   │   ├── raw_data_quality_metrics.csv
│   │   └── raw_data_quality_plots/
│   │       └── ...
│   └── shank_4/
│       ├── raw_data_quality_metrics.csv
│       └── raw_data_quality_plots/
│           └── ...
└── session_2/
    ├── shank_1/
    │   ├── raw_data_quality_metrics.csv
    │   └── raw_data_quality_plots/
    │       └── ...
    ├── shank_2/
    │   ├── raw_data_quality_metrics.csv
    │   └── raw_data_quality_plots/
    │       └── ...
    ├── shank_3/
    │   ├── raw_data_quality_metrics.csv
    │   └── raw_data_quality_plots/
    │       └── ...
    └── shank_4/
        ├── raw_data_quality_metrics.csv
        └── raw_data_quality_plots/
            └── ...
```
