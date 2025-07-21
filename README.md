# Up & Up Streamlit Dashboards

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
   - Add your configuration secrets (e.g., API keys, database credentials)
   ```toml
   # Example secrets.toml structure
   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   # Add other required credentials
   ```

## Adding Dependencies

To add new dependencies to your project:

```bash
poetry add <package-name>
```

For example:

```bash
poetry add pandas
poetry add streamlit
poetry add google-cloud-bigquery
```

For development dependencies, add the `--dev` flag:

```bash
poetry add --dev pytest
```

After adding new dependencies, update the requirements.txt file:

```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

This command will create/update requirements.txt with all your project dependencies, making it easier to install dependencies in environments where Poetry isn't available.

## Running the App

1. Activate the Poetry shell (optional but recommended):

   ```bash
   poetry shell
   ```

2. Run a specific dashboard using Streamlit:

   ```bash
   poetry run streamlit run apps/collections/app.py
   ```

   Or if you're in Poetry shell:

   ```bash
   streamlit run apps/<DASHBOARD_NAME>/app.py
   ```

3. The app will open automatically in your default web browser. By default, Streamlit runs on:
   - Local URL: http://localhost:8501
   - Network URL: http://192.168.x.x:8501

## Deployment to Streamlit Cloud

1. Create a Streamlit Cloud account at [streamlit.io](https://streamlit.io)

2. Deploy your app:

   - Click "Create app" in the Streamlit Cloud dashboard (top right corner)
   - Choose "Deploy a public app from GitHub"
   - Select your repository and branch
   - Set the main file path: `apps/<DASHBOARD_NAME>/app.py`
   - Click "Deploy"

3. Configure secrets in Streamlit Cloud:
   - In your deployed app, click the three dots (⋮) menu
   - Select "Settings"
   - Navigate to "Secrets"
   - Paste your secrets in TOML format:
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

Note: Make sure your repository is public or you have connected your GitHub account with Streamlit Cloud. Never commit secrets directly to your repository - always use Streamlit's secrets management system.

For more detailed instructions on BigQuery integration, see the [Streamlit BigQuery Tutorial](https://docs.streamlit.io/develop/tutorials/databases/bigquery).
