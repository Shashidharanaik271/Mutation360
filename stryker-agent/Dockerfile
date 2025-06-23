# IMPORTANT: We will replace this line later with the actual path from GHCR.
# Example: FROM ghcr.io/your-org/your-repo:base-latest
FROM ghcr.io/shashidharanaik271/mutation360:base-latest

# Set up the Python application directory
WORKDIR /app
COPY ./requirements.txt .

# Install the packages into the activated virtual environment
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY ./app /app

# The entrypoint will now automatically use the Python from the virtual environment
ENTRYPOINT ["python", "/app/main.py"]
