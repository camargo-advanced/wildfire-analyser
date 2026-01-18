## 🔧 Task Monitoring for Scientific Deliverables (Asynchronous Mode)

Scientific deliverables (GeoTIFF exports) are generated in **Google Earth Engine as asynchronous tasks**.
This allows frontend applications and external systems to:

* Request a single scientific deliverable on demand.
* Avoid blocking user interfaces.
* Monitor processing progress independently.
* Notify users when results are ready (e.g. via email).

The `wildfire-analyser` library exposes the **GEE task ID** for each scientific export, enabling this workflow.

---

## 1. Requesting a Scientific Deliverable

To request a **single scientific deliverable** (for example, `DNBR`):

```bash
python3 -m wildfire_analyser.client \
  --roi polygons/canakkale_aoi_1.geojson \
  --start-date 2023-07-01 \
  --end-date 2023-07-21 \
  --deliverables DNBR \
  --days-before-after 1
```

### Example output

```text
Scientific outputs:
  DNBR -> https://storage.googleapis.com/your-bucket/dnbr_2023_07_01_2023_07_21_20260118T141712_455cf071.tif
         (gee_task_id=GWPUZIDAD4TGMXCLWOJNBRFT)
```

### Important notes

* The file **may not exist yet** when the URL is printed.
* The export runs asynchronously in Google Earth Engine.
* The `gee_task_id` uniquely identifies the export task.
* This task ID can be used by another process to monitor completion.

---

## 2. Monitoring a Google Earth Engine Task

The project provides a **standalone task monitor** that can be run independently from the client.

This is intended to be executed by:

* a background worker.
* a container job.
* a backend service triggered by the frontend.

### Command

```bash
python3 -m wildfire_analyser.gee_task_monitor \
  --gee-task-id GWPUZIDAD4TGMXCLWOJNBRFT \
  --deliverable DNBR \
  --user-email user@email.com
```

### What this does

* Authenticates using the same `.env` credentials as the client.
* Polls the Google Earth Engine task status.
* Blocks until the task reaches a terminal state.
* Exits successfully when the task is **COMPLETED**.
* Raises an error if the task **FAILED** or was **CANCELLED**.

### Example output

```text
[GEE] task=GWPUZIDAD4TGMXCLWOJNBRFT state=RUNNING
[GEE] task=GWPUZIDAD4TGMXCLWOJNBRFT state=RUNNING
[GEE] task=GWPUZIDAD4TGMXCLWOJNBRFT state=COMPLETED
Deliverable 'DNBR' completed.
User: user@email.com
Email sending not implemented yet.
```

---

## 3. Intended Architecture (Frontend / Backend)

This design supports a clean, scalable architecture:

```text
Frontend
  |
  | 1. User requests scientific deliverable
  |
Backend / API
  |
  | 2. Calls wildfire-analyser client
  | 3. Receives gee_task_id
  |
Frontend
  |
  | 4. Starts background worker (or container)
  |
Task Monitor
  |
  | 5. Polls GEE task status
  | 6. (Optional) sends notification when completed
```

### Key design principles

* No polling inside the main analysis pipeline.
* No frontend dependency on Google Earth Engine APIs.
* Stateless workers.
* Compatible with containers, batch jobs, or Cloud Run.
* Suitable for production-scale workflows.

---

## 4. Notes for Developers

* The task monitor uses `ee.data.getTaskStatus`, the **official and supported** API for tracking existing GEE tasks.
* Authentication is performed via **service account credentials** using the same `.env` file as the main client.
* Email notification is intentionally **not implemented** in the example and can be added externally.