# Import core modules and components
from pathlib import Path

from omagent_core.utils.container import container
from omagent_core.utils.registry import registry

# Import all registered modules
registry.import_module()

CURRENT_PATH = Path(__file__).parents[0]


# Register required components
container.register_stm("SharedMemSTM")
container.register_callback(callback="AppCallback")
container.register_input(input="AppInput")

# Compile container config
container.compile_config(CURRENT_PATH)
