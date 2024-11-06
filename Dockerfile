FROM python:3.9-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set up your working directory and install dependencies
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

# Expose the port
EXPOSE 8080

# Command to run the app
CMD ["python", "app.py"]
