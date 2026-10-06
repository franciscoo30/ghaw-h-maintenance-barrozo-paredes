---
license: cc-by-4.0
citation: |
  @dataset{valenzuela_toledo_ghaw_h_2026,
    author    = {Valenzuela-Toledo, Pablo and Kehrer, Timo and Panichella, Sebastiano},
    title     = {{GHAW-H}: A Dataset of GitHub Agentic Workflow Histories},
    year      = {2026},
    publisher = {Zenodo},
    version   = {v0.1.2},
    doi       = {10.5281/zenodo.22084012},
    url       = {https://doi.org/10.5281/zenodo.22084012}
  }
configs:
- config_name: lock_file_snapshot
  data_files:
  - split: data
    path: data/lock_file_snapshot.parquet
- config_name: repository
  data_files:
  - split: data
    path: data/repository.parquet
- config_name: source_markdown_file_history
  data_files:
  - split: data
    path: data/source_markdown_file_history.parquet
- config_name: source_markdown_file_snapshot
  data_files:
  - split: data
    path: data/source_markdown_file_snapshot.parquet
- config_name: source_markdown_file_version
  data_files:
  - split: data
    path: data/source_markdown_file_version.parquet
---

# GHAW-H: GitHub Agentic Workflow Histories

<img src="docs/logo/early_adopters.png" alt="Early adopters logo" width="500" height="400">

## Overview

GHAW-H is a dataset capturing the emergence of GitHub Agentic Workflows (GH-AW) among early-adopter open-source repositories. This release spans 262 repositories, 2820 observed GH-AW source markdown file snapshots, 2820 source-version records across 604 file histories, and 2820 associated lock-file snapshots.

Public documentation, executable notebooks, schema material, and the project website are available in the [GHAW-H companion repository](https://github.com/pavt/GHAW-H) and at [pavt.github.io/GHAW-H](https://pavt.github.io/GHAW-H/).

## GitHub Agentic Workflows Challenge at NLBSE 2027

GHAW-H is the dataset for the GitHub Agentic Workflows Challenge hosted at [NLBSE 2027](https://nlbse2027.github.io/), the 6th International Workshop on Natural Language-based Software Engineering, co-located with [ICSE 2027](https://conf.researchr.org/home/icse-2027) in Dublin, Ireland. Researchers and practitioners are invited to study natural-language agentic workflow specifications, their compiled GitHub Actions workflows, and their evolution in public repositories.

| Milestone | Date |
| --- | --- |
| Paper submission | November 13, 2026 |
| Author notification | December 11, 2026 |
| Camera-ready | January 29, 2027 |

All deadlines are Anywhere on Earth (AoE).

[Read the full challenge call →](https://pavt.github.io/GHAW-H/calls/nlbse-2027-ghaw-challenge/)

## Quick Look

The overview of the GHAW-H dataset is as follows:

| Dataset | #Repo | #Source Histories | #Source Versions | #Lock Snapshots |
| --- | ---: | ---: | ---: | ---: |
| GHAW-H | 262 | 604 | 2,820 | 2,820 |

<a href="data_analysis/figs/gawd_cumulative_all_repositories.pdf"><img src="data_analysis/figs/gawd_cumulative_all_repositories.png" alt="Cumulative observed GH-AW adoption by repository" width="720"></a>

<a href="data_analysis/figs/gawd_cumulative_language_usage.pdf"><img src="data_analysis/figs/gawd_cumulative_language_usage.png" alt="Cumulative observed GH-AW adoption by repository language" width="720"></a>

## Intended Uses

Pending.

## Dataset Schema

![Dataset Schema](docs/gh-aw-er-v0.1.svg)

A detailed explanation about the fields of the tables can be found in [Tables dictionary](docs/table_dictionary.md).


## Example Notebooks

These notebooks are included with the release and can be run from the release package or opened in Colab from the project repository.

| Description | Notebook Link | Open in Colab |
| --- | --- | --- |
| Basic dataset loading | [load_GAWD.ipynb](data_analysis/load_GAWD.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pavt/GHAW-H/blob/main/notebooks/load_GAWD.ipynb) |
| Dataset overview | [dataset_overview.ipynb](data_analysis/dataset_overview.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pavt/GHAW-H/blob/main/notebooks/dataset_overview.ipynb) |
| Analysis of repository language usage | [language_usage.ipynb](data_analysis/language_usage.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pavt/GHAW-H/blob/main/notebooks/language_usage.ipynb) |
| Analysis enabled by file-version histories | [history_data.ipynb](data_analysis/history_data.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pavt/GHAW-H/blob/main/notebooks/history_data.ipynb) |


## License

This dataset aggregates content from GitHub repositories. Each source repository retains its original copyright and license (e.g., MIT, Apache-2.0, GPL family, Creative Commons variants, etc.). Files, histories, and any other artifacts originating from those repositories remain governed by their original licenses.

Users must verify and comply with the specific license of any source repository or file they extract or use from this collection. Do not assume a universal re-license. If you believe content appears here in a way that conflicts with its license, please contact the maintainers, and it will be removed.

## Citation

Please cite the archived GHAW-H v0.1.2 dataset release:

> Valenzuela-Toledo, P., Kehrer, T., & Panichella, S. (2026). *GHAW-H: A Dataset of GitHub Agentic Workflow Histories* (Version v0.1.2) [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.22084012

```bibtex
@dataset{valenzuela_toledo_ghaw_h_2026,
  author    = {Valenzuela-Toledo, Pablo and Kehrer, Timo and Panichella, Sebastiano},
  title     = {{GHAW-H}: A Dataset of GitHub Agentic Workflow Histories},
  year      = {2026},
  publisher = {Zenodo},
  version   = {v0.1.2},
  doi       = {10.5281/zenodo.22084012},
  url       = {https://doi.org/10.5281/zenodo.22084012}
}
```
