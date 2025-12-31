#!/usr/bin/env python3
"""
Porto Mailer - Módulo de Configurações
=======================================
Gerencia todas as configurações persistentes do aplicativo.
"""

import json
import os
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import copy


def get_app_data_dir() -> Path:
    """Retorna o diretório de dados do aplicativo."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    
    app_dir = base / "Krvo"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


@dataclass
class EmailContact:
    """Representa um contato de email."""
    name: str
    email: str
    active: bool = True
    
    def to_graph_format(self) -> Dict:
        """Converte para formato da API Graph."""
        return {"emailAddress": {"address": self.email}}


@dataclass 
class EmailList:
    """Lista de contatos de email."""
    name: str
    description: str = ""
    contacts: List[EmailContact] = field(default_factory=list)
    
    def get_active_contacts(self) -> List[EmailContact]:
        return [c for c in self.contacts if c.active]
    
    def to_graph_format(self) -> List[Dict]:
        return [c.to_graph_format() for c in self.get_active_contacts()]


@dataclass
class DirectoryRule:
    """Regra de envio para um diretório."""
    name: str
    pattern: str  # Padrão do caminho (ex: "relatorios/aging")
    email_list: str  # Nome da lista de emails
    subject_template: str
    body_template: str
    stress_category: str = "default"
    priority: int = 50
    active: bool = True
    
    def format_subject(self, filename: str, filepath: str = "") -> str:
        now = datetime.now()
        return self.subject_template.format(
            filename=filename,
            filepath=filepath,
            date=now.strftime("%d/%m/%Y"),
            datetime=now.strftime("%d/%m/%Y %H:%M"),
        )
    
    def format_body(self, filename: str, filepath: str = "") -> str:
        now = datetime.now()
        return self.body_template.format(
            filename=filename,
            filepath=filepath,
            date=now.strftime("%d/%m/%Y"),
            datetime=now.strftime("%d/%m/%Y %H:%M"),
        )


@dataclass
class StressLimit:
    """Limites de rate limiting para uma categoria."""
    category: str
    max_per_day: int = 5
    max_per_week: int = 20
    cooldown_minutes: int = 10


@dataclass
class AzureCredentials:
    """Credenciais do Azure AD."""
    client_id: str = ""
    tenant_id: str = ""
    email: str = ""
    password: str = ""  # Armazenado de forma segura
    
    def is_configured(self) -> bool:
        return all([self.client_id, self.tenant_id, self.email, self.password])


@dataclass
class AppSettings:
    """Configurações completas do aplicativo."""
    # Credenciais Azure
    azure: AzureCredentials = field(default_factory=AzureCredentials)
    
    # Listas de email
    email_lists: Dict[str, EmailList] = field(default_factory=dict)
    
    # Regras de diretório
    directory_rules: List[DirectoryRule] = field(default_factory=list)
    
    # Limites de stress
    stress_limits: Dict[str, StressLimit] = field(default_factory=dict)
    
    # Configurações gerais
    root_paths: List[str] = field(default_factory=list)
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".pdf", ".html", ".htm", ".xlsx", ".xls", 
        ".docx", ".doc", ".csv", ".txt", ".png", 
        ".jpg", ".jpeg"
    ])
    max_attachment_mb: int = 25
    
    # Interface
    theme: str = "dark"
    language: str = "pt-BR"
    minimize_to_tray: bool = True
    start_minimized: bool = False
    
    # Metadados
    version: str = "1.0.0"
    last_updated: str = ""


class SettingsManager:
    """Gerencia persistência e acesso às configurações."""
    
    SETTINGS_FILE = "settings.json"
    STRESS_LOG_FILE = "stress_log.json"
    TOKEN_CACHE_FILE = "token_cache.json"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or get_app_data_dir()
        self.settings_path = self.config_dir / self.SETTINGS_FILE
        self.stress_path = self.config_dir / self.STRESS_LOG_FILE
        self.token_path = self.config_dir / self.TOKEN_CACHE_FILE
        
        self._settings: Optional[AppSettings] = None
        self._load_or_create()
    
    def _load_or_create(self) -> None:
        """Carrega configurações existentes ou cria padrão."""
        if self.settings_path.exists():
            try:
                self._settings = self._load_from_file()
            except Exception as e:
                print(f"[AVISO] Erro ao carregar config: {e}. Criando nova.")
                self._settings = self._create_default()
                self._save_to_file()
        else:
            self._settings = self._create_default()
            self._save_to_file()
    
    def _create_default(self) -> AppSettings:
        """Cria configurações padrão."""
        settings = AppSettings()
        
        # Listas padrão
        settings.email_lists = {
            "admin": EmailList(
                name="Administradores",
                description="Equipe de administração",
                contacts=[]
            ),
            "interno": EmailList(
                name="Equipe Interna",
                description="Funcionários internos",
                contacts=[]
            ),
            "clientes": EmailList(
                name="Clientes",
                description="Lista de clientes",
                contacts=[]
            ),
            "alertas": EmailList(
                name="Alertas",
                description="Destinatários de alertas críticos",
                contacts=[]
            ),
        }
        
        # Regras padrão
        settings.directory_rules = [
            DirectoryRule(
                name="Relatórios Gerais",
                pattern="relatorios",
                email_list="interno",
                subject_template="[AUTO] Relatório - {filename}",
                body_template="""Prezados,

Segue em anexo o relatório: {filename}

Data: {date}

Este é um e-mail automático.

—
Enviado via Krvo 🐦‍⬛""",
                stress_category="relatorios",
                priority=50,
            ),
            DirectoryRule(
                name="Alertas",
                pattern="alertas",
                email_list="alertas",
                subject_template="[ALERTA] {filename} - {date}",
                body_template="""⚠️ ALERTA

Arquivo: {filename}
Data: {datetime}

Verifique os detalhes no anexo.

—
Enviado via Krvo 🐦‍⬛""",
                stress_category="alertas",
                priority=100,
            ),
        ]
        
        # Limites de stress padrão
        settings.stress_limits = {
            "relatorios": StressLimit("relatorios", 5, 25, 15),
            "alertas": StressLimit("alertas", 50, 200, 1),
            "default": StressLimit("default", 3, 10, 30),
        }
        
        settings.last_updated = datetime.now().isoformat()
        return settings
    
    def _load_from_file(self) -> AppSettings:
        """Carrega configurações do arquivo JSON."""
        with open(self.settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        settings = AppSettings()
        
        # Azure credentials
        if "azure" in data:
            settings.azure = AzureCredentials(**data["azure"])
        
        # Email lists
        if "email_lists" in data:
            for key, lst_data in data["email_lists"].items():
                contacts = [EmailContact(**c) for c in lst_data.get("contacts", [])]
                settings.email_lists[key] = EmailList(
                    name=lst_data.get("name", key),
                    description=lst_data.get("description", ""),
                    contacts=contacts
                )
        
        # Directory rules
        if "directory_rules" in data:
            settings.directory_rules = [
                DirectoryRule(**rule) for rule in data["directory_rules"]
            ]
        
        # Stress limits
        if "stress_limits" in data:
            for key, limit_data in data["stress_limits"].items():
                settings.stress_limits[key] = StressLimit(**limit_data)
        
        # Configurações simples
        for key in ["root_paths", "allowed_extensions", "max_attachment_mb",
                    "theme", "language", "minimize_to_tray", "start_minimized",
                    "version", "last_updated"]:
            if key in data:
                setattr(settings, key, data[key])
        
        return settings
    
    def _save_to_file(self) -> None:
        """Salva configurações no arquivo JSON."""
        data = {
            "azure": asdict(self._settings.azure),
            "email_lists": {
                key: {
                    "name": lst.name,
                    "description": lst.description,
                    "contacts": [asdict(c) for c in lst.contacts]
                }
                for key, lst in self._settings.email_lists.items()
            },
            "directory_rules": [asdict(rule) for rule in self._settings.directory_rules],
            "stress_limits": {
                key: asdict(limit) 
                for key, limit in self._settings.stress_limits.items()
            },
            "root_paths": self._settings.root_paths,
            "allowed_extensions": self._settings.allowed_extensions,
            "max_attachment_mb": self._settings.max_attachment_mb,
            "theme": self._settings.theme,
            "language": self._settings.language,
            "minimize_to_tray": self._settings.minimize_to_tray,
            "start_minimized": self._settings.start_minimized,
            "version": self._settings.version,
            "last_updated": datetime.now().isoformat(),
        }
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @property
    def settings(self) -> AppSettings:
        """Acesso às configurações."""
        return self._settings
    
    def save(self) -> None:
        """Salva as configurações atuais."""
        self._save_to_file()
    
    def reload(self) -> None:
        """Recarrega do arquivo."""
        self._load_or_create()
    
    def reset_to_default(self) -> None:
        """Reseta para configurações padrão."""
        self._settings = self._create_default()
        self._save_to_file()
    
    def export_config(self, path: Path) -> None:
        """Exporta configurações para arquivo."""
        data = {
            "email_lists": {
                key: {
                    "name": lst.name,
                    "description": lst.description,
                    "contacts": [asdict(c) for c in lst.contacts]
                }
                for key, lst in self._settings.email_lists.items()
            },
            "directory_rules": [asdict(rule) for rule in self._settings.directory_rules],
            "stress_limits": {
                key: asdict(limit) 
                for key, limit in self._settings.stress_limits.items()
            },
            "exported_at": datetime.now().isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_config(self, path: Path, merge: bool = False) -> None:
        """Importa configurações de arquivo."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not merge:
            self._settings.email_lists.clear()
            self._settings.directory_rules.clear()
            self._settings.stress_limits.clear()
        
        # Importa listas
        for key, lst_data in data.get("email_lists", {}).items():
            contacts = [EmailContact(**c) for c in lst_data.get("contacts", [])]
            self._settings.email_lists[key] = EmailList(
                name=lst_data.get("name", key),
                description=lst_data.get("description", ""),
                contacts=contacts
            )
        
        # Importa regras
        for rule_data in data.get("directory_rules", []):
            self._settings.directory_rules.append(DirectoryRule(**rule_data))
        
        # Importa limites
        for key, limit_data in data.get("stress_limits", {}).items():
            self._settings.stress_limits[key] = StressLimit(**limit_data)
        
        self._save_to_file()


# Instância global
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager(config_dir: Optional[Path] = None) -> SettingsManager:
    """Retorna instância global do gerenciador de configurações."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager(config_dir)
    return _settings_manager


def get_settings() -> AppSettings:
    """Atalho para acessar configurações."""
    return get_settings_manager().settings
