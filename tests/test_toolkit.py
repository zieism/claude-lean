"""Toolkit tests (stdlib unittest only): installer idempotency and safety, uninstall, checkpoints, quiet wrapper,
usage parsing (repeated content blocks), privacy of the report, skill format, portability of the package."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = ["bash"]
sys.path.insert(0, str(ROOT / "scripts"))
import usage_report  # noqa: E402


def sh(script, *args, env=None, cwd=None):
    return subprocess.run(SH + [str(ROOT / "scripts" / script), *args], capture_output=True, text=True,
                          env={**os.environ, **(env or {})}, cwd=cwd)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.cdir = self.tmp / "claude"; self.cdir.mkdir()
        self.settings = self.cdir / "settings.json"
        self.settings.write_text(json.dumps({"model": "opus", "theme": "dark", "permissions": {"allow": ["Read"]}}, indent=2))
        self.env = {"CLAUDE_CONFIG_DIR": str(self.cdir)}
        self.skill = self.cdir / "skills/claude-lean/SKILL.md"
        self.alias = self.cdir / "skills/token-efficient-workflow/SKILL.md"


class TestInstaller(Base):
    def test_install_is_idempotent_and_preserves_settings(self):
        before = sha(self.settings)
        r1 = sh("install.sh", env=self.env); self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        self.assertTrue(self.skill.exists() and (self.cdir / "budget-manager/usage_report.py").exists())
        man1 = (self.cdir / "budget-manager/MANIFEST").read_text()
        r2 = sh("install.sh", env=self.env); self.assertEqual(r2.returncode, 0)
        self.assertNotIn("install   ", r2.stdout); self.assertEqual(r2.stdout.count("unchanged"), 4)
        self.assertIn("name: token-efficient-workflow", self.alias.read_text()); self.assertIn("claude-lean", self.alias.read_text())
        self.assertEqual(man1, (self.cdir / "budget-manager/MANIFEST").read_text())
        self.assertEqual(sha(self.settings), before)                       # settings + model untouched
        self.assertEqual(json.loads(self.settings.read_text())["model"], "opus")

    def test_modified_skill_is_not_overwritten_without_force(self):
        sh("install.sh", env=self.env)
        self.skill.write_text(self.skill.read_text() + "\n<!-- my local edit -->\n")
        r = sh("install.sh", env=self.env)
        self.assertEqual(r.returncode, 3); self.assertIn("KEEP", r.stdout)
        self.assertIn("my local edit", self.skill.read_text())
        r = sh("install.sh", "--force", env=self.env)
        self.assertEqual(r.returncode, 0); self.assertNotIn("my local edit", self.skill.read_text())
        self.assertTrue(list(self.skill.parent.glob("SKILL.md.bak-*")))    # backup kept

    def test_foreign_existing_skill_is_kept(self):
        self.skill.parent.mkdir(parents=True); self.skill.write_text("---\nname: token-efficient-workflow\n---\nmine\n")
        r = sh("install.sh", env=self.env)
        self.assertEqual(r.returncode, 3); self.assertEqual(self.skill.read_text().splitlines()[-1], "mine")

    def test_dry_run_changes_nothing(self):
        r = sh("install.sh", "--dry-run", "--project", str(self.tmp / "proj"), env=self.env)
        self.assertEqual(r.returncode, 0); self.assertFalse(self.skill.exists()); self.assertFalse((self.tmp / "proj").exists())


class TestUpgradeFromV01(Base):
    """v0.1.0 / v0.1.1 installed the full skill as skills/token-efficient-workflow/SKILL.md (recorded in MANIFEST)."""
    OLD = "---\nname: token-efficient-workflow\ndescription: old full skill\n---\n# Token-efficient workflow\n"

    def legacy_install(self, content, recorded):
        self.alias.parent.mkdir(parents=True); self.alias.write_text(content)
        man = self.cdir / "budget-manager/MANIFEST"; man.parent.mkdir(parents=True)
        man.write_text(f"{hashlib.sha256(recorded.encode()).hexdigest()} {self.alias}\n")

    def test_unmodified_legacy_skill_becomes_alias(self):
        self.legacy_install(self.OLD, self.OLD)
        r = sh("install.sh", env=self.env); self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("upgrade   " + str(self.alias), r.stdout)
        self.assertTrue(self.skill.exists()); self.assertIn("Load the `claude-lean` skill", self.alias.read_text())
        self.assertEqual(sh("uninstall.sh", env=self.env).returncode, 0)
        self.assertFalse(self.alias.exists() or self.skill.exists())

    def test_customized_legacy_skill_is_never_overwritten_or_deleted(self):
        custom = self.OLD + "\nmy own rules\n"
        self.legacy_install(custom, self.OLD)                      # recorded hash = original; file was customized
        r = sh("install.sh", env=self.env)
        self.assertEqual(r.returncode, 3); self.assertIn("KEEP      " + str(self.alias), r.stdout)
        self.assertEqual(self.alias.read_text(), custom); self.assertTrue(self.skill.exists())
        self.assertEqual(sh("install.sh", env=self.env).returncode, 3)
        self.assertEqual(self.alias.read_text(), custom)           # repeated installs still keep it
        r = sh("uninstall.sh", env=self.env)
        self.assertEqual(r.returncode, 3); self.assertEqual(self.alias.read_text(), custom); self.assertFalse(self.skill.exists())

    def test_no_alias_option_leaves_legacy_path_alone(self):
        r = sh("install.sh", "--no-alias", env=self.env)
        self.assertEqual(r.returncode, 0); self.assertTrue(self.skill.exists()); self.assertFalse(self.alias.exists())


class TestUninstall(Base):
    def test_uninstall_removes_only_unmodified_files(self):
        sh("install.sh", env=self.env)
        (self.cdir / "budget-manager/quiet.sh").write_text("#!/bin/sh\necho edited\n")
        r = sh("uninstall.sh", env=self.env)
        self.assertEqual(r.returncode, 3); self.assertFalse(self.skill.exists())
        self.assertTrue((self.cdir / "budget-manager/quiet.sh").exists())
        r = sh("uninstall.sh", "--force", env=self.env)
        self.assertEqual(r.returncode, 0); self.assertFalse((self.cdir / "budget-manager/quiet.sh").exists())
        self.assertTrue(self.settings.exists()); self.assertEqual(json.loads(self.settings.read_text())["model"], "opus")
        self.assertEqual(sh("uninstall.sh", env=self.env).returncode, 0)   # second run: nothing to do


class TestCheckpoints(Base):
    def test_project_checkpoints_created_once_and_never_overwritten(self):
        proj = self.tmp / "proj"; (proj / ".git").mkdir(parents=True)
        sh("install.sh", "--project", str(proj), env=self.env)
        ck = proj / ".claude/checkpoints"
        for f in ("TEMPLATE.md", "README.md", "PROJECT_MEMORY.md", "ACTIVE"):
            self.assertTrue((ck / f).exists(), f)
        self.assertIn(".claude/logs/", (proj / ".gitignore").read_text())
        (ck / "PROJECT_MEMORY.md").write_text("my memory"); (ck / "ACTIVE").write_text("T-1\n")
        (ck / "T-1.md").write_text((ck / "TEMPLATE.md").read_text().replace("<The single next concrete step.>", "run stage 2"))
        sh("install.sh", "--project", str(proj), env=self.env)
        self.assertEqual((ck / "PROJECT_MEMORY.md").read_text(), "my memory")
        self.assertEqual((proj / ".gitignore").read_text().count(".claude/logs/"), 1)
        # recovery: the active task and its next action are recoverable from files alone
        task = (ck / "ACTIVE").read_text().strip()
        nxt = (ck / f"{task}.md").read_text().split("## Next action", 1)[1].strip().splitlines()[0]
        self.assertEqual((task, nxt), ("T-1", "run stage 2"))


class TestQuiet(unittest.TestCase):
    def run_q(self, *cmd):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        p = subprocess.run(SH + [str(ROOT / "scripts/quiet.sh"), "job", "--", *cmd], capture_output=True, text=True,
                           env={**os.environ, "CC_LOG_DIR": str(d)})
        return p.returncode, p.stdout, list(d.glob("*-job.log"))

    def test_success_full_log_short_output(self):
        rc, out, logs = self.run_q(sys.executable, "-c", "for i in range(400): print('row', i)\nprint('12 passed in 0.2s')")
        self.assertEqual(rc, 0); self.assertEqual(len(logs[0].read_text().splitlines()), 401)
        self.assertLessEqual(len(out.splitlines()), 25); self.assertIn("12 passed", out)

    def test_failure_exit_code_and_first_error(self):
        rc, out, _ = self.run_q(sys.executable, "-c", "raise RuntimeError('boom')")
        self.assertEqual(rc, 1); self.assertIn("exit=1", out); self.assertIn("RuntimeError: boom", out)

    def test_usage_error(self):
        p = subprocess.run(SH + [str(ROOT / "scripts/quiet.sh"), "x"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


SECRET = "PRIVATE-PROMPT-TEXT-7f3a"


def transcript(dirpath, sid="s1"):
    a = lambda mid, blocks, think=0: {"type": "assistant", "timestamp": "2026-01-01T10:00:%02dZ" % len(blocks), "requestId": "r" + mid,
                                      "message": {"id": mid, "model": "model-a", "content": blocks,
                                                  "usage": {"input_tokens": 3, "output_tokens": 50, "cache_creation_input_tokens": 200,
                                                            "cache_read_input_tokens": 1000, "output_tokens_details": {"thinking_tokens": think}}}}
    recs = [{"type": "user", "timestamp": "2026-01-01T10:00:00Z", "message": {"content": SECRET}},
            a("m1", [{"type": "thinking", "thinking": SECRET}], 20),                                  # one line per block,
            a("m1", [{"type": "text", "text": SECRET}], 20),                                          # usage repeated
            a("m1", [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": SECRET}}], 20),
            {"type": "user", "timestamp": "2026-01-01T10:00:05Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": SECRET, "is_error": True}]}},
            a("m2", [{"type": "tool_use", "id": "t2", "name": "Read", "input": {}}, {"type": "tool_use", "id": "t3", "name": "Bash", "input": {}}]),
            {"type": "user", "isCompactSummary": True, "timestamp": "2026-01-01T10:30:00Z", "message": {"content": SECRET}}]
    p = Path(dirpath) / "proj-x"; p.mkdir(parents=True, exist_ok=True)
    (p / f"{sid}.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    return p


class TestUsage(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.d); transcript(self.d)

    def test_repeated_blocks_counted_once(self):
        (sid, _, files), = list(usage_report.find_sessions(str(self.d)))
        r = usage_report.analyse(files)
        self.assertEqual(r["assistant_messages"], 2)
        self.assertEqual((r["input_tokens"], r["output_tokens"], r["cache_creation_input_tokens"], r["cache_read_input_tokens"]),
                         (6, 100, 400, 2000))
        self.assertEqual(r["thinking_tokens"], 20); self.assertEqual(dict(r["tools"]), {"Bash": 2, "Read": 1})
        self.assertEqual((r["tool_errors"], r["compactions"], r["duration_min"]), (1, 1, 30.0))

    def test_stage_windows(self):
        (_, _, files), = list(usage_report.find_sessions(str(self.d)))
        self.assertEqual(usage_report.analyse(files, "2026-01-01T10:00:00", "2026-01-01T10:00:01")["assistant_messages"], 1)

    def test_report_never_prints_transcript_content(self):
        for args in ([], ["--json"]):
            p = subprocess.run([sys.executable, str(ROOT / "scripts/usage_report.py"), "--root", str(self.d), *args], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr); self.assertNotIn(SECRET, p.stdout + p.stderr)
            self.assertIn("NOT subscription usage limits", p.stdout)

    def test_unsupported_format_fails_clearly(self):
        bad = self.d / "proj-y"; bad.mkdir()
        (bad / "s2.jsonl").write_text(json.dumps({"type": "assistant", "message": {"id": "x", "model": "m", "content": []}}) + "\n")
        p = subprocess.run([sys.executable, str(ROOT / "scripts/usage_report.py"), "--root", str(self.d)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 3); self.assertIn("usage object", p.stderr)


class TestPackage(unittest.TestCase):
    def test_skill_frontmatter(self):
        for d, must in (("claude-lean", "Never switch models automatically"), ("token-efficient-workflow", "Load the `claude-lean` skill")):
            t = (ROOT / "skills" / d / "SKILL.md").read_text()
            m = re.match(r"---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", t, re.S)
            self.assertTrue(m, d); self.assertEqual(m.group(1), d); self.assertLess(len(m.group(2)), 1024); self.assertIn(must, t)

    def test_no_private_paths_or_identifiers(self):
        pats = [r"/ro" + r"ot/", r"/ho" + r"me/[a-z]", r"\b100\.\d+\.\d+\.\d+\b", r"\.ts" + r"\.net", r"sk-" + r"ant", r"gh" + r"p_",
                r"BEGIN [A-Z ]*PRIV" + r"ATE KEY", r"quant-" + r"research", r"ap" + r"ex", r"@gm" + r"ail"]
        for f in ROOT.rglob("*"):
            if f.is_file() and ".git" not in f.parts and f.suffix not in (".pyc",) and f.name != "LICENSE" and f.name != "CHANGELOG.md":
                t = f.read_text(errors="ignore")
                for p in pats:
                    self.assertIsNone(re.search(p, t, re.I), f"{f.relative_to(ROOT)} matches {p}")


class TestModelPreservation(Base):
    """Claude Lean must never change the user's model or effort selection, or any unrelated setting."""
    OWNED = ("skills/claude-lean/", "skills/token-efficient-workflow/", "budget-manager/", "projects/")

    def setUp(self):
        super().setUp()
        self.settings.write_text(json.dumps({"model": "opus", "effortLevel": "high", "alwaysThinkingEnabled": True,
                                             "env": {"ANTHROPIC_MODEL": "user-choice", "MAX_THINKING_TOKENS": "16000"},
                                             "theme": "dark", "permissions": {"allow": ["Read"]}}, indent=2))
        (self.cdir / "settings.local.json").write_text(json.dumps({"model": "sonnet", "effortLevel": "low"}))
        other = self.cdir / "skills/my-other-skill/SKILL.md"; other.parent.mkdir(parents=True)
        other.write_text("---\nname: my-other-skill\ndescription: unrelated\n---\nbody\n")
        transcript(self.cdir / "projects")

    def snap(self):
        return {str(f.relative_to(self.cdir)): sha(f) for f in self.cdir.rglob("*") if f.is_file()
                and not str(f.relative_to(self.cdir)).startswith(self.OWNED)}

    def test_full_lifecycle_never_touches_model_effort_or_unrelated_files(self):
        before = self.snap()
        env = {**self.env, "ANTHROPIC_MODEL": "must-not-be-written-anywhere"}
        proj = self.tmp / "proj"; proj.mkdir()
        for args in ([], [], ["--project", str(proj)], ["--force"]):
            self.assertIn(sh("install.sh", *args, env=env).returncode, (0,), args)
            self.assertEqual(self.snap(), before, f"install {args} changed a non-toolkit file")
        q = subprocess.run(SH + [str(self.cdir / "budget-manager/quiet.sh"), "t", "--", "true"], capture_output=True, text=True,
                           env={**os.environ, **env, "CC_LOG_DIR": str(self.tmp / "logs")})
        self.assertEqual(q.returncode, 0)
        r = subprocess.run([sys.executable, str(self.cdir / "budget-manager/usage_report.py"), "--json"], capture_output=True,
                           text=True, env={**os.environ, **env})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sh("uninstall.sh", env=env).returncode, 0)
        self.assertEqual(self.snap(), before)
        s = json.loads(self.settings.read_text())
        self.assertEqual((s["model"], s["effortLevel"], s["alwaysThinkingEnabled"], s["env"]["ANTHROPIC_MODEL"]),
                         ("opus", "high", True, "user-choice"))
        self.assertEqual(json.loads((self.cdir / "settings.local.json").read_text())["model"], "sonnet")
        for f in list(self.tmp.rglob("*")):
            if f.is_file() and f.suffix in (".json", ".md", ".sh", ".py") and "projects" not in f.parts:
                self.assertNotIn("must-not-be-written-anywhere", f.read_text(errors="ignore"), str(f))

    def test_scripts_contain_no_model_selection_code(self):
        forbidden = [r"ANTHROPIC_(DEFAULT_[A-Z]+_)?MODEL", r"CLAUDE_CODE_SUBAGENT_MODEL", r"--model\b", r"(^|[\s\"'])/model\b",
                     r"\bclaude\s+(-p|--print)\b", r"effortLevel", r"alwaysThinkingEnabled",
                     r"(>|\bcp\b|\bmv\b|\btee\b|sed -i|write_text|open\([^)]*[\"']w)[^\n]*settings(\.local)?\.json"]
        for f in [p for p in (ROOT / "scripts").iterdir() if p.suffix in (".sh", ".py")]:
            t = f.read_text()
            for pat in forbidden:
                self.assertIsNone(re.search(pat, t, re.M), f"{f.name} matches {pat}")

    def test_skill_and_docs_never_recommend_model_switching(self):
        skill = (ROOT / "skills/claude-lean/SKILL.md").read_text()
        for must in ("Never switch models automatically", "never recommend a model change to reduce token usage",
                     "Never run `/model`", "effort"):
            self.assertIn(must, skill)
        self.assertIsNone(re.search(r"\b(opus|sonnet|haiku)\b", skill, re.I))
        for f in [ROOT / "README.md", *(ROOT / "docs").glob("*.md"), ROOT / "skills/claude-lean/SKILL.md", ROOT / "skills/token-efficient-workflow/SKILL.md"]:
            self.assertIsNone(re.search(r"(switch|change|use)\w* (to )?(a )?(cheaper|smaller|faster) model|switch\w* to (opus|sonnet|haiku)",
                                        f.read_text(), re.I), f.name)


if __name__ == "__main__":
    unittest.main()
