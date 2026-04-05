import pytest


@pytest.fixture
def loader():
    from src.infrastructure.plugin_loader import PluginLoader

    return PluginLoader()


def test_get_unknown_plugin_returns_none(loader):
    assert loader.get("unknown") is None


def test_load_from_path_registers_chatops_commands(loader, tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    alert_file = bin_dir / "chatops-alert"
    help_file = bin_dir / "chatops-help"
    alert_file.write_text("#!/bin/sh\necho OK\n")
    help_file.write_text("#!/bin/sh\necho OK\n")
    alert_file.chmod(0o755)
    help_file.chmod(0o755)

    monkeypatch.setenv("PATH", str(bin_dir))

    loader.load_from_path()

    alert_command = loader.get("alert")
    help_command = loader.get("help")

    assert alert_command is not None
    assert help_command is not None
    assert alert_command.command_name == "alert"
    assert help_command.command_name == "help"
    assert alert_command.executable_path.endswith("chatops-alert")
    assert help_command.executable_path.endswith("chatops-help")
    commands = loader.list_commands()
    assert commands["alert"] == "No description available"
    assert commands["help"] == "No description available"


def test_load_from_path_skips_non_executable_files(loader, tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    non_exec = bin_dir / "chatops-alert"
    non_exec.write_text("echo OK\n")
    non_exec.chmod(0o644)

    monkeypatch.setenv("PATH", str(bin_dir))

    loader.load_from_path()

    assert loader.get("alert") is None


def test_reload_clears_and_reloads_from_path(loader, tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    alert_file = bin_dir / "chatops-alert"
    alert_file.write_text("#!/bin/sh\necho OK\n")
    alert_file.chmod(0o755)

    monkeypatch.setenv("PATH", str(bin_dir))

    loader.load_from_path()
    assert loader.get("alert") is not None

    # PATHを変更してリロード
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setenv("PATH", str(empty_dir))
    loader.reload()

    assert loader.get("alert") is None
