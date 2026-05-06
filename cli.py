#!/usr/bin/env python3
"""
Porto Mailer - Interface de Linha de Comando
=============================================

Permite enviar emails via terminal ou integração com outros sistemas.

Uso:
    porto_mailer send <arquivo> [arquivo2] ...
    porto_mailer send --folder <pasta>
    porto_mailer status
    porto_mailer auth test
    porto_mailer auth clear
    porto_mailer config show
    porto_mailer config export <arquivo.json>
    porto_mailer config import <arquivo.json>

Exemplos:
    porto_mailer send relatorio.pdf
    porto_mailer send --dry-run documento.xlsx
    porto_mailer send --force --folder ./relatorios
    porto_mailer status
    porto_mailer auth test

Flags globais:
    --dry-run     Simula sem enviar
    --force       Ignora rate limiting
    --json        Saída em JSON
    --quiet       Modo silencioso
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Optional

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.settings import get_settings_manager, get_settings
from src.auth import get_authenticator
from src.sender import EmailSender
from src.stress_controller import get_controller


def print_banner():
    print("""
╔══════════════════════════════════════════════════╗
║             KRVO v1.0.0 - CLI                    ║
║        Mensageiro Digital 🐦‍⬛                    ║
╚══════════════════════════════════════════════════╝
    """)


def cmd_mail(args):
    """Envia email direto para um endereço, sem regras."""
    if not args.quiet:
        print_banner()

    from src.sender import EmailSender
    sender = EmailSender()

    recipients = [args.to]
    subject = args.subject or "Sem assunto"
    body = args.body or ""
    attachments = args.attach or []

    if not args.quiet:
        print(f"[INFO] Destinatário: {args.to}")
        print(f"[INFO] Assunto: {subject}")
        if attachments:
            print(f"[INFO] Anexos: {', '.join(attachments)}")
        if args.dry_run:
            print("[INFO] Modo SIMULAÇÃO ativado")
        print()

    success, msg = sender.send_custom_email(
        recipients=recipients,
        subject=subject,
        body=body,
        attachments=[Path(a) for a in attachments] if attachments else None,
        force=args.force,
        dry_run=args.dry_run,
    )

    if args.json:
        import json as _json
        print(_json.dumps({"success": success, "message": msg}, ensure_ascii=False))
    else:
        icon = "✅" if success else "❌"
        print(f"{icon} {msg}")

    return 0 if success else 1


def cmd_send(args):
    """Comando de envio de arquivos."""
    if not args.quiet:
        print_banner()
    
    # Coleta arquivos
    files: List[Path] = []
    
    if args.folder:
        folder = Path(args.folder)
        if not folder.exists():
            print(f"[ERRO] Pasta não encontrada: {folder}")
            return 1
        
        settings = get_settings()
        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in settings.allowed_extensions:
                files.append(item)
        
        if not args.quiet:
            print(f"[INFO] Encontrados {len(files)} arquivos em {folder}")
    
    if args.files:
        for f in args.files:
            path = Path(f)
            if path.exists():
                files.append(path)
            else:
                print(f"[AVISO] Arquivo não encontrado: {f}")
    
    if not files:
        print("[ERRO] Nenhum arquivo para enviar")
        return 1
    
    if not args.quiet:
        print(f"[INFO] Arquivos: {len(files)}")
        if args.dry_run:
            print("[INFO] Modo SIMULAÇÃO ativado")
        if args.force:
            print("[INFO] Rate limiting IGNORADO")
        print()
    
    # Envia
    sender = EmailSender()
    results = sender.send_files(files, force=args.force, dry_run=args.dry_run)
    
    # Saída
    success_count = sum(1 for _, s, _, _ in results if s)
    fail_count = len(results) - success_count
    
    if args.json:
        output = {
            "success": fail_count == 0,
            "sent": success_count,
            "failed": fail_count,
            "results": [
                {"file": p, "success": s, "message": m}
                for p, s, m, _ in results
            ]
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        for path, success, msg, _ in results:
            icon = "✅" if success else "❌"
            print(f"{icon} {Path(path).name}: {msg}")
        
        print()
        print(f"Resultado: {success_count} enviados, {fail_count} falhas")
    
    return 0 if fail_count == 0 else 1


def cmd_status(args):
    """Mostra status do sistema."""
    if not args.quiet:
        print_banner()
    
    # Auth status
    try:
        auth = get_authenticator()
        auth_status = auth.get_status()
    except Exception as e:
        auth_status = {"error": str(e)}
    
    # Stress status
    stress = get_controller()
    stress_status = stress.get_status()
    
    if args.json:
        output = {
            "auth": auth_status,
            "rate_limits": stress_status,
            "settings": {
                "extensions": get_settings().allowed_extensions,
                "max_attachment_mb": get_settings().max_attachment_mb,
                "email_lists": list(get_settings().email_lists.keys()),
                "rules_count": len(get_settings().directory_rules),
            }
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("=== AUTENTICAÇÃO ===")
        print(f"Configurado: {'Sim' if auth_status.get('configured') else 'Não'}")
        print(f"Token em cache: {'Sim' if auth_status.get('has_cached_token') else 'Não'}")
        if auth_status.get('email'):
            print(f"Email: {auth_status['email']}")
        
        print("\n=== RATE LIMITS ===")
        for cat, info in stress_status.items():
            icon = "✅" if info["can_send"] else "⛔"
            print(f"{icon} {cat}: {info['today']}/{info['today_limit']} hoje | {info['week']}/{info['week_limit']} semana")
        
        print("\n=== CONFIGURAÇÃO ===")
        print(f"Listas de email: {len(get_settings().email_lists)}")
        print(f"Regras: {len(get_settings().directory_rules)}")
        print(f"Extensões: {len(get_settings().allowed_extensions)}")
    
    return 0


def cmd_auth_test(args):
    """Testa autenticação."""
    if not args.quiet:
        print_banner()
        print("Testando autenticação...")
    
    try:
        auth = get_authenticator()
        
        if not auth.is_configured():
            print("[ERRO] Credenciais não configuradas")
            return 1
        
        result = auth.test_connection()
        
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result["success"]:
                print(f"✅ Conectado!")
                print(f"   Nome: {result['user_name']}")
                print(f"   Email: {result['user_email']}")
            else:
                print(f"❌ Falha: {result['error']}")
        
        return 0 if result["success"] else 1
        
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            print(f"❌ Erro: {e}")
        return 1


def cmd_auth_clear(args):
    """Limpa cache de tokens."""
    auth = get_authenticator()
    auth.clear_cache()
    
    if args.json:
        print(json.dumps({"success": True, "message": "Cache limpo"}))
    else:
        print("✅ Cache de tokens limpo")
    
    return 0


def cmd_config_show(args):
    """Mostra configuração atual."""
    settings = get_settings()
    
    output = {
        "azure_configured": settings.azure.is_configured(),
        "azure_email": settings.azure.email if settings.azure.email else None,
        "email_lists": {
            k: {
                "name": v.name,
                "contacts_count": len(v.contacts)
            }
            for k, v in settings.email_lists.items()
        },
        "directory_rules": [
            {
                "name": r.name,
                "pattern": r.pattern,
                "email_list": r.email_list,
                "active": r.active
            }
            for r in settings.directory_rules
        ],
        "allowed_extensions": settings.allowed_extensions,
        "max_attachment_mb": settings.max_attachment_mb,
    }
    
    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("=== CONFIGURAÇÃO ===\n")
        
        print("Azure AD:")
        print(f"  Configurado: {'Sim' if output['azure_configured'] else 'Não'}")
        if output['azure_email']:
            print(f"  Email: {output['azure_email']}")
        
        print("\nListas de Email:")
        for key, info in output['email_lists'].items():
            print(f"  • {key}: {info['name']} ({info['contacts_count']} contatos)")
        
        print("\nRegras de Diretório:")
        for rule in output['directory_rules']:
            status = "●" if rule['active'] else "○"
            print(f"  {status} {rule['name']}: {rule['pattern']} → {rule['email_list']}")
        
        print(f"\nExtensões: {', '.join(output['allowed_extensions'])}")
        print(f"Tamanho máximo: {output['max_attachment_mb']}MB")
    
    return 0


def cmd_config_export(args):
    """Exporta configuração."""
    path = Path(args.file)
    
    try:
        get_settings_manager().export_config(path)
        
        if args.json:
            print(json.dumps({"success": True, "file": str(path)}))
        else:
            print(f"✅ Configuração exportada para: {path}")
        
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            print(f"❌ Erro: {e}")
        return 1


def cmd_config_import(args):
    """Importa configuração."""
    path = Path(args.file)
    
    if not path.exists():
        if args.json:
            print(json.dumps({"success": False, "error": "Arquivo não encontrado"}))
        else:
            print(f"❌ Arquivo não encontrado: {path}")
        return 1
    
    try:
        get_settings_manager().import_config(path, merge=args.merge)
        
        if args.json:
            print(json.dumps({"success": True, "file": str(path), "merged": args.merge}))
        else:
            mode = "mesclada" if args.merge else "importada"
            print(f"✅ Configuração {mode} de: {path}")
        
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            print(f"❌ Erro: {e}")
        return 1


def cmd_stress_reset(args):
    """Reseta contadores de rate limiting."""
    stress = get_controller()
    stress.force_reset(args.category if hasattr(args, 'category') else None)
    
    if args.json:
        print(json.dumps({"success": True, "category": args.category if hasattr(args, 'category') else "all"}))
    else:
        cat = args.category if hasattr(args, 'category') and args.category else "todos"
        print(f"✅ Contadores resetados: {cat}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Krvo - Mensageiro Digital 🐦‍⬛",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  krvo send arquivo.pdf
  krvo send --folder ./relatorios --dry-run
  krvo status --json
  krvo auth test
  krvo config export backup.json
        """
    )
    
    # Flags globais
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    parser.add_argument("--quiet", "-q", action="store_true", help="Modo silencioso")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # === MAIL ===
    mail_parser = subparsers.add_parser("mail", help="Enviar email direto para um endereço")
    mail_parser.add_argument("to", help="Email do destinatário")
    mail_parser.add_argument("--subject", "-s", help="Assunto do email")
    mail_parser.add_argument("--body", "-b", help="Corpo do email")
    mail_parser.add_argument("--attach", "-a", nargs="*", metavar="ARQUIVO", help="Arquivos a anexar")
    mail_parser.add_argument("--dry-run", action="store_true", help="Simular envio")
    mail_parser.add_argument("--force", action="store_true", help="Ignorar rate limiting")

    # === SEND ===
    send_parser = subparsers.add_parser("send", help="Enviar arquivos por email")
    send_parser.add_argument("files", nargs="*", help="Arquivos para enviar")
    send_parser.add_argument("--folder", "-f", help="Pasta com arquivos para enviar")
    send_parser.add_argument("--dry-run", action="store_true", help="Simular envio")
    send_parser.add_argument("--force", action="store_true", help="Ignorar rate limiting")
    
    # === STATUS ===
    subparsers.add_parser("status", help="Mostrar status do sistema")
    
    # === AUTH ===
    auth_parser = subparsers.add_parser("auth", help="Gerenciar autenticação")
    auth_sub = auth_parser.add_subparsers(dest="auth_cmd")
    auth_sub.add_parser("test", help="Testar conexão")
    auth_sub.add_parser("clear", help="Limpar cache de tokens")
    
    # === CONFIG ===
    config_parser = subparsers.add_parser("config", help="Gerenciar configurações")
    config_sub = config_parser.add_subparsers(dest="config_cmd")
    config_sub.add_parser("show", help="Mostrar configuração")
    
    export_parser = config_sub.add_parser("export", help="Exportar configuração")
    export_parser.add_argument("file", help="Arquivo de destino")
    
    import_parser = config_sub.add_parser("import", help="Importar configuração")
    import_parser.add_argument("file", help="Arquivo de origem")
    import_parser.add_argument("--merge", action="store_true", help="Mesclar com config existente")
    
    # === STRESS ===
    stress_parser = subparsers.add_parser("stress", help="Gerenciar rate limiting")
    stress_sub = stress_parser.add_subparsers(dest="stress_cmd")
    reset_parser = stress_sub.add_parser("reset", help="Resetar contadores")
    reset_parser.add_argument("category", nargs="?", help="Categoria específica")
    
    # === GUI ===
    subparsers.add_parser("gui", help="Abrir interface gráfica")
    
    # Parse
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Roteamento
    if args.command == "mail":
        return cmd_mail(args)

    elif args.command == "send":
        return cmd_send(args)
    
    elif args.command == "status":
        return cmd_status(args)
    
    elif args.command == "auth":
        if args.auth_cmd == "test":
            return cmd_auth_test(args)
        elif args.auth_cmd == "clear":
            return cmd_auth_clear(args)
        else:
            print("Use: porto_mailer auth [test|clear]")
            return 1
    
    elif args.command == "config":
        if args.config_cmd == "show":
            return cmd_config_show(args)
        elif args.config_cmd == "export":
            return cmd_config_export(args)
        elif args.config_cmd == "import":
            return cmd_config_import(args)
        else:
            print("Use: porto_mailer config [show|export|import]")
            return 1
    
    elif args.command == "stress":
        if args.stress_cmd == "reset":
            return cmd_stress_reset(args)
        else:
            print("Use: porto_mailer stress reset [categoria]")
            return 1
    
    elif args.command == "gui":
        from gui import run_gui
        run_gui()
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
