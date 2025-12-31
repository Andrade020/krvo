#!/usr/bin/env python3
"""
Porto Mailer - Módulo de Envio de Emails
========================================
Envio de emails com anexos via Microsoft Graph API.
"""

import base64
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .settings import get_settings, DirectoryRule
from .auth import get_authenticator
from .stress_controller import get_controller


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".html": "text/html",
    ".htm": "text/html",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".zip": "application/zip",
}


class EmailSender:
    """Gerencia envio de emails via Microsoft Graph."""
    
    def __init__(self):
        self.auth = get_authenticator()
        self.stress = get_controller()
    
    @property
    def headers(self) -> Dict[str, str]:
        return self.auth.get_headers()
    
    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Valida arquivo para envio.
        
        Returns:
            (válido, mensagem)
        """
        settings = get_settings()
        
        if not file_path.exists():
            return False, f"Arquivo não encontrado: {file_path}"
        
        if not file_path.is_file():
            return False, f"Não é um arquivo: {file_path}"
        
        ext = file_path.suffix.lower()
        if ext not in settings.allowed_extensions:
            return False, f"Extensão não permitida: {ext}"
        
        size = file_path.stat().st_size
        max_bytes = settings.max_attachment_mb * 1024 * 1024
        
        if size > max_bytes:
            size_mb = size / (1024 * 1024)
            return False, f"Arquivo muito grande: {size_mb:.1f}MB (máx: {settings.max_attachment_mb}MB)"
        
        if size == 0:
            return False, "Arquivo vazio"
        
        return True, "OK"
    
    def find_matching_rule(self, file_path: Path) -> Optional[DirectoryRule]:
        """
        Encontra regra que corresponde ao caminho.
        
        Returns:
            DirectoryRule ou None se nenhuma corresponder
        """
        settings = get_settings()
        file_str = str(file_path).replace("\\", "/").lower()
        
        # Ordena por prioridade
        sorted_rules = sorted(
            [r for r in settings.directory_rules if r.active],
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            pattern = rule.pattern.replace("\\", "/").lower()
            if pattern in file_str:
                return rule
        
        return None
    
    def get_recipients(self, list_name: str) -> List[Dict]:
        """Obtém lista de destinatários no formato Graph."""
        settings = get_settings()
        
        if list_name in settings.email_lists:
            return settings.email_lists[list_name].to_graph_format()
        
        return []
    
    def prepare_email(
        self, 
        file_path: Path, 
        rule: DirectoryRule,
        custom_recipients: Optional[List[str]] = None,
        custom_subject: Optional[str] = None,
        custom_body: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepara payload do email.
        """
        filename = file_path.name
        filepath = str(file_path)
        
        # Assunto e corpo
        subject = custom_subject or rule.format_subject(filename, filepath)
        body = custom_body or rule.format_body(filename, filepath)
        
        # Destinatários
        if custom_recipients:
            recipients = [
                {"emailAddress": {"address": email}}
                for email in custom_recipients
            ]
        else:
            recipients = self.get_recipients(rule.email_list)
        
        if not recipients:
            raise ValueError(f"Nenhum destinatário na lista '{rule.email_list}'")
        
        # Lê e codifica arquivo
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        
        ext = file_path.suffix.lower()
        content_type = CONTENT_TYPES.get(ext, "application/octet-stream")
        
        return {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body
                },
                "toRecipients": recipients,
                "attachments": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": filename,
                        "contentType": content_type,
                        "contentBytes": content
                    }
                ]
            }
        }
    
    def send_file(
        self, 
        file_path: str | Path,
        rule: Optional[DirectoryRule] = None,
        custom_recipients: Optional[List[str]] = None,
        custom_subject: Optional[str] = None,
        custom_body: Optional[str] = None,
        force: bool = False,
        dry_run: bool = False
    ) -> Tuple[bool, str, Dict]:
        """
        Envia arquivo por email.
        
        Args:
            file_path: Caminho do arquivo
            rule: Regra específica (se None, detecta automaticamente)
            custom_recipients: Lista de emails (sobrescreve regra)
            custom_subject: Assunto personalizado
            custom_body: Corpo personalizado
            force: Ignora rate limiting
            dry_run: Apenas simula
        
        Returns:
            (sucesso, mensagem, detalhes)
        """
        file_path = Path(file_path).resolve()
        details = {"file": str(file_path)}
        
        # Valida arquivo
        valid, msg = self.validate_file(file_path)
        if not valid:
            return False, msg, details
        
        # Encontra ou usa regra
        if rule is None:
            rule = self.find_matching_rule(file_path)
            if rule is None:
                return False, "Nenhuma regra corresponde a este arquivo", details
        
        details["rule"] = rule.name
        details["category"] = rule.stress_category
        
        # Verifica rate limiting
        if not force:
            can_send, reason = self.stress.can_send(rule.stress_category)
            if not can_send:
                return False, f"Rate limit: {reason}", details
        
        # Prepara email
        try:
            payload = self.prepare_email(
                file_path, rule, 
                custom_recipients, custom_subject, custom_body
            )
        except ValueError as e:
            return False, str(e), details
        
        recipients = payload["message"]["toRecipients"]
        details["recipients"] = [r["emailAddress"]["address"] for r in recipients]
        details["subject"] = payload["message"]["subject"]
        
        if dry_run:
            return True, "Simulação concluída", details
        
        # Envia
        try:
            resp = requests.post(
                f"{GRAPH_BASE_URL}/me/sendMail",
                json=payload,
                headers=self.headers,
                timeout=60
            )
            resp.raise_for_status()
            
            # Registra envio
            self.stress.record_send(
                category=rule.stress_category,
                filename=file_path.name,
                recipients_count=len(recipients),
                success=True
            )
            
            return True, "Email enviado com sucesso", details
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            self.stress.record_send(
                category=rule.stress_category,
                filename=file_path.name,
                recipients_count=len(recipients),
                success=False
            )
            return False, error_msg, details
            
        except requests.exceptions.RequestException as e:
            return False, f"Erro de conexão: {e}", details
    
    def send_files(
        self, 
        file_paths: List[str | Path],
        force: bool = False,
        dry_run: bool = False
    ) -> List[Tuple[str, bool, str, Dict]]:
        """
        Envia múltiplos arquivos.
        
        Returns:
            Lista de (caminho, sucesso, mensagem, detalhes)
        """
        results = []
        
        for path in file_paths:
            success, msg, details = self.send_file(path, force=force, dry_run=dry_run)
            results.append((str(path), success, msg, details))
        
        return results
    
    def send_custom_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[str | Path]] = None,
        stress_category: str = "default",
        force: bool = False,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Envia email customizado (sem regra).
        
        Args:
            recipients: Lista de emails
            subject: Assunto
            body: Corpo do email
            attachments: Lista de arquivos anexos (opcional)
            stress_category: Categoria para rate limiting
            force: Ignora rate limiting
            dry_run: Apenas simula
        
        Returns:
            (sucesso, mensagem)
        """
        if not recipients:
            return False, "Nenhum destinatário especificado"
        
        # Verifica rate limiting
        if not force:
            can_send, reason = self.stress.can_send(stress_category)
            if not can_send:
                return False, f"Rate limit: {reason}"
        
        # Prepara destinatários
        to_recipients = [
            {"emailAddress": {"address": email}}
            for email in recipients
        ]
        
        # Prepara anexos
        attachment_list = []
        if attachments:
            settings = get_settings()
            max_bytes = settings.max_attachment_mb * 1024 * 1024
            
            for att_path in attachments:
                att_path = Path(att_path)
                
                if not att_path.exists():
                    return False, f"Anexo não encontrado: {att_path}"
                
                size = att_path.stat().st_size
                if size > max_bytes:
                    return False, f"Anexo muito grande: {att_path.name}"
                
                with open(att_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode("utf-8")
                
                ext = att_path.suffix.lower()
                content_type = CONTENT_TYPES.get(ext, "application/octet-stream")
                
                attachment_list.append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att_path.name,
                    "contentType": content_type,
                    "contentBytes": content
                })
        
        # Monta payload
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body
                },
                "toRecipients": to_recipients,
            }
        }
        
        if attachment_list:
            payload["message"]["attachments"] = attachment_list
        
        if dry_run:
            return True, f"Simulação: enviaria para {len(recipients)} destinatário(s)"
        
        # Envia
        try:
            resp = requests.post(
                f"{GRAPH_BASE_URL}/me/sendMail",
                json=payload,
                headers=self.headers,
                timeout=60
            )
            resp.raise_for_status()
            
            self.stress.record_send(
                category=stress_category,
                filename=attachments[0].name if attachments else "email_custom",
                recipients_count=len(recipients),
                success=True
            )
            
            return True, "Email enviado com sucesso"
            
        except requests.exceptions.HTTPError as e:
            return False, f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        except requests.exceptions.RequestException as e:
            return False, f"Erro de conexão: {e}"


# Funções de conveniência
def send_file(
    file_path: str | Path,
    force: bool = False,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """Atalho para enviar arquivo."""
    sender = EmailSender()
    success, msg, _ = sender.send_file(file_path, force=force, dry_run=dry_run)
    return success, msg


def send_files(
    file_paths: List[str | Path],
    force: bool = False,
    dry_run: bool = False
) -> Dict[str, Tuple[bool, str]]:
    """Atalho para enviar múltiplos arquivos."""
    sender = EmailSender()
    results = sender.send_files(file_paths, force=force, dry_run=dry_run)
    return {path: (success, msg) for path, success, msg, _ in results}
