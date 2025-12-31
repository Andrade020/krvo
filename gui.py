#!/usr/bin/env python3
"""
Porto Mailer - Interface Gráfica Principal
==========================================
Aplicação desktop moderna para envio automatizado de emails.
"""

import sys
import os
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable
from tkinter import filedialog, messagebox
import tkinter as tk

try:
    import customtkinter as ctk
except ImportError:
    print("Instalando customtkinter...")
    os.system(f"{sys.executable} -m pip install customtkinter --break-system-packages -q")
    import customtkinter as ctk

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.settings import (
    get_settings_manager, get_settings, 
    EmailContact, EmailList, DirectoryRule, StressLimit
)
from src.auth import get_authenticator
from src.sender import EmailSender
from src.stress_controller import get_controller


# Cores do tema
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "text": "#eaeaea",
    "text_dim": "#a0a0a0",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#ef4444",
    "border": "#2d3748",
}


class LogFrame(ctk.CTkFrame):
    """Frame de log com histórico de ações."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        
        title = ctk.CTkLabel(
            self, text="📋 Log de Atividades",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text"],
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")
    
    def log(self, message: str, level: str = "info"):
        self.log_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        icon = icons.get(level, "•")
        self.log_text.insert("end", f"[{timestamp}] {icon} {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def clear(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=30, fg_color=COLORS["bg_dark"], **kwargs)
        
        self.connection_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"]
        )
        self.connection_label.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            self, text="Krvo v1.0.0",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"]
        ).pack(side="right", padx=10)
    
    def set_connected(self, email: str = ""):
        text = f"● {email}" if email else "● Conectado"
        self.connection_label.configure(text=text, text_color=COLORS["success"])
    
    def set_ready(self):
        """Status neutro - pronto para usar."""
        self.connection_label.configure(text="● Pronto", text_color=COLORS["text_dim"])
    
    def set_disconnected(self):
        """Só mostra se houver problema de conexão."""
        self.connection_label.configure(text="", text_color=COLORS["text_dim"])
    
    def set_error(self, msg: str = ""):
        text = f"● {msg}" if msg else "● Verifique as configurações"
        self.connection_label.configure(text=text, text_color=COLORS["warning"])


class SendPanel(ctk.CTkFrame):
    def __init__(self, parent, log_callback: Callable, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        self.selected_files: List[Path] = []
        self._create_widgets()
    
    def _create_widgets(self):
        ctk.CTkLabel(
            self, text="📤 Enviar Arquivos",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        drop_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        drop_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            drop_frame,
            text="📁 Clique para selecionar arquivos",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"]
        ).pack(pady=30)
        
        btn_frame = ctk.CTkFrame(drop_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 15))
        
        ctk.CTkButton(
            btn_frame, text="Selecionar Arquivos",
            command=self._select_files,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Selecionar Pasta",
            command=self._select_folder,
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["border"],
            width=150
        ).pack(side="left", padx=5)
        
        self.files_listbox = ctk.CTkTextbox(
            self, height=100,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text"]
        )
        self.files_listbox.pack(fill="x", padx=20, pady=10)
        self.files_listbox.configure(state="disabled")
        
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=10)
        
        self.dry_run_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame, text="Modo Simulação",
            variable=self.dry_run_var,
            text_color=COLORS["text"]
        ).pack(side="left", padx=5)
        
        self.force_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame, text="Ignorar Rate Limit",
            variable=self.force_var,
            text_color=COLORS["text"]
        ).pack(side="left", padx=20)
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=15)
        
        self.send_btn = ctk.CTkButton(
            action_frame, text="🚀 Enviar",
            command=self._send_files,
            fg_color=COLORS["success"],
            hover_color="#22c55e",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40, width=200
        )
        self.send_btn.pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame, text="🗑️ Limpar",
            command=self._clear_files,
            fg_color=COLORS["bg_dark"],
            height=40, width=100
        ).pack(side="left", padx=5)
    
    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="Selecionar Arquivos",
            filetypes=[
                ("Todos suportados", "*.pdf *.xlsx *.xls *.docx *.doc *.csv *.txt *.html *.png *.jpg"),
                ("Todos", "*.*"),
            ]
        )
        if files:
            for f in files:
                path = Path(f)
                if path not in self.selected_files:
                    self.selected_files.append(path)
            self._update_files_list()
            self.log(f"Selecionados {len(files)} arquivo(s)")
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="Selecionar Pasta")
        if folder:
            settings = get_settings()
            count = 0
            for item in Path(folder).iterdir():
                if item.is_file() and item.suffix.lower() in settings.allowed_extensions:
                    if item not in self.selected_files:
                        self.selected_files.append(item)
                        count += 1
            self._update_files_list()
            self.log(f"Selecionados {count} arquivo(s) da pasta")
    
    def _update_files_list(self):
        self.files_listbox.configure(state="normal")
        self.files_listbox.delete("1.0", "end")
        for i, f in enumerate(self.selected_files, 1):
            size_kb = f.stat().st_size / 1024
            self.files_listbox.insert("end", f"{i}. {f.name} ({size_kb:.1f} KB)\n")
        self.files_listbox.configure(state="disabled")
    
    def _clear_files(self):
        self.selected_files.clear()
        self._update_files_list()
        self.log("Lista limpa")
    
    def _send_files(self):
        if not self.selected_files:
            messagebox.showwarning("Aviso", "Selecione ao menos um arquivo!")
            return
        
        self.send_btn.configure(state="disabled", text="Enviando...")
        
        def send_thread():
            try:
                sender = EmailSender()
                results = sender.send_files(
                    self.selected_files,
                    force=self.force_var.get(),
                    dry_run=self.dry_run_var.get()
                )
                
                success_count = sum(1 for _, s, _, _ in results if s)
                fail_count = len(results) - success_count
                
                for path, success, msg, _ in results:
                    level = "success" if success else "error"
                    self.log(f"{Path(path).name}: {msg}", level)
                
                self.log(f"Resultado: {success_count} OK, {fail_count} falhas", 
                        "success" if fail_count == 0 else "warning")
            except Exception as e:
                self.log(f"Erro: {e}", "error")
            finally:
                self.send_btn.configure(state="normal", text="🚀 Enviar")
        
        threading.Thread(target=send_thread, daemon=True).start()


class EmailListsPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, log_callback: Callable, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        self._create_widgets()
    
    def _create_widgets(self):
        ctk.CTkLabel(
            self, text="📧 Listas de Email",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            self, text="Configure as listas de destinatários.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"]
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        ctk.CTkButton(
            self, text="+ Nova Lista",
            command=self._add_list,
            fg_color=COLORS["accent"],
            width=120
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        self.lists_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.lists_frame.pack(fill="both", expand=True, padx=20)
        self._load_lists()
    
    def _load_lists(self):
        for widget in self.lists_frame.winfo_children():
            widget.destroy()
        
        for key, email_list in get_settings().email_lists.items():
            self._create_list_card(key, email_list)
    
    def _create_list_card(self, key: str, email_list: EmailList):
        card = ctk.CTkFrame(self.lists_frame, fg_color=COLORS["bg_light"], corner_radius=8)
        card.pack(fill="x", pady=5)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header, text=f"📋 {email_list.name} ({len(email_list.contacts)} contatos)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left")
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="✏️", width=30,
            command=lambda k=key: self._edit_list(k),
            fg_color="transparent"
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(btn_frame, text="🗑️", width=30,
            command=lambda k=key: self._delete_list(k),
            fg_color="transparent"
        ).pack(side="left", padx=2)
        
        if email_list.contacts:
            preview = ", ".join([c.email for c in email_list.contacts[:3]])
            if len(email_list.contacts) > 3:
                preview += f" +{len(email_list.contacts) - 3}"
            ctk.CTkLabel(card, text=preview, font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"]).pack(anchor="w", padx=10, pady=(0, 10))
    
    def _add_list(self):
        dialog = ListEditorDialog(self, "Nova Lista", None)
        self.wait_window(dialog)
        if dialog.result:
            settings = get_settings()
            settings.email_lists[dialog.result["key"]] = EmailList(
                name=dialog.result["name"],
                description=dialog.result.get("description", ""),
                contacts=[EmailContact(name="", email=e) for e in dialog.result["emails"]]
            )
            get_settings_manager().save()
            self._load_lists()
            self.log(f"Lista '{dialog.result['name']}' criada", "success")
    
    def _edit_list(self, key: str):
        email_list = get_settings().email_lists.get(key)
        if not email_list:
            return
        
        dialog = ListEditorDialog(self, "Editar Lista", {
            "key": key,
            "name": email_list.name,
            "description": email_list.description,
            "emails": [c.email for c in email_list.contacts]
        })
        self.wait_window(dialog)
        if dialog.result:
            email_list.name = dialog.result["name"]
            email_list.description = dialog.result.get("description", "")
            email_list.contacts = [EmailContact(name="", email=e) for e in dialog.result["emails"]]
            get_settings_manager().save()
            self._load_lists()
            self.log(f"Lista '{dialog.result['name']}' atualizada", "success")
    
    def _delete_list(self, key: str):
        email_list = get_settings().email_lists.get(key)
        if email_list and messagebox.askyesno("Confirmar", f"Excluir lista '{email_list.name}'?"):
            del get_settings().email_lists[key]
            get_settings_manager().save()
            self._load_lists()
            self.log(f"Lista excluída", "warning")


class ListEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, data: Optional[dict]):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x550")
        self.configure(fg_color=COLORS["bg_dark"])
        self.result = None
        self.data = data or {}
        self.grab_set()
        self._create_widgets()
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 275
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        ctk.CTkLabel(self, text="Nome:", text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 5))
        self.name_entry = ctk.CTkEntry(self, width=400, fg_color=COLORS["bg_medium"])
        self.name_entry.pack(padx=20)
        if self.data.get("name"):
            self.name_entry.insert(0, self.data["name"])
        
        ctk.CTkLabel(self, text="Identificador:", text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(15, 5))
        self.key_entry = ctk.CTkEntry(self, width=400, fg_color=COLORS["bg_medium"])
        self.key_entry.pack(padx=20)
        if self.data.get("key"):
            self.key_entry.insert(0, self.data["key"])
            self.key_entry.configure(state="disabled")
        
        ctk.CTkLabel(self, text="Emails (um por linha):", text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(15, 5))
        self.emails_text = ctk.CTkTextbox(self, width=400, height=200, fg_color=COLORS["bg_medium"])
        self.emails_text.pack(padx=20)
        if self.data.get("emails"):
            self.emails_text.insert("1.0", "\n".join(self.data["emails"]))
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Salvar", command=self._save, fg_color=COLORS["success"], width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, fg_color=COLORS["bg_medium"], width=100).pack(side="left", padx=10)
    
    def _save(self):
        name = self.name_entry.get().strip()
        key = self.key_entry.get().strip().lower().replace(" ", "_") or name.lower().replace(" ", "_")
        emails = [e.strip() for e in self.emails_text.get("1.0", "end").split("\n") if "@" in e]
        
        if not name:
            messagebox.showerror("Erro", "Nome é obrigatório")
            return
        
        self.result = {"key": key, "name": name, "emails": emails}
        self.destroy()


class RulesPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, log_callback: Callable, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        self._create_widgets()
    
    def _create_widgets(self):
        ctk.CTkLabel(self, text="📁 Regras de Diretório",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self, text="Configure como diferentes arquivos devem ser tratados.",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 15))
        
        ctk.CTkButton(self, text="+ Nova Regra", command=self._add_rule,
            fg_color=COLORS["accent"], width=120).pack(anchor="w", padx=20, pady=(0, 15))
        
        self.rules_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.rules_frame.pack(fill="both", expand=True, padx=20)
        self._load_rules()
    
    def _load_rules(self):
        for widget in self.rules_frame.winfo_children():
            widget.destroy()
        
        sorted_rules = sorted(get_settings().directory_rules, key=lambda r: r.priority, reverse=True)
        for i, rule in enumerate(sorted_rules):
            self._create_rule_card(i, rule)
    
    def _create_rule_card(self, index: int, rule: DirectoryRule):
        card = ctk.CTkFrame(self.rules_frame, fg_color=COLORS["bg_light"], corner_radius=8)
        card.pack(fill="x", pady=5)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        
        status_icon = "●" if rule.active else "○"
        status_color = COLORS["success"] if rule.active else COLORS["text_dim"]
        
        ctk.CTkLabel(header, text=f"{status_icon} {rule.name} (P:{rule.priority})",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=status_color).pack(side="left")
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="✏️", width=30,
            command=lambda i=index: self._edit_rule(i), fg_color="transparent").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="🗑️", width=30,
            command=lambda i=index: self._delete_rule(i), fg_color="transparent").pack(side="left", padx=2)
        
        ctk.CTkLabel(card, text=f"Padrão: {rule.pattern} | Lista: {rule.email_list}",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"]).pack(anchor="w", padx=10, pady=(0, 10))
    
    def _add_rule(self):
        dialog = RuleEditorDialog(self, "Nova Regra", None)
        self.wait_window(dialog)
        if dialog.result:
            get_settings().directory_rules.append(DirectoryRule(**dialog.result))
            get_settings_manager().save()
            self._load_rules()
            self.log(f"Regra '{dialog.result['name']}' criada", "success")
    
    def _edit_rule(self, index: int):
        sorted_rules = sorted(get_settings().directory_rules, key=lambda r: r.priority, reverse=True)
        rule = sorted_rules[index]
        original_index = get_settings().directory_rules.index(rule)
        
        from dataclasses import asdict
        dialog = RuleEditorDialog(self, "Editar Regra", asdict(rule))
        self.wait_window(dialog)
        if dialog.result:
            get_settings().directory_rules[original_index] = DirectoryRule(**dialog.result)
            get_settings_manager().save()
            self._load_rules()
            self.log(f"Regra atualizada", "success")
    
    def _delete_rule(self, index: int):
        sorted_rules = sorted(get_settings().directory_rules, key=lambda r: r.priority, reverse=True)
        rule = sorted_rules[index]
        if messagebox.askyesno("Confirmar", f"Excluir regra '{rule.name}'?"):
            get_settings().directory_rules.remove(rule)
            get_settings_manager().save()
            self._load_rules()
            self.log("Regra excluída", "warning")


class RuleEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, data: Optional[dict]):
        super().__init__(parent)
        self.title(title)
        self.geometry("550x650")
        self.configure(fg_color=COLORS["bg_dark"])
        self.result = None
        self.data = data or {}
        self.grab_set()
        self._create_widgets()
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 275
        y = (self.winfo_screenheight() // 2) - 325
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text="Nome:", text_color=COLORS["text"]).pack(anchor="w", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(scroll, width=450, fg_color=COLORS["bg_medium"])
        self.name_entry.pack()
        if self.data.get("name"):
            self.name_entry.insert(0, self.data["name"])
        
        ctk.CTkLabel(scroll, text="Padrão (ex: relatorios/vendas):", text_color=COLORS["text"]).pack(anchor="w", pady=(15, 5))
        self.pattern_entry = ctk.CTkEntry(scroll, width=450, fg_color=COLORS["bg_medium"])
        self.pattern_entry.pack()
        if self.data.get("pattern"):
            self.pattern_entry.insert(0, self.data["pattern"])
        
        ctk.CTkLabel(scroll, text="Lista de Destinatários:", text_color=COLORS["text"]).pack(anchor="w", pady=(15, 5))
        list_names = list(get_settings().email_lists.keys())
        self.list_combo = ctk.CTkComboBox(scroll, width=450, values=list_names, fg_color=COLORS["bg_medium"])
        self.list_combo.pack()
        if self.data.get("email_list") and self.data["email_list"] in list_names:
            self.list_combo.set(self.data["email_list"])
        
        ctk.CTkLabel(scroll, text="Template Assunto:", text_color=COLORS["text"]).pack(anchor="w", pady=(15, 5))
        self.subject_entry = ctk.CTkEntry(scroll, width=450, fg_color=COLORS["bg_medium"])
        self.subject_entry.pack()
        self.subject_entry.insert(0, self.data.get("subject_template", "[AUTO] {filename}"))
        
        ctk.CTkLabel(scroll, text="Template Corpo:", text_color=COLORS["text"]).pack(anchor="w", pady=(15, 5))
        self.body_text = ctk.CTkTextbox(scroll, width=450, height=120, fg_color=COLORS["bg_medium"])
        self.body_text.pack()
        self.body_text.insert("1.0", self.data.get("body_template", "Anexo: {filename}\nData: {date}"))
        
        ctk.CTkLabel(scroll, text="Categoria (rate limit):", text_color=COLORS["text"]).pack(anchor="w", pady=(15, 5))
        self.category_entry = ctk.CTkEntry(scroll, width=450, fg_color=COLORS["bg_medium"])
        self.category_entry.pack()
        self.category_entry.insert(0, self.data.get("stress_category", "default"))
        
        ctk.CTkLabel(scroll, text="Prioridade:", text_color=COLORS["text"]).pack(anchor="w", pady=(15, 5))
        self.priority_entry = ctk.CTkEntry(scroll, width=100, fg_color=COLORS["bg_medium"])
        self.priority_entry.pack(anchor="w")
        self.priority_entry.insert(0, str(self.data.get("priority", 50)))
        
        self.active_var = ctk.BooleanVar(value=self.data.get("active", True))
        ctk.CTkCheckBox(scroll, text="Regra Ativa", variable=self.active_var, text_color=COLORS["text"]).pack(anchor="w", pady=15)
        
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Salvar", command=self._save, fg_color=COLORS["success"], width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, fg_color=COLORS["bg_medium"], width=100).pack(side="left", padx=10)
    
    def _save(self):
        name = self.name_entry.get().strip()
        pattern = self.pattern_entry.get().strip()
        if not name or not pattern:
            messagebox.showerror("Erro", "Nome e padrão são obrigatórios")
            return
        
        try:
            priority = int(self.priority_entry.get().strip())
        except ValueError:
            priority = 50
        
        self.result = {
            "name": name,
            "pattern": pattern,
            "email_list": self.list_combo.get(),
            "subject_template": self.subject_entry.get().strip(),
            "body_template": self.body_text.get("1.0", "end").strip(),
            "stress_category": self.category_entry.get().strip() or "default",
            "priority": priority,
            "active": self.active_var.get()
        }
        self.destroy()


class SettingsPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, log_callback: Callable, status_bar: StatusBar, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self.log = log_callback
        self.status_bar = status_bar
        self._create_widgets()
    
    def _create_widgets(self):
        settings = get_settings()
        
        ctk.CTkLabel(self, text="⚙️ Configurações",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 15))
        
        # Azure Section
        azure_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        azure_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(azure_frame, text="🔐 Credenciais Azure AD",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(azure_frame, text="Client ID:", text_color=COLORS["text_dim"]).pack(anchor="w", padx=15)
        self.client_entry = ctk.CTkEntry(azure_frame, width=400, fg_color=COLORS["bg_medium"])
        self.client_entry.pack(padx=15, pady=(0, 10))
        if settings.azure.client_id:
            self.client_entry.insert(0, settings.azure.client_id)
        
        ctk.CTkLabel(azure_frame, text="Tenant ID:", text_color=COLORS["text_dim"]).pack(anchor="w", padx=15)
        self.tenant_entry = ctk.CTkEntry(azure_frame, width=400, fg_color=COLORS["bg_medium"])
        self.tenant_entry.pack(padx=15, pady=(0, 10))
        if settings.azure.tenant_id:
            self.tenant_entry.insert(0, settings.azure.tenant_id)
        
        ctk.CTkLabel(azure_frame, text="Email:", text_color=COLORS["text_dim"]).pack(anchor="w", padx=15)
        self.email_entry = ctk.CTkEntry(azure_frame, width=400, fg_color=COLORS["bg_medium"])
        self.email_entry.pack(padx=15, pady=(0, 10))
        if settings.azure.email:
            self.email_entry.insert(0, settings.azure.email)
        
        ctk.CTkLabel(azure_frame, text="Senha:", text_color=COLORS["text_dim"]).pack(anchor="w", padx=15)
        self.pass_entry = ctk.CTkEntry(azure_frame, width=400, show="•", fg_color=COLORS["bg_medium"])
        self.pass_entry.pack(padx=15, pady=(0, 10))
        if settings.azure.password:
            self.pass_entry.insert(0, settings.azure.password)
        
        azure_btn_frame = ctk.CTkFrame(azure_frame, fg_color="transparent")
        azure_btn_frame.pack(pady=15)
        
        ctk.CTkButton(azure_btn_frame, text="💾 Salvar", command=self._save_azure,
            fg_color=COLORS["success"], width=120).pack(side="left", padx=5)
        ctk.CTkButton(azure_btn_frame, text="🔌 Testar", command=self._test_connection,
            fg_color=COLORS["accent"], width=120).pack(side="left", padx=5)
        
        # Export/Import
        export_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        export_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(export_frame, text="💼 Backup",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", padx=15, pady=(15, 10))
        
        btn_row = ctk.CTkFrame(export_frame, fg_color="transparent")
        btn_row.pack(pady=15)
        
        ctk.CTkButton(btn_row, text="📤 Exportar", command=self._export_config,
            fg_color=COLORS["bg_dark"], width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="📥 Importar", command=self._import_config,
            fg_color=COLORS["bg_dark"], width=120).pack(side="left", padx=5)
    
    def _save_azure(self):
        settings = get_settings()
        settings.azure.client_id = self.client_entry.get().strip()
        settings.azure.tenant_id = self.tenant_entry.get().strip()
        settings.azure.email = self.email_entry.get().strip()
        settings.azure.password = self.pass_entry.get()
        get_settings_manager().save()
        self.log("Credenciais salvas", "success")
    
    def _test_connection(self):
        self.log("Testando conexão...")
        def test():
            try:
                auth = get_authenticator()
                auth.clear_cache()
                result = auth.test_connection()
                if result["success"]:
                    self.log(f"Conectado: {result['user_email']}", "success")
                    self.status_bar.set_connected(result['user_email'])
                else:
                    self.log(f"Falha: {result['error']}", "error")
                    self.status_bar.set_ready()
            except Exception as e:
                self.log(f"Erro: {e}", "error")
                self.status_bar.set_ready()
        threading.Thread(target=test, daemon=True).start()
    
    def _export_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            get_settings_manager().export_config(Path(path))
            self.log("Config exportada", "success")
    
    def _import_config(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            get_settings_manager().import_config(Path(path))
            self.log("Config importada", "success")


class AboutPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        self._create_widgets()
    
    def _create_widgets(self):
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(pady=40)
        
        ctk.CTkLabel(logo_frame, text="🐦‍⬛", font=ctk.CTkFont(size=72)).pack()
        ctk.CTkLabel(logo_frame, text="Krvo",
            font=ctk.CTkFont(size=36, weight="bold"), text_color=COLORS["accent"]).pack(pady=(10, 5))
        ctk.CTkLabel(logo_frame, text="Mensageiro Digital",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"]).pack()
        ctk.CTkLabel(logo_frame, text="v1.0.0",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"]).pack(pady=(5,0))
        
        ctk.CTkLabel(self, text="Como um corvo mensageiro, leva suas mensagens\ncom precisão e confiabilidade.",
            font=ctk.CTkFont(size=13), text_color=COLORS["text"], justify="center").pack(pady=20)
        
        features_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        features_frame.pack(fill="x", padx=50, pady=20)
        
        for feat in ["✦ Envio por regras de diretório", "✦ Listas configuráveis", 
                     "✦ Rate limiting inteligente", "✦ Templates personalizáveis", "✦ CLI + GUI"]:
            ctk.CTkLabel(features_frame, text=feat, font=ctk.CTkFont(size=12),
                text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=3)
        
        dev_frame = ctk.CTkFrame(self, fg_color="transparent")
        dev_frame.pack(side="bottom", pady=20)
        
        ctk.CTkLabel(dev_frame, text="Lucas Rafael de Andrade Dev. Software LTDA",
            font=ctk.CTkFont(size=10), text_color=COLORS["text_dim"]).pack()
        
        links = ctk.CTkFrame(dev_frame, fg_color="transparent")
        links.pack(pady=5)
        
        ctk.CTkButton(links, text="in", width=25, height=25, font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_dark"],
            command=lambda: webbrowser.open("https://www.linkedin.com/in/lucas-rafael-de-andrade/")).pack(side="left", padx=3)
        ctk.CTkButton(links, text="gh", width=25, height=25, font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_dark"],
            command=lambda: webbrowser.open("https://github.com/Andrade020")).pack(side="left", padx=3)


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Krvo - Mensageiro Digital")
        self.geometry("1100x750")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Tenta carregar ícone
        try:
            icon_path = Path(__file__).parent / "assets" / "krvo.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except:
            pass
        
        self._create_widgets()
        self._check_connection()
    
    def _create_widgets(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        sidebar = ctk.CTkFrame(main, width=200, fg_color=COLORS["bg_medium"], corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        ctk.CTkLabel(sidebar, text="🐦‍⬛", font=ctk.CTkFont(size=36)).pack(pady=(20, 5))
        ctk.CTkLabel(sidebar, text="Krvo",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["accent"]).pack()
        
        self.nav_buttons = {}
        for text, key in [("📤 Enviar", "send"), ("📧 Listas", "lists"),
                          ("📁 Regras", "rules"), ("⚙️ Config", "settings"), ("ℹ️ Sobre", "about")]:
            btn = ctk.CTkButton(sidebar, text=text, font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color=COLORS["bg_light"],
                anchor="w", height=40, command=lambda k=key: self._show_panel(k))
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn
        
        content = ctk.CTkFrame(main, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)
        
        self.log_frame = LogFrame(content, height=150)
        self.log_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.panels_container = ctk.CTkFrame(content, fg_color="transparent")
        self.panels_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_bar = StatusBar(content)
        self.status_bar.pack(fill="x", side="bottom")
        
        self.panels = {
            "send": SendPanel(self.panels_container, self.log_frame.log),
            "lists": EmailListsPanel(self.panels_container, self.log_frame.log),
            "rules": RulesPanel(self.panels_container, self.log_frame.log),
            "settings": SettingsPanel(self.panels_container, self.log_frame.log, self.status_bar),
            "about": AboutPanel(self.panels_container),
        }
        
        self._show_panel("send")
        self.log_frame.log("Krvo iniciado - pronto para enviar mensagens 🐦‍⬛", "info")
    
    def _show_panel(self, key: str):
        for p in self.panels.values():
            p.pack_forget()
        self.panels[key].pack(fill="both", expand=True)
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color=COLORS["bg_light"] if k == key else "transparent")
    
    def _check_connection(self):
        def check():
            try:
                auth = get_authenticator()
                if auth.is_configured():
                    result = auth.test_connection()
                    if result["success"]:
                        self.status_bar.set_connected(result["user_email"])
                        self.log_frame.log(f"Conectado: {result['user_email']}", "success")
                        return
                    else:
                        # Tem config mas falhou - mostra pronto, não erro
                        self.status_bar.set_ready()
                else:
                    # Não configurado ainda - fica neutro
                    self.status_bar.set_ready()
                    self.log_frame.log("Configure suas credenciais em ⚙️ Config", "info")
            except Exception as e:
                # Erro silencioso na inicialização
                self.status_bar.set_ready()
        threading.Thread(target=check, daemon=True).start()


def run_gui():
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
