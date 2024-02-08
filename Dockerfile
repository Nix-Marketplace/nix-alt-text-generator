# Use the official Python 3.11 image as the base image
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory inside the container
WORKDIR /app

# Run and update the package manager and pip
RUN apt-get update \
    && pip install --upgrade pip \
    && apt-get install -y libkrb5-dev gcc

# Copy the requirements.txt file to the working directory
COPY . ./

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the NiceGUI app will run
EXPOSE 8080
ENV PORT 8080

# Set the command to run the NiceGUI app
CMD ["python3", "main.py"]