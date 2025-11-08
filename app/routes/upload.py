#routes/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime

from services.file_parser import FileParser
from services.openai_service import OpenAIService
from agents.virtual_lab import VirtualLab
import os

router = APIRouter()

# Initialize services
openai_service = OpenAIService(os.getenv("OPENAI_API_KEY"))
virtual_lab = VirtualLab(openai_service, None)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process project brief"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    allowed_types = ['pdf', 'docx', 'txt']
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{file_ext}' not supported. Use: {', '.join(allowed_types)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse file to text
        text_content = FileParser.parse_file(file_content, file.filename)
        
        if len(text_content.strip()) < 50:
            raise HTTPException(status_code=400, detail="File appears to be empty or too short")
        
        # Process with AI agent
        result = await virtual_lab.process_project(text_content)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Return structured response
        return JSONResponse({
            "success": True,
            "project_id": str(uuid.uuid4()),
            "filename": file.filename,
            "extracted_data": result["extracted_data"],
            "strategy": result["strategy"],
            "status": result["status"],
            "processed_at": datetime.now().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/confirm")
async def confirm_extraction(project_data: dict):
    """User confirms or edits extracted data"""
    
    # In a real app, you'd save this to database
    # For MVP, just return confirmation
    
    return JSONResponse({
        "success": True,
        "message": "Data confirmed",
        "data": project_data
    })