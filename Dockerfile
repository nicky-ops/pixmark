FROM python:3.9-slim

# Create the app directory
RUN mkdir /app

# Set the working directory inside the container
WORKDIR /app

# prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Upgrade pip
RUN pip install --upgrade pip

# Copy the Django project and install dependancies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project to the container
COPY app /app/

# Expose the Django port
EXPOSE 8000

# RUN DJANGO'S DEV SERVER
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
