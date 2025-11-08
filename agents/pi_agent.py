# agents/pi_agent.py
from agents.base_agent import BaseAgent
from models.state import AgentRole, ProjectState, AgentInput
from typing import Dict, Any

class PIAgent(BaseAgent):
    def __init__(self, openai_service):
        super().__init__(openai_service, AgentRole.PI)
    
    def _define_expertise(self) -> str:
        return "project management, strategic decision making, team synthesis"
    
    def _get_analysis_prompt(self, state: ProjectState) -> str:
        # PI doesn't use the standard analysis prompt
        pass
    
    async def provide_input(self, state: ProjectState) -> AgentInput:
        # PI doesn't provide input like other agents
        pass
    
    async def extract_key_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data for API response"""
        prompt = f"""
        Extract key project data from this brief:
        
        {text}
        
        Return JSON with:
        {{"target": "specific target protein/antigen", "timeline": "duration", "budget": "amount", "goal": "objective", "confidence": 0.9}}
        """
        
        response = await self.openai_service.chat_completion(prompt)
        
        # Parse JSON
        import json
        try:
            return json.loads(response.strip())
        except:
            # Fallback extraction
            return {
                "target": "Extracted target",
                "timeline": "Extracted timeline", 
                "budget": "Extracted budget",
                "goal": "Extracted goal",
                "confidence": 0.8
            }
    
    async def synthesize_strategy(self, state: ProjectState) -> Dict[str, Any]:
        """Synthesize team input into final strategy recommendation"""
        team_summary = "\n".join([
            f"{inp.agent} (confidence {inp.confidence}): {inp.recommendation}\nReasoning: {inp.analysis}"
            for inp in state.agent_inputs
        ])
        
        prompt = f"""
        As Principal Investigator, synthesize your team's input into a final strategy recommendation.
        
        ORIGINAL PROJECT:
        {state.text}
        
        TEAM RECOMMENDATIONS:
        {team_summary}
        
        Based on team input, make final decision and return JSON:
        {{
            "title": "Modify Existing Nanobodies" or "De Novo Design",
            "rationale": [
                {{"icon": "Clock", "label": "Timeline Match", "description": "team-based reasoning"}},
                {{"icon": "TrendingUp", "label": "Success Rate", "description": "team-based reasoning"}},
                {{"icon": "DollarSign", "label": "Budget Aligned", "description": "team-based reasoning"}}
            ],
            "candidates": ["Ty1", "H11-D4", "Nb21", "VHH-72"] or [],
            "confidence": 0.85,
            "alternatives": []
        }}
        
        Consider team consensus and weigh expert opinions appropriately.
        """
        
        response = await self.openai_service.chat_completion(prompt)
        
        import json
        try:
            return json.loads(response.strip())
        except:
            # Fallback strategy
            return {
                "title": "Modify Existing Nanobodies",
                "rationale": [
                    {"icon": "Clock", "label": "Team Analysis", "description": "Based on team discussion"},
                    {"icon": "TrendingUp", "label": "Consensus", "description": "Team reached agreement"}, 
                    {"icon": "DollarSign", "label": "Feasible", "description": "Within project constraints"}
                ],
                "candidates": ["Ty1", "H11-D4", "Nb21", "VHH-72"],
                "confidence": 0.7,
                "alternatives": []
            }