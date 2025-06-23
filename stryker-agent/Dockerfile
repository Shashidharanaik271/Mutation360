# Use your pre-built base image, which now includes all Python packages
FROM ghcr.io/shashidharanaik271/mutation360:base-latest

# The WORKDIR is already /app from the base image.
# All Python packages are already installed.

# Just copy the application code into the container
COPY ./app /app

# The entrypoint will now automatically use the Python from the virtual environment
ENTRYPOINT ["python", "/app/main.py"]
