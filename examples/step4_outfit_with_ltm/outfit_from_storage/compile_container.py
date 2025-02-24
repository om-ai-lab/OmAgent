from pathlib import Path

from omagent_core.utils.container import container
from omagent_core.utils.registry import registry

CURRENT_PATH = Path(__file__).parents[0]

# Import all registered modules
registry.import_module()

# Register components
container.register_stm("SharedMemSTM")
container.register_ltm("MilvusLTM")
container.register_callback(callback="AppCallback")
container.register_input(input="AppInput")

# Compile and save container configuration to current directory
container.compile_config(CURRENT_PATH)
