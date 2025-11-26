# wildfire-analyser

Python project for analyzing wildfires in natural reserves.

## Installation and Usage

Follow the steps below to install and test `wildfire-analyser` inside an isolated environment:

```bash
mkdir /tmp/test
cd /tmp/test

python3 -m venv venv
source venv/bin/activate

pip install wildfire-analyser
```

### Required Files Before Running the Client

Before running the client, you **must** prepare two items:

---

#### **1. Add a GeoJSON polygon**

Create a folder named `polygons` in the project root and place your ROI polygon file inside it:

```
/tmp/test/
├── polygons/
│   └── your_polygon.geojson
└── venv/
```

An example GeoJSON file is available in the repository.

---

#### **2. Create the `.env` file with GEE authentication data**

In the project root, add a `.env` file containing your Google Earth Engine authentication variables.

A `.env` template is also available in the GitHub repository.

```
/tmp/test/
├── .env
├── polygons/
└── venv/
```

---

### Running the Client

After adding the `.env` file and your GeoJSON polygon:

```bash
python3 -m wildfire_analyser.client
```

This will start the analysis process, generate the configured deliverables, and save the output files in the current directory.



## Setup Instructions for Developers

1. **Clone the repository**

```bash
git clone git@github.com:camargo-advanced/wildfire-analyser.git
cd wildfire-analyser
```

2. **Create a virtual environment**

```bash
python3 -m venv venv
```

3. **Activate the virtual environment**

```bash
source venv/bin/activate
```

4. **Install dependencies**
   Make sure the virtual environment is activated, then run:

```bash
pip install -r requirements.txt
```

5. **Configure environment variables**
   Copy your version of `.env` file to the root folder with your GEE authentication credentials. A template file `.env.template` is provided as an example.

6. **Run the sample client application**

```bash
python3 -m wildfire_analyser.client
```

## Useful Commands

* **Deactivate the virtual environment**:

```bash
deactivate
```
