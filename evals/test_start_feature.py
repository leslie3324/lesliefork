"""Local Git integration tests; no network or business repository writes."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/start-feature/scripts/start_feature.py"


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


class StartFeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="start-feature-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "origin.git"
        self.source = self.root / "publisher"
        self.repo = self.root / "checkout"
        self.worktree = self.root / "new worktree"
        git(self.root, "init", "--bare", str(self.remote))
        git(self.root, "init", "-b", "pro", str(self.source))
        git(self.source, "config", "user.name", "Test")
        git(self.source, "config", "user.email", "test@example.invalid")
        git(self.source, "config", "commit.gpgsign", "false")
        (self.source / "code.txt").write_text("base\n")
        git(self.source, "add", "code.txt")
        git(self.source, "-c", "core.hooksPath=/dev/null", "commit", "-m", "base")
        git(self.source, "remote", "add", "origin", str(self.remote))
        git(self.source, "push", "origin", "pro")
        git(self.root, "clone", "-b", "pro", str(self.remote), str(self.repo))

    def run_script(self, branch="feat/example", *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.repo), branch, str(self.worktree), *extra],
            capture_output=True, text=True,
        )

    def assert_not_created(self):
        self.assertFalse(self.worktree.exists())
        self.assertNotIn("refs/heads/feat/example", git(
            self.repo, "for-each-ref", "--format=%(refname)", "refs/heads",
        ).splitlines())

    def test_latest_pro_and_original_dirty_index_preserved(self):
        old_base = git(self.repo, "rev-parse", "origin/pro")
        (self.source / "code.txt").write_text("updated pro\n")
        git(self.source, "add", "code.txt")
        git(self.source, "-c", "core.hooksPath=/dev/null", "commit", "-m", "update pro")
        git(self.source, "push", "origin", "pro")
        latest = git(self.source, "rev-parse", "HEAD")
        self.assertNotEqual(old_base, latest)

        git(self.repo, "checkout", "-b", "test")
        (self.repo / "code.txt").write_text("staged test change\n")
        git(self.repo, "add", "code.txt")
        (self.repo / "code.txt").write_text("unstaged test change\n")
        (self.repo / "untracked.txt").write_text("keep\n")
        before = [git(self.repo, *args) for args in (
            ("status", "--porcelain"), ("diff", "--cached"), ("diff",),
            ("rev-parse", "HEAD"), ("branch", "--show-current"),
        )]
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.worktree, "rev-parse", "HEAD"), latest)
        self.assertEqual(git(self.worktree, "branch", "--show-current"), "feat/example")
        self.assertEqual((self.worktree / "code.txt").read_text(), "updated pro\n")
        self.assertEqual(git(self.worktree, "status", "--porcelain"), "")
        after = [git(self.repo, *args) for args in (
            ("status", "--porcelain"), ("diff", "--cached"), ("diff",),
            ("rev-parse", "HEAD"), ("branch", "--show-current"),
        )]
        self.assertEqual(before, after)
        self.assertIn(str(self.worktree), result.stdout)

    def test_invalid_or_existing_branch_refused(self):
        for branch in ("test", "feat/bad..name"):
            with self.subTest(branch=branch):
                self.assertNotEqual(self.run_script(branch).returncode, 0)
                self.assert_not_created()
        git(self.repo, "branch", "feat/example")
        original = git(self.repo, "rev-parse", "feat/example")
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertFalse(self.worktree.exists())
        self.assertEqual(git(self.repo, "rev-parse", "feat/example"), original)

    def test_existing_path_refused(self):
        self.worktree.mkdir()
        marker = self.worktree / "keep.txt"
        marker.write_text("keep\n")
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertEqual(marker.read_text(), "keep\n")

    def test_fetch_failure_does_not_use_cached_pro(self):
        git(self.repo, "remote", "set-url", "origin", str(self.root / "missing.git"))
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assert_not_created()

    def test_missing_remote_pro_does_not_use_cached_ref(self):
        git(self.remote, "update-ref", "-d", "refs/heads/pro")
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assert_not_created()

    def test_test_cannot_be_selected_as_base(self):
        self.assertNotEqual(self.run_script("feat/example", "--base", "origin/test").returncode, 0)
        self.assert_not_created()

    def test_unignored_nested_worktree_refused(self):
        self.worktree = self.repo / ".worktrees" / "example"
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assert_not_created()


if __name__ == "__main__":
    unittest.main()
