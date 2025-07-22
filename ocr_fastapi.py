from fastapi import FastAPI,HTTPException,File, Path,UploadFile
from fastapi.responses import JSONResponse
from ocr_db import media_status,insert_media_status,query_ocr_in_db
from ocr_schemas import QueryRequest, FolderRequest
import os
from tasks import ocr_image_task, process_video_task,process_folder_task
from celery.result import AsyncResult

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

allowed_image_types = ["image/jpeg", "image/png", "image/jpg"]

@app.get("/task_status/{task_id}")
async def get_status(task_id: str = Path(...)):
    result = AsyncResult(task_id)
    return {
        "status": result.status,
        "result": result.result if result.ready() else None
    }

@app.post("/img_ocr")
async def ocr_cikart(file: UploadFile = File(...)):
    if file.content_type not in allowed_image_types:
        raise HTTPException(status_code=400, detail="Sadece JPEG ve PNG formatındaki resimler desteklenmektedir.")
    
    try:
        contents = await file.read()
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        task = ocr_image_task.delay(file_path) 
        return {"message": "OCR işlemi başarıyla başlatıldı.", "filename": file.filename, "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR işlemi sırasında hata oluştu: {str(e)}")

@app.post("/video_ocr")
async def upload_video_ocr(file:UploadFile=File(...),frame_interval: int=25):
    try:
        video_path = os.path.join(UPLOAD_DIR,file.filename)
        with open(video_path,"wb") as f:
            content = await file.read()
            f.write(content)
        
        insert_media_status(video_path)
        task = process_video_task.delay(video_path, frame_interval)
        return JSONResponse(content={
            "message": "Video OCR işlemi başarıyla başlatıldı.",
            "file_path": video_path,
            "task_id": task.id
        })

    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))


@app.post("/folder_ocr")
async def folder_ocr_endpoint(data: FolderRequest):
    task = process_folder_task.delay(data.folder_path, data.frame_interval)
    return {"message": "Folder OCR işlemi başlatıldı.", "task_id": task.id}

@app.post("/query")
async def query_ocr(request_data: QueryRequest):
    try:
        results, total_count = query_ocr_in_db(request_data.query, request_data.filter, request_data.limit)
        return JSONResponse(content={"results": results, "total": total_count})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media_status")
def get_media_status():
    results=media_status()
    return JSONResponse(content=results)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ocr_fastapi:app", host="0.0.0.0", port=8003, reload=True)
