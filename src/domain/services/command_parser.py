from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field


@dataclass
class ParsedCommand:
    name: str
    kwargs: dict[str, str | bool] = field(default_factory=dict)
    args: list[str] = field(default_factory=list)


def _parse_tokens(tokens: list[str]) -> tuple[dict[str, str | bool], list[str]]:
    """shlex 分割済みトークン列を kwargs と位置引数に分類する。

    対応形式:
      --key value   -> kwargs["key"] = "value"
      --key=value   -> kwargs["key"] = "value"
      --flag        -> kwargs["flag"] = True  (次トークンがオプションでない場合)
      positional    -> args[]
    """
    kwargs: dict[str, str | bool] = {}
    args: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--"):
            key_part = token[2:]
            if "=" in key_part:
                # --key=value 形式
                key, _, value = key_part.partition("=")
                kwargs[key] = value
                i += 1
            elif i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                # --key value 形式
                kwargs[key_part] = tokens[i + 1]
                i += 2
            else:
                # --flag 形式
                kwargs[key_part] = True
                i += 1
        else:
            args.append(token)
            i += 1
    return kwargs, args


def parse_command(text: str) -> ParsedCommand | None:
    """テキストから !コマンド名 [--key val...] [arg...] をシェル互換形式で解析する。

    shlex.split で引用符・エスケープを処理した後、
    kwargs (--key value / --flag) と位置引数 (args) に分類する。

    Returns:
        ParsedCommand: コマンドが1つ見つかった場合
        None: コマンドが含まれない場合

    Raises:
        ValueError: コマンドが複数含まれる場合
    """
    if not text or not text.strip():
        return None

    command_pattern = re.compile(r"(?:^|(?<=\s))!([A-Za-z]\w*)")
    matches = command_pattern.findall(text)

    if len(matches) == 0:
        return None
    if len(matches) > 1:
        raise ValueError(f"multiple commands detected: {matches}")

    full_match = command_pattern.search(text)
    command_name = matches[0].lower()
    rest = text[full_match.end() :].strip()

    try:
        tokens = shlex.split(rest)
    except ValueError as exc:
        raise ValueError(f"failed to parse command arguments: {exc}") from exc

    kwargs, args = _parse_tokens(tokens)
    return ParsedCommand(name=command_name, kwargs=kwargs, args=args)
