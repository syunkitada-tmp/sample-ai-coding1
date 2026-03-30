"""ドメイン層の独自例外クラス。"""


class CommandParseError(ValueError):
    """コマンド解析上の基底例外。"""


class MultipleCommandsError(CommandParseError):
    """1 メッセージに複数のコマンドが含まれていた場合。"""


class CommandSyntaxError(CommandParseError):
    """コマンドの引数構文が不正な場合（引用符の閉じ忘れなど）。"""


class NoRetryError(Exception):
    """プラグインがリトライなし失敗を要求する場合に送出する例外。

    executor はこの例外を受け取ると retry_count を上限値に設定してから
    mark_failed_no_retry() を呼び出し、リトライキューに戻さない。
    """
