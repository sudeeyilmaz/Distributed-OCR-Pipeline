from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str
    filter: str = ""
    limit: int = 50

class FolderRequest(BaseModel):
    folder_path: str
    frame_interval: Optional[int] = 25