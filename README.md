# wildfire-analyser

Python project for analyzing wildfires in natural reserves.

## 📦 Installing the wildfire-analyser library

You can install the library directly from PyPI:

```bash
pip install wildfire-analyser
```

After installation, you can import and use the main classes normally:

```python
from wildfire_analyser import PostFireAssessment, Deliverable, FireSeverity
```

To use the example client included in the package, run:

```bash
python3 -m wildfire_analyser.client
```

Make sure your environment includes the required credentials (e.g., `.env` file) before running the client.

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
