from omagent_core.utils.container import container
from omagent_core.utils.registry import registry
from pathlib import Path

CURRENT_PATH = Path(__file__).parents[0]

registry.import_module()

container.register_stm(stm='RedisSTM')
container.register_ltm(ltm='MilvusLTM')
container.register_callback(callback='AppCallback')
container.register_input(input='AppInput')

# Compile container config
container.compile_config(CURRENT_PATH)