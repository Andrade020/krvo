#!/usr/bin/env python3
"""
Porto Mailer - Controle de Rate Limiting
========================================
Evita spam controlando frequência de envios.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, asdict

from .settings import get_settings_manager, get_settings


@dataclass
class SendRecord:
    """Registro de um envio."""
    timestamp: str
    category: str
    filename: str
    recipients_count: int
    success: bool = True


class StressController:
    """Controlador de frequência de envio."""
    
    def __init__(self):
        manager = get_settings_manager()
        self.log_file = manager.stress_path
        self.records: Dict[str, List[Dict]] = {}
        self._load_records()
    
    def _load_records(self) -> None:
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = data.get("records", {})
                    self._cleanup_old()
            except (json.JSONDecodeError, IOError):
                self.records = {}
        else:
            self.records = {}
    
    def _save_records(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump({"records": self.records}, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[ERRO] Não foi possível salvar stress log: {e}")
    
    def _cleanup_old(self) -> None:
        """Remove registros com mais de 7 dias."""
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        
        for category in list(self.records.keys()):
            self.records[category] = [
                r for r in self.records[category]
                if r.get("timestamp", "") > cutoff
            ]
            if not self.records[category]:
                del self.records[category]
    
    def _get_limits(self, category: str) -> Tuple[int, int, int]:
        """Retorna (max_dia, max_semana, cooldown_min) para categoria."""
        settings = get_settings()
        
        if category in settings.stress_limits:
            limit = settings.stress_limits[category]
            return (limit.max_per_day, limit.max_per_week, limit.cooldown_minutes)
        
        if "default" in settings.stress_limits:
            limit = settings.stress_limits["default"]
            return (limit.max_per_day, limit.max_per_week, limit.cooldown_minutes)
        
        return (5, 20, 15)  # Fallback
    
    def _count_recent(self, category: str, since: datetime) -> int:
        if category not in self.records:
            return 0
        
        since_str = since.isoformat()
        return sum(
            1 for r in self.records[category]
            if r.get("timestamp", "") >= since_str and r.get("success", True)
        )
    
    def _get_last_send_time(self, category: str) -> Optional[datetime]:
        if category not in self.records or not self.records[category]:
            return None
        
        timestamps = [
            r.get("timestamp") for r in self.records[category] 
            if r.get("timestamp") and r.get("success", True)
        ]
        if not timestamps:
            return None
        
        try:
            return datetime.fromisoformat(max(timestamps))
        except ValueError:
            return None
    
    def can_send(self, category: str) -> Tuple[bool, str]:
        """
        Verifica se pode enviar nesta categoria.
        
        Returns:
            (pode_enviar, motivo_se_bloqueado)
        """
        max_dia, max_semana, cooldown_min = self._get_limits(category)
        now = datetime.now()
        
        # Cooldown
        last_send = self._get_last_send_time(category)
        if last_send:
            elapsed = (now - last_send).total_seconds() / 60
            if elapsed < cooldown_min:
                remaining = cooldown_min - elapsed
                return False, f"Aguarde {remaining:.0f} min (cooldown de {cooldown_min} min)"
        
        # Limite diário
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        count_today = self._count_recent(category, today_start)
        if count_today >= max_dia:
            return False, f"Limite diário atingido ({count_today}/{max_dia})"
        
        # Limite semanal
        week_start = now - timedelta(days=7)
        count_week = self._count_recent(category, week_start)
        if count_week >= max_semana:
            return False, f"Limite semanal atingido ({count_week}/{max_semana})"
        
        return True, "OK"
    
    def record_send(
        self, 
        category: str, 
        filename: str, 
        recipients_count: int,
        success: bool = True
    ) -> None:
        """Registra um envio."""
        record = SendRecord(
            timestamp=datetime.now().isoformat(),
            category=category,
            filename=filename,
            recipients_count=recipients_count,
            success=success
        )
        
        if category not in self.records:
            self.records[category] = []
        
        self.records[category].append(asdict(record))
        self._save_records()
    
    def get_status(self, category: Optional[str] = None) -> Dict:
        """Status dos limites."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        
        settings = get_settings()
        categories = [category] if category else list(settings.stress_limits.keys())
        
        status = {}
        for cat in categories:
            max_dia, max_semana, cooldown = self._get_limits(cat)
            count_today = self._count_recent(cat, today_start)
            count_week = self._count_recent(cat, week_start)
            last_send = self._get_last_send_time(cat)
            can, reason = self.can_send(cat)
            
            status[cat] = {
                "today": count_today,
                "today_limit": max_dia,
                "week": count_week,
                "week_limit": max_semana,
                "cooldown_min": cooldown,
                "last_send": last_send.isoformat() if last_send else None,
                "can_send": can,
                "reason": reason if not can else None,
            }
        
        return status
    
    def get_history(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Retorna histórico de envios."""
        if category:
            records = self.records.get(category, [])
        else:
            records = []
            for cat_records in self.records.values():
                records.extend(cat_records)
        
        # Ordena por timestamp decrescente
        records = sorted(records, key=lambda r: r.get("timestamp", ""), reverse=True)
        return records[:limit]
    
    def force_reset(self, category: Optional[str] = None) -> None:
        """Reseta contadores."""
        if category:
            if category in self.records:
                del self.records[category]
        else:
            self.records = {}
        
        self._save_records()


# Instância global
_controller: Optional[StressController] = None


def get_controller() -> StressController:
    """Retorna instância global do controlador."""
    global _controller
    if _controller is None:
        _controller = StressController()
    return _controller
