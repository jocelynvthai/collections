# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the entire project
COPY . .


# Run the main app (collections by default)
CMD streamlit run apps/collections/app.py --server.port=8080 --server.address=0.0.0.0