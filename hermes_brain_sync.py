#!/usr/bin/env python3
"""
hermes_brain_sync — Zero-Token Bi-Directional Memory & Skill Mirror for AI Agents.
Syncs local agent memories, learned skills, and custom scripts into a Git-backed Obsidian Vault.
Supports sync (agent -> vault), restore (vault -> agent), mirror pruning (--prune), dry-run, and JSON telemetry.
"""

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_EXCLUDES = [
    "*.lock", "*.tmp", ".git", "__pycache__",
    "node_modules", ".cache", "*.pyc", ".DS_Store"
]


def run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
    res = subprocess.run(cmd, cwd=cwd, shell=False, capture_output=True, text=True)
    return res.returncode == 0, res.stdout.strip(), res.stderr.strip()


def is_excluded(rel_path: Path, exclude_patterns: List[str]) -> bool:
    """Return True if rel_path matches any exclusion glob pattern or directory segment."""
    posix_rel = rel_path.as_posix()
    name = rel_path.name
    for pat in exclude_patterns:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(posix_rel, pat):
            return True
        if any(fnmatch.fnmatch(part, pat) for part in rel_path.parts):
            return True
    return False


def collect_files(source_dir: Path, exclude_patterns: List[str]) -> List[Path]:
    """Collect relative file paths from source_dir, filtering out exclusion patterns."""
    if not source_dir.exists():
        return []
    collected: List[Path] = []
    for item in sorted(source_dir.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(source_dir)
        if not is_excluded(rel, exclude_patterns):
            collected.append(rel)
    return collected


def mirror_directory(
    src: Path,
    dst: Path,
    exclude_patterns: List[str],
    dry_run: bool = False,
    prune: bool = False,
) -> Tuple[int, int]:
    """Mirrors files from src to dst. Returns (copied_count, pruned_count)."""
    rel_files = collect_files(src, exclude_patterns) if src.exists() else []
    src_set = set(rel_files)
    copied = 0
    for rel in rel_files:
        src_file = src / rel
        dst_file = dst / rel
        if not dry_run:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
        copied += 1

    pruned = 0
    if prune and dst.exists():
        for dst_rel in collect_files(dst, [".git"]):
            if dst_rel not in src_set:
                if not dry_run:
                    (dst / dst_rel).unlink()
                pruned += 1

    return copied, pruned


def detect_git_branch(repo_path: Path) -> str:
    ok, out, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if ok and out and out != "HEAD":
        return out
    return "main"


def sync_brain(
    agent_root: str,
    vault_dir: str,
    sync_folder: str = "_Agent_Sync",
    auto_push: bool = False,
    restore: bool = False,
    dry_run: bool = False,
    prune: bool = False,
    custom_excludes: Optional[List[str]] = None,
    commit_msg: Optional[str] = None,
    output_json: bool = False,
) -> Dict[str, Any]:
    agent_path = Path(agent_root).resolve()
    vault_path = Path(vault_dir).resolve()
    sync_path = vault_path / sync_folder

    excludes = list(DEFAULT_EXCLUDES)
    if custom_excludes:
        excludes.extend(custom_excludes)

    result: Dict[str, Any] = {
        "status": "success",
        "mode": "restore" if restore else "sync",
        "agent_root": str(agent_path),
        "vault_dir": str(vault_path),
        "sync_dir": str(sync_path),
        "dry_run": dry_run,
        "prune": prune,
        "counts": {"memories": 0, "skills": 0, "scripts": 0, "total": 0},
        "pruned": 0,
        "git_pushed": False,
        "git_output": None,
        "error": None,
    }

    if restore:
        src_base = sync_path
        dst_base = agent_path
        if not src_base.exists():
            result["status"] = "error"
            result["error"] = f"Vault sync folder does not exist: {sync_path}"
            if not output_json:
                print(f"[!] Error: {result['error']}", file=sys.stderr)
            return result
    else:
        src_base = agent_path
        dst_base = sync_path

    if not output_json:
        action_verb = "Restoring" if restore else "Starting agent brain synchronization"
        dry_str = " (DRY-RUN)" if dry_run else ""
        print(f"[*] {action_verb}{dry_str}...")
        print(f"    Source: {src_base}")
        print(f"    Target: {dst_base}")

    total_cnt = 0
    total_pruned = 0
    for cat in ["memories", "skills", "scripts"]:
        src_cat = src_base / cat
        dst_cat = dst_base / cat
        cnt, pruned_cnt = mirror_directory(
            src_cat, dst_cat, excludes, dry_run=dry_run, prune=prune
        )
        result["counts"][cat] = cnt
        total_cnt += cnt
        total_pruned += pruned_cnt
        if not output_json and (cnt > 0 or pruned_cnt > 0):
            prune_info = f", {pruned_cnt} pruned" if pruned_cnt > 0 else ""
            print(f"  -> {cat.capitalize()}: {cnt} file(s) mirrored{prune_info}.")

    result["counts"]["total"] = total_cnt
    result["pruned"] = total_pruned

    # Git Versioning (only forward sync, non-dry-run, auto_push requested)
    if not restore and auto_push and not dry_run and (vault_path / ".git").exists():
        if not output_json:
            print("  -> Updating Git repository...")
        branch = detect_git_branch(vault_path)
        has_remote, remotes, _ = run_cmd(["git", "remote"], cwd=vault_path)
        if has_remote and "origin" in remotes.splitlines():
            pull_ok, _, pull_err = run_cmd(
                ["git", "pull", "--rebase", "origin", branch], cwd=vault_path
            )
            if not pull_ok and "couldn't find remote ref" not in pull_err.lower():
                result["status"] = "error"
                result["error"] = f"Git pull --rebase failed: {pull_err}"
                if not output_json:
                    print(f"  [!] {result['error']}", file=sys.stderr)
                return result

        add_ok, _, add_err = run_cmd(["git", "add", "--", sync_folder], cwd=vault_path)
        if not add_ok:
            result["status"] = "error"
            result["error"] = f"Git add failed: {add_err}"
            if not output_json:
                print(f"  [!] {result['error']}", file=sys.stderr)
            return result

        _, out, _ = run_cmd(["git", "status", "--porcelain", "--", sync_folder], cwd=vault_path)
        if out:
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
            msg = commit_msg or f"chore(sync): automated brain mirror {now_iso}"
            c_ok, _, c_err = run_cmd(["git", "commit", "-m", msg], cwd=vault_path)
            if not c_ok:
                result["status"] = "error"
                result["error"] = f"Git commit failed: {c_err}"
                if not output_json:
                    print(f"  [!] {result['error']}", file=sys.stderr)
                return result

            p_ok, p_out, p_err = run_cmd(["git", "push", "origin", branch], cwd=vault_path)
            result["git_pushed"] = p_ok
            result["git_output"] = p_out if p_ok else p_err
            if not p_ok:
                result["status"] = "error"
                result["error"] = f"Git push failed: {p_err}"
            if not output_json:
                if p_ok:
                    print("  [✓] Successfully committed and pushed to remote Git repository.")
                else:
                    print(f"  [!] Git push error: {p_err}", file=sys.stderr)
        else:
            result["git_pushed"] = False
            result["git_output"] = "clean"
            if not output_json:
                print("  [✓] Vault already up-to-date. No diff detected.")
    elif not output_json:
        print("  [✓] Mirror operation finished successfully.")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hermes Brain Sync: Automated Git/Obsidian bi-directional mirror for AI agents."
    )
    parser.add_argument("--agent-root", default=".", help="Path to AI agent working directory (default: current dir)")
    parser.add_argument("--vault", required=True, help="Path to your Obsidian Vault directory")
    parser.add_argument("--sync-folder", default="_Agent_Sync", help="Subfolder name inside vault (default: _Agent_Sync)")
    parser.add_argument("--push", action="store_true", help="Automatically commit and git push changes to remote")
    parser.add_argument("--restore", action="store_true", help="Reverse sync: Restore brain from vault into agent-root")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync actions without modifying filesystem or Git")
    parser.add_argument("--prune", action="store_true", help="Prune stale files in destination not present in source")
    parser.add_argument("--exclude", action="append", default=[], help="Additional glob pattern to exclude (repeatable)")
    parser.add_argument("--commit-msg", default=None, help="Custom commit message for Git versioning")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON summary")

    args = parser.parse_args()
    res = sync_brain(
        agent_root=args.agent_root,
        vault_dir=args.vault,
        sync_folder=args.sync_folder,
        auto_push=args.push,
        restore=args.restore,
        dry_run=args.dry_run,
        prune=args.prune,
        custom_excludes=args.exclude,
        commit_msg=args.commit_msg,
        output_json=args.json,
    )

    if args.json:
        print(json.dumps(res, indent=2))

    sys.exit(0 if res.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
