# Interface Web Streamlit - Split Audio

Interface web moderna e intuitiva para o Split Audio, permitindo processamento e transcrição de áudio sem usar linha de comando.

## Características

- Interface visual intuitiva no navegador
- Drag-and-drop de arquivos de áudio
- 3 modos de processamento
- Seleção fácil de modelos Whisper
- Progress bars em tempo real
- Visualização e download de resultados
- 100% em Python, sem necessidade de HTML/CSS/JavaScript

## Instalação

1. Certifique-se de que todas as dependências estão instaladas:

```bash
pip install -r requirements.txt
```

Isso instalará o Streamlit junto com todas as outras dependências do projeto.

## Como Usar

### 1. Iniciar a Interface

No diretório do projeto, execute:

```bash
streamlit run streamlit_app.py
```

O Streamlit abrirá automaticamente uma janela do navegador em `http://localhost:8501`

Se não abrir automaticamente, acesse manualmente este endereço.

### 2. Configurar o Processamento

Na **barra lateral esquerda**, configure:

#### Modo de Processamento:
- **Apenas Dividir**: Divide o áudio em segmentos (sem transcrição)
- **Dividir + Transcrever Segmentos**: Divide e transcreve cada segmento
- **Transcrição Completa** (Recomendado): Divide e gera transcrição única

#### Modelo Whisper (se transcrever):
- **tiny**: Mais rápido (~1.4 min/min de áudio), qualidade básica
- **base**: Balanceado (~2-3 min/min), **recomendado**
- **small**: Boa qualidade (~3-4 min/min)
- **medium**: Alta qualidade (~4-5 min/min)
- **large**: Melhor qualidade (~5-6 min/min), muito lento

#### Duração dos Segmentos:
- Configure quantos minutos terá cada segmento (padrão: 4 minutos)

### 3. Carregar Arquivo

Na área principal:
- **Arraste** seu arquivo de áudio para a área de upload, ou
- **Clique** para selecionar do seu computador

**Formatos suportados:** MP3, WAV, M4A, AAC, FLAC, OGG, WMA

**Tamanho máximo:** 500MB (para arquivos maiores, use o CLI)

### 4. Processar

1. Clique no botão **"🚀 Processar Áudio"**
2. Aguarde o processamento (verá progress bar e status em tempo real)
3. Revise os resultados quando concluído

### 5. Baixar Resultados

Após o processamento, você pode:

- **Ver transcrição completa** na aba "📄 Transcrição Completa"
- **Ver segmentos individuais** na aba "📁 Segmentos"
- **Baixar arquivos** na aba "⬇️ Downloads":
  - Transcrição completa (.txt)
  - Transcrição detalhada (.txt)
  - ZIP com tudo (áudios + transcrições)

## Estrutura de Arquivos Criados

Ao processar, o sistema cria uma pasta com o nome do arquivo + `_dividido`:

```
arquivo_original_dividido/
├── arquivo_original_parte_01.m4a
├── arquivo_original_parte_02.m4a
├── ...
├── arquivo_original_transcricao_completa.txt     (modo transcrição completa)
└── arquivo_original_transcricao_detalhada.txt    (modo transcrição completa)
```

## Dicas de Uso

### Para Arquivos Pequenos (< 30 min)
- Use o modelo **base** ou **small**
- Segmentos de 4-5 minutos
- Modo: **Transcrição Completa**

### Para Arquivos Grandes (> 1 hora)
- Use o modelo **tiny** para velocidade
- Segmentos de 2-3 minutos (melhor para transcrição)
- Considere usar o CLI para arquivos muito grandes

### Primeira Execução
- Na primeira vez que usar um modelo Whisper, ele será **baixado** (pode demorar alguns minutos)
- Downloads subsequentes não serão necessários
- O download acontece automaticamente

### Processamento Longo
- Durante o processamento, a UI ficará bloqueada
- **Não feche a janela** do navegador
- Você pode **acompanhar o progresso** pela barra e status
- O sistema **salva incrementalmente**, então se parar, parte do trabalho não é perdido

## Diferenças entre CLI e Interface Web

| Aspecto | CLI | Interface Web |
|---------|-----|---------------|
| Facilidade de uso | Requer conhecimento de terminal | Intuitiva, drag-and-drop |
| Configuração | Argumentos de linha de comando | Interface visual |
| Progresso | Barra de texto | Progress bar visual |
| Resultados | Arquivos no sistema | Download ou visualização web |
| Arquivos grandes | Sem limite | Limite de 500MB |
| Múltiplos arquivos | Scripts batch | Um por vez |

## Resolução de Problemas

### Erro: "Module 'streamlit' not found"
```bash
pip install streamlit>=1.28.0
```

### Erro: "Port 8501 already in use"
Outra instância está rodando. Feche-a ou use outra porta:
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Arquivo muito grande
Use o CLI para arquivos maiores que 500MB:
```bash
python split_audio.py arquivo.m4a --transcrever-completa --modelo tiny
```

### Modelo Whisper não carrega
- Verifique conexão com internet (primeira vez baixa o modelo)
- Verifique espaço em disco (modelos podem ter alguns GB)
- Tente um modelo menor (tiny ou base)

### Transcrição em branco
- Verifique se o áudio tem fala audível
- Tente outro modelo (base ou small)
- Verifique formato do arquivo de áudio

## Arquitetura Técnica

- **streamlit_app.py**: Interface principal com UI
- **audio_processor.py**: Wrappers das funções de processamento com callbacks
- **split_audio.py**: Funções originais do CLI (não modificadas)
- **.streamlit/config.toml**: Configurações do servidor e tema

## CLI ainda funciona?

**Sim!** A interface web foi construída sem modificar o código CLI original.

Você pode continuar usando o CLI normalmente:

```bash
# CLI continua funcionando normalmente
python split_audio.py arquivo.m4a --transcrever-completa
```

## Suporte

- Para problemas com a interface web: verifique este README
- Para problemas com processamento de áudio: veja README.md principal
- Para funcionalidades do Whisper: [OpenAI Whisper](https://github.com/openai/whisper)

## Contribuindo

Sugestões e melhorias são bem-vindas! A interface foi projetada para ser simples e fácil de estender.
