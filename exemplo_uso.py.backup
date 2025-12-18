#!/usr/bin/env python3
"""
Exemplo de uso do Split Audio
Este arquivo demonstra como usar o script split_audio.py
"""

import os
import subprocess
import sys

def exemplo_uso():
    """Demonstra como usar o split_audio.py"""

    print("🎵 Exemplo de Uso do Split Audio - Transcrição com IA")
    print("=" * 55)

    # Verifica se o script existe
    if not os.path.exists("split_audio.py"):
        print("❌ Arquivo split_audio.py não encontrado!")
        return

    # Lista arquivos de áudio disponíveis
    extensoes_audio = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma']
    arquivos_audio = []

    for arquivo in os.listdir('.'):
        if any(arquivo.lower().endswith(ext) for ext in extensoes_audio):
            arquivos_audio.append(arquivo)

    if not arquivos_audio:
        print("📁 Nenhum arquivo de áudio encontrado no diretório atual.")
        print("💡 Coloque um arquivo de áudio (.mp3, .wav, .m4a, etc.) neste diretório.")
        return

    print(f"📁 Arquivos de áudio encontrados:")
    for i, arquivo in enumerate(arquivos_audio, 1):
        tamanho = os.path.getsize(arquivo) / (1024 * 1024)  # MB
        print(f"   {i}. {arquivo} ({tamanho:.1f} MB)")

    # Exemplo de uso
    arquivo_exemplo = arquivos_audio[0]
    print(f"\n🎯 Exemplo: Transcrevendo '{arquivo_exemplo}'")
    print(f"📝 Funcionalidade: Divisão + Transcrição com salvamento incremental")

    # Mostra as diferentes opções
    print(f"\n🔧 Opções disponíveis:")
    print(f"   1. Apenas dividir: python split_audio.py {arquivo_exemplo}")
    print(f"   2. Dividir + transcrever: python split_audio.py {arquivo_exemplo} --transcrever")
    print(f"   3. 🚀 Transcrição completa: python split_audio.py {arquivo_exemplo} --transcrever-completa")
    print(f"   4. Modelo rápido: python split_audio.py {arquivo_exemplo} --transcrever-completa --modelo tiny")
    print(f"   5. Segmentos de 2min: python split_audio.py {arquivo_exemplo} --transcrever-completa --segmentos 2")

    # Pergunta se quer executar
    resposta = input("\n❓ Deseja executar a transcrição completa agora? (s/n): ").lower()

    if resposta in ['s', 'sim', 'y', 'yes']:
        try:
            print(f"\n🚀 Executando transcrição completa: python split_audio.py {arquivo_exemplo} --transcrever-completa --modelo tiny")
            print(f"💡 Isso vai salvar a transcrição a cada segmento processado!")
            resultado = subprocess.run([sys.executable, "split_audio.py", arquivo_exemplo, "--transcrever-completa", "--modelo", "tiny"],
                                    capture_output=False, text=True)

            if resultado.returncode == 0:
                print("\n✅ Exemplo executado com sucesso!")
                print(f"📄 Verifique o arquivo de transcrição em: {arquivo_exemplo.replace('.', '_')}dividido/")
            else:
                print("\n❌ Erro ao executar o exemplo.")

        except Exception as e:
            print(f"\n❌ Erro: {e}")
    else:
        print(f"\n💡 Para executar a transcrição completa:")
        print(f"   python split_audio.py {arquivo_exemplo} --transcrever-completa --modelo tiny")
        print(f"   📄 Arquivo será salvo em: {arquivo_exemplo.replace('.', '_')}dividido/")
        print(f"   🔄 Acompanhe o progresso na barra e no arquivo de transcrição!")

if __name__ == "__main__":
    exemplo_uso()
