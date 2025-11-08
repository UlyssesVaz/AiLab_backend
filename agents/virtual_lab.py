# agents/virtual_lab.py
from models.state import ProjectState, AgentRole, ProgressEvent, EventType
from agents.pi_agent import PIAgent
from agents.immunologist import ImmunologistAgent  
from agents.ml_specialist import MLSpecialistAgent
from agents.comp_biologist import CompBiologistAgent
from services.openai_service import OpenAIService
from typing import Dict, Any
from datetime import datetime

class VirtualLab:
    def __init__(self, openai_service: OpenAIService, progress_callback=None):
        self.pi = PIAgent(openai_service)
        self.immunologist = ImmunologistAgent(openai_service)
        self.ml_specialist = MLSpecialistAgent(openai_service)
        self.comp_biologist = CompBiologistAgent(openai_service)
        self.progress_callback = progress_callback
        self.events = []
    
    def emit_event(self, event: "ProgressEvent"):
        self.events.append(event)
        if self.progress_callback:
            self.progress_callback(event)


    async def process_project(self, text: str) -> Dict[str, Any]:
        """Main workflow - maintains exact API contract"""
        try:
            self.emit_event(ProgressEvent(
                event_type=EventType.STEP_START,
                timestamp=datetime.utcnow(),
                step_name="Starting Virtual Lab Analysis",
                progress=0.0
            ))
            # Initialize state
            state = ProjectState(text=text)
            
            # Team meeting: each agent provides input
            state.agent_inputs.append(await self.immunologist.provide_input(state))
            state.agent_inputs.append(await self.ml_specialist.provide_input(state)) 
            state.agent_inputs.append(await self.comp_biologist.provide_input(state))
            
            # PI synthesizes
            extracted_data = await self.pi.extract_key_data(text)
            strategy = await self.pi.synthesize_strategy(state)
            
            # Return in exact format expected by routes/upload.py
            return {
                "extracted_data": extracted_data,
                "strategy": strategy, 
                "status": "complete",
                "error": "",
                "progress_events": [event.dict() for event in self.events],
            }
            
        except Exception as e:
            return {
                "extracted_data": {},
                "strategy": {},
                "status": "error",
                "error": str(e)
            }