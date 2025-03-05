import yaml
from pathlib import Path

def generate_container_files():
    # 读取模板文件
    template_path = Path('examples/sc_cot/container_2.yaml')
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)
    
    # 生成从13到24的配置文件
    for i in range(25, 35):
        # 更新配置
        new_config = template.copy()
        new_config['name'] = f'container_{i}'
        
        # 计算conductor端口和redis端口
        # conductor端口从8080开始，每个加1
        conductor_port = 8080 + (i - 1)  # i=1时是8080, i=13时是8092
        # redis端口从6379开始，每个加1
        redis_port = 6379 + (i - 1)  # i=1时是6379, i=13时是6391
        
        # 更新conductor端口
        new_config['conductor_config']['base_url']['value'] = f'http://140.207.201.47:{conductor_port}'
        
        # 更新redis端口
        new_config['connectors']['redis_stream_client']['port']['value'] = redis_port
        new_config['connectors']['redis_stm_client']['port']['value'] = redis_port
        
        # 生成新的配置文件
        output_path = template_path.parent / f'container_{i}.yaml'
        with open(output_path, 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False)
        
        print(f'Generated {output_path} with conductor port {conductor_port} and redis port {redis_port}')

if __name__ == '__main__':
    generate_container_files() 