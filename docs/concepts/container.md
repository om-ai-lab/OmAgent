# Container

The Container module is a dependency injection and service container implementation that manages components and their dependencies in the OmAgent core system. It follows the IoC (Inversion of Control) pattern to handle component registration, configuration, and retrieval.

## Key Features
### 1. Component Management
- Registers and manages different types of components (connections, memories, callbacks, etc.)
- Handles component dependencies automatically
- Provides type-safe access to registered components

### 2. Connector Management
Manages service connectors that components might depend on
- Automatically injects required connectors into components

### 3. Special Component Types
- STM (Short-term Memory)
- LTM (Long-term Memory)
- Callback handlers
- Input handlers

### 4. Configuration Management
- Can compile configurations to YAML
- Loads configurations from YAML files
- Supports environment variables and descriptions in configs


## Register
Examples of registering:
```python
from omagent_core.utils.container import container
from omagent_core.services.handlers.redis_stream_handler import RedisStreamHandler

# Register a connector using component name
container.register_connector(RedisConnector, name="redis_client")

# Register a component using component class
container.register_component(RedisStreamHandler)

# Register STM component
container.register_stm("RedisSTM")

# Register LTM component
container.register_ltm("MilvusLTM")

# Register callback and input handlers
container.register_callback("AppCallback")
container.register_input("AppInput")
```

## Configuration Management

1. **Compile Configuration**: Container can automatically generate YAML configuration template files. You can change the values of the parameters in the template files which will take effect when loading the configuration. The ```env_var``` indicates the environment variable names for the parameters, don't change it because it is just for demonstration.
   ```python
   from pathlib import Path
   container.compile_config(Path('./config_dir'))
   ```



2. **Load Configuration**: Load settings from YAML files. This will update the container with the settings in the YAML file.
   ```python
   container.from_config('container.yaml')
   ```

## Component Retrieval

Access registered components:
```python
# Get a connector
redis_client = container.get_connector("redis_client")

# Get STM component
stm = container.stm

# Get LTM component
ltm = container.ltm

# Get callback handler
callback = container.callback

# Get input handler
input_handler = container.input
```


## Best Practices

1. **Early Registration**: Register all components at application startup
2. **Configuration Files**: Use YAML configuration files for better maintainability
3. **Compile Configuration**: Prepare a separated script to compile container configuration before application startup. 
4. **Update Container**: Update the container with the settings in project entry file. Do register default Special Components (STM, LTM, Callback, Input) before update.
5. **Single Instance**: Use the global container instance provided by the framework