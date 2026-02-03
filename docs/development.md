# Development Setup

This document describes how to set up a **local development environment**
for the `wildfire-analyser` project.

These instructions are intended for **developers and contributors**.
End users should refer to the main `README.md` for installation and usage
via PyPI.

---

## Repository Overview

`wildfire-analyser` is a Python project for **post-fire assessment and burned
area analysis** using **Sentinel-2 imagery** and **Google Earth Engine (GEE)**.

The project implements a reproducible, dependency-driven processing pipeline
that produces:

- Scientific raster products (GeoTIFF)
- Visual preview products (JPEG thumbnails)
- Burned area statistics (paper-ready tables)

---

## Setup Instructions for Developers

### 1. Clone the repository

```bash
git clone git@github.com:Brazil-Flying-Labs/wildfire-analyser.git
cd wildfire-analyser
````

---

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

---

### 3. Activate the virtual environment

```bash
source venv/bin/activate
```

---

### 4. Install development dependencies

Install all dependencies required for local development and testing:

```bash
pip install -r requirements.txt
```

---

### 5. Configure environment variables

Create a `.env` file in the project root containing your
Google Earth Engine credentials and optional configuration.

A `.env.template` file is provided in the repository as a reference.

Example structure:

```text
.env
polygons/
venv/
```

Required variables:

* `GEE_PRIVATE_KEY_JSON` — Google Earth Engine service account credentials
* `GCS_BUCKET_NAME` — Google Cloud Storage bucket for scientific exports (optional)

---

### 6. Prepare a Region of Interest (ROI)

Add one or more GeoJSON polygon files under the `polygons/` directory.

Example:

```text
polygons/
├── canakkale_aoi_1.geojson
└── canakkale_aoi_2.geojson
```

These files define the spatial extent of the analysis.

---

### 7. Run the CLI locally

Run the main command-line interface in development mode:

```bash
python3 -m wildfire_analyser.cli \
  --roi polygons/canakkale_aoi_1.geojson \
  --start-date 2023-07-01 \
  --end-date 2023-07-21 \
  --deliverables \
    DNBR_VISUAL \
    DNBR_AREA_STATISTICS \
  --days-before-after 0
```

---

## Deliverables Overview

Deliverables are grouped into three categories:

### Scientific products (GeoTIFF)

These trigger Google Earth Engine export tasks:

* `RGB_PRE_FIRE`
* `RGB_POST_FIRE`
* `NDVI_PRE_FIRE`
* `NDVI_POST_FIRE`
* `NBR_PRE_FIRE`
* `NBR_POST_FIRE`
* `DNDVI`
* `DNBR`
* `RBR`

---

### Visual products (JPEG thumbnails)

These generate preview URLs via GEE thumbnails:

* `RGB_PRE_FIRE_VISUAL`
* `RGB_POST_FIRE_VISUAL`
* `DNDVI_VISUAL`
* `DNBR_VISUAL`
* `RBR_VISUAL`

---

### Burn severity statistics

These compute burned area statistics in hectares and percentage:

* `DNBR_AREA_STATISTICS`
* `DNDVI_AREA_STATISTICS`
* `RBR_AREA_STATISTICS`

---

## Paper Preset Mode

The CLI supports **paper presets**, which are predefined configurations
designed to reproduce published scientific results.

Example:

```bash
python3 -m wildfire_analyser.cli \
  --deliverables PAPER_DENIZ_FUSUN_RAMAZAN
```

This preset:

* Executes multiple runs
* Uses paper-aligned temporal windows
* Produces only visual outputs and statistics
* Skips scientific GeoTIFF exports
* Prints results grouped by study area

---

## Useful Commands

### Deactivate the virtual environment

```bash
deactivate
```

---

Claro — ajustei o texto para **inglês correto, tom profissional e padrão de projeto Python**, mantendo simples e claro.

---

### Build and publish a new PyPI release

> This step is intended for project maintainers only.

1. **Ensure your PyPI credentials are properly configured**
   (for example, using `~/.pypirc`).

2. **Update the project version** in `pyproject.toml`.

3. **Build the distribution packages:**

```bash
rm -rf dist/*
python -m build
```

4. **Upload the packages to PyPI:**

```bash
twine upload dist/*
```

---

## Citation

If you use this software for scientific or academic work, please cite:

> *Spatial and statistical analysis of burned areas with Landsat-8/9 and
> Sentinel-2 satellites: 2023 Çanakkale forest fires*
> Deniz Bitek, Fusun Balik Sanli, Ramazan Cuneyt Erenoglu.

Please also cite this repository as the reference implementation.

---

## License

This project is released under the **MIT License**.
See the `LICENSE` file for details.

