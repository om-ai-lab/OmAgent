# Import core modules and components
from omagent_core.utils.container import container

# Import workflow related modules
from pathlib import Path
from omagent_core.utils.registry import registry

# Set up path and import modules
CURRENT_PATH = root_path = Path(__file__).parents[0]
registry.import_module()

# Register required components
container.register_callback(callback='AppCallback')
container.register_input(input='AppInput')
container.register_stm("SharedMemSTM")
# Compile container config
container.compile_config(CURRENT_PATH)



