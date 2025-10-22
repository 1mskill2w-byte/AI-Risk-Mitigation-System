"""
Ollama Client for LLM integration
"""
import requests
import json
from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from datetime import datetime

logger = structlog.get_logger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM"""
    text: str
    model: str
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model: str = "llama3.1",
                 timeout: int = 120):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.logger = logger.bind(component="ollama_client")
        
    def health_check(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning("Ollama health check failed", error=str(e))
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            self.logger.error("Failed to list models", error=str(e))
            return []
    
    async def generate(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      temperature: float = 0.7,
                      max_tokens: Optional[int] = None,
                      stream: bool = False) -> LLMResponse:
        """Generate response from Ollama"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            self.logger.info("Generating response", 
                           model=self.model, 
                           prompt_length=len(prompt))
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return LLMResponse(
                    text=data.get("response", ""),
                    model=self.model,
                    timestamp=datetime.now(),
                    metadata={
                        "total_duration": data.get("total_duration"),
                        "load_duration": data.get("load_duration"),
                        "prompt_eval_count": data.get("prompt_eval_count"),
                        "eval_count": data.get("eval_count"),
                        "eval_duration": data.get("eval_duration")
                    }
                )
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error("LLM generation failed", error=str(e))
            raise
    
    async def chat(self, 
                   messages: List[Dict[str, str]], 
                   temperature: float = 0.7,
                   max_tokens: Optional[int] = None) -> LLMResponse:
        """Chat completion with message history"""
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            self.logger.info("Chat completion", 
                           model=self.model, 
                           message_count=len(messages))
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return LLMResponse(
                    text=data.get("message", {}).get("content", ""),
                    model=self.model,
                    timestamp=datetime.now(),
                    metadata={
                        "total_duration": data.get("total_duration"),
                        "load_duration": data.get("load_duration"),
                        "prompt_eval_count": data.get("prompt_eval_count"),
                        "eval_count": data.get("eval_count"),
                        "eval_duration": data.get("eval_duration")
                    }
                )
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error("Chat completion failed", error=str(e))
            raise
