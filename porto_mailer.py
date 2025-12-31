#!/usr/bin/env python3
"""
Porto Mailer - Ponto de Entrada Principal
==========================================

Sistema de envio automático de emails via Microsoft Graph API.

Uso:
    python porto_mailer.py          # Abre interface gráfica
    python porto_mailer.py gui      # Abre interface gráfica
    python porto_mailer.py send ... # Modo CLI
    python porto_mailer.py --help   # Ajuda

Desenvolvido por Lucas Rafael de Andrade Desenvolvimento de Software LTDA
"""

import sys
from pathlib import Path

# Adiciona o diretório ao path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Ponto de entrada principal."""
    
    # Se não há argumentos ou é "gui", abre interface gráfica
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui"):
        try:
            from gui import run_gui
            run_gui()
        except ImportError as e:
            print(f"Erro ao carregar interface gráfica: {e}")
            print("Tente: pip install customtkinter")
            sys.exit(1)
    else:
        # Modo CLI
        from cli import main as cli_main
        sys.exit(cli_main())


if __name__ == "__main__":
    main()
