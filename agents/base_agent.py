# agents/base_agent.py
from abc import ABC, abstractmethod
from models.state import ProjectState, AgentInput, AgentRole
from services.openai_service import OpenAIService

class BaseAgent(ABC):
    def __init__(self, openai_service: OpenAIService, role: AgentRole):
        self.openai_service = openai_service
        self.role = role
        self.expertise = self._define_expertise()
    
    @abstractmethod
    def _define_expertise(self) -> str:
        """Define this agent's area of expertise"""
        pass
    
    @abstractmethod
    def _get_analysis_prompt(self, state: ProjectState) -> str:
        """Generate the prompt for this agent's analysis"""
        pass
    
    async def provide_input(self, state: ProjectState) -> AgentInput:
        """Standard method all agents use to provide input"""
        prompt = self._get_analysis_prompt(state)
        
        response = await self.openai_service.chat_completion(prompt)
        
        # Parse structured response
        analysis, recommendation, confidence, reasoning = self._parse_response(response)
        
        return AgentInput(
            agent=self.role,
            analysis=analysis,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _parse_response(self, response: str) -> tuple:
        """Parse agent response into structured components"""
        # Simple parsing - in production could use structured outputs
        lines = response.strip().split('\n')
        
        analysis = response  # Full response as analysis
        
        # Extract recommendation
        if "de novo" in response.lower():
            recommendation = "De Novo Design"
        else:
            recommendation = "Modify Existing Nanobodies"
            
        # Extract confidence (look for numbers like 0.8, 80%, etc.)
        import re
        conf_match = re.search(r'confidence[:\s]*([0-9.]+)', response.lower())
        confidence = float(conf_match.group(1)) if conf_match else 0.7
        
        # Extract reasoning points
        reasoning = [line.strip('- ') for line in lines if line.strip().startswith('- ')]
        
        return analysis, recommendation, confidence, reasoning