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
