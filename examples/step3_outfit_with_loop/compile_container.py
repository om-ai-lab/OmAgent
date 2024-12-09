# Import core modules and components
from omagent_core.utils.container import container
from omagent_core.utils.registry import registry
from pathlib import Path

# Import all registered modules
registry.import_module()

CURRENT_PATH = Path(__file__).parents[0]


# Register required components
container.register_stm("RedisSTM")
container.register_callback(callback='AppCallback')
container.register_input(input='AppInput')

# Compile container config
container.compile_config(CURRENT_PATH)
