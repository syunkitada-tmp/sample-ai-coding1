def test_plugin_loading():
    """Verify chatops-alert and chatops-help are discovered from PATH in a realistic environment."""
    from src.infrastructure.plugin_loader import PluginLoader

    loader = PluginLoader()
    loader.load_from_path()

    assert loader.get("alert") is not None
    assert loader.get("help") is not None
    assert loader.get("alert").command_name == "alert"
    assert loader.get("help").command_name == "help"
