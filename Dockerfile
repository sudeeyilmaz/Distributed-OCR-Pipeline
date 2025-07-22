FROM python:3.12-slim

WORKDIR /OCR-TRANSLATE

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /OCR-TRANSLATE

RUN mkdir -p /OCR-TRANSLATE/uploads

EXPOSE 8003
EXPOSE 5555

CMD ["uvicorn", "ocr_fastapi:app", "--host", "0.0.0.0", "--port", "8003"]
