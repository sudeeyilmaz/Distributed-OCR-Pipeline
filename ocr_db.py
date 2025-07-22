import mysql.connector
from mysql.connector import Error
import os
import json
from ocr_utils import convert_to_json_serializable


def create_connection():
    try:
        connection = mysql.connector.connect(
            host = 'mysql',
            user ='ocr',
            password = "1234",
            database = 'ocr_db'
        )
        if connection.is_connected():
            print("MySQL bağlantısı başarılı..")
            return connection
    except Error as e:
        print(f"Bağlantı hatası: {e}")
        return None
    
def media_status():
    conn = create_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT media_path, status, elapsed_time, last_updated, progress
        FROM media_status
        ORDER BY last_updated DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def insert_media_status(media_path, status='queued', frame_count=0, elapsed_time=0.0):
    conn = create_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO media_status (media_path, status, frame_count, elapsed_time)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE status = VALUES(status)
    """, (media_path, status, frame_count, elapsed_time))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def check_video_processed(media_path):
    conn = create_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ocr_video_results WHERE media_path = %s", (media_path,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0


def query_ocr_in_db(query: str, filter_val: str = None, limit: int = 50):
    query = query.lower()
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        filter_clause = "AND media_path LIKE %s" if filter_val else ""
        filter_param = f"%{filter_val}%" if filter_val else None

        if filter_val:
            cursor.execute(f"""
                SELECT COUNT(*) as total
                FROM ocr_video_results
                WHERE LOWER(text_content) LIKE %s {filter_clause}
            """, ('%' + query + '%', filter_param))
        else:
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM ocr_video_results
                WHERE LOWER(text_content) LIKE %s
            """, ('%' + query + '%',))
        total_count = cursor.fetchone()["total"]

        if filter_val:
            cursor.execute(f"""
                SELECT id, text_content, media_path, frame_number, timestamp, bbox
                FROM ocr_video_results
                WHERE LOWER(text_content) LIKE %s {filter_clause}
                LIMIT %s
            """, ('%' + query + '%', filter_param, limit))
        else:
            cursor.execute("""
                SELECT id, text_content, media_path, frame_number, timestamp, bbox
                FROM ocr_video_results
                WHERE LOWER(text_content) LIKE %s
                LIMIT %s
            """, ('%' + query + '%', limit))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        results_clean = convert_to_json_serializable(results)

        os.makedirs("search_result", exist_ok=True)
        with open(f"search_result/{query}.json", "w", encoding="utf-8") as f:
            json.dump(results_clean, f, ensure_ascii=False, indent=2)

        return results_clean, total_count

    except Exception as e:
        raise e
