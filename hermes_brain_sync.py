#!/usr/bin/env python3
"""
hermes_brain_sync — Zero-Token Bi-Directional Memory & Skill Mirror for AI Agents.
Syncs local agent memories, learned skills, and custom scripts into a Git-backed Obsidian Vault.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    return res.returncode == 0, res.stdout.strip(), res.stderr.strip()

def sync_brain(agent_root, vault_dir, sync_folder="_Agent_Sync", auto_push=False):
    agent_root = Path(agent_root).resolve()
    vault_dir = Path(vault_dir).resolve()
    sync_dir = vault_dir / sync_folder

    print(f"[*] Starting agent brain synchronization...")
    print(f"    Source: {agent_root}")
    print(f"    Target Vault: {sync_dir}")

    sync_dir.mkdir(parents=True, exist_ok=True)
    dest_mem = sync_dir / "memories"
    dest_skills = sync_dir / "skills"
    dest_scripts = sync_dir / "scripts"

    # 1. Sync Memories
    src_mem = agent_root / "memories"
    if src_mem.exists():
        print("  -> Mirroring persistent memory files...")
        shutil.copytree(src_mem, dest_mem, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.lock", "*.tmp"))

    # 2. Sync Skills
    src_skills = agent_root / "skills"
    if src_skills.exists():
        print("  -> Mirroring procedural skills...")
        shutil.copytree(
            src_skills, 
            dest_skills, 
            dirs_exist_ok=True, 
            ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".cache", "*.pyc")
        )

    # 3. Sync Custom Scripts / Helpers
    src_scripts = agent_root / "scripts"
    if src_scripts.exists():
        print("  -> Mirroring automation scripts...")
        dest_scripts.mkdir(parents=True, exist_ok=True)
        for item in src_scripts.glob("*.py"):
            shutil.copy2(item, dest_scripts / item.name)

    # 4. Git Versioning
    if auto_push and (vault_dir / ".git").exists():
        print("  -> Updating Git repository...")
        run_cmd("git pull --rebase origin main", cwd=vault_dir)
        run_cmd(f"git add {sync_folder}", cwd=vault_dir)
        
        ok, out, _ = run_cmd(f"git status --porcelain {sync_folder}", cwd=vault_dir)
        if out:
            run_cmd('git commit -m "chore(sync): automated AI agent brain & memory mirror"', cwd=vault_dir)
            p_ok, _, p_err = run_cmd("git push origin main", cwd=vault_dir)
            if p_ok:
                print("  [✓] Successfully committed and pushed to remote Git repository.")
            else:
                print(f"  [!] Git push error: {p_err}")
        else:
            print("  [✓] Vault already up-to-date. No diff detected.")
    else:
        print("  [✓] Local mirror updated successfully.")

def main():
    parser = argparse.ArgumentParser(description="Hermes Brain Sync: Automated Git/Obsidian mirror for AI agents.")
    parser.add_argument("--agent-root", default=".", help="Path to AI agent working directory (default: current dir)")
    parser.add_argument("--vault", required=True, help="Path to your Obsidian Vault directory")
    parser.add_argument("--sync-folder", default="_Agent_Sync", help="Subfolder name inside vault (default: _Agent_Sync)")
    parser.add_argument("--push", action="store_true", help="Automatically commit and git push changes to remote")

    args = parser.parse_args()
    sync_brain(args.agent_root, args.vault, args.sync_folder, args.push)

if __name__ == "__main__":
    main()
