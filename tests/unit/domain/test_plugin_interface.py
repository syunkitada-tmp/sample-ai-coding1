from src.domain.interfaces.plugin import CommandRegistry


def test_command_registry_fields_are_assigned_correctly() -> None:
    registry = CommandRegistry(
        command_name="alert",
        executable_path="/usr/local/bin/chatops-alert",
        description="A command to send alerts.",
    )

    assert registry.command_name == "alert"
    assert registry.executable_path == "/usr/local/bin/chatops-alert"
    assert registry.description == "A command to send alerts."
