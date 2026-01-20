# 🔍 FastAPI Async OCR Service

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-High%20Performance-009688)
![Celery](https://img.shields.io/badge/Celery-Async%20Tasks-green)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)

A robust, **asynchronous Optical Character Recognition (OCR) microservice** designed to extract text from various media formats. Built with **FastAPI** for the REST interface and **Celery** for handling heavy background processing tasks (like video parsing).

This project is fully containerized using **Docker**, making it easy to deploy and scale.

## 🚀 Key Features

* **📷 Image OCR:** Extracts text from standard image formats (`.jpg`, `.png`).
* **🎥 Video OCR:** Processes video files by extracting frames at specified intervals and performing OCR on them asynchronously.
* **📂 Batch Processing:** Scans entire folders to process multiple media files in the background.
* **⚡ Asynchronous Architecture:** Uses **Celery** workers to handle long-running tasks without blocking the main API thread.
* **🔎 Searchable Database:** Extracted text is indexed in a database, allowing users to search for keywords within processed media.
* **🐳 Docker Ready:** Includes `docker-compose` for one-command orchestration of the API, Workers, and Database.

## 🛠️ Tech Stack

* **Framework:** FastAPI (Python)
* **Task Queue:** Celery
* **Broker:** Redis (via Docker)
* **Containerization:** Docker & Docker Compose
* **OCR Engine:** Tesseract (Integrated in Worker)
* **Database:** SQL / MongoDB (Abstracted in `ocr_db.py`)

## 📂 Project Structure

text
├── ocr_fastapi.py      # Main API Gateway (Routes)
├── tasks.py            # Celery Worker Tasks (Image/Video Processing)
├── ocr_db.py           # Database Interactions
├── ocr_schemas.py      # Pydantic Models for Data Validation
├── docker-compose.yml  # Orchestration Config
├── Dockerfile          # Container Definition
└── requirements.txt    # Dependencies
## ⚙️ Installation & Usage
Since the project is containerized, the easiest way to run it is via Docker.

1. Clone the repository
Bash

git clone [https://github.com/sudeeyilmaz/Distributed-OCR-Pipeline.git](https://github.com/sudeeyilmaz/Distributed-OCR-Pipeline.git)
cd Distributed-OCR-Pipeline
2. Build and Run with Docker
Bash

docker-compose up --build
This command starts the FastAPI server, Celery workers, and the Redis broker.

3. Access the API
Once running, the API is accessible at:

API Root: http://localhost:8003

Swagger Documentation: http://localhost:8003/docs
## 🏗️ How It Works (Architecture)
1. Client sends a request (e.g., upload video) to FastAPI.

2. FastAPI saves the file and pushes a task to the Celery/Redis Queue.

3. Celery Worker picks up the task, processes the video frame-by-frame using OCR, and saves the text results to the Database.

4. Client can poll /task_status to check progress or use /query to search the results once finished.
