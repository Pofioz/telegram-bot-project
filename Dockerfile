# Use the full Debian "Bullseye" version of the Python image
FROM python:3.11-bullseye

# Set the working directory in the container
WORKDIR /app

# Install ALL system dependencies FIRST, including build-essential tools and voice-related libraries
RUN apt-get update && \
    apt-get install -y ffmpeg build-essential libopus-dev libffi-dev libgirepository1.0-dev libcairo2-dev libpango1.0-dev libglib2.0-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# --- ADD THIS LINE TO FORCE CACHE INVALIDATION ---
RUN echo "Forcing pip install layer to run"

# Install any needed packages specified in requirements.txt
# This step now runs AFTER system dependencies are installed
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Command to run the bot when the container starts
CMD ["python", "-m", "bot.main"]