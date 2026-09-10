FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy all files from the current directory (app.py, requirements.txt, model) into the container
COPY . .

# Install dependencies without caching to keep the image small
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Start the API with Gunicorn (a production WSGI server)
# -w 2           : two worker processes (a 2-core Codespace)
# -b 0.0.0.0:7860: listen on port 7860 on all network interfaces
# app:superkart_api : the Flask object `superkart_api` inside app.py
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "app:superkart_api"]
