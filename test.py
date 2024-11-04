if __name__ == "__main__":
    from omagent_core.utils.container import container
    from omagent_core.utils.registry import registry
    from omagent_core.services.handlers.redis_stream_handler import RedisStreamHandler
    
    registry.import_module()
    
    # container.register_component(component='RedisStreamHandler', component_category='handler')
    container.register_component(component=RedisStreamHandler)
    
    print(container.compile_config())
    