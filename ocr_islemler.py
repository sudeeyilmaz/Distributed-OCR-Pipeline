import easyocr
from ocr_db import create_connection
import time
import cv2
from ocr_utils import convert_to_json_serializable
import json
import difflib
import os
print("EasyOCR Reader başlatılıyor...") 
try:
    reader = easyocr.Reader(['tr'], gpu=False, model_storage_directory='/OCR-TRANSLATE/models',verbose=True,download_enabled=False)
    print("EasyOCR Reader başarıyla başlatıldı.") 
except Exception as e:
    print(f"Hata: EasyOCR Reader başlatılamadı: {str(e)}") 
    reader = None

def normalize_text(text):
    return ''.join(e.lower() for e in text if e.isalnum())

def are_similar(text1, text2, threshold=0.85):
    ratio = difflib.SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()
    return ratio > threshold

def insert_ocr_results(video_path, ocr_every_n_frames=25, start_time=None, end_time=None):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE media_status SET status = %s WHERE media_path = %s", ('processing', video_path))
        conn.commit()

        start_timer = time.time()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Video cannot be opened")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval_frame_count = ocr_every_n_frames

        frame_count = 0

        if start_time is not None:
            start_time = float(start_time)
        if end_time is not None:
            end_time = float(end_time)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = frame_count / fps

            if start_time is not None and current_time < start_time:
                frame_count += 1
                continue

            if end_time is not None and current_time > end_time:
                break

            if frame_count % interval_frame_count == 0:
                # Preprocessing kaldırıldı, doğrudan OCR yapılacak
                results = reader.readtext(frame)
                print(f"OCR results at frame {frame_count}: {results}")
                for result in results:
                    text_content = result[1].strip()
                    bbox_serializable = convert_to_json_serializable(result[0])
                    bbox_str = json.dumps(bbox_serializable)

                    cursor.execute(
                        "SELECT id, text_content FROM ocr_video_results WHERE media_path = %s ORDER BY id DESC LIMIT 10",
                        (video_path,)
                    )
                    recent_rows = cursor.fetchall()
                    
                    matched_row = None
                    for row in recent_rows:
                        existing_text = row[1]
                        if text_content in existing_text or existing_text in text_content:
                            matched_row = row
                            break
                    
                    try:
                        if matched_row:
                            new_text = existing_text
                            if text_content not in existing_text:
                                new_text = existing_text + " " + text_content
                            cursor.execute(
                                "UPDATE ocr_video_results SET text_content = %s WHERE id = %s",
                                (new_text, matched_row[0])
                            )
                            conn.commit()
                            print(f"Updated: {new_text}, id: {matched_row[0]}")
                        else:
                            cursor.execute(
                                "INSERT INTO ocr_video_results (text_content, media_path, frame_number, timestamp, bbox) VALUES (%s, %s, %s, %s, %s)",
                                (text_content, video_path, frame_count, current_time, bbox_str)
                            )
                            conn.commit()
                            print(f"Inserted: {text_content}, frame: {frame_count}")
                    except Exception as e:
                        print(f"Error inserting/updating result: {e}")

            percent = min((frame_count / total_frames) * 100, 100.0)
            cursor.execute(
                "UPDATE media_status SET progress = %s WHERE media_path = %s",
                (percent, video_path)
            )
            conn.commit()

            frame_count += 1

        cap.release()
        elapsed = time.time() - start_timer

        cursor.execute(
            "UPDATE media_status SET status = %s, frame_count = %s, elapsed_time = %s, progress = 100 WHERE media_path = %s",
            ('processed', frame_count, elapsed, video_path)
        )
        conn.commit()
        return "Processed", frame_count

    except Exception as e:
        cursor.execute("UPDATE media_status SET status = %s WHERE media_path = %s", ('failed', video_path))
        conn.commit()
        return f"Error: {e}", 0

    finally:
        cursor.close()
        conn.close()



def ocr_reader(img_path):
    print(f"ocr_reader fonksiyonu çağrıldı, görsel yolu: {img_path}") # DEBUG
    try:
        if reader is None:
            print("Hata: EasyOCR Reader başlatılamadığı için ocr_reader çalışamaz.") # DEBUG
            return "OCR motoru başlatılamadı."

        if not os.path.exists(img_path):
            print(f"Hata: OCR için görsel dosyası bulunamadı: {img_path}") # DEBUG
            raise FileNotFoundError(f"Görsel dosyası bulunamadı: {img_path}")

        print(f"Görsel okunuyor: {img_path}") # DEBUG
        image = cv2.imread(img_path)
        

        if image is None:
            print(f"Hata: cv2.imread görseli okuyamadı. Dosya bozuk veya format desteklenmiyor: {img_path}") # DEBUG
            raise ValueError(f"Görsel okunamadı veya dosya bozuk: {img_path}")
        print(f"Image shape: {image.shape}")

        print(f"Görsel başarıyla okundu, EasyOCR readtext başlatılıyor: {img_path}") # DEBUG
        results = reader.readtext(image, detail=1, paragraph=True)
        print(f"EasyOCR readtext tamamlandı, sonuçlar: {results}") # DEBUG
        texts = [item[1] for item in results]
        
        return " ".join(texts)
    except Exception as e:
        print(f"OCR okuma işlemi sırasında beklenmeyen bir hata oluştu ({img_path}): {str(e)}") # DEBUG
        raise
