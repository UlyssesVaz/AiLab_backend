# agents/virtual_lab.py - FIXED VERSION
from models.state import ProjectState, AgentRole, ProgressEvent, EventType
from agents.pi_agent import PIAgent
from agents.immunologist import ImmunologistAgent  
from agents.ml_specialist import MLSpecialistAgent
from agents.comp_biologist import CompBiologistAgent
from services.openai_service import OpenAIService
from typing import Dict, Any, List
from datetime import datetime

class VirtualLab:
    def __init__(self, openai_service: OpenAIService, progress_callback=None):
        self.pi = PIAgent(openai_service)
        self.immunologist = ImmunologistAgent(openai_service)
        self.ml_specialist = MLSpecialistAgent(openai_service)
        self.comp_biologist = CompBiologistAgent(openai_service)
        self.progress_callback = progress_callback
        self.events = []  # Stores dicts, not objects
    
    def emit_event(self, event_type: EventType, step_name: str, progress: float, 
                   message: str = "", agent_role: AgentRole = None):
        """
        Emit progress event - stores as dict immediately (JSON-safe)
        No serialization issues!
        """
        event_dict = {
            "event_type": event_type.value,  # Convert enum to string immediately
            "timestamp": datetime.utcnow().isoformat(),  # Convert datetime to ISO string immediately
            "step_name": step_name,
            "agent_role": agent_role.value if agent_role else None,  # Convert enum to string
            "progress": progress,
            "message": message
        }
        
        self.events.append(event_dict)
        
        if self.progress_callback:
            self.progress_callback(event_dict)
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all events - already JSON-safe dicts"""
        return self.events

    async def analyze_brief(self, text: str) -> Dict[str, Any]:
        """
        PHASE 1: Quick extraction for Checkpoint 1
        Returns extracted data for user confirmation
        """
        try:
            self.events = []  # Reset events for new session
            
            self.emit_event(
                event_type=EventType.STEP_START,
                step_name="Analyzing Project Brief",
                progress=0.0,
                message="Reading and interpreting your document...",
                agent_role=AgentRole.PI
            )
            
            # PI does quick extraction
            extracted_data = await self.pi.extract_key_data(text)
            
            self.emit_event(
                event_type=EventType.STEP_COMPLETE,
                step_name="Brief Analysis Complete",
                progress=100.0,
                message="Key information extracted - ready for your confirmation",
                agent_role=AgentRole.PI
            )
            
            return {
                "extracted_data": extracted_data,
                "status": "awaiting_confirmation",
                "checkpoint": "understanding_confirmation",
                "progress_events": self.get_events(),
            }
            
        except Exception as e:
            self.emit_event(
                event_type=EventType.ERROR,
                step_name="Analysis Error",
                progress=0.0,
                message=f"Error during extraction: {str(e)}"
            )
            return {
                "extracted_data": {},
                "status": "error",
                "error": str(e),
                "progress_events": self.get_events(),
            }

    async def generate_full_analysis(self, text: str, confirmed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 2: Full multi-agent analysis after Checkpoint 1 confirmation
        Returns strategy + workflow options for Checkpoint 2
        """
        try:
            self.events = []  # Reset for Phase 2
            
            # Initialize state
            state = ProjectState(text=text)
            
            self.emit_event(
                event_type=EventType.STEP_START,
                step_name="Initializing Virtual Lab",
                progress=0.0,
                message="Starting multi-agent analysis with confirmed parameters...",
                agent_role=AgentRole.PI
            )
            
            # Store confirmed data in state for agents to reference
            state.metadata = {"confirmed_parameters": confirmed_data}
            
            self.emit_event(
                event_type=EventType.STEP_COMPLETE,
                step_name="Virtual Lab Initialized",
                progress=5.0,
                message="Team assembled and ready",
                agent_role=AgentRole.PI
            )
            
            # Immunologist Analysis
            self.emit_event(
                event_type=EventType.AGENT_THINKING,
                step_name="Immunological Analysis",
                progress=15.0,
                message="Analyzing antigen properties, epitope mapping, and binding requirements...",
                agent_role=AgentRole.IMMUNOLOGIST
            )
            
            immunologist_input = await self.immunologist.provide_input(state)
            state.agent_inputs.append(immunologist_input)
            
            self.emit_event(
                event_type=EventType.STEP_COMPLETE,
                step_name="Immunological Analysis Complete",
                progress=30.0,
                message="Immunological assessment complete - recommendations documented",
                agent_role=AgentRole.IMMUNOLOGIST
            )
            
            # ML Specialist Analysis
            self.emit_event(
                event_type=EventType.AGENT_THINKING,
                step_name="Machine Learning Analysis",
                progress=35.0,
                message="Evaluating ML approaches, model selection, and data requirements...",
                agent_role=AgentRole.ML_SPECIALIST
            )
            
            ml_input = await self.ml_specialist.provide_input(state)
            state.agent_inputs.append(ml_input)
            
            self.emit_event(
                event_type=EventType.STEP_COMPLETE,
                step_name="ML Analysis Complete",
                progress=50.0,
                message="ML strategy and computational approach defined",
                agent_role=AgentRole.ML_SPECIALIST
            )
            
            # Computational Biologist Analysis
            self.emit_event(
                event_type=EventType.AGENT_THINKING,
                step_name="Computational Biology Analysis",
                progress=55.0,
                message="Performing structural analysis, sequence optimization, and modeling...",
                agent_role=AgentRole.COMP_BIOLOGIST
            )
            
            comp_bio_input = await self.comp_biologist.provide_input(state)
            state.agent_inputs.append(comp_bio_input)
            
            self.emit_event(
                event_type=EventType.STEP_COMPLETE,
                step_name="Computational Biology Complete",
                progress=70.0,
                message="Structural insights and sequence recommendations ready",
                agent_role=AgentRole.COMP_BIOLOGIST
            )
            
            # PI Strategy Synthesis
            self.emit_event(
                event_type=EventType.AGENT_THINKING,
                step_name="Strategy Synthesis",
                progress=75.0,
                message="Synthesizing team insights into comprehensive strategy...",
                agent_role=AgentRole.PI
            )
            
            strategy = await self.pi.synthesize_strategy(state)
            
            self.emit_event(
                event_type=EventType.STEP_COMPLETE,
                step_name="Strategy Synthesis Complete",
                progress=90.0,
                message="Strategy synthesized - generating workflow options...",
                agent_role=AgentRole.PI
            )
            
            # Generate workflow options
            self.emit_event(
                event_type=EventType.STEP_START,
                step_name="Workflow Construction",
                progress=92.0,
                message="Building execution workflow with selectable steps...",
                agent_role=AgentRole.PI
            )
            
            workflow_options = self._generate_workflow_options(strategy, confirmed_data)
            
            self.emit_event(
                event_type=EventType.STEP_COMPLETE,
                step_name="Analysis Complete",
                progress=100.0,
                message="Full analysis complete - ready for your review and selection",
                agent_role=AgentRole.PI
            )
            
            return {
                "extracted_data": confirmed_data,
                "strategy": strategy,
                "workflow_options": workflow_options,
                "agent_insights": {
                    "immunologist": immunologist_input,
                    "ml_specialist": ml_input,
                    "comp_biologist": comp_bio_input
                },
                "status": "awaiting_workflow_selection",
                "checkpoint": "workflow_selection",
                "progress_events": self.get_events(),
            }
            
        except Exception as e:
            self.emit_event(
                event_type=EventType.ERROR,
                step_name="Analysis Error",
                progress=0.0,
                message=f"Error during analysis: {str(e)}"
            )
            return {
                "extracted_data": confirmed_data,
                "strategy": {},
                "status": "error",
                "error": str(e),
                "progress_events": self.get_events(),
            }
    
    def _generate_workflow_options(self, strategy: Dict[str, Any], confirmed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate selectable workflow options based on strategy
        This is a simplified version - you'll enhance with DAG logic later
        """
        # Extract strategy type to determine workflow
        strategy_type = strategy.get("title", "").lower()
        
        # Define common workflow steps (MVP - hardcoded for now)
        workflow_steps = [
            {
                "id": "fetch_candidates",
                "name": "Fetch Candidate Sequences",
                "description": "Retrieve nanobody sequences from PDB database",
                "required": True,
                "selected": True,
                "estimated_time": "2 hours",
                "estimated_cost": "$0"
            },
            {
                "id": "filter_candidates",
                "name": "Filter Candidates",
                "description": "Apply sequence and structural filters",
                "required": True,
                "selected": True,
                "estimated_time": "1 hour",
                "estimated_cost": "$0"
            },
            {
                "id": "run_esm",
                "name": "ESM Affinity Prediction",
                "description": "Run ESM language model for binding affinity prediction",
                "required": False,
                "selected": True,
                "estimated_time": "4 hours",
                "estimated_cost": "$50",
                "rounds": 2
            },
            {
                "id": "run_alphafold",
                "name": "AlphaFold3 Structural Prediction",
                "description": "Generate 3D structures for top candidates",
                "required": False,
                "selected": True,
                "estimated_time": "8 hours",
                "estimated_cost": "$200"
            },
            {
                "id": "affinity_maturation",
                "name": "In Silico Affinity Maturation",
                "description": "Optimize binding through computational mutation",
                "required": False,
                "selected": True,
                "estimated_time": "12 hours",
                "estimated_cost": "$100"
            },
            {
                "id": "in_vitro_testing",
                "name": "In Vitro Validation",
                "description": "Experimental binding assays (requires lab work)",
                "required": False,
                "selected": False,  # Default off due to cost
                "estimated_time": "2 weeks",
                "estimated_cost": "$15,000"
            }
        ]
        
        # Calculate totals
        selected_steps = [s for s in workflow_steps if s["selected"]]
        total_cost = sum(
            int(s.get("estimated_cost", "$0").replace("$", "").replace(",", ""))
            for s in selected_steps
        )
        
        return {
            "steps": workflow_steps,
            "total_estimated_cost": f"${total_cost:,}",
            "total_estimated_time": "~1 week (computational only)",
            "budget_available": confirmed_data.get("budget", "Unknown"),
            "constraints": {
                "timeline": confirmed_data.get("timeline", "Unknown"),
                "budget": confirmed_data.get("budget", "Unknown")
            }
        }

    async def process_project(self, text: str) -> Dict[str, Any]:
        """
        LEGACY METHOD - Full one-shot analysis (no checkpoints)
        Keep for backward compatibility
        """
        try:
            # Phase 1: Extract
            extract_result = await self.analyze_brief(text)
            if extract_result["status"] == "error":
                return extract_result
            
            # Phase 2: Full analysis (auto-confirm)
            full_result = await self.generate_full_analysis(
                text,
                extract_result["extracted_data"]
            )
            
            return full_result
            
        except Exception as e:
            return {
                "extracted_data": {},
                "strategy": {},
                "status": "error",
                "error": str(e),
                "progress_events": self.get_events(),
            }