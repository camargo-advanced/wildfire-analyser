# Step-by-Step Guide: Creating a Service Account for GEE Code + Creating a Bucket and Assigning Required Permissions

This guide explains, step by step, how to:

1. Create a **Google Cloud project** (if you don’t already have one).
2. Create a **service account** to authenticate Python/Node code that uses Google Earth Engine (GEE).
3. Generate a **JSON key** for the service account.
4. Create a **Google Cloud Storage (GCS) bucket**.
5. Assign the **required permissions** so the service account can **write to the bucket** using GEE export tasks (e.g., `Export.image.toCloudStorage`).
6. (Optional but recommended) Configure a **lifecycle rule** to delete files every 24 hours.

> Note: This guide assumes you already have a Google account with access to Google Cloud and Google Earth Engine.

---

## 1. Create (or choose) a Google Cloud Project

1. Go to:  
   https://console.cloud.google.com/

2. At the top of the page, open the project selector.

3. You may:
   - **Use an existing project**, or  
   - Click **“New Project”** and create one:
     - Name example: `wildfire-assessment-geospatial`
     - Choose the appropriate organization (if applicable)
     - Click **Create**

4. Make sure the project is selected (visible in the top bar).

---

## 2. Enable the Required APIs

Inside your selected project:

1. Go to **APIs & Services** → **Library**
2. Enable the following APIs:
   - **Earth Engine API**
   - **Cloud Storage JSON API**

Both are required for scripts that use GEE and export data to Cloud Storage.

---

## 3. Create the Service Account (for your GEE code)

1. Navigate to:  
   **IAM & Admin** → **Service Accounts**

2. Click **“Create Service Account”**

3. Fill out the form:
   - **Service account name**: e.g., `gee-service-account`
   - **Description**: “Service account for Google Earth Engine scripts”
   - The service account email will look like:  
     `gee-service-account@wildfire-assessment.iam.gserviceaccount.com`

4. Click **Create and Continue**

5. Assign basic roles such as:
   - `Viewer` (or `Project Viewer`)

6. Click **Continue** → **Done**

Keep the service account email handy—we will use it to assign bucket permissions.

---

## 4. Create a JSON Key for the Service Account

1. In **IAM & Admin** → **Service Accounts**, click on the service account you created.

2. Open the **Keys** tab.

3. Click **“Add Key”** → **“Create new key”**

4. Choose:
   - **JSON**

5. Click **Create**  
   A `.json` key file will be downloaded, e.g.:
   `wildfire-assessment-gee-service-account.json`

> **Important:**  
> - Keep this file secure.  
> - **Never** upload it to a public repository.

---

## 5. Create a Cloud Storage Bucket

1. Go to:  
   https://console.cloud.google.com/storage/browser

2. Click **“Create Bucket”**

3. Configure:
   - **Bucket name**: e.g., `post-fire-assessment-data`  
     (must be globally unique)
   - **Region**: choose as appropriate (e.g., `us-central1`)
   - **Storage class**: Nearline (default or Standard, depending on your needs)

4. Leave other settings as default unless you have specific requirements.

5. Click **Create**

> **Important note about billing and free tier:**  
> When you create your first bucket or project, Google Cloud may ask you to add a **credit card** for billing verification.  
> - You must add a valid card to activate the free tier and use Cloud Storage with GEE.  
> - As long as you stay within the **free tier limits** and do not enable or use paid resources beyond that, **you will not be charged**.  
> - You can monitor usage and costs in **Billing → Reports** in the Google Cloud Console and set **budgets/alerts** to avoid unexpected charges.

---

## 6. Grant the Service Account Permission to Write to the Bucket

To allow GEE export tasks (and Python scripts using GEE) to write into the bucket, assign write permissions.

1. Open the bucket you created (e.g., `post-fire-assessment-data`)
2. Go to the **Permissions** tab
3. Click **“Grant Access”**
4. In **New principals**, add:
