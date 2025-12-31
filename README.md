# 🐦‍⬛ Krvo

**Mensageiro Digital** - Sistema de envio automático de emails via Microsoft Graph API.

*Como um corvo mensageiro, leva suas mensagens com precisão e confiabilidade.*

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Platform](https://img.shields.io/badge/platform-Windows%20|%20Linux%20|%20Mac-lightgrey)

## ✨ Funcionalidades

- 📤 **Envio automatizado** de arquivos por email
- 📁 **Regras por diretório** - configure como cada pasta deve ser tratada
- 📧 **Listas de destinatários** - gerencie grupos de contatos
- ⏱️ **Rate limiting** - evita spam com controle de frequência
- 📝 **Templates** - assuntos e corpos personalizáveis
- 🖥️ **Interface gráfica** moderna e intuitiva
- 💻 **CLI completo** para automação e integração
- 🔐 **Autenticação segura** via Microsoft Graph (ROPC)

## 📥 Instalação

### Opção 1: Executável (Windows)

1. Baixe o arquivo `Krvo.zip` da página de releases
2. Extraia para uma pasta de sua escolha
3. Execute `Krvo.exe`

### Opção 2: Via Python

```bash
# Clone ou baixe o projeto
git clone https://github.com/Andrade020/krvo.git
cd krvo

# Instale as dependências
pip install -r requirements.txt

# Execute
python krvo.py
```

## 🚀 Uso Rápido

### Interface Gráfica

```bash
python krvo.py
# ou
python krvo.py gui
```

### Linha de Comando

```bash
# Enviar um arquivo
python krvo.py send documento.pdf

# Enviar múltiplos arquivos
python krvo.py send relatorio1.pdf relatorio2.xlsx

# Enviar todos arquivos de uma pasta
python krvo.py send --folder ./relatorios

# Modo simulação (não envia de verdade)
python krvo.py send --dry-run arquivo.pdf

# Ignorar rate limiting
python krvo.py send --force arquivo.pdf

# Ver status do sistema
python krvo.py status

# Testar autenticação
python krvo.py auth test

# Saída em JSON (para integração)
python krvo.py status --json
```

## ⚙️ Configuração Inicial

### 1. Credenciais Azure AD

Para usar o Krvo, você precisa de um App Registration no Azure AD:

1. Acesse [portal.azure.com](https://portal.azure.com)
2. Vá em **Azure Active Directory** → **App registrations** → **New registration**
3. Configure:
   - Nome: `Krvo`
   - Tipo: **Accounts in this organizational directory only**
4. Em **Authentication**:
   - Adicione plataforma **Mobile and desktop applications**
   - Ative **Allow public client flows** (necessário para ROPC)
5. Em **API Permissions**, adicione:
   - `Microsoft Graph` → `Mail.Send` (Delegated)
   - `Microsoft Graph` → `Mail.Read` (Delegated)
   - `Microsoft Graph` → `Mail.ReadWrite` (Delegated)
6. Clique em **Grant admin consent**

Depois, no Krvo:
- Vá em **Config** → insira Client ID, Tenant ID, Email e Senha
- Clique em **Testar Conexão**

### 2. Listas de Email

1. Vá em **Listas** → **+ Nova Lista**
2. Configure nome, identificador e emails dos destinatários
3. Salve

### 3. Regras de Diretório

1. Vá em **Regras** → **+ Nova Regra**
2. Configure:
   - **Padrão**: parte do caminho que identifica os arquivos (ex: `relatorios/vendas`)
   - **Lista**: qual lista de destinatários usar
   - **Template de Assunto**: use `{filename}`, `{date}`, `{datetime}`
   - **Template de Corpo**: texto do email
   - **Prioridade**: maior = mais específico (verificado primeiro)
3. Salve

## 🔌 Integração com Outros Sistemas

O Krvo pode ser chamado por outros programas:

### Python

```python
import subprocess
import json

# Enviar arquivo
result = subprocess.run(
    ["python", "krvo.py", "send", "--json", "arquivo.pdf"],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)
print(f"Sucesso: {data['success']}")
```

### Batch/PowerShell

```batch
REM Windows
python krvo.py send --json arquivo.pdf > resultado.json
```

```powershell
# PowerShell
$result = python krvo.py send --json arquivo.pdf | ConvertFrom-Json
if ($result.success) { Write-Host "Enviado!" }
```

## 📁 Estrutura de Arquivos

```
krvo/
├── krvo.py             # Ponto de entrada principal
├── gui.py              # Interface gráfica
├── cli.py              # Interface de linha de comando
├── requirements.txt    # Dependências Python
├── build.bat           # Build para Windows
├── build.sh            # Build para Linux/Mac
├── assets/
│   ├── krvo.ico        # Ícone do aplicativo
│   └── krvo_*.png      # Ícones em vários tamanhos
├── src/
│   ├── __init__.py
│   ├── settings.py     # Gerenciamento de configurações
│   ├── auth.py         # Autenticação Microsoft Graph
│   ├── sender.py       # Envio de emails
│   └── stress_controller.py  # Rate limiting
└── README.md
```

## 🔨 Build (Gerar .exe)

### Windows

```batch
build.bat             # Build padrão
build.bat onefile     # Executável único
build.bat debug       # Com console de debug
```

### Linux/Mac

```bash
chmod +x build.sh
./build.sh
```

O executável será gerado em `dist/Krvo/`.

## 🛡️ Segurança

- Credenciais em `%APPDATA%/Krvo/` (Windows) ou `~/.config/Krvo/` (Linux)
- Tokens cacheados e renovados automaticamente
- Senhas não transmitidas após autenticação inicial

## 🐛 Troubleshooting

| Erro | Solução |
|------|---------|
| ROPC desabilitado | Azure AD → Authentication → Allow public client flows |
| MFA ativo | Use conta de serviço sem MFA |
| Permissões não concedidas | Azure AD → API Permissions → Grant admin consent |
| Rate limit | Use `--force` ou Config → Resetar Contadores |

---

<sub>Desenvolvido por Lucas Rafael de Andrade Desenvolvimento de Software LTDA</sub>
