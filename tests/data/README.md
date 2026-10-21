# Dataset provenance

## Download the example recording

From the repository root, in your environment with SpikeInterface and its
SpikeGLX reader dependencies (`neo` and `probeinterface`) installed, run:

```sh
python tests/data/fetch_test_data.py
```

The committed `manifest.json` pins two raw Neuropixels files (11.6 MB) to an
upstream commit and verifies their sizes and SHA-256 checksums. The downloader
saves the first shank as `neuropixels-2010-spikeglx/si_recording`, which both
example scripts load. This is a 192-channel, 0.5-second recording.

Valid downloads and converted recordings are reused. Missing or changed
converted files cause the derived recording to be rebuilt. Downloaded files,
the derived recording, and the generated `inventory.json` are Git-ignored.
Verify a completed download and conversion without network access with:

```sh
python tests/data/fetch_test_data.py --verify-only
```

Run this setup on shared cluster storage before running `examples/slurm_example.py`.
The manifest currently covers only the Neuropixels example below; the other
datasets are historical provenance entries and are not downloaded by this command.

- **neuropixels-2010-spikeglx** (NP2010, Neuropixels 2.0): Neuropixels 2.0 recordings by Steve Lenzi (Sainsbury Wellcome Centre), clipped to 0.5 s by Joe Ziminski; from [spikewrap](https://github.com/neuroinformatics-unit/spikewrap/tree/a40a9df2cdb473c3bbf6ad7e6be961e2da328734).
- **neuropixels-1300-openephys** (NP1300, Neuropixels Opto): recorded by Sue Su (Allen Institute), clipped to 1,000 samples by Alessio Buccino; from [Neo fixtures](https://gin.g-node.org/NeuralEnsemble/ephy_testing_data/src/master/openephysbinary), via spikewrap. The second recording duplicates the first.
- **no-probe-openephys:** four 0.5 s, 16-channel recordings supplied by Alessio Buccino; Neo fixture `v0.5.x_two_nodes`, via spikewrap.
- **cambridge-neurotech-64:** first 90 s of a 64-channel mouse postsubiculum recording from [DANDI 000939](https://dandiarchive.org/dandiset/000939), associated with [Duszkiewicz et al. (2024)](https://doi.org/10.1038/s41593-024-01588-5). Obtained from the [OSSS course Zenodo record](https://zenodo.org/records/21908762), prepared by Joseph Ziminski and Chris Halcrow; CC BY 4.0.

The raw example files are preserved unchanged; the conversion selects the first
shank without filtering. Exact source URLs and checksums are in `manifest.json`;
`inventory.json` additionally records checksums of the locally generated files.
