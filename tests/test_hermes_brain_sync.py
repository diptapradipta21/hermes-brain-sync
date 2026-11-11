#!/usr/bin/env python3
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hermes_brain_sync import DEFAULT_EXCLUDES, collect_files, sync_brain


class TestHermesBrainSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_brain_sync_")
        self.agent_root = Path(self.test_dir) / "agent"
        self.vault_dir = Path(self.test_dir) / "vault"

        (self.agent_root / "memories").mkdir(parents=True)
        (self.agent_root / "skills" / "sub").mkdir(parents=True)
        (self.agent_root / "scripts").mkdir(parents=True)

        (self.agent_root / "memories" / "profile.md").write_text("user notes", encoding="utf-8")
        (self.agent_root / "memories" / "temp.tmp").write_text("skip me", encoding="utf-8")
        (self.agent_root / "skills" / "search.md").write_text("search skill", encoding="utf-8")
        (self.agent_root / "skills" / "sub" / "nested.md").write_text("nested skill", encoding="utf-8")
        (self.agent_root / "scripts" / "tool.py").write_text("print('tool')", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sync_forward(self):
        res = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            auto_push=False,
            restore=False,
            dry_run=False,
            output_json=True,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["counts"]["memories"], 1)
        self.assertEqual(res["counts"]["skills"], 2)
        self.assertEqual(res["counts"]["scripts"], 1)
        self.assertEqual(res["counts"]["total"], 4)

        sync_dir = self.vault_dir / "_Agent_Sync"
        self.assertTrue((sync_dir / "memories" / "profile.md").exists())
        self.assertFalse((sync_dir / "memories" / "temp.tmp").exists())
        self.assertTrue((sync_dir / "skills" / "sub" / "nested.md").exists())
        self.assertTrue((sync_dir / "scripts" / "tool.py").exists())

    def test_exclusion_glob_precision(self):
        (self.agent_root / "memories" / "locked_notes.md").write_text("keep", encoding="utf-8")
        (self.agent_root / "memories" / "pycharm_guide.md").write_text("keep", encoding="utf-8")
        (self.agent_root / "memories" / "state.lock").write_text("skip", encoding="utf-8")
        (self.agent_root / "memories" / ".gitignore").write_text("*.tmp", encoding="utf-8")
        (self.agent_root / "memories" / ".git").mkdir()
        (self.agent_root / "memories" / ".git" / "config").write_text("skip", encoding="utf-8")

        rels = {p.as_posix() for p in collect_files(self.agent_root / "memories", DEFAULT_EXCLUDES)}
        self.assertIn("locked_notes.md", rels)
        self.assertIn("pycharm_guide.md", rels)
        self.assertIn(".gitignore", rels)
        self.assertNotIn("state.lock", rels)
        self.assertNotIn(".git/config", rels)

    def test_prune_and_dry_run(self):
        stale = self.vault_dir / "_Agent_Sync" / "memories" / "stale.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("old", encoding="utf-8")

        dry = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            dry_run=True,
            prune=True,
            output_json=True,
        )
        self.assertEqual(dry["pruned"], 1)
        self.assertTrue(stale.exists())

        real = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            dry_run=False,
            prune=True,
            output_json=True,
        )
        self.assertEqual(real["pruned"], 1)
        self.assertFalse(stale.exists())

    def test_git_push_with_quoted_commit_message(self):
        bare = Path(self.test_dir) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)
        subprocess.run(["git", "clone", str(bare), str(self.vault_dir)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.vault_dir), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.vault_dir), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.vault_dir), "checkout", "-b", "main"], check=True, capture_output=True)

        res = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            auto_push=True,
            commit_msg='chore: sync "quoted" $(noop) message',
            output_json=True,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["git_pushed"])
        log_out = subprocess.run(
            ["git", "-C", str(self.vault_dir), "log", "-1", "--pretty=%s"],
            check=True, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(log_out, 'chore: sync "quoted" $(noop) message')

    def test_dry_run(self):
        res = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            dry_run=True,
            output_json=True,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["counts"]["total"], 4)
        sync_dir = self.vault_dir / "_Agent_Sync"
        self.assertFalse(sync_dir.exists())

    def test_restore_mode(self):
        sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            output_json=True,
        )
        shutil.rmtree(self.agent_root)
        self.agent_root.mkdir()

        res = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            restore=True,
            output_json=True,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["counts"]["total"], 4)
        self.assertTrue((self.agent_root / "memories" / "profile.md").exists())
        self.assertTrue((self.agent_root / "skills" / "sub" / "nested.md").exists())
        self.assertEqual((self.agent_root / "memories" / "profile.md").read_text(encoding="utf-8"), "user notes")

    def test_restore_missing_vault(self):
        empty_vault = Path(self.test_dir) / "nonexistent"
        res = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(empty_vault),
            restore=True,
            output_json=True,
        )
        self.assertEqual(res["status"], "error")


if __name__ == "__main__":
    unittest.main()
