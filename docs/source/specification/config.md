# Config

The configuration file defines the pipeline to be run. This makes it standardized and easy to share.

## Example config

```yaml
bad_channel_detection:
  method: 'coherence+psd'
```

## `bad_channel_detection`

See [`detect_bad_channels`](https://spikeinterface.readthedocs.io/en/latest/api.html#spikeinterface.preprocessing.detect_bad_channels) for a list of valid arguments.

The `neighborhood_r2` method is not supported by the SpikeSorted pipeline and is rejected as an input.
