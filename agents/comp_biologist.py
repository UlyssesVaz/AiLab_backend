# agents/comp_biologist.py
from agents.base_agent import BaseAgent
from models.state import AgentRole, ProjectState

class CompBiologistAgent(BaseAgent):
    def __init__(self, openai_service):
        super().__init__(openai_service, AgentRole.COMP_BIOLOGIST)
    
    def _define_expertise(self) -> str:
        return "protein design workflows, molecular dynamics, Rosetta, experimental validation"
    
    def _get_analysis_prompt(self, state: ProjectState) -> str:
        previous_inputs = "\n".join([
            f"{inp.agent}: {inp.analysis}" for inp in state.agent_inputs
        ])
        
        return f"""
        You are a Computational Biologist with expertise in {self.expertise}.
        
        PROJECT BRIEF:
        {state.text}
        
        PREVIOUS TEAM DISCUSSION:
        {previous_inputs}
        
        From your computational implementation perspective, analyze:
        1. Workflow design and implementation feasibility  
        2. Resource requirements (compute, time, expertise)
        3. Expected success rates for different approaches
        4. Your recommendation: "Modify Existing Nanobodies" or "De Novo Design"
        
        Focus on practical implementation and what's actually achievable.
        """