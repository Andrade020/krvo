#!/usr/bin/env python3
"""
Aggressive reproduction script for CustomTkinter Segmentation Fault on Linux

This version creates MORE widgets to stress-test the system.
"""

import customtkinter as ctk

print(f"CustomTkinter version: {ctk.__version__}")
print("="*60)
print("AGGRESSIVE SEGFAULT TEST")
print("="*60)
print()

COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#0f3460',
    'accent': '#e94560',
    'text': '#eaeaea',
    'text_dim': '#a0a0a0',
    'success': '#4ecca3',
}


class StatusBar(ctk.CTkFrame):
    """Custom status bar widget"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=30, fg_color=COLORS["bg_dark"], **kwargs)
        self.label = ctk.CTkLabel(self, text="Status", font=ctk.CTkFont(size=11))
        self.label.pack(side="left", padx=10)
        ctk.CTkLabel(self, text="v1.0.0", font=ctk.CTkFont(size=11)).pack(side="right", padx=10)


class LogFrame(ctk.CTkFrame):
    """Custom log frame with text widget"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.textbox = ctk.CTkTextbox(self, height=100, fg_color=COLORS["bg_dark"])
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)
    
    def log(self, msg):
        self.textbox.insert("end", msg + "\n")


class SendPanel(ctk.CTkFrame):
    """Panel with file selection widgets - similar to real app"""
    def __init__(self, parent, log_callback=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        
        ctk.CTkLabel(self, text="Enviar Arquivos", 
            font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        # File list frame
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_light"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(list_frame, text="Arquivos selecionados:").pack(anchor="w", padx=10, pady=5)
        
        self.file_listbox = ctk.CTkTextbox(list_frame, height=150)
        self.file_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Selecionar Arquivos", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Selecionar Pasta", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Limpar", width=100).pack(side="left", padx=5)
        
        # Options
        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.pack(fill="x", padx=20, pady=10)
        
        self.dry_run = ctk.CTkCheckBox(opt_frame, text="Modo Simulacao")
        self.dry_run.pack(side="left", padx=10)
        
        self.force = ctk.CTkCheckBox(opt_frame, text="Ignorar Rate Limit")
        self.force.pack(side="left", padx=10)
        
        # Send button
        ctk.CTkButton(self, text="ENVIAR", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"], height=40).pack(pady=20)


class EmailListsPanel(ctk.CTkFrame):
    """Panel for managing email lists"""
    def __init__(self, parent, log_callback=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header, text="Listas de Email",
            font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Nova Lista", width=120).pack(side="right")
        
        # Lists container
        self.lists_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_light"])
        self.lists_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add some dummy lists
        for i in range(5):
            frame = ctk.CTkFrame(self.lists_frame, fg_color=COLORS["bg_dark"])
            frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(frame, text=f"Lista {i+1}", 
                font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(frame, text=f"{i+2} contatos",
                text_color=COLORS["text_dim"]).pack(side="left", padx=10)
            ctk.CTkButton(frame, text="Editar", width=60).pack(side="right", padx=5, pady=5)
            ctk.CTkButton(frame, text="Excluir", width=60, 
                fg_color="transparent").pack(side="right", padx=5, pady=5)


class RulesPanel(ctk.CTkFrame):
    """Panel for managing rules"""
    def __init__(self, parent, log_callback=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header, text="Regras de Diretorio",
            font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Nova Regra", width=120).pack(side="right")
        
        # Rules container
        self.rules_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_light"])
        self.rules_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add some dummy rules with more widgets each
        for i in range(5):
            frame = ctk.CTkFrame(self.rules_frame, fg_color=COLORS["bg_dark"])
            frame.pack(fill="x", pady=5, padx=5)
            
            left = ctk.CTkFrame(frame, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(left, text=f"Regra {i+1}", 
                font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"Padrao: /caminho/pasta{i+1}/*",
                text_color=COLORS["text_dim"], font=ctk.CTkFont(size=11)).pack(anchor="w")
            ctk.CTkLabel(left, text=f"Lista: lista_{i+1}",
                text_color=COLORS["text_dim"], font=ctk.CTkFont(size=11)).pack(anchor="w")
            
            right = ctk.CTkFrame(frame, fg_color="transparent")
            right.pack(side="right", padx=10, pady=10)
            
            ctk.CTkSwitch(right, text="Ativo").pack(side="left", padx=5)
            ctk.CTkButton(right, text="Editar", width=60).pack(side="left", padx=5)
            ctk.CTkButton(right, text="Excluir", width=60, 
                fg_color="transparent").pack(side="left", padx=5)


class SettingsPanel(ctk.CTkScrollableFrame):
    """Settings panel with MANY widgets - this is the heavy one"""
    def __init__(self, parent, log_callback=None, status_bar=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        
        ctk.CTkLabel(self, text="Configuracoes",
            font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=20)
        
        # Azure Section - MANY inputs
        azure = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        azure.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(azure, text="Credenciais Azure AD",
            font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        for field in ["Client ID", "Tenant ID", "Email", "Senha"]:
            ctk.CTkLabel(azure, text=f"{field}:", text_color=COLORS["text_dim"]).pack(anchor="w", padx=15)
            entry = ctk.CTkEntry(azure, width=400, 
                show="*" if field == "Senha" else None)
            entry.pack(padx=15, pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(azure, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Salvar", fg_color=COLORS["success"], width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Testar", fg_color=COLORS["accent"], width=120).pack(side="left", padx=5)
        
        # Rate Limits Section
        rate = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        rate.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(rate, text="Rate Limits",
            font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        for cat in ["default", "relatorios", "alertas"]:
            row = ctk.CTkFrame(rate, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=f"{cat}:", width=100).pack(side="left")
            ctk.CTkLabel(row, text="0/5 dia | 0/25 sem", 
                text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        
        ctk.CTkButton(rate, text="Resetar Contadores", 
            fg_color=COLORS["bg_dark"]).pack(pady=15)
        
        # General Settings
        gen = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        gen.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(gen, text="Geral",
            font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        ctk.CTkLabel(gen, text="Extensoes permitidas:").pack(anchor="w", padx=15)
        ctk.CTkEntry(gen, width=400).pack(padx=15, pady=(0, 10))
        
        ctk.CTkLabel(gen, text="Tamanho maximo (MB):").pack(anchor="w", padx=15)
        ctk.CTkEntry(gen, width=100).pack(anchor="w", padx=15, pady=(0, 15))
        
        # Export/Import
        exp = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        exp.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(exp, text="Backup",
            font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        btn_row = ctk.CTkFrame(exp, fg_color="transparent")
        btn_row.pack(pady=15)
        ctk.CTkButton(btn_row, text="Exportar", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="Importar", width=120).pack(side="left", padx=5)


class AboutPanel(ctk.CTkFrame):
    """About panel"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_medium"], **kwargs)
        
        ctk.CTkLabel(self, text="K", font=ctk.CTkFont(size=72, weight="bold"),
            text_color=COLORS["accent"]).pack(pady=(40, 10))
        ctk.CTkLabel(self, text="Krvo", font=ctk.CTkFont(size=36, weight="bold")).pack()
        ctk.CTkLabel(self, text="Mensageiro Digital", 
            text_color=COLORS["text_dim"]).pack()
        ctk.CTkLabel(self, text="v1.0.0", text_color=COLORS["text_dim"]).pack(pady=10)
        
        features = ctk.CTkFrame(self, fg_color=COLORS["bg_light"], corner_radius=10)
        features.pack(fill="x", padx=50, pady=30)
        
        for f in ["Envio por regras", "Listas configuraveis", "Rate limiting", "CLI + GUI"]:
            ctk.CTkLabel(features, text=f"* {f}").pack(anchor="w", padx=20, pady=3)
        
        ctk.CTkLabel(self, text="Desenvolvido por Lucas Rafael",
            text_color=COLORS["text_dim"], font=ctk.CTkFont(size=10)).pack(side="bottom", pady=20)


def test_aggressive():
    """More aggressive test that mimics real application structure"""
    
    print("Creating main window...")
    app = ctk.CTk()
    app.geometry("1100x750")
    app.title("Aggressive Segfault Test")
    ctk.set_appearance_mode("dark")
    app.configure(fg_color=COLORS["bg_dark"])
    
    # Main container
    main = ctk.CTkFrame(app, fg_color="transparent")
    main.pack(fill="both", expand=True)
    
    # Sidebar
    print("Creating sidebar...")
    sidebar = ctk.CTkFrame(main, width=200, fg_color=COLORS["bg_medium"], corner_radius=0)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)
    
    ctk.CTkLabel(sidebar, text="K", font=ctk.CTkFont(size=42, weight="bold"),
        text_color=COLORS["accent"]).pack(pady=(20, 5))
    ctk.CTkLabel(sidebar, text="Krvo", font=ctk.CTkFont(size=18, weight="bold")).pack()
    
    # Navigation buttons
    for name in ["Enviar", "Listas", "Regras", "Config", "Sobre"]:
        ctk.CTkButton(sidebar, text=name, fg_color="transparent", 
            anchor="w", height=40).pack(fill="x", padx=10, pady=2)
    
    # Content area
    content = ctk.CTkFrame(main, fg_color="transparent")
    content.pack(side="left", fill="both", expand=True)
    
    # Now create all the custom class instances - THIS IS WHERE IT SHOULD CRASH
    print()
    print("Creating StatusBar (custom class 1)...")
    status_bar = StatusBar(content)
    print("  OK")
    
    print("Creating LogFrame (custom class 2)...")
    log_frame = LogFrame(content, height=150)
    print("  OK")
    
    panels_container = ctk.CTkFrame(content, fg_color="transparent")
    
    print("Creating SendPanel (custom class 3)...")
    p1 = SendPanel(panels_container)
    print("  OK")
    
    print("Creating EmailListsPanel (custom class 4)...")
    p2 = EmailListsPanel(panels_container)
    print("  OK")
    
    print("Creating RulesPanel (custom class 5)...")
    p3 = RulesPanel(panels_container)
    print("  OK")
    
    print("Creating SettingsPanel (custom class 6 - ScrollableFrame with MANY widgets)...")
    p4 = SettingsPanel(panels_container, status_bar=status_bar)
    print("  OK")
    
    print("Creating AboutPanel (custom class 7)...")
    p5 = AboutPanel(panels_container)
    print("  OK")
    
    # Pack everything
    log_frame.pack(fill="x", padx=10, pady=(10, 5))
    panels_container.pack(fill="both", expand=True, padx=10, pady=5)
    status_bar.pack(fill="x", side="bottom")
    
    p1.pack(fill="both", expand=True)
    
    print()
    print("="*60)
    print("SUCCESS! All widgets created without crash!")
    print("="*60)
    print()
    print("If you see this, the bug may require specific conditions.")
    print("Try running multiple times or with different Python/Tk versions.")
    
    app.after(5000, app.destroy)
    app.mainloop()


if __name__ == "__main__":
    test_aggressive()