import customtkinter as ctk
import sys
from pathlib import Path

# Adiciona src ao path (igual o gui.py faz)
sys.path.insert(0, str(Path(__file__).parent))

from src.settings import get_settings_manager, get_settings, EmailContact, EmailList, DirectoryRule
from src.auth import get_authenticator
from src.sender import EmailSender
from src.stress_controller import get_controller

COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "accent": "#e94560",
    "text": "#eaeaea",
    "text_dim": "#a0a0a0",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#ef4444",
}

class LogFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        title = ctk.CTkLabel(self, text="Log de Atividades", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", padx=10, pady=(10, 5))
        self.log_text = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_dark"], wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")
    
    def log(self, message, level="info"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.configure(state="disabled")

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=30, fg_color=COLORS["bg_dark"], **kwargs)
        self.connection_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11))
        self.connection_label.pack(side="left", padx=10)
        ctk.CTkLabel(self, text="Krvo v1.0.0", font=ctk.CTkFont(size=11)).pack(side="right", padx=10)

class SendPanel(ctk.CTkFrame):
    def __init__(self, parent, log_callback, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        ctk.CTkLabel(self, text="Enviar Arquivos", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        drop_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        drop_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(drop_frame, text="Clique para selecionar arquivos", font=ctk.CTkFont(size=13)).pack(pady=30)
        btn_frame = ctk.CTkFrame(drop_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 15))
        ctk.CTkButton(btn_frame, text="Selecionar Arquivos", fg_color=COLORS["accent"], width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Selecionar Pasta", fg_color=COLORS["bg_dark"], width=150).pack(side="left", padx=5)
        self.files_listbox = ctk.CTkTextbox(self, height=100, font=ctk.CTkFont(size=11), fg_color=COLORS["bg_dark"])
        self.files_listbox.pack(fill="x", padx=20, pady=10)
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkCheckBox(options_frame, text="Modo Simulacao").pack(side="left", padx=5)
        ctk.CTkCheckBox(options_frame, text="Ignorar Rate Limit").pack(side="left", padx=20)
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(action_frame, text="Enviar", fg_color=COLORS["success"], font=ctk.CTkFont(size=14, weight="bold"), height=40, width=200).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Limpar", fg_color=COLORS["bg_dark"], height=40, width=100).pack(side="left", padx=5)

class EmailListsPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, log_callback, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        ctk.CTkLabel(self, text="Listas de Email", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkLabel(self, text="Configure as listas de destinatarios.", font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 15))
        ctk.CTkButton(self, text="+ Nova Lista", fg_color=COLORS["accent"], width=120).pack(anchor="w", padx=20, pady=(0, 15))
        for i in range(5):
            card = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=8)
            card.pack(fill="x", padx=20, pady=5)
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(header, text=f"Lista {i+1} ({i+2} contatos)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
            btn_frame = ctk.CTkFrame(header, fg_color="transparent")
            btn_frame.pack(side="right")
            ctk.CTkButton(btn_frame, text="Editar", width=60, fg_color="transparent").pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Excluir", width=60, fg_color="transparent").pack(side="left", padx=2)

class RulesPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, log_callback, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        ctk.CTkLabel(self, text="Regras de Diretorio", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkLabel(self, text="Configure como diferentes arquivos devem ser tratados.", font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 15))
        ctk.CTkButton(self, text="+ Nova Regra", fg_color=COLORS["accent"], width=120).pack(anchor="w", padx=20, pady=(0, 15))
        for i in range(5):
            card = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=8)
            card.pack(fill="x", padx=20, pady=5)
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(header, text=f"Regra {i+1} (P:{50+i})", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
            btn_frame = ctk.CTkFrame(header, fg_color="transparent")
            btn_frame.pack(side="right")
            ctk.CTkButton(btn_frame, text="Editar", width=60, fg_color="transparent").pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Excluir", width=60, fg_color="transparent").pack(side="left", padx=2)
            ctk.CTkLabel(card, text=f"Padrao: /path/to/folder{i}/* | Lista: lista_{i}", font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"]).pack(anchor="w", padx=10, pady=(0, 10))

class SettingsPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, log_callback, status_bar, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        self.status_bar = status_bar
        settings = get_settings()
        ctk.CTkLabel(self, text="Configuracoes", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 15))
        azure_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        azure_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(azure_frame, text="Credenciais Azure AD", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        ctk.CTkLabel(azure_frame, text="Client ID:").pack(anchor="w", padx=15)
        self.client_entry = ctk.CTkEntry(azure_frame, width=400, fg_color=COLORS["bg_medium"])
        self.client_entry.pack(padx=15, pady=(0, 10))
        ctk.CTkLabel(azure_frame, text="Tenant ID:").pack(anchor="w", padx=15)
        self.tenant_entry = ctk.CTkEntry(azure_frame, width=400, fg_color=COLORS["bg_medium"])
        self.tenant_entry.pack(padx=15, pady=(0, 10))
        ctk.CTkLabel(azure_frame, text="Email:").pack(anchor="w", padx=15)
        self.email_entry = ctk.CTkEntry(azure_frame, width=400, fg_color=COLORS["bg_medium"])
        self.email_entry.pack(padx=15, pady=(0, 10))
        ctk.CTkLabel(azure_frame, text="Senha:").pack(anchor="w", padx=15)
        self.pass_entry = ctk.CTkEntry(azure_frame, width=400, show="*", fg_color=COLORS["bg_medium"])
        self.pass_entry.pack(padx=15, pady=(0, 10))
        azure_btn_frame = ctk.CTkFrame(azure_frame, fg_color="transparent")
        azure_btn_frame.pack(pady=15)
        ctk.CTkButton(azure_btn_frame, text="Salvar", fg_color=COLORS["success"], width=120).pack(side="left", padx=5)
        ctk.CTkButton(azure_btn_frame, text="Testar", fg_color=COLORS["accent"], width=120).pack(side="left", padx=5)
        export_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        export_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(export_frame, text="Backup", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        btn_row = ctk.CTkFrame(export_frame, fg_color="transparent")
        btn_row.pack(pady=15)
        ctk.CTkButton(btn_row, text="Exportar", fg_color=COLORS["bg_dark"], width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="Importar", fg_color=COLORS["bg_dark"], width=120).pack(side="left", padx=5)

class AboutPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(pady=40)
        ctk.CTkLabel(logo_frame, text="K", font=ctk.CTkFont(size=72, weight="bold"), text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(logo_frame, text="Krvo", font=ctk.CTkFont(size=36, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(logo_frame, text="Mensageiro Digital", font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"]).pack()
        ctk.CTkLabel(logo_frame, text="v1.0.0", font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"]).pack(pady=(5,0))
        features_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        features_frame.pack(fill="x", padx=50, pady=20)
        for feat in ["Envio por regras de diretorio", "Listas configuraveis", "Rate limiting inteligente", "Templates personalizaveis", "CLI + GUI"]:
            ctk.CTkLabel(features_frame, text="* " + feat, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=3)
