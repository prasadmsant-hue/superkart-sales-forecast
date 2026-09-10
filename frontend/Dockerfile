FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the Streamlit app and its requirements into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face runs the container as a non-root user, so Streamlit gets a writable home directory
ENV HOME=/tmp

# Run the Streamlit app on port 8501, reachable from outside the container.
# XSRF protection is disabled so that file uploads (batch prediction) work through the hosting proxy.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableXsrfProtection=false"]
