"""Configuración centralizada - Single Source of Truth"""
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

if os.environ.get('ENVIRONMENT') != 'test':
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
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DATA_DIR.mkdir(exist_ok=True)

        self.llm = LLMConfig(
            primary=os.getenv("PRIMARY_LLM", "glm"),
            fallback=os.getenv("FALLBACK_LLM", "groq"),
            glm_api_key=os.getenv("GLM_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

        self.db_url = os.environ.get("DATABASE_URL", "")

        @dataclass
        class DatabaseConfig:
            url: str = ""

        self.db = DatabaseConfig(url=os.getenv("DATABASE_URL", ""))

config = SignalIQConfig()
