# Transcriber - Transcritor Automatico de Audio/Video

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![faster-whisper](https://img.shields.io/badge/faster--whisper-1.1+-green.svg)
![Pyannote](https://img.shields.io/badge/Pyannote-3.3+-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Interface web moderna para converter videos em audio, dividir em segmentos, transcrever automaticamente e identificar falantes usando IA**

</div>

---

## Interface

![Transcriber Interface](https://i.imgur.com/o8sKoPO.png)

---

## O que faz?

O **Transcriber** e uma aplicacao web que automatiza o processo de transcricao de audio e video com identificacao de falantes:

1. **Aceita Videos**: MP4, AVI, MOV, MKV, FLV, WMV, WEBM, M4V, MPG, MPEG
2. **Aceita Audios**: MP3, WAV, M4A, AAC, FLAC, OGG, WMA
3. **Converte Automaticamente**: Extrai audio de videos
4. **Divide em Segmentos**: Quebra em partes menores (configuravel)
5. **Transcreve com IA**: Usa faster-whisper para gerar texto
6. **Identifica Falantes**: Usa Pyannote para diarizacao (quem fala quando)
7. **Salva Resultados**: Transcricao completa + detalhada + por falante

### Caracteristicas Principais

- **Interface Drag-and-Drop**: Arraste arquivos para processar
- **Suporte a Videos**: Converte automaticamente para audio
- **8 Modelos Whisper**: De rapido (tiny) a preciso (large-v3)
- **Diarizacao (Identificacao de Falantes)**: Sabe quem disse o que
- **Progress Bar em Tempo Real**: Acompanhe o processamento
- **Salvamento Incremental**: Nao perde progresso se interromper
- **Download Facilitado**: Baixe transcricoes individuais ou ZIP completo
- **CLI e Web**: Use via linha de comando ou interface Streamlit
- **100% Python**: Streamlit + MoviePy + faster-whisper + Pyannote

---

## Novidade: Identificacao de Falantes

O Transcriber agora identifica automaticamente diferentes falantes no audio:

```
[FALANTE 1] Bom dia, vamos comecar a reuniao.
[FALANTE 2] Claro, o primeiro ponto da pauta e...

[FALANTE 1] Perfeito, sobre isso eu gostaria de comentar que...
[FALANTE 3] Posso adicionar uma observacao?
```

### Como Funciona

```
Audio
  |
  v
[Pyannote] -> Timeline de falantes (quem fala de 0:00-0:15, etc.)
  |
  v
[faster-whisper] -> Transcricao com timestamps precisos
  |
  v
[Combinar] -> Associa cada frase ao falante correto
  |
  v
Saida: "[FALANTE 1] texto... [FALANTE 2] texto..."
```

---

## Instalacao

### Pre-requisitos

- Python 3.13+
- pip (gerenciador de pacotes)
- ffmpeg (para conversao de video)
- Token do HuggingFace (para diarizacao)

### Passo a Passo

1. **Clone o repositorio**

   ```bash
   git clone https://github.com/ramon141/transcriber
   cd transcriber
   ```

2. **Crie um ambiente virtual**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o Token HuggingFace (para diarizacao)**

   A identificacao de falantes usa modelos do HuggingFace que requerem autenticacao:

   a. Crie uma conta em [huggingface.co](https://huggingface.co)

   b. Gere um token em [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

   c. Aceite os termos de uso dos modelos:
      - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
      - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

   d. Crie um arquivo `.env` na raiz do projeto:

   ```bash
   echo "HF_TOKEN=hf_seu_token_aqui" > .env
   ```

5. **Inicie a aplicacao**

   **Interface Web (Streamlit):**
   ```bash
   source venv/bin/activate && STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run streamlit_app.py --server.headless=true
   ```

   **Linha de Comando (CLI):**
   ```bash
   python split_audio.py arquivo.wav --diarizar
   ```

6. **Acesse no navegador**

   - Abre automaticamente em: `http://localhost:8501`
   - Ou acesse manualmente este endereco

---

## Como Usar

### Interface Web (Streamlit)

#### 1. Configure na Barra Lateral

**Modelo de Transcricao:**

- **tiny**: Mais rapido - Qualidade basica
- **base**: Balanceado - **Recomendado**
- **small**: Boa qualidade
- **medium**: Alta qualidade
- **large**: Alta precisao - Mais lento
- **large-v1**: Large versao 1
- **large-v2**: Large versao 2 - Melhor que v1
- **large-v3**: Large versao 3 - **Mais recente e preciso**

**Duracao dos Segmentos:**

- 1 a 10 minutos (padrao: 4 minutos)
- Segmentos menores = processamento mais rapido
- Segmentos maiores = menos arquivos gerados

**Identificar Falantes (Diarizacao):**

- Ativado por padrao quando o token HF esta configurado
- Desative se quiser apenas transcricao simples (mais rapido)

#### 2. Carregue o Arquivo

- **Arraste** o arquivo para a area de upload
- **Ou clique** para selecionar do computador
- Limite de 500MB por arquivo

#### 3. Processe

1. Clique em **"Processar Audio"**
2. Acompanhe o progresso em tempo real
3. Aguarde a conclusao

#### 4. Visualize os Resultados

**Aba "Transcricao Completa":**
- Visualize o texto completo
- Copie diretamente da interface

**Aba "Segmentos":**
- Veja transcricoes por segmento
- Timestamps para cada parte

**Aba "Por Falante":** (quando diarizacao ativada)
- Transcricao organizada por falante
- Estatisticas de tempo de fala
- Cores diferentes para cada falante

**Aba "Downloads":**
- Baixe transcricao completa (.txt)
- Baixe transcricao detalhada (.txt)
- Baixe transcricao com falantes (.txt)
- Baixe ZIP com tudo (audios + transcricoes)

---

### Linha de Comando (CLI)

**Transcricao simples:**
```bash
python split_audio.py arquivo.wav
```

**Com diarizacao (identificacao de falantes):**
```bash
python split_audio.py arquivo.wav --diarizar
```

**Especificando modelo:**
```bash
python split_audio.py arquivo.wav --diarizar --modelo large
```

**Todas as opcoes:**
```bash
python split_audio.py arquivo.wav \
    --duracao 5 \           # Duracao dos segmentos em minutos
    --modelo base \         # Modelo Whisper (tiny/base/small/medium/large/large-v1/large-v2/large-v3)
    --diarizar              # Ativar identificacao de falantes
```

---

## Fluxo de Processamento

```mermaid
graph LR
    A[Upload Arquivo] --> B{Tipo?}
    B -->|Video| C[Extrai Audio]
    B -->|Audio| D{Diarizacao?}
    C --> D
    D -->|Sim| E[Pyannote: Identifica Falantes]
    D -->|Nao| F[Divide em Segmentos]
    E --> F
    F --> G[Transcreve com faster-whisper]
    G --> H{Diarizacao?}
    H -->|Sim| I[Combina Falantes + Texto]
    H -->|Nao| J[Gera Arquivos]
    I --> J
    J --> K[Download]
```

**Exemplo Pratico (com diarizacao):**

```
Entrada: reuniao.mp4 (1 hora, 3 participantes)
         |
         v
Extracao: reuniao.wav
         |
         v
Diarizacao: Pyannote identifica 3 falantes
         |
         v
Divisao: 15 segmentos de 4 minutos
         |
         v
Transcricao: faster-whisper processa cada segmento
         |
         v
Combinacao: Associa texto aos falantes
         |
         v
Saida:
  - reuniao_transcricao_completa.txt
  - reuniao_transcricao_detalhada.txt
  - reuniao_transcricao_com_falantes.txt
  - 15 arquivos de audio (M4A)
```

---

## Estrutura de Saida

```
arquivo_original_dividido/
├── arquivo_original_parte_01.m4a
├── arquivo_original_parte_02.m4a
├── arquivo_original_parte_03.m4a
├── ...
├── arquivo_original_transcricao_completa.txt
├── arquivo_original_transcricao_detalhada.txt
└── arquivo_original_transcricao_com_falantes.txt  (quando diarizacao ativada)
```

**Transcricao com Falantes:**

```
TRANSCRICAO COM IDENTIFICACAO DE FALANTES
==================================================

Arquivo original: reuniao.mp4
Falantes identificados: 3

ESTATISTICAS POR FALANTE:
------------------------------
  FALANTE 1: 45 falas (12.5 min)
  FALANTE 2: 32 falas (8.3 min)
  FALANTE 3: 28 falas (7.2 min)

==================================================

TRANSCRICAO:

[FALANTE 1] Bom dia a todos, vamos comecar a reuniao.
[FALANTE 2] Bom dia! Estou pronto.

[FALANTE 3] Bom dia, pessoal.
[FALANTE 1] Otimo, o primeiro ponto da pauta e...
```

---

## Tempos de Processamento

### Por Modelo (1 hora de audio)

| Modelo       | Velocidade   | Qualidade | Recomendacao          |
|--------------|--------------|-----------|------------------------|
| **tiny**     | Muito rapido | Basica    | Testes rapidos         |
| **base**     | Rapido       | Boa       | Uso geral              |
| **small**    | Moderado     | Muito boa | Conteudo importante    |
| **medium**   | Lento        | Excelente | Alta qualidade         |
| **large**    | Muito lento  | Maxima    | Alta precisao          |
| **large-v1** | Muito lento  | Maxima    | Versao 1 do large      |
| **large-v2** | Muito lento  | Maxima    | Melhor que v1          |
| **large-v3** | Muito lento  | Maxima    | Mais recente e preciso |

### Dicas de Performance

**Para Arquivos Pequenos (< 30 min):**
- Modelo: `base` ou `small`
- Segmentos: 4-5 minutos

**Para Arquivos Grandes (> 1 hora):**
- Modelo: `tiny` (velocidade) ou `base` (qualidade)
- Segmentos: 2-3 minutos
- Salvamento incremental evita perda de dados

**Para Videos:**
- Primeira conversao para audio pode demorar
- Apos conversao, processamento segue normal
- Videos HD podem ter audio pesado

**Diarizacao:**
- Requer GPU para melhor performance
- Automaticamente usa CUDA ou Apple MPS se disponivel
- Em CPU e significativamente mais lento

---

## Casos de Uso

### Transcrever Aulas Gravadas

```
Upload: aula_gravada.mp4
Modelo: base
Diarizacao: Desativada (apenas um falante)
Resultado: Transcricao completa da aula
```

### Transcrever Podcasts com Multiplos Hosts

```
Upload: podcast_ep05.mp3
Modelo: small
Diarizacao: Ativada
Resultado: Texto identificando cada participante
```

### Documentar Reunioes

```
Upload: reuniao_gravada.m4a
Modelo: base
Diarizacao: Ativada
Resultado: Ata da reuniao com identificacao de quem disse o que
```

### Transcrever Entrevistas

```
Upload: entrevista.wav
Modelo: small
Diarizacao: Ativada
Resultado: Transcricao com [ENTREVISTADOR] e [ENTREVISTADO]
```

---

## Solucao de Problemas

### Erro: "Module 'streamlit' not found"

```bash
pip install streamlit>=1.28.0
```

### Erro: "Module 'faster_whisper' not found"

```bash
pip install faster-whisper>=1.1.0
```

### Erro: Token HuggingFace nao configurado

1. Crie arquivo `.env` na raiz do projeto
2. Adicione: `HF_TOKEN=hf_seu_token_aqui`
3. Certifique-se de aceitar os termos dos modelos no HuggingFace

### Erro: 403 Access Denied (HuggingFace)

Voce precisa aceitar os termos de uso dos modelos:
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

### Erro na conversao de video

- Verifique se o ffmpeg esta instalado
- Mac: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: [Baixe aqui](https://ffmpeg.org/download.html)

### Porta 8501 ja em uso

```bash
streamlit run streamlit_app.py --server.port 8502
```

### Arquivo muito grande (>500MB)

- Divida o arquivo antes de processar
- Use ferramentas de corte de video
- Ou reduza a qualidade do video

### Modelo Whisper nao carrega

- **Primeira vez**: Faz download automatico (internet necessaria)
- **Espaco em disco**: Modelos ocupam 100MB a 3GB
- **Tente modelo menor**: Comece com `tiny` ou `base`

### Transcricao vazia ou ruim

- **Audio instrumental**: Whisper so transcreve fala
- **Audio com ruido**: Use modelo `small` ou superior
- **Idioma errado**: Sistema usa portugues por padrao
- **Volume baixo**: Normalize o audio antes

### Processamento interrompido

- **Nao se preocupe!** Salvamento incremental preserva progresso
- Verifique a pasta de saida - transcricoes parciais estao salvas
- Abra o arquivo `_transcricao_completa.txt` para ver o que foi processado

### Diarizacao lenta

- GPU recomendada (CUDA ou Apple MPS)
- Em CPU, a diarizacao e significativamente mais lenta
- Desative diarizacao se nao precisar identificar falantes

### Falantes identificados incorretamente

- Aumente a qualidade do audio
- Certifique-se de que os falantes tem vozes distintas
- Audios com muito ruido de fundo podem confundir o modelo

---

## Arquitetura Tecnica

### Componentes

```
transcriber/
├── streamlit_app.py          # Interface web (frontend + logica)
├── audio_processor.py        # Processamento de audio/video
├── split_audio.py            # Funcoes core (dividir, transcrever, CLI)
├── diarization.py            # Identificacao de falantes (Pyannote)
├── requirements.txt          # Dependencias Python
├── .env                      # Token HuggingFace (nao commitado)
└── .streamlit/
    └── config.toml           # Configuracoes do Streamlit
```

### Tecnologias

- **[Streamlit](https://streamlit.io/)**: Framework web Python
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)**: Transcricao otimizada (CTranslate2)
- **[Pyannote.audio](https://github.com/pyannote/pyannote-audio)**: Diarizacao (identificacao de falantes)
- **[MoviePy](https://zulko.github.io/moviepy/)**: Processamento de video
- **[librosa](https://librosa.org/)**: Analise de audio
- **[pydub](https://github.com/jiaaro/pydub)**: Manipulacao de audio

### Fluxo de Dados

1. **Upload** -> Streamlit recebe arquivo
2. **Deteccao** -> Identifica se e video ou audio
3. **Conversao** (se video) -> MoviePy extrai audio
4. **Diarizacao** (se ativada) -> Pyannote identifica falantes
5. **Divisao** -> librosa divide em segmentos
6. **Transcricao** -> faster-whisper processa cada segmento
7. **Combinacao** (se diarizacao) -> Associa texto aos falantes
8. **Salvamento** -> Arquivos TXT criados incrementalmente
9. **Download** -> Streamlit oferece arquivos para download

---

## Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## Autor

**Ramon**

- GitHub: [@ramon141](https://github.com/ramon141)

---

## Agradecimentos

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Implementacao otimizada do Whisper
- [Pyannote.audio](https://github.com/pyannote/pyannote-audio) - Diarizacao de falantes
- [Streamlit](https://streamlit.io/) - Framework web Python
- [MoviePy](https://zulko.github.io/moviepy/) - Processamento de video
- [librosa](https://librosa.org/) - Analise de audio
- [soundfile](https://pysoundfile.readthedocs.io/) - Leitura/escrita de audio

---

<div align="center">

**Se este projeto foi util, considere dar uma estrela!**

Feito com Python

</div>
