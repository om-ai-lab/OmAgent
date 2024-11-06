if __name__ == "__main__":
    # from omagent_core.utils.container import container
    # from omagent_core.utils.registry import registry
    # from omagent_core.services.handlers.redis_stream_handler import RedisStreamHandler
    # from omagent_core.base import BotBase
    
    # registry.import_module()
    
    # # container.register_component(component='RedisStreamHandler')
    # # container.register_component(component=RedisStreamHandler)
    
    # # container_config = container.compile_config()
    # # print(container_config)
    # # container_config['connectors']['conductor_config']['base_url']['value'] = 'test'
    # # print(111, container_config)
    # # container.update_from_config(container_config)
    # # print(container._connectors['conductor_config'].base_url)
    
    # container.register_stm(stm='RedisSTM')
    
    # class Test(BotBase):
    #     a: int = 1
    
    # t = Test()
    
    # print(t.stm)
    
    from omagent_core.utils.build import build_from_file
    
    res = build_from_file('examples/naive_test/configs')
    print(res)
