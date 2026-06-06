"""Configuración centralizada - Single Source of Truth"""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMConfig:
    primary: str = "glm"
    fallback: str = "groq"
    glm_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

class SignalIQConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.llm = LLMConfig(
            primary=os.getenv("PRIMARY_LLM", "glm"),
            fallback=os.getenv("FALLBACK_LLM", "groq"),
            glm_api_key=os.getenv("GLM_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

config = SignalIQConfig()
