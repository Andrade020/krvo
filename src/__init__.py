#!/usr/bin/env python3
"""
Porto Mailer - Sistema de Envio Automático de Emails
====================================================

Desenvolvido por Lucas Rafael de Andrade Desenvolvimento de Software LTDA

Sistema para envio automatizado de emails via Microsoft Graph API,
com suporte a regras por diretório, rate limiting e interface gráfica.
"""

__version__ = "1.0.0"
__author__ = "Lucas Rafael de Andrade"

from .settings import (
    get_settings,
    get_settings_manager,
    SettingsManager,
    AppSettings,
    EmailContact,
    EmailList,
    DirectoryRule,
    StressLimit,
    AzureCredentials,
)

from .auth import (
    get_authenticator,
    get_token,
    get_headers,
    GraphAuthenticator,
)

from .stress_controller import (
    get_controller,
    StressController,
)

from .sender import (
    send_file,
    send_files,
    EmailSender,
)

__all__ = [
    # Versão
    "__version__",
    "__author__",
    
    # Configurações
    "get_settings",
    "get_settings_manager",
    "SettingsManager",
    "AppSettings",
    "EmailContact",
    "EmailList",
    "DirectoryRule",
    "StressLimit",
    "AzureCredentials",
    
    # Autenticação
    "get_authenticator",
    "get_token",
    "get_headers",
    "GraphAuthenticator",
    
    # Controle de Stress
    "get_controller",
    "StressController",
    
    # Envio
    "send_file",
    "send_files",
    "EmailSender",
]
