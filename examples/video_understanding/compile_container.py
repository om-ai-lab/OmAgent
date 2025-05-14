# Import core modules and components
# Import workflow related modules
from pathlib import Path

from omagent_core.utils.container import container
from omagent_core.utils.registry import registry

# Set up path and import modules
CURRENT_PATH = root_path = Path(__file__).parents[0]
registry.import_module(project_path=CURRENT_PATH.joinpath("agent"))

# Register required components
container.register_callback(callback="DefaultCallback")
container.register_input(input="AppInput")
container.register_stm("SharedMemSTM")
container.register_ltm(ltm="VideoMilvusLTM")
# Compile container config
container.compile_config(CURRENT_PATH)
