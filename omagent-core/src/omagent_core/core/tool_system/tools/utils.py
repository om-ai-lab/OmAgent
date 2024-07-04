import platform


def get_platform() -> str:
    """Get platform."""
    system = platform.system()
    if system == "Darwin":
        return "MacOS"
    return system
