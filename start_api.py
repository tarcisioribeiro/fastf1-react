#!/usr/bin/env python3
"""
Script para iniciar a API Flask em background e manter
o processo rodando para consumir dados da API da Fórmula 1.
"""

import os
import sys
import time
import signal
import subprocess
from datetime import datetime

def log(message):
    """Log com timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def start_api():
    """Inicia a API Flask"""
    log("Iniciando API Flask na porta 5000...")

    # Criar diretório de cache se não existir
    cache_dir = '.fastf1_cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        log(f"Diretório de cache criado: {cache_dir}")

    # Iniciar API
    process = subprocess.Popen(
        [sys.executable, 'api.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    log(f"API iniciada (PID: {process.pid})")
    log("A API está consumindo dados da FastF1 API...")
    log("Endpoints disponíveis:")
    log("  - http://localhost:5000/api/drivers/standings")
    log("  - http://localhost:5000/api/constructors/standings")
    log("  - http://localhost:5000/api/races/latest")
    log("  - http://localhost:5000/api/qualifying/latest")
    log("")
    log("Pressione Ctrl+C para parar a API")

    return process

def handle_shutdown(signum, frame):
    """Handler para shutdown gracioso"""
    log("\nRecebido sinal de shutdown. Encerrando API...")
    sys.exit(0)

def main():
    """Main function"""
    # Registrar handler para Ctrl+C
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Iniciar API
    api_process = start_api()

    try:
        # Manter o processo rodando e mostrar logs
        while True:
            # Verificar se o processo ainda está rodando
            if api_process.poll() is not None:
                log("API encerrada inesperadamente!")
                break

            # Mostrar output da API
            line = api_process.stdout.readline()
            if line:
                print(line.strip())

            time.sleep(0.1)

    except KeyboardInterrupt:
        log("\nEncerrando API...")
    finally:
        # Terminar processo da API
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log("Forçando encerramento da API...")
            api_process.kill()

        log("API encerrada com sucesso!")

if __name__ == '__main__':
    main()
