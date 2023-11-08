# --- Builder Stage ---
# Use an official Python runtime as a parent image
FROM python:3.9-slim as builder

# Install poetry and pyminifier
RUN pip install --upgrade pip
#RUN pip install setuptools==57.5.0
#RUN pip install pyminifier
RUN pip install poetry

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the pyproject.toml (and optionally poetry.lock) file into the container
COPY pyproject.toml poetry.lock* /usr/src/app/

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy the current directory contents into the container at /usr/src/app
COPY repogpt/ repogpt/

# Minify and obfuscate Python code
#RUN pyminifier --obfuscate-variables --destdir repogpt/ repogpt/*.py

# --- Final Stage ---
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install curl
RUN apt-get update \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the installed packages and minified code from the builder stage
COPY --from=builder /usr/local /usr/local
COPY --from=builder /usr/src/app /usr/src/app

# Make port 8000 available to the world outside this container
EXPOSE 8000

RUN curl --version

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run uvicorn when the container launches
# Note: ENTRYPOINT is necessary instead of CMD, otherwise the turn off signal from the server doesn't shutdown the container
ENTRYPOINT ["uvicorn", "repogpt.routes:app", "--host", "0.0.0.0", "--port", "8000"]
