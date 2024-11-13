## Deployment

We offer two deployment options:  
1. Deployment with only Conductor, suited for CLI-based development and testing.  
2. Deployment including both Conductor and the App backend, providing support for smartphone app functionality.  

## Docker and Docker Compose Installation

First, ensure that your environment has Docker and Docker Compose installed. If not, please refer to the [Docker official documentation](https://docs.docker.com/get-docker/) and the [Docker Compose official documentation](https://docs.docker.com/compose/install/) for installation instructions.

## Deployment with Conductor Only

Run from the current directory:
```bash
docker-compose -f conductor/docker-compose.yml up -d
```
The basic deployment of Conductor includes three images: a Redis database, an Elasticsearch database, and the Conductor service. Once deployment is complete, access the Conductor UI at `http://localhost:5001`. (Note: On Mac systems, port 5000 is typically occupied, so we use port 5001; you can specify another port during Conductor deployment.) Access the Conductor API via `http://localhost:8080`.

## Deployment Including Conductor and App Backend

To support app development and debugging, we also need to deploy additional services: the App backend service, a MySQL database, and a MinIO object storage service.

1. Create Data Directories
   Run from the current directory:
   ```bash
   mkdir -p ../pv-data/mysql/data ../pv-data/mysql/log ../pv-data/minio-data
   ```
   This will create data directories for the MySQL database and the MinIO object storage service. (Note: Ensure the directories have adequate read and write permissions.)

2. Modify Configuration Items
   Edit `config/bootstrap.yaml`, changing the `linker.cos.minio.urlPrefix:` IP address to your local IP (or to the corresponding public IP if external access is required).

3. Start Services
   Run from the current directory:
   ```bash
   docker-compose -f conductor_with_app/conductor/docker-compose.yaml up -d
   ```

4. Now you can link the app to backend automatically(if within the same local area network) or by setting the IP address(http://<your_ip>:8082 by default) in the app. Details see [here](../docs/concepts/app.md).