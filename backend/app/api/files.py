from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from app.database import get_db
from app.models.file import File as FileModel
from typing import Optional

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/{file_id}")
def download_file(file_id: int, download: Optional[bool] = False, db: Session = Depends(get_db)):
    f = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    response = FileResponse(f.file_path, media_type=f.content_type, filename=f.filename)
    disp = "attachment" if download else "inline"
    response.headers["Content-Disposition"] = f'{disp}; filename="{f.filename}"'
    return response
