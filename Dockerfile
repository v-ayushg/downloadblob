# Use the official Python image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn flask

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose port 5000
EXPOSE 5000

# Run the Gunicorn server
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
