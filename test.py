if __name__ == "__main__":
    from omagent_core.utils.container import container
    from omagent_core.utils.registry import registry
    
    registry.import_module()
    
    container.register_handler('RedisStreamHandler')
    
    print(container.compile_config())
    