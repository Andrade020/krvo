#!/usr/bin/env python3
"""
Porto Mailer - Módulo de Autenticação Microsoft Graph
=====================================================
Autenticação via ROPC com cache de tokens.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
from dataclasses import dataclass, asdict

from .settings import get_settings_manager, get_settings


GRAPH_SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "offline_access",
]


@dataclass
class TokenData:
    """Dados do token em cache."""
    access_token: str
    refresh_token: str
    expires_at: str
    token_type: str = "Bearer"
    
    def is_expired(self, margin_seconds: int = 300) -> bool:
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now() >= (expires - timedelta(seconds=margin_seconds))
        except:
            return True
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TokenData":
        return cls(**data)


class TokenCache:
    """Cache de tokens em arquivo."""
    
    def __init__(self, cache_path: Optional[Path] = None):
        if cache_path:
            self.cache_path = cache_path
        else:
            manager = get_settings_manager()
            self.cache_path = manager.token_path
    
    def save(self, token_data: TokenData) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(token_data.to_dict(), f, indent=2)
        try:
            os.chmod(self.cache_path, 0o600)
        except:
            pass
    
    def load(self) -> Optional[TokenData]:
        if not self.cache_path.exists():
            return None
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TokenData.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
    
    def clear(self) -> None:
        if self.cache_path.exists():
            self.cache_path.unlink()


class GraphAuthenticator:
    """
    Autenticador Microsoft Graph usando ROPC.
    """
    
    def __init__(self):
        self.cache = TokenCache()
        self._current_token: Optional[TokenData] = None
    
    @property
    def credentials(self):
        """Obtém credenciais das configurações."""
        return get_settings().azure
    
    @property
    def token_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.credentials.tenant_id}/oauth2/v2.0/token"
    
    def is_configured(self) -> bool:
        """Verifica se as credenciais estão configuradas."""
        return self.credentials.is_configured()
    
    def _request_token_with_password(self) -> TokenData:
        """Obtém token via ROPC."""
        if not self.is_configured():
            raise RuntimeError("Credenciais não configuradas. Configure em Configurações > Azure.")
        
        payload = {
            "client_id": self.credentials.client_id,
            "scope": " ".join(GRAPH_SCOPES),
            "username": self.credentials.email,
            "password": self.credentials.password,
            "grant_type": "password",
        }
        
        resp = requests.post(self.token_url, data=payload, timeout=30)
        
        if resp.status_code != 200:
            error_data = resp.json()
            error = error_data.get("error", "unknown")
            desc = error_data.get("error_description", "Sem descrição")
            
            # Analisa erros comuns
            if "AADSTS50126" in desc:
                raise RuntimeError("Credenciais inválidas. Verifique email e senha.")
            elif "AADSTS7000218" in desc:
                raise RuntimeError("ROPC desabilitado. Peça ao admin habilitar 'Allow public client flows'.")
            elif "AADSTS50076" in desc or "AADSTS50079" in desc:
                raise RuntimeError("MFA ativo. ROPC não suporta autenticação multifator.")
            elif "AADSTS65001" in desc:
                raise RuntimeError("Permissões não concedidas. Faça login interativo primeiro.")
            elif "AADSTS700016" in desc:
                raise RuntimeError("App não encontrado. Verifique Client ID e Tenant ID.")
            else:
                raise RuntimeError(f"Erro de autenticação: {error} - {desc}")
        
        data = resp.json()
        expires_in = data.get("expires_in", 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        token_data = TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=expires_at.isoformat(),
            token_type=data.get("token_type", "Bearer"),
        )
        
        self.cache.save(token_data)
        return token_data
    
    def _refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """Renova token usando refresh token."""
        payload = {
            "client_id": self.credentials.client_id,
            "scope": " ".join(GRAPH_SCOPES),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        
        try:
            resp = requests.post(self.token_url, data=payload, timeout=30)
            
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            token_data = TokenData(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", refresh_token),
                expires_at=expires_at.isoformat(),
                token_type=data.get("token_type", "Bearer"),
            )
            
            self.cache.save(token_data)
            return token_data
            
        except Exception:
            return None
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Obtém token válido.
        
        Estratégia:
        1. Cache se válido
        2. Refresh se expirado
        3. Re-autentica se refresh falhar
        """
        if not force_refresh:
            cached = self.cache.load()
            
            if cached and not cached.is_expired():
                self._current_token = cached
                return cached.access_token
            
            if cached and cached.refresh_token:
                refreshed = self._refresh_token(cached.refresh_token)
                if refreshed:
                    self._current_token = refreshed
                    return refreshed.access_token
        
        token_data = self._request_token_with_password()
        self._current_token = token_data
        return token_data.access_token
    
    def get_headers(self) -> Dict[str, str]:
        """Headers HTTP com autenticação."""
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }
    
    def clear_cache(self) -> None:
        """Limpa cache de tokens."""
        self.cache.clear()
        self._current_token = None
    
    def test_connection(self) -> Dict:
        """
        Testa a conexão com o Graph API.
        
        Returns:
            Dict com resultado do teste
        """
        try:
            token = self.get_token()
            
            resp = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=self.get_headers(),
                timeout=15
            )
            
            if resp.status_code == 200:
                user = resp.json()
                return {
                    "success": True,
                    "user_name": user.get("displayName", ""),
                    "user_email": user.get("mail", user.get("userPrincipalName", "")),
                    "job_title": user.get("jobTitle", ""),
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {resp.status_code}: {resp.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_status(self) -> Dict:
        """Retorna status da autenticação."""
        cached = self.cache.load()
        
        return {
            "configured": self.is_configured(),
            "has_cached_token": cached is not None,
            "token_expired": cached.is_expired() if cached else None,
            "expires_at": cached.expires_at if cached else None,
            "email": self.credentials.email if self.is_configured() else None,
        }


# Instância global
_authenticator: Optional[GraphAuthenticator] = None


def get_authenticator() -> GraphAuthenticator:
    """Retorna instância global do autenticador."""
    global _authenticator
    if _authenticator is None:
        _authenticator = GraphAuthenticator()
    return _authenticator


def get_token() -> str:
    """Atalho para obter token."""
    return get_authenticator().get_token()


def get_headers() -> Dict[str, str]:
    """Atalho para obter headers."""
    return get_authenticator().get_headers()
