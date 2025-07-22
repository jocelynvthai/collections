# Up&Up Streamlit Dashboards

A collection of Streamlit dashboards for Up & Up, built with Python and Streamlit. This project uses Poetry for dependency management and includes various data analysis tools powered by pandas and Google BigQuery.

## Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- Google Cloud credentials (for BigQuery integration)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd upandup-dashboards
   ```
2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
3. Configure secrets:
   - Create a `.streamlit/secrets.toml` file
   - Add your configuration secrets (see the [Streamlit BigQuery Tutorial](https://docs.streamlit.io/develop/tutorials/databases/bigquery))
     ```toml
     [gcp_service_account]
     type = "service_account"
     project_id = "your-project-id"
     private_key_id = "your-private-key-id"
     private_key = "your-private-key"
     client_email = "your-client-email"
     client_id = "your-client-id"
     auth_uri = "https://accounts.google.com/o/oauth2/auth"
     token_uri = "https://oauth2.googleapis.com/token"
     auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
     client_x509_cert_url = "your-cert-url"
     ```

## Project Structure

```
├── poetry.lock
├── pyproject.toml
├── requirements.txt
├── .streamlit
    ├── config.toml
    └── secrets.toml  <- add BigQuery secret here
├── README.md
└── apps
    ├── your_dashboard_name  <- copy this folder and use as skeleton
    │   ├── app.py
    │   └── data.py
    ├── dashboard_1
    │   ├── app.py
    │   └── data.py
    └── dashboard_2
    │   ├── app.py
    │   └── data.py
```

- In the `apps` directory, there is a folder called `your_dashboard_name`. This will give you skeleton code on creating your own streamlit dashboard (connecting to BigQuery, querying data, etc. )

## Adding Dependencies

To add new dependencies to your project:

```bash
poetry add <package-name>
```

After adding new dependencies, update the `requirements.txt` file:

```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes --only main
```

## Running the App Locally

Option 1:

- Activate the Poetry shell (optional but recommended):
  ```bash
  poetry shell
  ```

````

- Run the app in the poetry shell

  ```bash
  streamlit run apps/your_dashboard_name/app.py
  ```

  Option 2:

- Without poetry shell
  ```bash
  poetry run streamlit run apps/your_dashboard_name/app.py
  ```

The app will open automatically in your default web browser. By default, Streamlit runs on:

- Local URL: http://localhost:8501
- Network URL: http://192.168.x.x:8501

## Deployment to Streamlit Cloud

1. Create a Streamlit Cloud account at [streamlit.io](https://streamlit.io)
2. Deploy your app:
   - Click "Create app" in the Streamlit Cloud dashboard (top right corner)
   - Choose "Deploy a public app from GitHub"
   - Select your repository and branch
   - Set the main file path: `apps/your_dashboard_name/app.py`
   - Click "Deploy"
3. Configure secrets in Streamlit Cloud:
   - In your deployed app, click the three dots (⋮) menu
   - Select "Settings"
   - Navigate to "Secrets"
   - Paste your secrets in TOML format:

## Deployment with Google Cloud Run

1. Create a Docker file with name `your_dashboard_name.Dockerfile` in the root with the following contents:

   ```
   # Use Python 3.11 slim image
   FROM python:3.11-slim

   # Set working directory
   WORKDIR /app

   # Copy requirements and config
   COPY requirements.txt .
   COPY .streamlit/ ./.streamlit/

   # Copy only the collections app's code
   COPY apps/your_dashboard_name/ .

   # Install dependencies
   RUN pip install -r requirements.txt

   # Run the main app
   CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0
   ```

2. Create a new directory in the apps folder called `your_dashboard_name`
3. Create an `app.py` file that contains the master code for the dashboard
4. Deploy container at [Google Cloud Run](https://cloud.google.com/run) using a Github Repository

   a. Set up with Cloud Build: authenticate Github select the Build Type as Dockerfile with the source location set to "/your_dashboard_name/Dockerfile

   b. Choose a service name (typically upandup-your_dashboard_name)

   c. Set Authentication as "Allow unauthenticated invocations"

   d. Create Volume and Volume Mounts if app requires credential secrets (ex. google cloud service account to access BigQuery)

   e. Create
````
