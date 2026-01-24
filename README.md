<!--
SPDX-License-Identifier: MIT

wildfire-analyser
=================

An open-source Python pipeline for post-fire assessment and burned area
analysis using Sentinel-2 imagery and Google Earth Engine (GEE).

This project provides a reproducible, automated workflow for computing
fire-related spectral indices, generating visual products, and producing 
burned area statistics for scientific and operational use.

The library is designed with a clear separation between:
- Scientific computation (core library)
- Dependency-driven execution (DAG)
- Command-line interfaces (CLI tools)

Copyright (C) 2025
Marcelo Camargo.

Licensed under the MIT License. See the LICENSE file for details.
-->

## Project Architecture (Overview)

The wildfire-analyser project is organized into three conceptual layers:

- **Core library (`fire_assessment`)**  
  Implements scientific computation, dependency resolution, and Earth Engine logic.

- **Execution layer (DAG)**  
  Automatically resolves and executes dependencies required for each deliverable.

- **Command-line interfaces (CLI)**  
  User-facing tools for running analyses and monitoring Earth Engine tasks.

## Outputs

All generated outputs (GeoTIFFs, thumbnails, statistics) are considered
runtime artifacts and are not committed to version control.

## Scientific Background

This project is **based on the peer-reviewed study**:

> **Spatial and statistical analysis of burned areas with Landsat-8/9 and Sentinel-2 satellites: 2023 Çanakkale forest fires**
> **Authors:** Deniz Bitek, Fusun Balik Sanli, Ramazan Cuneyt Erenoglu
> **Study area:** Çanakkale Province, Turkey

The methodology implemented in `wildfire-analyser` follows the **same analytical framework and burn severity thresholds** described in the paper, particularly for the **Sentinel-2–based analysis**, including:

* dNBR, dNDVI and RBR indices
* Burn severity classification tables
* Area statistics in hectares and percentage

Minor numerical differences may occur due to cloud masking, spatial sampling, and Google Earth Engine implementation details.

---

## Installation and Usage

Follow the steps below to install and test `wildfire-analyser` inside an isolated environment:

```bash
mkdir test
cd test

python3 -m venv venv
source venv/bin/activate

pip install wildfire-analyser
```
---

## Required Files Before Running the Client

Before running the client, you **must** prepare the following items:

---

### 1. Add a GeoJSON polygon (ROI)

Create a folder named `polygons` in the project root and place your ROI polygon file inside it:

```
/tmp/test/
├── polygons/
│   └── your_polygon.geojson
└── venv/
```

Example GeoJSON files are available in the repository (e.g. `canakkale_aoi_1.geojson`).

---

### 2. Create the `.env` file with GEE credentials

In the project root, add a `.env` file containing your Google Earth Engine authentication variables.

A `.env.template` file is available in the repository.

```
/tmp/test/
├── .env
├── polygons/
└── venv/
```

---

## Running the Client (Standard Mode)

After adding the `.env` file and your GeoJSON polygon:

```bash
python3 -m wildfire_analyser.cli \
  --roi polygons/canakkale_aoi_1.geojson \
  --start-date 2023-07-01 \
  --end-date 2023-07-21 \
  --deliverables \
    DNBR_VISUAL \
    DNDVI_VISUAL \
    RBR_VISUAL \
    DNBR_AREA_STATISTICS \
    DNDVI_AREA_STATISTICS \
    RBR_AREA_STATISTICS \
  --days-before-after 0

```

This will:

* Run the post-fire assessment pipeline
* Generate **visual thumbnail URLs**
* Generate **scientific GeoTIFF outputs** (when applicable)
* Compute **burned area statistics**
* Print all results to the terminal

---

## Deliverables

You may explicitly select deliverables using `--deliverables`.

### Scientific products

* `RGB_PRE_FIRE`
* `RGB_POST_FIRE`
* `NDVI_PRE_FIRE`
* `NDVI_POST_FIRE`
* `NBR_PRE_FIRE`
* `NBR_POST_FIRE`
* `DNDVI`
* `DNBR`
* `RBR`

### Visual products

* `RGB_PRE_FIRE_VISUAL`
* `RGB_POST_FIRE_VISUAL`
* `DNDVI_VISUAL`
* `DNBR_VISUAL`
* `RBR_VISUAL`

### Severity maps and statistics

* `DNBR_AREA_STATISTICS`
* `DNDVI_AREA_STATISTICS`
* `RBR_AREA_STATISTICS`

Example:

```bash
python3 -m wildfire_analyser.cli \
   --roi polygons/canakkale_aoi_1.geojson \
   --start-date 2023-07-01 \
   --end-date 2023-07-21 \
   --deliverables DNBR_VISUAL DNBR_AREA_STATISTICS \
```

If `--deliverables` is **not provided**, **all available deliverables** are generated.

---

## Paper Preset Mode (Reproducibility)

The client also supports **paper presets**, which are predefined experimental configurations designed to reproduce published results.

### Example preset: `PAPER_DENIZ_FUSUN_RAMAZAN`

Run:

```bash
python3 -m wildfire_analyser.cli \
  --deliverables PAPER_DENIZ_FUSUN_RAMAZAN
```

This preset:

* Executes the analysis for **two distinct burned areas**
* Uses **paper-aligned temporal windows**
* Generates **only visual outputs and statistics**
* Does **not export scientific GeoTIFFs**
* Prints results **grouped by area**

Internally, it runs:

| Area   | ROI                       | Pre-fire   | Post-fire  |
| ------ | ------------------------- | ---------- | ---------- |
| Area 1 | `canakkale_aoi_1.geojson` | 2023-07-01 | 2023-07-21 |
| Area 2 | `canakkale_aoi_2.geojson` | 2023-07-31 | 2023-08-30 |

---

## Help

For help and full usage information:

```bash
python3 -m wildfire_analyser.cli --help
```

## Additional Documentation 

The following documents provide more detailed and advanced guidance for
development, environment setup, and asynchronous processing workflows.
They are not required if the environment is already configured, but are
recommended for first-time setup, developers, and production deployments.

* **Development Guide**
  Internal architecture, project conventions, and contribution guidelines.
  [`docs/development.md`](docs/development.md)

* **Environment & Credentials Setup**
  Step-by-step instructions for configuring Google Earth Engine,
  service accounts, environment variables, and Cloud Storage.
  [`docs/environment-setup.md`](docs/environment-setup.md)

* 🔧 **Asynchronous GEE Task Monitoring**
  Detailed explanation of asynchronous scientific exports, `gee_task_id`
  handling, and task monitoring using the standalone CLI tool.
 [`docs/gee_task_monitoring.md`](docs/gee_task_monitoring.md)

---

### When to read these documents

* Read **environment-setup.md** before running the pipeline in a new system.
* Read **gee_task_monitoring.md** when integrating with frontend/backend
  architectures or background workers.
* Read **development.md** if you plan to modify or extend the codebase.
---