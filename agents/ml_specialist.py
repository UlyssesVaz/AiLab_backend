# agents/ml_specialist.py  
from agents.base_agent import BaseAgent
from models.state import AgentRole, ProjectState

class MLSpecialistAgent(BaseAgent):
    def __init__(self, openai_service):
        super().__init__(openai_service, AgentRole.ML_SPECIALIST)
    
    def _define_expertise(self) -> str:
        return "protein language models (ESM), structure prediction (AlphaFold), computational protein design"
    
    def _get_analysis_prompt(self, state: ProjectState) -> str:
        previous_inputs = "\n".join([
            f"{inp.agent}: {inp.analysis}" for inp in state.agent_inputs
        ])
        
        return f"""
        You are an ML Specialist with expertise in {self.expertise}.
        
        PROJECT BRIEF:
        {state.text}
        
        PREVIOUS TEAM DISCUSSION:
        {previous_inputs}
        
        From your ML/computational perspective, analyze:
        1. Computational feasibility given timeline and budget
        2. Available tools (ESM, AlphaFold, Rosetta) suitability
        3. Data requirements and availability
        4. Your recommendation: "Modify Existing Nanobodies" or "De Novo Design"
        
        Consider that modification requires existing scaffolds while de novo needs more compute.
        """
