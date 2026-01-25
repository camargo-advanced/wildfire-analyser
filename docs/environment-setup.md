### Step-by-Step Guide: Creating a Service Account for GEE Code, Creating a Bucket, and Assigning Required Permissions

This guide explains how to:

1. Create a **Google Cloud project**.
2. Create a **service account** for authenticating Python/Node.js code that uses Google Earth Engine (GEE).
3. Generate a **JSON key** for the service account.
4. Register your account/project with **Google Earth Engine**.
5. Create a **Google Cloud Storage (GCS) bucket**.
6. Grant the required **permissions** so the service account can write GEE exports to the bucket.
7. Grant **public read access** to exported objects (required).
8. Configure a **lifecycle rule** to delete files after 24 hours.

> Note: This guide assumes you already have a Google account with access to Google Cloud and Google Earth Engine.

---

## 1. Create (or Choose) a Google Cloud Project

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Open the project selector at the top of the page.
3. Either select an existing project or click **New Project**:

   * Example name: `post-fire-assessment`
   * Select the appropriate organization (if applicable)
   * Click **Create**
4. Ensure the project is selected in the top bar.

---

## 2. Enable the Required APIs

1. Go to **APIs & Services → Library**
2. Enable:

   * **Earth Engine API**
   * **Cloud Storage JSON API**

---

## 3. Create the Service Account

1. Go to **IAM & Admin → Service Accounts**
2. Click **Create Service Account**
3. Fill in:

   * **Name**: `gee-service-account`
   * **Description**: Service account for Google Earth Engine scripts
4. Click **Create and Continue**
5. Assign a basic role:

   * `Viewer` or `Project Viewer`
6. Click **Continue → Done**

Save the service account email for later use.

---

## 4. Create a JSON Key for the Service Account

1. Open the service account you created.
2. Go to the **Keys** tab.
3. Click **Add Key → Create new key**
4. Select **JSON**
5. Click **Create**

A JSON key file will be downloaded.

> Keep this file secure and never commit it to a public repository.

---

## 5. Register Google Earth Engine

Google Earth Engine must be enabled and registered for your **Google account and project**.

1. In Google Cloud Console, click **View all products**
2. Under **Geospatial**, select **Earth Engine**
3. Open **Configuration → Manage registration**
4. Complete and submit the registration form
5. Wait for approval

### Organization type

* Select **Non-profit** if the project is for NGOs, research, or social impact
* Select **For-profit** only for commercial use

---

## 6. Create a Cloud Storage Bucket

1. Go to [https://console.cloud.google.com/storage/browser](https://console.cloud.google.com/storage/browser)
2. Click **Create Bucket**
3. Configure:

   * **Bucket name**: e.g. `wildfire-analyser-outputs` (must be globally unique)
   * **Region**: e.g. `us-central1`
   * **Storage class**: Standard or Nearline
4. Click **Create**
5. Disable **Public access prevention** for the bucket and confirm

---

## 7. Grant Permissions to the Service Account

### 7.1 Allow the service account to write objects

1. Open the bucket → **Permissions**
2. Click **Grant access**
3. Add the service account email
4. Assign role:

   * `Storage Object Admin`
     *(or `Storage Object Creator` for write-only access)*
5. Click **Save**

** 7.2 Grant public read access to exported objects (required)**

> This step is **mandatory** because the exported files will be accessed publicly via direct URLs.

1. In the same **Permissions** tab, click **Grant access**
2. Add:

   ```
   allUsers
   ```
3. Assign role:

   ```
   Storage Object Viewer
   ```
4. Click **Save**

---

## 8. Configure a Lifecycle Rule to Delete Files After 24 Hours

1. Open the bucket
2. Go to the **Lifecycle** tab
3. Click **Add a rule**
4. Set:

   * **Action**: Delete object
   * **Condition**: Age = `1` day
5. Click **Save**

---

## Final Notes

* Ensure the service account email used in permissions matches the one used in your GEE code.
* Permission and lifecycle changes may take a few minutes to propagate.
