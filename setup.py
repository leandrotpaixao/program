#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador/Launcher do Monte Carlo PRO
Executa automaticamente: clone, setup, dependências e inicia a app
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


class Colors:
    """Cores para terminal"""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Exibe cabeçalho bonito"""
    print(f"""{Colors.BOLD}{Colors.BLUE}
    ╔═══════════════════════════════════════════════════════════╗
    ║      🎲 MONTE CARLO PRO - Análise de Loterias           ║
    ║          Instalador Automático v2.0                      ║
    ╚═══════════════════════════════════════════════════════════╝
    {Colors.RESET}""")


def print_step(step_num, step_name):
    """Exibe etapa do processo"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[Etapa {step_num}]{Colors.RESET} {step_name}...")


def print_success(msg):
    """Exibe mensagem de sucesso"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    """Exibe mensagem de erro"""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg):
    """Exibe aviso"""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg):
    """Exibe informação"""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def run_command(cmd, description=""):
    """
    Executa comando e retorna sucesso/erro
    
    Args:
        cmd: Comando a executar (string ou list)
        description: Descrição do que está fazendo
    
    Returns:
        (sucesso: bool, output: str)
    """
    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=300
            )
        else:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
        
        if result.returncode == 0:
            if description:
                print_success(description)
            return True, result.stdout
        else:
            if description:
                print_error(description)
            print(f"  Erro: {result.stderr}")
            return False, result.stderr
    
    except subprocess.TimeoutExpired:
        print_error(f"Timeout ao executar: {description}")
        return False, "Timeout"
    except Exception as e:
        print_error(f"Erro ao executar: {str(e)}")
        return False, str(e)


def check_python_version():
    """
    Verifica se Python 3.8+ está instalado
    """
    print_step(1, "Verificando versão do Python")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ é necessário. Você tem: {version.major}.{version.minor}")
        print_info("Baixe em: https://www.python.org/downloads/")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} encontrado")
    return True


def check_git():
    """
    Verifica se Git está instalado
    """
    print_step(2, "Verificando Git")
    
    ok, _ = run_command("git --version", "Git encontrado")
    if not ok:
        print_warning("Git não encontrado. Será feito download manual do ZIP.")
        return False
    return True


def clone_repository(use_git=True):
    """
    Clona repositório ou baixa ZIP
    """
    print_step(3, "Baixando código do repositório")
    
    repo_url = "https://github.com/leandrotpaixao/program.git"
    repo_dir = "monte_carlo_pro_app"
    
    if os.path.exists(repo_dir):
        print_info(f"Diretório '{repo_dir}' já existe. Pulando clone.")
        return True
    
    if use_git:
        ok, _ = run_command(
            ["git", "clone", repo_url, repo_dir],
            f"Repositório clonado em '{repo_dir}'"
        )
        return ok
    else:
        # Download do ZIP
        print_info("Baixando arquivo ZIP...")
        zip_url = "https://github.com/leandrotpaixao/program/archive/refs/heads/main.zip"
        zip_file = "program-main.zip"
        
        ok, _ = run_command(
            f"curl -L -o {zip_file} {zip_url}",
            "Arquivo ZIP baixado"
        )
        if not ok:
            print_warning("curl não disponível. Tentando com wget...")
            ok, _ = run_command(
                f"wget -O {zip_file} {zip_url}",
                "Arquivo ZIP baixado com wget"
            )
        
        if ok and os.path.exists(zip_file):
            ok, _ = run_command(
                f"unzip -q {zip_file}",
                "ZIP extraído"
            )
            if ok:
                os.rename("program-main", repo_dir)
                os.remove(zip_file)
                return True
    
    return False


def setup_venv(repo_dir):
    """
    Cria e ativa ambiente virtual
    """
    print_step(4, "Criando ambiente virtual")
    
    venv_dir = os.path.join(repo_dir, "venv")
    
    if os.path.exists(venv_dir):
        print_info("Ambiente virtual já existe")
        return True
    
    ok, _ = run_command(
        [sys.executable, "-m", "venv", venv_dir],
        "Ambiente virtual criado"
    )
    return ok


def get_pip_command(repo_dir):
    """
    Retorna caminho do pip correto para o OS
    """
    venv_dir = os.path.join(repo_dir, "venv")
    
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        return os.path.join(venv_dir, "bin", "pip")


def get_python_command(repo_dir):
    """
    Retorna caminho do python correto para o OS
    """
    venv_dir = os.path.join(repo_dir, "venv")
    
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        return os.path.join(venv_dir, "bin", "python")


def install_dependencies(repo_dir):
    """
    Instala dependências no ambiente virtual
    """
    print_step(5, "Instalando dependências")
    
    pip_cmd = get_pip_command(repo_dir)
    requirements_file = os.path.join(repo_dir, "requirements.txt")
    
    if not os.path.exists(requirements_file):
        print_error(f"Arquivo {requirements_file} não encontrado")
        return False
    
    print_info("Isso pode levar alguns minutos...")
    
    # Atualizar pip
    ok, _ = run_command(
        [pip_cmd, "install", "--upgrade", "pip"],
        "Pip atualizado"
    )
    if not ok:
        print_warning("Erro ao atualizar pip, continuando...")
    
    # Instalar requirements
    ok, _ = run_command(
        [pip_cmd, "install", "-r", requirements_file],
        "Dependências instaladas"
    )
    return ok


def create_launcher_scripts(repo_dir):
    """
    Cria scripts de launcher para Windows e Unix
    """
    print_step(6, "Criando scripts de execução")
    
    python_cmd = get_python_command(repo_dir)
    main_module = "monte_carlo_pro.main"
    
    # Launcher para Windows
    launcher_bat = os.path.join(repo_dir, "monte_carlo.bat")
    bat_content = f'''@echo off
cd /d "%~dp0"
"{python_cmd}" -m {main_module}
pause
'''
    
    with open(launcher_bat, "w") as f:
        f.write(bat_content)
    print_success(f"Script Windows criado: {launcher_bat}")
    
    # Launcher para Unix
    launcher_sh = os.path.join(repo_dir, "monte_carlo.sh")
    sh_content = f'''#!/bin/bash
cd "$(dirname "$0")"
"{python_cmd}" -m {main_module}
'''
    
    with open(launcher_sh, "w") as f:
        f.write(sh_content)
    
    os.chmod(launcher_sh, 0o755)
    print_success(f"Script Unix criado: {launcher_sh}")
    
    return True


def create_desktop_shortcut(repo_dir):
    """
    Cria atalho de desktop (Windows)
    """
    if platform.system() != "Windows":
        return
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = Path(winshell.desktop())
        launcher_bat = os.path.join(repo_dir, "monte_carlo.bat")
        shortcut_path = desktop / "Monte Carlo PRO.lnk"
        
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.TargetPath = launcher_bat
        shortcut.WorkingDirectory = repo_dir
        shortcut.IconLocation = launcher_bat
        shortcut.save()
        
        print_success(f"Atalho de desktop criado: {shortcut_path}")
    except Exception as e:
        print_warning(f"Não foi possível criar atalho: {str(e)}")


def run_application(repo_dir):
    """
    Executa a aplicação
    """
    print_step(7, "Iniciando Monte Carlo PRO")
    
    python_cmd = get_python_command(repo_dir)
    main_module = "monte_carlo_pro.main"
    
    print_info("Abrindo interface gráfica...\n")
    
    try:
        if platform.system() == "Windows":
            # Windows: usar subprocess sem bloquear
            subprocess.Popen(
                [python_cmd, "-m", main_module],
                cwd=repo_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            print_success("Aplicação iniciada em nova janela")
        else:
            # Unix: executar normalmente
            subprocess.run(
                [python_cmd, "-m", main_module],
                cwd=repo_dir
            )
    except Exception as e:
        print_error(f"Erro ao iniciar aplicação: {str(e)}")
        return False
    
    return True


def show_summary(repo_dir):
    """
    Exibe resumo final
    """
    print(f"""
{Colors.BOLD}{Colors.GREEN}
    ╔═══════════════════════════════════════════════════════════╗
    ║             ✓ INSTALAÇÃO CONCLUÍDA COM SUCESSO!          ║
    ╚═══════════════════════════════════════════════════════════╝
{Colors.RESET}
    📁 Diretório: {repo_dir}
    🐍 Python: {get_python_command(repo_dir)}
    📦 Dependências instaladas
    
{Colors.BOLD}Como usar:{Colors.RESET}
    
    {Colors.YELLOW}• Windows:{Colors.RESET}
      Execute: monte_carlo.bat
      Ou clique 2x no arquivo no explorador
    
    {Colors.YELLOW}• Linux/Mac:{Colors.RESET}
      Execute: ./monte_carlo.sh
      Ou: python -m monte_carlo_pro.main
    
{Colors.BOLD}Próximos passos:{Colors.RESET}
    1. A interface gráfica abrirá automaticamente
    2. Clique em "⬇️ Baixar CEF" para carregar histórico
    3. Configure os filtros desejados
    4. Clique em "🎯 Gerar e Analisar"
    5. Veja o ranking de jogos!
    
{Colors.BOLD}Suporte:{Colors.RESET}
    GitHub: https://github.com/leandrotpaixao/program
    Issues: Reporte problemas no repositório
    
{Colors.YELLOW}Divirta-se! 🍀{Colors.RESET}
    """)


def main():
    """
    Função principal do instalador
    """
    print_header()
    
    # Etapa 1: Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Etapa 2: Verificar Git
    has_git = check_git()
    
    # Etapa 3: Clonar repositório
    if not clone_repository(use_git=has_git):
        print_error("Falha ao clonar repositório")
        sys.exit(1)
    
    repo_dir = "monte_carlo_pro_app"
    
    # Etapa 4: Criar ambiente virtual
    if not setup_venv(repo_dir):
        print_error("Falha ao criar ambiente virtual")
        sys.exit(1)
    
    # Etapa 5: Instalar dependências
    if not install_dependencies(repo_dir):
        print_error("Falha ao instalar dependências")
        sys.exit(1)
    
    # Etapa 6: Criar scripts de launcher
    create_launcher_scripts(repo_dir)
    
    # Etapa 7: Criar atalho de desktop (Windows)
    if platform.system() == "Windows":
        create_desktop_shortcut(repo_dir)
    
    # Exibir resumo
    show_summary(repo_dir)
    
    # Etapa 8: Executar aplicação
    print_info("Iniciando aplicação...")
    run_application(repo_dir)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Instalação cancelada pelo usuário{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Erro durante instalação: {str(e)}{Colors.RESET}")
        sys.exit(1)
