# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the microservice code into the container
COPY . .

# Make port 5001 available to the world outside this container
EXPOSE 6006

# Define environment variable
ENV FLASK_APP=app.py

# Use Gunicorn as the WSGI server for production
CMD ["python","app.py"]
