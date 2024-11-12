## Deploy

我们提供两种部署方式：  
1. 仅包含Conductor的部署，适合基于CLI的开发和测试；  
2. 包含Conductor以及App后端的部署，提供对于智能手机App功能的支持。  

## Docker 和 Docker Compose 安装
首先请确保您的环境已经安装docker以及docker-compose。如果没有，可以参考[docker官方文档](https://docs.docker.com/get-docker/) 和 [docker-compose官方文档](https://docs.docker.com/compose/install/) 进行安装。

## 仅包含Conductor的部署

从当前目录运行：
```bash
docker-compose -f conductor/docker-compose.yml up -d
```
Conductor的基础部署包含一个Redis数据库，一个Elasticsearch数据库，以及Conductor服务共三个镜像。
部署完成后可以通过访问 `http://localhost:5001` 访问Conductor UI。（注：Mac系统默认会占用5000端口，因此我们使用5001端口，你可以在部署Conductor的时候指定其它端口。）
通过 `http://localhost:8080` 调用Conductor API。

## 包含Conductor和App后端的部署

为了支持app的开发和调试我们需要额外部署App后端服务，以及MySQL数据库和minio对象存储服务这两个中间件。

1. 创建数据目录
   从当前目录运行：
   ```bash
   mkdir -p ../pv-data/mysql/data ../pv-data/mysql/log ../pv-data/minio-data
   ```
这会为MySQL数据库和minio对象存储服务创建数据目录。（注：请注意保证目录具有足够的读写权限）

2. 修改配置项
   修改config/om-app-agent/resources/bootstrap-test.yaml中的linker.cos.minio.urlPrefix:后的ip为本机ip（如需公网访问，需要修改为对应公网ip）

3. 启动服务
   从当前目录运行：
   ```bash
    docker-compose -f conductor_with_app/conductor/docker-compose.yaml up -d
    ```