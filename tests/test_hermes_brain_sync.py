#!/usr/bin/env python3
import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys

# Ensure parent is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hermes_brain_sync import sync_brain, collect_files

class TestHermesBrainSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_brain_sync_")
        self.agent_root = Path(self.test_dir) / "agent"
        self.vault_dir = Path(self.test_dir) / "vault"
        
        # Create dummy agent structure
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
            output_json=True
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["counts"]["memories"], 1) # temp.tmp filtered
        self.assertEqual(res["counts"]["skills"], 2)
        self.assertEqual(res["counts"]["scripts"], 1)
        self.assertEqual(res["counts"]["total"], 4)

        # Verify files on target
        sync_dir = self.vault_dir / "_Agent_Sync"
        self.assertTrue((sync_dir / "memories" / "profile.md").exists())
        self.assertFalse((sync_dir / "memories" / "temp.tmp").exists())
        self.assertTrue((sync_dir / "skills" / "sub" / "nested.md").exists())
        self.assertTrue((sync_dir / "scripts" / "tool.py").exists())

    def test_dry_run(self):
        res = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            dry_run=True,
            output_json=True
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["counts"]["total"], 4)
        sync_dir = self.vault_dir / "_Agent_Sync"
        self.assertFalse(sync_dir.exists())

    def test_restore_mode(self):
        # First sync to vault
        sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            output_json=True
        )

        # Now wipe agent root
        shutil.rmtree(self.agent_root)
        self.agent_root.mkdir()

        # Run restore
        res = sync_brain(
            agent_root=str(self.agent_root),
            vault_dir=str(self.vault_dir),
            restore=True,
            output_json=True
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
            output_json=True
        )
        self.assertEqual(res["status"], "error")

if __name__ == "__main__":
    unittest.main()
