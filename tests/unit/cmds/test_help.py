import os
from pathlib import Path

from cmds.help import main as help_main


def _make_executable(file_path: Path) -> None:
    file_path.write_text("#!/bin/sh\necho ok\n")
    file_path.chmod(0o755)


def test_run_returns_list_of_commands(tmp_path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _make_executable(bin_dir / "chatops-alert")
    _make_executable(bin_dir / "chatops-deploy")
    monkeypatch.setenv("PATH", str(bin_dir))

    exit_code, output = help_main.run([])

    assert exit_code == 0
    assert "!alert:" in output
    assert "!deploy:" in output


def test_run_returns_no_commands_message(tmp_path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", str(bin_dir))

    exit_code, output = help_main.run([])

    assert exit_code == 0
    assert "no commands are available" in output.lower()


def test_main_exits_with_code_zero(monkeypatch, capsys) -> None:
    monkeypatch.setenv("PATH", "")

    try:
        help_main.main()
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "no commands are available" in captured.out.lower()
