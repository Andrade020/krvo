import customtkinter as ctk

COLORS = {'bg_medium': '#16213e', 'bg_light': '#0f3460', 'bg_dark': '#1a1a2e'}

class Panel1(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_medium'], **kwargs)
        for i in range(5):
            ctk.CTkEntry(self, width=300).pack(pady=5)
        ctk.CTkButton(self, text='Send').pack(pady=10)

class Panel2(ctk.CTkScrollableFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_medium'], **kwargs)
        for i in range(8):
            f = ctk.CTkFrame(self, fg_color=COLORS['bg_light'])
            f.pack(fill='x', pady=3)
            ctk.CTkLabel(f, text=f'List {i}').pack(side='left', padx=10, pady=8)
            ctk.CTkButton(f, text='Edit', width=50).pack(side='right', padx=5)

class Panel3(ctk.CTkScrollableFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_medium'], **kwargs)
        for i in range(8):
            f = ctk.CTkFrame(self, fg_color=COLORS['bg_light'])
            f.pack(fill='x', pady=3)
            ctk.CTkLabel(f, text=f'Rule {i}').pack(side='left', padx=10, pady=8)
            ctk.CTkSwitch(f, text='Active').pack(side='right', padx=5)

class Panel4(ctk.CTkScrollableFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_medium'], **kwargs)
        for field in ['Client ID', 'Tenant ID', 'Email', 'Password']:
            ctk.CTkLabel(self, text=field).pack(anchor='w', padx=10)
            ctk.CTkEntry(self, width=350).pack(padx=10, pady=(0,10))
        ctk.CTkButton(self, text='Save').pack(pady=10)
        ctk.CTkButton(self, text='Test').pack(pady=5)

class Panel5(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_medium'], **kwargs)
        ctk.CTkLabel(self, text='About', font=ctk.CTkFont(size=24)).pack(pady=30)
        ctk.CTkLabel(self, text='Version 1.0').pack()
