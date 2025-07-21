# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and config
COPY ../../requirements.txt .
COPY ../../.streamlit/ ./.streamlit/

# Copy only this app's code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Run the main app (collections by default)
CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0