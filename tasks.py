import os
from celery import Celery
from ocr_islemler import ocr_reader, insert_ocr_results 
from ocr_db import insert_media_status,check_video_processed

celery_app = Celery(
    'ocr_translate_app', # Uygulamanız için benzersiz bir isim
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

celery_app.conf.update(
    task_track_started=True, 
    task_acks_late=True, 
    worker_prefetch_multiplier=1, 
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Istanbul', 
    enable_utc=True,
)


@celery_app.task(bind=True) 
def ocr_image_task(self, file_path: str):
    try:
        print(f"OCR işlemi başlatıldı: {file_path} (Task ID: {self.request.id})")
        ocr_text = ocr_reader(file_path) 
        print(f"OCR işlemi tamamlandı: {file_path}")

        return {"filename": os.path.basename(file_path), "text": ocr_text}
    except Exception as e:
        print(f"OCR işlemi sırasında hata oluştu: {file_path} - {str(e)}")
        raise 

@celery_app.task(bind=True)
def process_video_task(self, video_path: str, frame_interval: int):
    
    try:
        print(f"Video OCR işlemi başlatıldı: {video_path} (Task ID: {self.request.id})")
        insert_media_status(video_path) 

        status, total_frames = insert_ocr_results(video_path, frame_interval) 
        print(f"Video OCR işlemi tamamlandı: {video_path} - Status: {status}")
    
        return {
            "file_path": video_path,
            "status": status,
            "total_frames_processed": total_frames
        }
    except Exception as e:
        print(f"Video OCR işlemi sırasında hata oluştu: {video_path} - {str(e)}")
        raise 



@celery_app.task(bind=True)
def process_folder_task(self, folder_path: str, frame_interval: int):
    video_exts = ['.mp4', '.avi', '.mov', '.mkv']
    videos = [
        os.path.join(dp, f)
        for dp, _, files in os.walk(folder_path)
        for f in files
        if any(f.lower().endswith(ext) for ext in video_exts)
    ]

    processed = 0
    skipped = 0

    for video_path in videos:
        insert_media_status(video_path)

    for video_path in videos:
        if check_video_processed(video_path):
            skipped += 1
            continue

        result = insert_ocr_results(video_path, frame_interval)
        if result[0] == "Processed":
            processed += 1
        elif result[0] == "Video cannot be opened":
            continue
        else:
            skipped += 1

    return {
        "message": "Folder processed",
        "processed": processed,
        "skipped": skipped,
        "total": len(videos)
    }

