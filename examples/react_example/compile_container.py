from pathlib import Path
from omagent_core.utils.container import container

CURRENT_PATH = Path(__file__).parents[0]

# Load container configuration from YAML file
container.register_stm("RedisSTM")
container.from_config(CURRENT_PATH.joinpath('container.yaml'))

# Compile configuration
container.compile() 