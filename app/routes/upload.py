# routes/upload.py - WITH SSE SUPPORT
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import asyncio

from services.file_parser import FileParser
from services.openai_service import OpenAIService
from agents.virtual_lab import VirtualLab
import os

router = APIRouter()

# Initialize services
openai_service = OpenAIService(os.getenv("OPENAI_API_KEY"))

# In-memory storage (replace with database in production)
project_sessions = {}

class ConfirmDataRequest(BaseModel):
    """Request body for confirming extracted data (Checkpoint 1)"""
    project_id: str
    confirmed_data: Dict[str, Any]
    user_modified: bool = False

class WorkflowSelectionRequest(BaseModel):
    """Request body for workflow selections (Checkpoint 2)"""
    project_id: str
    selected_steps: List[str]
    modifications: Optional[Dict[str, Any]] = None
    user_notes: Optional[str] = None

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    PHASE 1: Upload and quick extraction
    Returns extracted data for Checkpoint 1 confirmation
    """
    
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
        # Read and parse file
        file_content = await file.read()
        text_content = FileParser.parse_file(file_content, file.filename)
        
        if len(text_content.strip()) < 50:
            raise HTTPException(status_code=400, detail="File appears to be empty or too short")
        
        # Create VirtualLab instance
        virtual_lab = VirtualLab(openai_service, None)
        
        # PHASE 1: Quick extraction only
        result = await virtual_lab.analyze_brief(text_content)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        # Create project session
        project_id = str(uuid.uuid4())
        project_sessions[project_id] = {
            "project_id": project_id,
            "filename": file.filename,
            "original_text": text_content,
            "extracted_data": result["extracted_data"],
            "phase": "checkpoint_1",
            "checkpoint_1_events": result["progress_events"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return JSONResponse({
            "success": True,
            "project_id": project_id,
            "filename": file.filename,
            "extracted_data": result["extracted_data"],
            "status": result["status"],
            "checkpoint": result["checkpoint"],
            "progress_events": result["progress_events"],
            "message": "Please confirm: Did I understand your project correctly?",
            "processed_at": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/confirm-understanding-stream")
async def confirm_understanding_stream(request: ConfirmDataRequest):
    """
    CHECKPOINT 1 (SSE VERSION): User confirms data, streams progress in real-time
    Returns SSE stream of progress events, then final result
    """
    
    # Validate project exists
    if request.project_id not in project_sessions:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session = project_sessions[request.project_id]
    
    # Validate we're at the right checkpoint
    if session["phase"] != "checkpoint_1":
        raise HTTPException(
            status_code=400, 
            detail=f"Project is in phase '{session['phase']}', expected 'checkpoint_1'"
        )
    
    async def event_generator():
        """Generate SSE events as analysis progresses"""
        
        try:
            # Update session
            session["confirmed_data"] = request.confirmed_data
            session["user_modified_extraction"] = request.user_modified
            session["checkpoint_1_confirmed_at"] = datetime.utcnow().isoformat()
            
            # Store events as they're emitted
            all_events = []
            
            def progress_callback(event_dict):
                """Called by VirtualLab when event occurs"""
                all_events.append(event_dict)
            
            # Create VirtualLab with callback
            virtual_lab_streaming = VirtualLab(openai_service, progress_callback)
            
            # Start analysis in background, yield events as they come
            analysis_task = asyncio.create_task(
                virtual_lab_streaming.generate_full_analysis(
                    text=session["original_text"],
                    confirmed_data=request.confirmed_data
                )
            )
            
            # Stream events as they're added to all_events
            last_event_count = 0
            while not analysis_task.done():
                # Check for new events
                if len(all_events) > last_event_count:
                    # Send new events
                    for event in all_events[last_event_count:]:
                        yield f"data: {json.dumps({'type': 'progress', 'event': event})}\n\n"
                    last_event_count = len(all_events)
                
                await asyncio.sleep(0.1)  # Check every 100ms
            
            # Get final result
            analysis_result = await analysis_task
            
            # Send any remaining events
            if len(all_events) > last_event_count:
                for event in all_events[last_event_count:]:
                    yield f"data: {json.dumps({'type': 'progress', 'event': event})}\n\n"
            
            if analysis_result["status"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'error': analysis_result.get('error', 'Unknown error')})}\n\n"
                return
            
            # Update session with results
            session["strategy"] = analysis_result["strategy"]
            session["workflow_options"] = analysis_result["workflow_options"]
            session["agent_insights"] = analysis_result["agent_insights"]
            session["phase"] = "checkpoint_2"
            session["checkpoint_2_events"] = analysis_result["progress_events"]
            session["updated_at"] = datetime.utcnow().isoformat()
            
            # Send final complete event with full result
            final_response = {
                "type": "complete",
                "data": {
                    "success": True,
                    "project_id": request.project_id,
                    "extracted_data": analysis_result["extracted_data"],
                    "strategy": analysis_result["strategy"],
                    "workflow_options": analysis_result["workflow_options"],
                    "status": analysis_result["status"],
                    "checkpoint": analysis_result["checkpoint"],
                    "message": "Analysis complete! Please review the workflow options."
                }
            }
            
            yield f"data: {json.dumps(final_response)}\n\n"
            
        except Exception as e:
            error_event = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@router.post("/confirm-understanding")
async def confirm_understanding(request: ConfirmDataRequest):
    """
    CHECKPOINT 1 (NON-STREAMING VERSION): For backward compatibility
    Returns complete result after all processing is done
    """
    
    # Validate project exists
    if request.project_id not in project_sessions:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session = project_sessions[request.project_id]
    
    if session["phase"] != "checkpoint_1":
        raise HTTPException(
            status_code=400, 
            detail=f"Project is in phase '{session['phase']}', expected 'checkpoint_1'"
        )
    
    try:
        session["confirmed_data"] = request.confirmed_data
        session["user_modified_extraction"] = request.user_modified
        session["checkpoint_1_confirmed_at"] = datetime.utcnow().isoformat()
        
        # Create VirtualLab without streaming
        virtual_lab = VirtualLab(openai_service, None)
        
        # Run full analysis
        analysis_result = await virtual_lab.generate_full_analysis(
            text=session["original_text"],
            confirmed_data=request.confirmed_data
        )
        
        if analysis_result["status"] == "error":
            raise HTTPException(status_code=500, detail=analysis_result.get("error", "Unknown error"))
        
        # Update session
        session["strategy"] = analysis_result["strategy"]
        session["workflow_options"] = analysis_result["workflow_options"]
        session["agent_insights"] = analysis_result["agent_insights"]
        session["phase"] = "checkpoint_2"
        session["checkpoint_2_events"] = analysis_result["progress_events"]
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return JSONResponse({
            "success": True,
            "project_id": request.project_id,
            "extracted_data": analysis_result["extracted_data"],
            "strategy": analysis_result["strategy"],
            "workflow_options": analysis_result["workflow_options"],
            "status": analysis_result["status"],
            "checkpoint": analysis_result["checkpoint"],
            "progress_events": analysis_result["progress_events"],
            "message": "Analysis complete! Please review the workflow options.",
            "processed_at": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/finalize-workflow")
async def finalize_workflow(request: WorkflowSelectionRequest):
    """
    CHECKPOINT 2: User selects final workflow options
    Saves everything for User 2 to review
    """
    
    if request.project_id not in project_sessions:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session = project_sessions[request.project_id]
    
    if session["phase"] != "checkpoint_2":
        raise HTTPException(
            status_code=400,
            detail=f"Project is in phase '{session['phase']}', expected 'checkpoint_2'"
        )
    
    session["final_workflow_selections"] = {
        "selected_steps": request.selected_steps,
        "modifications": request.modifications,
        "user_notes": request.user_notes
    }
    session["phase"] = "finalized"
    session["finalized_at"] = datetime.utcnow().isoformat()
    session["updated_at"] = datetime.utcnow().isoformat()
    
    all_steps = session["workflow_options"]["steps"]
    final_workflow = [step for step in all_steps if step["id"] in request.selected_steps]
    
    return JSONResponse({
        "success": True,
        "project_id": request.project_id,
        "status": "finalized",
        "message": "Workflow finalized and ready to share with team",
        "final_workflow": final_workflow,
        "share_url": f"/api/report/{request.project_id}",
        "finalized_at": datetime.utcnow().isoformat()
    })

@router.get("/report/{project_id}")
async def get_full_report(project_id: str):
    """
    USER 2 VIEW: Complete audit trail and decision history
    """
    
    if project_id not in project_sessions:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session = project_sessions[project_id]
    
    report = {
        "project_id": project_id,
        "filename": session["filename"],
        "created_at": session["created_at"],
        "finalized_at": session.get("finalized_at"),
        
        "checkpoint_1": {
            "original_extraction": session["extracted_data"],
            "user_confirmed_data": session.get("confirmed_data", session["extracted_data"]),
            "user_modified": session.get("user_modified_extraction", False),
            "progress_events": session.get("checkpoint_1_events", [])
        },
        
        "checkpoint_2": {
            "strategy_recommended": session.get("strategy", {}),
            "agent_insights": session.get("agent_insights", {}),
            "workflow_options_presented": session.get("workflow_options", {}),
            "user_selections": session.get("final_workflow_selections", {}),
            "progress_events": session.get("checkpoint_2_events", [])
        },
        
        "timeline": {
            "uploaded": session["created_at"],
            "understanding_confirmed": session.get("checkpoint_1_confirmed_at"),
            "workflow_finalized": session.get("finalized_at")
        },
        
        "status": session["phase"]
    }
    
    return JSONResponse(report)

@router.get("/project/{project_id}/status")
async def get_project_status(project_id: str):
    """Quick status check"""
    
    if project_id not in project_sessions:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session = project_sessions[project_id]
    
    return JSONResponse({
        "project_id": project_id,
        "phase": session["phase"],
        "updated_at": session["updated_at"],
        "checkpoints": {
            "checkpoint_1_complete": "checkpoint_1_confirmed_at" in session,
            "checkpoint_2_complete": "finalized_at" in session
        }
    })