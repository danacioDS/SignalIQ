"""Persistencia unificada - PostgreSQL + JSON state"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from signaliq.core.config import config

class SignalPersistence:
    """Maneja toda la persistencia de SignalIQ"""
    
    def __init__(self):
        self.state_file = config.DATA_DIR / "persistence_state.json"
        self._state_cache = None
    
    # PostgreSQL operations
    def get_db_connection(self):
        """Obtiene conexión a PostgreSQL"""
        if not config.db.url:
            raise ValueError("DATABASE_URL not configured")
        return psycopg2.connect(config.db.url)
    
    def save_signal(self, ticker: str, ndi: float, classification: str, metadata: Dict = None):
        """Guarda señal en PostgreSQL"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO signals (ticker, ndi, classification, metadata, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (ticker, ndi, classification, json.dumps(metadata or {})))
                conn.commit()
    
    def get_recent_signals(self, ticker: str, limit: int = 100) -> List[Dict]:
        """Obtiene señales recientes"""
        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM signals 
                    WHERE ticker = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (ticker, limit))
                return [dict(row) for row in cur.fetchall()]
    
    # JSON state operations (legacy de layer4)
    def get_state(self) -> Dict:
        """Obtiene estado de persistencia (streaks, etc.)"""
        if self._state_cache is None:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    self._state_cache = json.load(f)
            else:
                self._state_cache = {}
        return self._state_cache
    
    def save_state(self):
        """Guarda estado en JSON"""
        if self._state_cache is not None:
            with open(self.state_file, 'w') as f:
                json.dump(self._state_cache, f, indent=2)
    
    def update_streak(self, ticker: str, streak: int, last_ndi: float):
        """Actualiza streak de un ticker"""
        state = self.get_state()
        if ticker not in state:
            state[ticker] = {}
        state[ticker]['streak'] = streak
        state[ticker]['last_ndi'] = last_ndi
        state[ticker]['updated_at'] = datetime.now().isoformat()
        self.save_state()
    
    # Migración helper
    def migrate_json_to_postgres(self):
        """Migra datos de JSON a PostgreSQL (opcional)"""
        state = self.get_state()
        for ticker, data in state.items():
            self.save_signal(
                ticker=ticker,
                ndi=data.get('last_ndi', 0),
                classification='migrated',
                metadata={'streak': data.get('streak', 0)}
            )
        print(f"✅ Migrados {len(state)} tickers a PostgreSQL")
