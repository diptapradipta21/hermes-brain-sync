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
1. **Bi-Directional Mirroring:** Forward syncs (`agent -> vault`) and restores (`vault -> agent`) procedural skills, prompt templates, and persistent facts.
2. **Filters Heavy Build Artifacts:** Automatically excludes `.cache`, `node_modules`, `__pycache__`, and temporary locks.
3. **Automated Git Rebase & Push:** Seamlessly commits changes and pushes them to your private/team Obsidian Git repository.
4. **Agent Orchestration Ready:** Includes `--dry-run`, `--json` telemetry, and custom exclusions for automated cron pipelines.

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

### 2. Preview Changes (Dry Run)
```bash
python3 hermes_brain_sync.py --agent-root /path/to/hermes --vault /path/to/obsidian-vault --dry-run
```

### 3. Restore Brain from Vault (Disaster Recovery / New Node)
```bash
python3 hermes_brain_sync.py --vault /path/to/obsidian-vault --agent-root /path/to/new-hermes --restore
```

### 4. Machine-Readable JSON Telemetry
```bash
python3 hermes_brain_sync.py --agent-root . --vault /path/to/vault --json
```

Output:
```json
{
  "status": "success",
  "mode": "sync",
  "agent_root": "/opt/data",
  "vault_dir": "/opt/data/vault",
  "sync_dir": "/opt/data/vault/_Agent_Sync",
  "dry_run": false,
  "prune": false,
  "counts": {
    "memories": 4,
    "skills": 12,
    "scripts": 6,
    "total": 22
  },
  "pruned": 0,
  "git_pushed": false,
  "git_output": null,
  "error": null
}
```

### 5. Automated Cron Job (Sync Every Hour)
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

## 🛠️ CLI Options

| Flag | Description | Default |
|---|---|---|
| `--agent-root PATH` | Path to AI agent working directory | `.` |
| `--vault PATH` | Path to your Obsidian Vault directory | *(Required)* |
| `--sync-folder NAME` | Subfolder name inside vault | `_Agent_Sync` |
| `--push` | Commit and git push changes to remote Git vault | `False` |
| `--restore` | Reverse sync: restore vault files into agent root | `False` |
| `--dry-run` | Preview file operations without modifying disk or Git | `False` |
| `--prune` | Remove stale files in destination not present in source | `False` |
| `--exclude PATTERN` | Additional glob pattern to ignore (repeatable) | `[]` |
| `--commit-msg MSG` | Custom commit message for Git versioning | *(Auto-generated)* |
| `--json` | Output machine-readable JSON summary | `False` |

---

## 🧪 Running Tests

```bash
python3 tests/test_hermes_brain_sync.py
```

---

## 🛡️ Security Best Practices
- Never store plaintext API keys or credentials in synced directories.
- Always use a dedicated SSH deploy key with write permissions for your private vault repository.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
