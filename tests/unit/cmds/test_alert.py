from cmds.alert import main as alert_main


def test_run_returns_error_when_host_missing() -> None:
    exit_code, output = alert_main.run(["app01"])

    assert exit_code == 1
    assert output == '{"error": "--host is required"}'


def test_run_returns_success_with_host() -> None:
    exit_code, output = alert_main.run(["--host", "web01"])

    assert exit_code == 0
    assert output == '{"result": "Alert for web01"}'


def test_run_includes_additional_args_in_result() -> None:
    exit_code, output = alert_main.run(["--host", "web01", "app01"])

    assert exit_code == 0
    assert output == '{"result": "Alert for web01 app01"}'


def test_main_exits_with_correct_code_and_prints_output(monkeypatch, capsys) -> None:
    with monkeypatch.context() as m:
        m.setattr("sys.argv", ["chatops-alert", "--host", "web01"])
        try:
            alert_main.main()
        except SystemExit as exc:
            assert exc.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == '{"result": "Alert for web01"}'
