# Stage 1: Builder
FROM python:3.9-slim AS builder

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /install

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --upgrade pip

# Install packages into /install directory
RUN pip install --prefix=/install -r requirements.txt gunicorn Django==4.1.13

# Stage 2: Runtime
FROM python:3.9-slim

RUN useradd -m -r appuser

# Set work directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Add /usr/local/bin to PATH to find gunicorn
ENV PATH="/usr/local/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the Django app source code from host's ./app folder to container
COPY --chown=appuser:appuser ./app /app

USER appuser
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "bookmarks.wsgi:application"]