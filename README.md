# SPEED — LLM Inference Racing

Side-by-side speed comparison of LLM inference providers. Race **Groq** vs **Cerebras** on the same (or different) models and see real-time streaming speed, tokens per second, and time-to-first-token — all in a racing telemetry UI.

![Python](https://img.shields.io/badge/python-3.9+-blue) ![Flask](https://img.shields.io/badge/flask-latest-green)

## Why This Exists

In RAG architectures, we often focus on vector search latency — single-digit milliseconds is achievable with solutions like Atlas Vector Search. But in practice, the user experience is dominated by LLM inference — often several seconds, sometimes up to half a minute. A faster vector search step doesn't move the needle if the LLM call is the real bottleneck.

Pairing **fast vector search** (Atlas Vector Search) with **fast LLM inference** (Groq, Cerebras) is where things get interesting. When both layers are fast, the end-to-end RAG experience becomes genuinely snappy — and that's what users actually feel.

Providers like **Groq** and **Cerebras** offer dramatically faster inference with generous free tiers that are more than good enough for demos and prototyping. This tool lets you **compare providers and models side-by-side** so you can pick the best option before integrating into your project.

## Features

- **Compare mode** — race two models side-by-side with a unified scoreboard (tokens, time, TTFT, tok/s)
- **Auto-detect** — selecting a model available on both providers auto-enables compare mode
- **Streaming** — real-time token streaming with live speed telemetry
- **Reasoning support** — handles chain-of-thought models (shows "reasoning..." indicator, displays only the final answer)
- **Markdown rendering** — full markdown with syntax-highlighted code blocks, tables, etc.
- **Racing UI** — speed bars, winner detection, and a telemetry dashboard

## Setup

### 1. Get API Keys

Both take less than 5 minutes to set up:

- **Groq**: Sign up at [console.groq.com](https://console.groq.com) and create an API key
- **Cerebras**: Sign up at [cloud.cerebras.ai](https://cloud.cerebras.ai) and create an API key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example env file and add your API keys:

```bash
cp .env.example .env
```

Then edit `.env` with your keys:

```
GROQ_API_KEY=gsk_your_key_here
CEREBRAS_API_KEY=csk-your_key_here
```

### 4. Run

```bash
python app.py
```

Open [http://localhost:5222](http://localhost:5222) in your browser.

## Usage

- **Single mode**: Select a model from the dropdown and chat normally. Telemetry (tokens, time, TTFT, tok/s) appears below each response.
- **Compare mode**: Click **COMPARE** (or select a model available on both providers — it auto-switches). Two models race side-by-side and a scoreboard shows the results.
- **Clear**: Resets the conversation history.

## Important Note

This uses **free-tier API access**. Do not send sensitive or private data to these providers. This is intended for demos, prototyping, and experimentation only.

## License

MIT
