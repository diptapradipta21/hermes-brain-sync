# 🧠 Hermes Brain Sync

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Zero Token Cost](https://img.shields.io/badge/LLM%20Tokens-0-green.svg)](#)

> **Zero-token bi-directional memory, skills, and configuration mirror between headless AI Agents (VPS/cloud) and your local Obsidian Vault via Git.**

---

## 💡 The Problem
Running autonomous AI coding agents (Hermes, Claude Code, AutoGen) on remote servers or cloud VMs creates an isolation dilemma:
* Your agent continuously learns new skills, saves session memories, and creates helper scripts on the VPS.
* But you work on your MacBook/desktop using tools like **Obsidian** to organize your thoughts and projects.
* Traditional API syncing burns LLM tokens or requires bloated third-party cloud services.

## 🚀 The Solution
`hermes-brain-sync` is a lightweight, zero-token CLI tool that:
1. **Mirrors Agent Memories & Learned Skills:** Safely clones the agent's procedural skills, prompt templates, and persistent facts.
2. **Filters Heavy Build Artifacts:** Automatically excludes `.cache`, `node_modules`, `__pycache__`, and temporary locks.
3. **Automated Git Rebase & Push:** Seamlessly commits changes and pushes them to your private/team Obsidian Git repository so your laptop is always 100% in sync with your VPS agent.

---

## 📦 Installation

```bash
git clone https://github.com/diptapradipta21/hermes-brain-sync.git
cd hermes-brain-sync
chmod +x hermes_brain_sync.py
```

No external dependencies required (Pure Python Standard Library).

---

## ⚡ Quick Start

### 1. Basic Synchronization
```bash
python3 hermes_brain_sync.py --agent-root /path/to/hermes --vault /path/to/obsidian-vault --push
```

### 2. Set up Automated Cronjob (Sync Every Hour)
```bash
crontab -e
```
Add the following line:
```cron
0 * * * * python3 /path/to/hermes_brain_sync.py --agent-root /opt/data --vault /opt/data/obsidian-vault --push >> /var/log/brain_sync.log 2>&1
```

---

## 📂 Vault Structure

When synced, your Obsidian Vault will have a clean, organized folder structure:

```text
My-Obsidian-Vault/
├── 01 - Projects/
├── 02 - Notes/
└── _Agent_Sync/
    ├── memories/       <-- Persistent facts & preferences
    ├── skills/         <-- Procedural skills & markdown guides
    └── scripts/        <-- Custom agent helper scripts
```

---

## 🛡️ Security Best Practices
- Never store plaintext API keys or credentials in synced directories.
- Always use a dedicated SSH deploy key with write permissions for your private vault repository.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
