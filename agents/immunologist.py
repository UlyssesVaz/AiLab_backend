# agents/immunologist.py
from agents.base_agent import BaseAgent
from models.state import AgentRole, ProjectState


class ImmunologistAgent(BaseAgent):
    def __init__(self, openai_service):
        super().__init__(openai_service, AgentRole.IMMUNOLOGIST)
    
    def _define_expertise(self) -> str:
        return "antibody biology, immune responses, target druggability, nanobody engineering"
    
    def _get_analysis_prompt(self, state: ProjectState) -> str:
        previous_inputs = "\n".join([
            f"{inp.agent}: {inp.analysis}" for inp in state.agent_inputs
        ])
        
        return f"""
        You are an Immunologist with expertise in {self.expertise}.
        
        PROJECT BRIEF:
        {state.text}
        
        PREVIOUS TEAM DISCUSSION:
        {previous_inputs}
        
        From your immunology perspective, analyze:
        1. Target biology and druggability
        2. Likelihood existing nanobodies exist for this target
        3. Therapeutic vs research tool considerations
        4. Your recommendation: "Modify Existing Nanobodies" or "De Novo Design"
        
        Format your response with:
        - Clear analysis of the immunology aspects
        - Your recommendation with reasoning
        - Confidence level (0.0-1.0)
        - Key considerations for the team
        """
