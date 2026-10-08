#!/usr/bin/env python
"""Standalone guard tests for the repo-template BASE layer (H5770, H5733 §7 Q9).

Runs on a box that NEVER cloned claude-config:
    python3 -m unittest discover -s base/tests -v
(plain `python3 base/tests/test_base_pack.py` works too — unittest, no pytest).

Proves: the starter pack validates; a secret-path write and a secret-file read
are BLOCKED; clean calls PASS; override markers bypass their one rule;
force-push / package-publish are AUDIT-level; a malformed pack fails CLOSED;
an absent pack passes through.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agent_policy_mirror as ap  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(BASE_DIR, '.agent_policy.json')


def load_pack():
    return ap.load_policy(PACK_PATH)


def hit(rules, tool, tin, cwd='', root=''):
    return ap.evaluate(rules, tool, tin, cwd, root)


class TestStarterPack(unittest.TestCase):
    def setUp(self):
        self.rules = load_pack()
        self.assertIsNotNone(self.rules)
        self.ids = [r['id'] for r in self.rules]

    def test_pack_loads_and_is_v1(self):
        with open(PACK_PATH, encoding='utf-8') as fh:
            doc = json.load(fh)
        self.assertEqual(doc['schema_version'], ap.SUPPORTED_SCHEMA_VERSION)
        self.assertGreaterEqual(len(self.rules), 3)

    def test_secret_path_write_blocked(self):
        rule = hit(self.rules, 'Write', {'file_path': '/home/x/proj/.env'})
        self.assertIsNotNone(rule)
        self.assertEqual(rule['action'], 'block')
        self.assertEqual(rule['id'], 'env-file-write-deny')

    def test_secret_file_read_blocked(self):
        rule = hit(self.rules, 'Read',
                   {'file_path': '/home/x/proj/keys/id_rsa_backup'})
        self.assertIsNotNone(rule)
        self.assertEqual(rule['action'], 'block')
        self.assertEqual(rule['id'], 'secret-files-deny')

    def test_shell_cat_env_blocked(self):
        rule = hit(self.rules, 'Bash', {'command': 'cat .env && make test'})
        self.assertIsNotNone(rule)
        self.assertEqual(rule['action'], 'block')

    def test_clean_calls_pass(self):
        self.assertIsNone(hit(self.rules, 'Write',
                              {'file_path': '/home/x/proj/src/main.py'}))
        self.assertIsNone(hit(self.rules, 'Bash',
                              {'command': 'pytest -q tests/'}))
        self.assertIsNone(hit(self.rules, 'Read',
                              {'file_path': '/home/x/proj/README.md'}))

    def test_override_marker_bypasses_only_that_rule(self):
        cmd = 'cat .env  # [env-edit-ok]'
        self.assertIsNone(hit(self.rules, 'Bash', {'command': cmd}))
        # the OTHER rules still fire: a force-push is still audited
        rule = hit(self.rules, 'Bash',
                   {'command': 'git push --force origin main'})
        self.assertEqual(rule['action'], 'audit')

    def test_force_push_audited(self):
        rule = hit(self.rules, 'Bash',
                   {'command': 'git push --force origin main'})
        self.assertIsNotNone(rule)
        self.assertEqual(rule['id'], 'force-push-audit')
        self.assertEqual(rule['action'], 'audit')

    def test_package_publish_audited(self):
        rule = hit(self.rules, 'Bash', {'command': 'npm publish'})
        self.assertIsNotNone(rule)
        self.assertEqual(rule['id'], 'package-publish-audit')

    def test_edit_env_dotfile_variant_blocked(self):
        rule = hit(self.rules, 'Edit',
                   {'file_path': '/home/x/proj/.env.production'})
        self.assertIsNotNone(rule)
        self.assertEqual(rule['id'], 'env-file-write-deny')

    def test_neighbours_do_not_overreach(self):
        # `.env` fences the subtree but not a same-prefix neighbour.
        self.assertIsNone(hit(self.rules, 'Write',
                              {'file_path': '/home/x/proj/environment.yml'}))
        self.assertIsNone(hit(self.rules, 'Read',
                              {'file_path': '/home/x/proj/src/keys.py'}))


class TestFailDirections(unittest.TestCase):
    def test_malformed_pack_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, ap.POLICY_FILENAME)
            with open(p, 'w', encoding='utf-8') as fh:
                json.dump({'schema_version': '999', 'rules': []}, fh)
            with self.assertRaises(ap.PolicyError):
                ap.load_policy(p)

    def test_unreadable_pack_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, ap.POLICY_FILENAME)
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write('{not json')
            with self.assertRaises(ap.PolicyError):
                ap.load_policy(p)

    def test_absent_pack_passes_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(
                ap.load_policy(os.path.join(tmp, ap.POLICY_FILENAME)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
