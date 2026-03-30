"""ドメイン層の独自例外クラス。"""


class CommandParseError(ValueError):
    """コマンド解析上の基底例外。"""


class MultipleCommandsError(CommandParseError):
    """1 メッセージに複数のコマンドが含まれていた場合。"""


class CommandSyntaxError(CommandParseError):
    """コマンドの引数構文が不正な場合（引用符の閉じ忘れなど）。"""
