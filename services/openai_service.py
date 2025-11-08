#openai_service.py
import openai
from typing import Dict, Any
import json
import re
from pydantic import BaseModel

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    async def extract_project_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from project brief text"""
        
        prompt = f"""
        You are a scientific project analyst. Extract the following information from this project brief:
        
        Text: {text}
        
        Return a JSON object with these fields:
        - target: What protein/antigen they want to target (be specific)
        - timeline: Project timeline (extract duration like "3 months", "6 weeks")  
        - budget: Budget amount (extract numbers like "$50k", "$100,000")
        - goal: Primary objective (therapeutic development, research tool, etc.)
        - confidence: Your confidence in this extraction (0.0-1.0)
        
        If information is missing, use "Not specified" but still provide your best guess based on context.
        
        Return ONLY valid JSON, no other text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective for JSON extraction
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown if present)
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            return json.loads(content)
            
        except Exception as e:
            # Fallback: basic regex extraction
            return self._fallback_extraction(text)
    
    async def generate_strategy(self, extracted_data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Generate strategy recommendation based on extracted data"""
        
        prompt = f"""
        You are a computational biology strategy expert. Based on this project data, recommend an approach:
        
        Project Data:
        - Target: {extracted_data['target']}
        - Timeline: {extracted_data['timeline']}
        - Budget: {extracted_data['budget']}
        - Goal: {extracted_data['goal']}

        And here is the FULL, ORIGINAL PROJECT BRIEF for you to check for context:
        ---
        {original_text}
        ---
        
        Recommend either "Modify Existing Nanobodies" or "De Novo Design" based on:
        1. Timeline constraints (short = modify existing, long = de novo)
        2. Budget (lower = modify, higher = de novo)
        3. Target novelty (known targets = modify, novel = de novo)
        
        Return JSON with:
        {{
            "title": "Modify Existing Nanobodies" or "De Novo Design",
            "rationale": [
                {{"icon": "Clock", "label": "Timeline Match", "description": "explanation"}},
                {{"icon": "TrendingUp", "label": "Success Rate", "description": "explanation"}},
                {{"icon": "DollarSign", "label": "Budget Aligned", "description": "explanation"}}
            ],
            "candidates": ["Ty1", "H11-D4", "Nb21", "VHH-72"] or [],
            "confidence": 0.85,
            "alternatives": [{{"title": "Alternative approach", "why": "explanation"}}]
        }}
        
        Return ONLY valid JSON.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
                
            return json.loads(content)
            
        except Exception as e:
            # Fallback strategy
            return self._fallback_strategy(extracted_data)
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Regex-based fallback for data extraction"""
        timeline_match = re.search(r'(\d+)\s*(month|week|day)s?', text.lower())
        budget_match = re.search(r'\$?(\d+(?:,\d+)*(?:\.\d+)?)\s*[km]?', text.lower())
        
        return {
            "target": "SARS-CoV-2 spike protein",  # Default assumption
            "timeline": f"{timeline_match.group(1)} {timeline_match.group(2)}s" if timeline_match else "3 months",
            "budget": f"${budget_match.group(1)}" if budget_match else "Not specified",
            "goal": "Therapeutic development",
            "confidence": 0.5
        }
    
    def _fallback_strategy(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy based on simple rules"""
        timeline = extracted_data.get('timeline', '').lower()
        is_short_timeline = any(word in timeline for word in ['week', '1 month', '2 month'])
        
        return {
            "title": "Modify Existing Nanobodies" if is_short_timeline else "De Novo Design",
            "rationale": [
                {"icon": "Clock", "label": "Timeline Match", "description": "Based on timeline constraints"},
                {"icon": "TrendingUp", "label": "Success Rate", "description": "Proven approach"},
                {"icon": "DollarSign", "label": "Budget Aligned", "description": "Cost-effective solution"}
            ],
            "candidates": ["Ty1", "H11-D4", "Nb21", "VHH-72"] if is_short_timeline else [],
            "confidence": 0.7,
            "alternatives": []
        }
    
    async def chat_completion(self, prompt: str) -> str:
        """Simple chat completion for agent discussions"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")