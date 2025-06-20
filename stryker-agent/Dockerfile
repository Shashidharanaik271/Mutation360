# Use the official .NET 8 SDK as a base image
FROM mcr.microsoft.com/dotnet/sdk:8.0

# Set the working directory for the .NET project that will be mounted
WORKDIR /repo

# Install dotnet-stryker as a global tool
RUN dotnet tool install -g dotnet-stryker
# Add the dotnet tools directory to the PATH
ENV PATH="${PATH}:/root/.dotnet/tools"

# Install Git, Python, Pip, and essential build tools
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# --- VIRTUAL ENVIRONMENT SETUP ---
# Create a directory for the virtual environment
ENV VENV_PATH=/opt/venv
# Create the virtual environment
RUN python3 -m venv $VENV_PATH
# Add the virtual environment's bin directory to the PATH
# This ensures that any command like 'python' or 'pip' will use the venv's version
ENV PATH="$VENV_PATH/bin:$PATH"

# Set up the Python application directory
WORKDIR /app
COPY ./requirements.txt .

# Install the packages into the activated virtual environment
# We use 'python -m pip' to be explicit about using the venv's pip
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY ./app /app

# The entrypoint will now automatically use the Python from the virtual environment
# because of the PATH modification above.
ENTRYPOINT ["python", "/app/main.py"]