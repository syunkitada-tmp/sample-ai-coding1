import pytest
from src.domain.services.command_parser import parse_command, ParsedCommand


def test_parse_kwargs_and_positional():
    result = parse_command("!alert --host web01 app01")
    assert result.name == "alert"
    assert result.kwargs == {"host": "web01"}
    assert result.args == ["app01"]


def test_parse_kwargs_only():
    result = parse_command("!alert --host web01")
    assert result.kwargs == {"host": "web01"}
    assert result.args == []


def test_parse_positional_only():
    result = parse_command("!alert app01 app02")
    assert result.kwargs == {}
    assert result.args == ["app01", "app02"]


def test_parse_flag_kwarg():
    result = parse_command("!deploy --dry-run")
    assert result.kwargs == {"dry-run": True}
    assert result.args == []


def test_parse_kwarg_equals_syntax():
    result = parse_command("!alert --host=web01")
    assert result.kwargs == {"host": "web01"}
    assert result.args == []


def test_parse_command_no_args():
    result = parse_command("!help")
    assert isinstance(result, ParsedCommand)
    assert result.name == "help"
    assert result.kwargs == {}
    assert result.args == []


def test_parse_no_command_returns_none():
    result = parse_command("Good morning")
    assert result is None


def test_parse_plain_text_with_exclamation_not_at_start():
    result = parse_command("hello! world")
    assert result is None


def test_parse_multiple_commands_raises():
    with pytest.raises(ValueError, match="multiple commands"):
        parse_command("!alert --host web01\n!help")


def test_parse_multiple_commands_on_same_line_raises():
    with pytest.raises(ValueError, match="multiple commands"):
        parse_command("!alert --host web01 !help")


def test_parse_command_name_is_lowercased():
    result = parse_command("!Alert --host web01")
    assert result.name == "alert"


def test_parse_whitespace_only_text_returns_none():
    result = parse_command("   ")
    assert result is None


def test_parse_quoted_kwarg_value():
    """引用符で囲まれたオプション値はシェルと同様に1トークンとして扱われる"""
    result = parse_command('!alert --msg "hello world"')
    assert result.kwargs == {"msg": "hello world"}
    assert result.args == []


def test_parse_escaped_space_in_kwarg():
    """バックスラッシュエスケープによるスペースを含むオプション値"""
    result = parse_command(r"!alert --msg hello\ world")
    assert result.kwargs == {"msg": "hello world"}
    assert result.args == []


def test_parse_single_quoted_kwarg_value():
    """シングルクォートで囲まれたオプション値"""
    result = parse_command("!alert --msg 'foo bar'")
    assert result.kwargs == {"msg": "foo bar"}
    assert result.args == []


def test_parse_mixed_kwargs_and_quoted_positional():
    result = parse_command('!deploy --env prod "my app"')
    assert result.kwargs == {"env": "prod"}
    assert result.args == ["my app"]
