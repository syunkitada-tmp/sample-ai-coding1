from cmds.lib import utils


def test_parse_kwargs_parses_key_value_pairs() -> None:
    argv = ["--host", "web01", "--level", "critical"]

    kwargs, args = utils.parse_kwargs(argv)

    assert kwargs == {"host": "web01", "level": "critical"}
    assert args == ""


def test_parse_kwargs_parses_flags_and_args() -> None:
    argv = ["--force", "--host", "web01", "deploy", "now"]

    kwargs, args = utils.parse_kwargs(argv)

    assert kwargs == {"force": True, "host": "web01"}
    assert args == "deploy now"


def test_parse_args_returns_payload_dict() -> None:
    argv = ["--host", "web01", "deploy", "now"]

    result = utils.parse_args(argv)

    assert result == {
        "kwargs": {"host": "web01"},
        "args": "deploy now",
    }


def test_output_json_serializes_dict() -> None:
    data = {"result": "ok", "count": 1}

    assert utils.output_json(data) == '{"result": "ok", "count": 1}'


def test_output_text_returns_text() -> None:
    assert utils.output_text("hello world") == "hello world"


def test_exit_code_returns_zero_for_success() -> None:
    assert utils.exit_code(True) == 0


def test_exit_code_returns_one_for_failure() -> None:
    assert utils.exit_code(False) == 1
