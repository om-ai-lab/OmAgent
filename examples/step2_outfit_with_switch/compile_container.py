from pathlib import Path

from omagent_core.utils.container import container
from omagent_core.utils.registry import registry

# Load all registered workflow components
registry.import_module()

# Configure import path for agent modules
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

# Register core workflow components for state management, callbacks and input handling
container.register_stm("SharedMemSTM")
container.register_callback(callback="AppCallback")
container.register_input(input="AppInput")


# Compile container config
container.compile_config(CURRENT_PATH)
