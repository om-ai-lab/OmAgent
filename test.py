if __name__ == "__main__":
    # from omagent_core.utils.container import container
    # from omagent_core.utils.registry import registry
    # from omagent_core.services.handlers.redis_stream_handler import RedisStreamHandler
    
    # registry.import_module()
    
    # # container.register_component(component='RedisStreamHandler')
    # container.register_component(component=RedisStreamHandler)
    
    # container_config = container.compile_config()
    # print(container_config)
    # container_config['connectors']['conductor_config']['base_url']['value'] = 'test'
    # print(111, container_config)
    # container.update_from_config(container_config)
    # print(container._connectors['conductor_config'].base_url)
    
    
    from omagent_core.engine.configuration.configuration import Configuration
    c = {'base_url': 'test', 'auth_key': None, 'auth_secret': None, 'auth_token_ttl_min': 45, 'debug': False}
    config = Configuration(**c)
    print(config.base_url)
