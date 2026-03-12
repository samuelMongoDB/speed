from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv
import json
import os
import time
from groq import Groq
from cerebras.cloud.sdk import Cerebras

load_dotenv()

app = Flask(__name__)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

MODELS = {
    "groq": [
        "openai/gpt-oss-120b",
        "moonshotai/kimi-k2-instruct",
        "qwen/qwen3-32b",
        "openai/gpt-oss-20b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-3.3-70b-versatile",
    ],
    "cerebras": [
        "gpt-oss-120b",
        "llama3.1-8b",
    ],
}

ALL_MODELS = [{"id": m, "provider": "groq"} for m in MODELS["groq"]] + \
             [{"id": m, "provider": "cerebras"} for m in MODELS["cerebras"]]

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SPEED — LLM Racing</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github-dark-dimmed.min.css">
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11/highlight.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #030304;
    --surface: #0a0b0e;
    --surface2: #10121a;
    --border: #1a1c28;
    --border2: #252838;
    --text: #c8cad4;
    --text-dim: #5a5e72;
    --text-bright: #eef0f6;
    --groq: #00e5ff;
    --groq-dim: #00e5ff22;
    --groq-glow: #00e5ff44;
    --cerebras: #b44aff;
    --cerebras-dim: #b44aff22;
    --cerebras-glow: #b44aff44;
    --win: #00ffa3;
    --win-dim: #00ffa322;
    --accent: #ff3d71;
    --mono: 'JetBrains Mono', 'SF Mono', monospace;
    --sans: 'Outfit', sans-serif;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: var(--sans);
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Scan-line overlay */
  body::after {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 9999;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.03) 2px,
      rgba(0,0,0,0.03) 4px
    );
  }

  /* ═══════ HEADER ═══════ */
  header {
    padding: 0 28px;
    height: 56px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 20px;
    background: var(--surface);
    position: relative;
    flex-shrink: 0;
  }
  header::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, var(--groq-dim), transparent 30%, transparent 70%, var(--cerebras-dim));
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    user-select: none;
  }
  .logo-icon {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, var(--groq), var(--cerebras));
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 900;
    color: #000;
    font-family: var(--mono);
    letter-spacing: -1px;
  }
  .logo-text {
    font-family: var(--mono);
    font-weight: 700;
    font-size: 15px;
    color: var(--text-bright);
    letter-spacing: 3px;
    text-transform: uppercase;
  }

  .nav-divider {
    width: 1px;
    height: 24px;
    background: var(--border);
  }

  /* Selects */
  .selects-single, .selects-compare { display: flex; align-items: center; gap: 8px; }
  .selects-compare { display: none; }
  .selects-compare.show { display: flex; }
  .selects-single.hide { display: none; }

  select {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border2);
    border-radius: 6px;
    padding: 6px 10px;
    font-family: var(--mono);
    font-size: 11px;
    cursor: pointer;
    outline: none;
    transition: border-color 0.2s;
  }
  select:focus { border-color: var(--groq); }
  select:hover { border-color: var(--border2); background: #161826; }

  .vs-badge {
    font-family: var(--mono);
    font-weight: 700;
    font-size: 10px;
    color: var(--accent);
    letter-spacing: 2px;
    padding: 4px 8px;
    border: 1px solid var(--accent);
    border-radius: 4px;
    opacity: 0.7;
  }

  .header-right { margin-left: auto; display: flex; align-items: center; gap: 8px; }

  .hdr-btn {
    background: transparent;
    border: 1px solid var(--border2);
    color: var(--text-dim);
    border-radius: 6px;
    padding: 6px 14px;
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.5px;
  }
  .hdr-btn:hover { border-color: var(--text-dim); color: var(--text); }
  #compare-btn.active {
    background: linear-gradient(135deg, var(--groq-dim), var(--cerebras-dim));
    border-color: var(--groq);
    color: var(--text-bright);
    box-shadow: 0 0 20px var(--groq-glow), 0 0 20px var(--cerebras-glow);
  }

  /* ═══════ CHAT AREA ═══════ */
  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 28px;
    display: flex;
    flex-direction: column;
    gap: 24px;
    scrollbar-width: thin;
    scrollbar-color: var(--border2) transparent;
  }
  #chat::-webkit-scrollbar { width: 6px; }
  #chat::-webkit-scrollbar-track { background: transparent; }
  #chat::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

  /* Empty state */
  .empty-state {
    margin: auto;
    text-align: center;
    user-select: none;
    animation: fadeIn 0.6s ease;
  }
  .empty-state .big {
    font-family: var(--mono);
    font-size: 72px;
    font-weight: 900;
    letter-spacing: -4px;
    background: linear-gradient(135deg, var(--groq) 0%, var(--cerebras) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    margin-bottom: 12px;
  }
  .empty-state .sub {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 4px;
    text-transform: uppercase;
  }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

  /* ═══════ USER MESSAGE ═══════ */
  .msg { max-width: 860px; width: 100%; margin: 0 auto; line-height: 1.7; animation: msgIn 0.3s ease; }
  @keyframes msgIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

  .msg.user .label {
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 600;
    color: var(--text-dim);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .msg.user .content { color: var(--text-bright); font-weight: 400; font-size: 15px; }

  /* ═══════ ASSISTANT MESSAGE (single) ═══════ */
  .msg.assistant {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
  }
  .msg.assistant .label {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .msg.assistant .label .model-id { color: var(--text-dim); }

  /* Provider pill */
  .pill {
    font-family: var(--mono);
    font-size: 9px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }
  .pill.groq { background: var(--groq-dim); color: var(--groq); border: 1px solid var(--groq); }
  .pill.cerebras { background: var(--cerebras-dim); color: var(--cerebras); border: 1px solid var(--cerebras); }

  /* ═══════ COMPARE MODE ═══════ */
  .compare-row {
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    animation: msgIn 0.3s ease;
  }

  .compare-cell {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    position: relative;
    overflow: hidden;
  }
  .compare-cell::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0; right: 0;
    height: 2px;
  }
  .compare-cell.left::before { background: linear-gradient(90deg, var(--groq), transparent); }
  .compare-cell.right::before { background: linear-gradient(90deg, var(--cerebras), transparent); }

  .compare-cell .label {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .compare-cell .model-name { color: var(--text-dim); font-size: 11px; }
  .compare-cell .content { min-height: 40px; }

  /* ═══════ TELEMETRY — single mode ═══════ */
  .telemetry {
    margin-top: 16px;
    padding-top: 14px;
    border-top: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 11px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px 16px;
    align-items: center;
  }
  .tel-item { display: flex; align-items: center; gap: 5px; }
  .tel-label { color: var(--text-dim); font-size: 9px; letter-spacing: 1px; text-transform: uppercase; }
  .tel-value { color: var(--text); font-weight: 600; }

  .speed-bar-wrap {
    flex: 1; min-width: 100px; height: 6px;
    background: var(--surface2); border-radius: 3px; overflow: hidden;
  }
  .speed-bar {
    height: 100%; border-radius: 3px; width: 0%;
    transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
  }
  .speed-bar.groq { background: linear-gradient(90deg, var(--groq-dim), var(--groq)); box-shadow: 0 0 8px var(--groq-glow); }
  .speed-bar.cerebras { background: linear-gradient(90deg, var(--cerebras-dim), var(--cerebras)); box-shadow: 0 0 8px var(--cerebras-glow); }

  /* ═══════ SCOREBOARD — compare mode ═══════ */
  .scoreboard {
    max-width: 1400px;
    width: 100%;
    margin: -4px auto 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 20px;
    font-family: var(--mono);
    animation: verdictIn 0.3s ease;
  }
  @keyframes verdictIn { from { opacity: 0; } to { opacity: 1; } }

  .sb-row {
    display: grid;
    grid-template-columns: 1fr 70px 1fr;
    align-items: center;
    padding: 5px 0;
  }
  .sb-row + .sb-row { border-top: 1px solid var(--border); }

  .sb-val {
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
  }
  .sb-val.left { text-align: right; padding-right: 14px; }
  .sb-val.right { text-align: left; padding-left: 14px; }
  .sb-val.winner { color: var(--win); }

  .sb-label {
    text-align: center;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-dim);
  }

  /* Speed bars row */
  .sb-bars {
    display: grid;
    grid-template-columns: 1fr 70px 1fr;
    align-items: center;
    padding: 8px 0 2px;
    border-top: 1px solid var(--border);
  }
  .sb-bar-wrap {
    height: 8px;
    background: var(--surface2);
    border-radius: 4px;
    overflow: hidden;
  }
  .sb-bar-wrap.left { direction: rtl; margin-left: 14px; }
  .sb-bar-wrap.right { margin-right: 14px; }
  .sb-bar {
    height: 100%;
    border-radius: 4px;
    width: 0%;
    transition: width 0.8s cubic-bezier(0.22, 1, 0.36, 1);
  }
  .sb-bar.groq { background: linear-gradient(90deg, var(--groq-dim), var(--groq)); }
  .sb-bar.cerebras { background: linear-gradient(90deg, var(--cerebras-dim), var(--cerebras)); }
  .sb-bar.winner { background: linear-gradient(90deg, var(--win-dim), var(--win)) !important; }
  .sb-bars .sb-label { font-size: 9px; }

  /* ═══════ MARKDOWN CONTENT ═══════ */
  .content { word-wrap: break-word; font-size: 14px; line-height: 1.7; color: var(--text); }
  .content code {
    background: var(--surface2);
    padding: 2px 7px;
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text-bright);
    border: 1px solid var(--border);
  }
  .content pre {
    background: #080a12;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    border: 1px solid var(--border);
  }
  .content pre code { background: none; padding: 0; display: block; border: none; font-size: 12px; }
  .content table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 13px; }
  .content th, .content td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
  .content th { background: var(--surface2); font-weight: 600; color: var(--text-bright); font-size: 12px; }
  .content h1, .content h2, .content h3 { color: var(--text-bright); font-family: var(--sans); }
  .content h1 { font-size: 20px; margin: 18px 0 8px; font-weight: 800; }
  .content h2 { font-size: 17px; margin: 16px 0 6px; font-weight: 700; }
  .content h3 { font-size: 15px; margin: 14px 0 4px; font-weight: 600; }
  .content p { margin: 6px 0; }
  .content ul, .content ol { margin: 6px 0; padding-left: 22px; }
  .content li { margin: 2px 0; }
  .content blockquote { border-left: 2px solid var(--groq); padding-left: 14px; color: var(--text-dim); margin: 10px 0; font-style: italic; }
  .content hr { border: none; border-top: 1px solid var(--border); margin: 18px 0; }
  .content strong { color: var(--text-bright); font-weight: 600; }
  .content a { color: var(--groq); text-decoration: none; }
  .content a:hover { text-decoration: underline; }

  /* Reasoning indicator */
  .reasoning-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: var(--mono);
    color: var(--text-dim);
    font-size: 12px;
    padding: 8px 0;
  }
  .reasoning-indicator .dot-group { display: flex; gap: 3px; }
  .reasoning-indicator .dot {
    width: 4px; height: 4px;
    border-radius: 50%;
    background: var(--groq);
    animation: dotPulse 1.4s infinite;
  }
  .reasoning-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
  .reasoning-indicator .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes dotPulse { 0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1.2); } }

  /* ═══════ INPUT AREA ═══════ */
  #input-area {
    border-top: 1px solid var(--border);
    padding: 16px 28px;
    background: var(--surface);
    flex-shrink: 0;
  }
  #input-wrap {
    max-width: 860px;
    margin: 0 auto;
    display: flex;
    gap: 10px;
    position: relative;
  }
  #prompt {
    flex: 1;
    background: var(--surface2);
    color: var(--text-bright);
    border: 1px solid var(--border2);
    border-radius: 10px;
    padding: 12px 16px;
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 400;
    resize: none;
    outline: none;
    min-height: 46px;
    max-height: 200px;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  #prompt:focus {
    border-color: var(--groq);
    box-shadow: 0 0 0 3px var(--groq-dim);
  }
  #prompt::placeholder { color: var(--text-dim); }

  #send {
    background: var(--text-bright);
    color: var(--bg);
    border: none;
    border-radius: 10px;
    padding: 0 22px;
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    letter-spacing: 1px;
    text-transform: uppercase;
    transition: all 0.2s;
    white-space: nowrap;
  }
  #send:hover { background: #fff; box-shadow: 0 0 16px rgba(255,255,255,0.1); }
  #send:disabled { background: var(--border2); color: var(--text-dim); cursor: not-allowed; box-shadow: none; }
</style>
</head>
<body>
  <header>
    <div class="logo">
      <div class="logo-icon">//</div>
      <span class="logo-text">Speed</span>
    </div>
    <div class="nav-divider"></div>
    <div class="selects-single" id="single-select">
      <select id="model"></select>
    </div>
    <div class="selects-compare" id="compare-selects">
      <select id="model-left"></select>
      <span class="vs-badge">VS</span>
      <select id="model-right"></select>
    </div>
    <div class="header-right">
      <button class="hdr-btn" id="compare-btn">COMPARE</button>
      <button class="hdr-btn" id="clear-btn">CLEAR</button>
    </div>
  </header>

  <div id="chat">
    <div class="empty-state">
      <div class="big">SPEED</div>
      <div class="sub">LLM inference racing</div>
    </div>
  </div>

  <div id="input-area">
    <div id="input-wrap">
      <textarea id="prompt" rows="1" placeholder="Ask anything — race the models..." autofocus></textarea>
      <button id="send">SEND</button>
    </div>
  </div>

<script>
marked.setOptions({
  highlight: (code, lang) => { try { return lang ? hljs.highlight(code, {language: lang}).value : hljs.highlightAuto(code).value; } catch(e) { return code; } },
  breaks: true
});

const allModels = ALL_MODELS_JSON;
let compareMode = false;
let messages = [];
const MAX_TPS_SCALE = 1200; // for speed bar scaling

function baseName(id) { return id.replace(/^.*\//, ''); }
const groqModels = allModels.filter(m => m.provider === 'groq');
const cerebrasModels = allModels.filter(m => m.provider === 'cerebras');
const sharedBaseNames = new Set();
groqModels.forEach(g => {
  cerebrasModels.forEach(c => {
    if (baseName(g.id) === baseName(c.id)) sharedBaseNames.add(baseName(g.id));
  });
});

function optionText(m) {
  const shared = sharedBaseNames.has(baseName(m.id)) ? ' ⚔' : '';
  return m.provider.toUpperCase() + ' · ' + m.id + shared;
}

function populateSelect(sel) {
  sel.innerHTML = '';
  allModels.forEach(m => {
    const o = document.createElement('option');
    o.value = JSON.stringify(m);
    o.textContent = optionText(m);
    sel.appendChild(o);
  });
}

const selSingle = document.getElementById('model');
const selLeft = document.getElementById('model-left');
const selRight = document.getElementById('model-right');
populateSelect(selSingle);
populateSelect(selLeft);
populateSelect(selRight);
selLeft.value = JSON.stringify({id: 'openai/gpt-oss-120b', provider: 'groq'});
selRight.value = JSON.stringify({id: 'gpt-oss-120b', provider: 'cerebras'});

const compareBtn = document.getElementById('compare-btn');
const clearBtn = document.getElementById('clear-btn');
const chat = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send');

function setCompareMode(on) {
  compareMode = on;
  compareBtn.classList.toggle('active', compareMode);
  compareBtn.textContent = compareMode ? '⚔ RACING' : 'COMPARE';
  document.getElementById('single-select').classList.toggle('hide', compareMode);
  document.getElementById('compare-selects').classList.toggle('show', compareMode);
}

compareBtn.addEventListener('click', () => setCompareMode(!compareMode));

selSingle.addEventListener('change', () => {
  const m = JSON.parse(selSingle.value);
  const bn = baseName(m.id);
  const other = allModels.find(o => baseName(o.id) === bn && o.provider !== m.provider);
  if (other) {
    const groqModel = m.provider === 'groq' ? m : other;
    const cerebrasModel = m.provider === 'cerebras' ? m : other;
    selLeft.value = JSON.stringify(groqModel);
    selRight.value = JSON.stringify(cerebrasModel);
  } else {
    selLeft.value = JSON.stringify(m);
    selRight.value = JSON.stringify(m);
  }
  setCompareMode(true);
});

setCompareMode(true);

clearBtn.addEventListener('click', () => {
  messages = [];
  chat.innerHTML = '<div class="empty-state"><div class="big">SPEED</div><div class="sub">LLM inference racing</div></div>';
});

promptEl.addEventListener('input', () => { promptEl.style.height = 'auto'; promptEl.style.height = promptEl.scrollHeight + 'px'; });
promptEl.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
sendBtn.addEventListener('click', send);

function renderMd(text) { try { return marked.parse(text); } catch(e) { return text; } }
function stripThink(text) { return text.replace(/<think>[\s\S]*?<\/think>\n?/g, ''); }
function pill(provider) { return '<span class="pill ' + provider + '">' + provider + '</span>'; }

function addUserMsg(text) {
  const empty = chat.querySelector('.empty-state');
  if (empty) empty.remove();
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = '<div class="label">PROMPT</div><div class="content"></div>';
  div.querySelector('.content').textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function addAssistantMsg(modelInfo) {
  const empty = chat.querySelector('.empty-state');
  if (empty) empty.remove();
  const div = document.createElement('div');
  div.className = 'msg assistant';
  const barClass = modelInfo.provider;
  div.innerHTML =
    '<div class="label">' + pill(modelInfo.provider) + ' <span class="model-id">' + modelInfo.id + '</span></div>' +
    '<div class="content"></div>' +
    '<div class="telemetry">' +
      '<div class="tel-item"><span class="tel-label">Tokens</span><span class="tel-value tok-val">—</span></div>' +
      '<div class="tel-item"><span class="tel-label">Time</span><span class="tel-value time-val">—</span></div>' +
      '<div class="tel-item"><span class="tel-label">TTFT</span><span class="tel-value ttft-val">—</span></div>' +
      '<div class="tel-item"><span class="tel-label">Speed</span><span class="tel-value tps-val">—</span></div>' +
      '<div class="speed-bar-wrap"><div class="speed-bar ' + barClass + '"></div></div>' +
    '</div>';
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return {
    content: div.querySelector('.content'),
    telemetry: div.querySelector('.telemetry'),
    tokVal: div.querySelector('.tok-val'),
    timeVal: div.querySelector('.time-val'),
    ttftVal: div.querySelector('.ttft-val'),
    tpsVal: div.querySelector('.tps-val'),
    speedBar: div.querySelector('.speed-bar'),
  };
}

function addCompareRow(leftInfo, rightInfo) {
  const empty = chat.querySelector('.empty-state');
  if (empty) empty.remove();
  const row = document.createElement('div');
  row.className = 'compare-row';

  function cellHtml(info, side) {
    return '<div class="compare-cell ' + side + '">' +
      '<div class="label">' + pill(info.provider) + ' <span class="model-name">' + info.id + '</span></div>' +
      '<div class="content"></div>' +
    '</div>';
  }

  row.innerHTML = cellHtml(leftInfo, 'left') + cellHtml(rightInfo, 'right');
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;

  const cells = row.querySelectorAll('.compare-cell');
  return {
    left: { cell: cells[0], content: cells[0].querySelector('.content') },
    right: { cell: cells[1], content: cells[1].querySelector('.content') },
    row
  };
}

async function streamResponse(modelInfo, msgs, contentEl, telEls) {
  const t0 = performance.now();
  let full = '', tokIn = 0, tokOut = 0, contentChunks = 0, reasoningChunks = 0, isReasoning = true, firstContentTime = null;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: msgs, model: modelInfo.id, provider: modelInfo.provider })
    });
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += dec.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        if (data === '[DONE]') continue;
        const parsed = JSON.parse(data);

        if (parsed.usage) {
          tokIn = parsed.usage.prompt_tokens;
          tokOut = parsed.usage.completion_tokens;
          continue;
        }

        const hasReasoning = parsed.choices?.[0]?.delta?.reasoning;
        const hasContent = parsed.choices?.[0]?.delta?.content;

        if (hasReasoning) {
          reasoningChunks++;
          if (!hasContent) {
            contentEl.innerHTML = '<div class="reasoning-indicator"><div class="dot-group"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>reasoning</div>';
          }
        }
        if (hasContent) {
          contentChunks++;
          if (isReasoning) { isReasoning = false; firstContentTime = performance.now(); }
          full += hasContent;
          if (full.includes('<think>') && !full.includes('</think>')) {
            contentEl.innerHTML = '<div class="reasoning-indicator"><div class="dot-group"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>thinking</div>';
          } else {
            contentEl.innerHTML = renderMd(stripThink(full));
          }
        }

        // Live telemetry update (only for single mode with tel elements)
        if (telEls) {
          const elapsed = ((performance.now() - t0) / 1000);
          const displayOut = tokOut || contentChunks;
          if (displayOut > 0) {
            const liveTps = (displayOut / elapsed).toFixed(0);
            telEls.tpsVal.textContent = liveTps + ' tok/s';
            telEls.timeVal.textContent = elapsed.toFixed(1) + 's';
            telEls.speedBar.style.width = Math.min(100, (liveTps / MAX_TPS_SCALE) * 100) + '%';
          }
        }

        chat.scrollTop = chat.scrollHeight;
      }
    }
  } catch (e) {
    contentEl.textContent = 'Error: ' + e.message;
  }

  // Final render
  const clean = stripThink(full).trim();
  contentEl.innerHTML = renderMd(clean);
  contentEl.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));

  const elapsed = ((performance.now() - t0) / 1000);
  const displayOut = tokOut || contentChunks;
  const tps = displayOut > 0 ? Math.round(displayOut / elapsed) : 0;
  const ttft = firstContentTime ? ((firstContentTime - t0) / 1000).toFixed(2) : null;

  // Update single-mode telemetry if present
  if (telEls) {
    telEls.tokVal.textContent = (tokIn ? tokIn + ' → ' : '') + displayOut;
    telEls.timeVal.textContent = elapsed.toFixed(2) + 's';
    telEls.ttftVal.textContent = ttft ? ttft + 's' : '—';
    telEls.tpsVal.textContent = tps + ' tok/s';
    telEls.speedBar.style.width = Math.min(100, (tps / MAX_TPS_SCALE) * 100) + '%';
  }

  return { clean, elapsed, tps, tokOut: displayOut, tokIn, ttft, reasoningChunks, provider: modelInfo.provider };
}

async function send() {
  const text = promptEl.value.trim();
  if (!text) return;
  promptEl.value = ''; promptEl.style.height = 'auto';
  sendBtn.disabled = true;

  messages.push({ role: 'user', content: text });
  addUserMsg(text);

  if (compareMode) {
    const leftInfo = JSON.parse(selLeft.value);
    const rightInfo = JSON.parse(selRight.value);
    const { left: leftEls, right: rightEls, row: compareRow } = addCompareRow(leftInfo, rightInfo);

    const [L, R] = await Promise.all([
      streamResponse(leftInfo, messages, leftEls.content, null),
      streamResponse(rightInfo, messages, rightEls.content, null),
    ]);

    // Build scoreboard
    const leftWins = L.tps >= R.tps;
    const sb = document.createElement('div');
    sb.className = 'scoreboard';

    function sbRow(label, lVal, rVal, highlightWinner) {
      const lw = highlightWinner && leftWins ? ' winner' : '';
      const rw = highlightWinner && !leftWins ? ' winner' : '';
      return '<div class="sb-row">' +
        '<div class="sb-val left' + lw + '">' + lVal + '</div>' +
        '<div class="sb-label">' + label + '</div>' +
        '<div class="sb-val right' + rw + '">' + rVal + '</div>' +
      '</div>';
    }

    const lTok = (L.tokIn ? L.tokIn + ' → ' : '') + L.tokOut;
    const rTok = (R.tokIn ? R.tokIn + ' → ' : '') + R.tokOut;
    const lTime = L.elapsed.toFixed(2) + 's';
    const rTime = R.elapsed.toFixed(2) + 's';
    const lTtft = L.ttft ? L.ttft + 's' : '—';
    const rTtft = R.ttft ? R.ttft + 's' : '—';
    const lTps = L.tps + ' tok/s';
    const rTps = R.tps + ' tok/s';

    let html = '';
    html += sbRow('TOKENS', lTok, rTok, false);
    html += sbRow('TIME', lTime, rTime, false);
    if (L.reasoningChunks > 0 || R.reasoningChunks > 0) {
      html += sbRow('TTFT', lTtft, rTtft, false);
    }
    html += sbRow('SPEED', lTps, rTps, true);

    // Speed bars
    const maxTps = Math.max(L.tps, R.tps) || 1;
    const lPct = Math.round((L.tps / maxTps) * 100);
    const rPct = Math.round((R.tps / maxTps) * 100);
    const lBarClass = L.provider + (leftWins ? ' winner' : '');
    const rBarClass = R.provider + (!leftWins ? ' winner' : '');
    html += '<div class="sb-bars">' +
      '<div class="sb-bar-wrap left"><div class="sb-bar ' + lBarClass + '" style="width:' + lPct + '%"></div></div>' +
      '<div class="sb-label">TOK/S</div>' +
      '<div class="sb-bar-wrap right"><div class="sb-bar ' + rBarClass + '" style="width:' + rPct + '%"></div></div>' +
    '</div>';

    sb.innerHTML = html;
    compareRow.after(sb);
    chat.scrollTop = chat.scrollHeight;

    messages.push({ role: 'assistant', content: L.clean });
  } else {
    const modelInfo = JSON.parse(selSingle.value);
    const els = addAssistantMsg(modelInfo);
    const result = await streamResponse(modelInfo, messages, els.content, els);
    messages.push({ role: 'assistant', content: result.clean });
  }

  sendBtn.disabled = false;
  promptEl.focus();
}
</script>
</body>
</html>"""


@app.route('/')
def index():
    html = HTML.replace('ALL_MODELS_JSON', json.dumps(ALL_MODELS))
    return html


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    model = data.get('model')
    provider = data.get('provider', 'groq')
    msgs = data.get('messages', [])

    if provider not in MODELS or model not in MODELS.get(provider, []):
        return jsonify({"error": "Invalid model or provider"}), 400

    if len(msgs) > 50 or any(len(m.get('content', '')) > 20000 for m in msgs):
        return jsonify({"error": "Payload too large"}), 400

    client = groq_client if provider == 'groq' else cerebras_client

    def generate():
        retries = 2
        for attempt in range(retries + 1):
            try:
                stream = client.chat.completions.create(
                    model=model,
                    messages=msgs,
                    stream=True,
                    max_tokens=4096,
                )
                for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        content = getattr(delta, 'content', None)
                        reasoning = getattr(delta, 'reasoning', None)

                        out = {}
                        if content:
                            out['content'] = content
                        if reasoning:
                            out['reasoning'] = reasoning

                        if out:
                            yield f"data: {{\"choices\": [{{\"delta\": {json.dumps(out)}}}]}}\n\n"

                    # Usage from groq (in x_groq.usage)
                    if hasattr(chunk, 'x_groq') and chunk.x_groq and hasattr(chunk.x_groq, 'usage') and chunk.x_groq.usage:
                        u = chunk.x_groq.usage
                        pt = getattr(u, 'prompt_tokens', 0) or 0
                        ct = getattr(u, 'completion_tokens', 0) or 0
                        if pt or ct:
                            yield f"data: {{\"usage\": {{\"prompt_tokens\": {pt}, \"completion_tokens\": {ct}}}}}\n\n"
                    # Usage from cerebras (in chunk.usage directly)
                    if hasattr(chunk, 'usage') and chunk.usage:
                        u = chunk.usage
                        pt = getattr(u, 'prompt_tokens', 0) or 0
                        ct = getattr(u, 'completion_tokens', 0) or 0
                        if pt or ct:
                            yield f"data: {{\"usage\": {{\"prompt_tokens\": {pt}, \"completion_tokens\": {ct}}}}}\n\n"

                break  # success, exit retry loop
            except Exception as e:
                err_str = str(e).lower()
                if attempt < retries and ('429' in err_str or 'rate' in err_str or 'queue' in err_str):
                    time.sleep(1 + attempt)
                    continue
                yield f"data: {{\"choices\": [{{\"delta\": {{\"content\": \"Error: request failed. Please try again.\"}}}}]}}\n\n"
                break

        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5222)
