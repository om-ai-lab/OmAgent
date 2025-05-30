# MCP Tools Docker Setup

This directory contains Docker configurations for all MCP (Model Context Protocol) tools used by the robot agent.

## Services Overview

The setup includes the following services:

1. **VLM Server** (Port 8009): Vision Language Model for image analysis
2. **UT Dog Server** (Port 3000): Real robot control interface
3. **Thor Simulator** (Port 3001): AI2Thor simulation environment
4. **Memory Server** (Port 8080): Mem0-based memory management
5. **Milvus Server** (Port 8000): Vector database interface
6. **Milvus Database** (Port 19530): Vector database backend
7. **Switch Robot** (Port 8010): Orchestration service

## Prerequisites

- Docker and Docker Compose installed
- NVIDIA Docker support (optional, for GPU acceleration)
- At least 8GB RAM
- 50GB+ disk space (for models and data)

## Quick Start

1. **Clone and navigate to the directory:**
   ```bash
   cd robot_agent/mcp_tools
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configurations
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Check service status:**
   ```bash
   docker-compose ps
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f [service-name]
   ```

## Individual Service Control

### Start specific services:
```bash
# Start only the simulator
docker-compose up -d thor-simulator

# Start VLM and memory services
docker-compose up -d vlm-server memory-server

# Start database services
docker-compose up -d milvus etcd minio
```

### Stop services:
```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop vlm-server
```

## Service Details

### VLM Server
- **Purpose**: Vision Language Model for image analysis
- **Port**: 8009
- **GPU**: Optional NVIDIA GPU support
- **Volume**: Caches HuggingFace models

### UT Dog Server
- **Purpose**: Control real Unitree Go2 robot
- **Port**: 3000
- **Network**: Requires access to robot network

### Thor Simulator
- **Purpose**: AI2Thor simulation environment
- **Port**: 3001
- **Display**: Uses Xvfb for headless operation

### Memory Server
- **Purpose**: Mem0-based episodic memory
- **Port**: 8080
- **API Key**: Requires MEM0_API_KEY

### Milvus Services
- **Milvus Server**: MCP interface (Port 8000)
- **Milvus DB**: Vector database (Port 19530)
- **Supporting**: etcd, minio for metadata and storage

## Configuration

### Environment Variables

Edit `.env` file with your configuration:

```bash
# Required for memory service
MEM0_API_KEY=your_mem0_api_key_here

# Optional for Milvus authentication
MILVUS_TOKEN=your_milvus_token

# Robot network configuration
ROBOT_URL=http://172.16.44.211:18080
AUDIO_URL=http://172.16.44.211:8080
NAV_URL=http://localhost:8765
```

### GPU Support

For GPU acceleration with the VLM server, uncomment the GPU configuration in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## Development

### Building individual services:
```bash
# Build VLM server
docker-compose build vlm-server

# Build all services
docker-compose build
```

### Debugging:
```bash
# Run service in interactive mode
docker-compose run --rm vlm-server bash

# Check service logs
docker-compose logs vlm-server
```

## Network Architecture

All services communicate through the `mcp_network` bridge network:

- **Internal communication**: Services use container names as hostnames
- **External access**: Services expose ports to host for external access
- **Dependencies**: Services wait for their dependencies to be ready

## Volumes

- **milvus_data**: Persistent Milvus database storage
- **etcd_data**: Metadata storage for Milvus
- **minio_data**: Object storage for Milvus
- **huggingface_cache**: Cached model files for VLM

## Troubleshooting

### Common Issues:

1. **Out of memory**: Reduce concurrent services or increase Docker memory limit
2. **GPU not found**: Install NVIDIA Docker and enable GPU support
3. **Port conflicts**: Check if ports are already in use
4. **Service fails to start**: Check logs and environment variables

### Health Checks:

```bash
# Check if services are responding
curl http://localhost:8009/health  # VLM server
curl http://localhost:3000/health  # UT Dog server
curl http://localhost:3001/health  # Thor simulator
curl http://localhost:8080/health  # Memory server
curl http://localhost:8000/health  # Milvus server
```

## Production Deployment

For production deployment:

1. Use proper secrets management instead of `.env` files
2. Configure proper backup strategies for volumes
3. Set up monitoring and logging
4. Use Docker Swarm or Kubernetes for orchestration
5. Configure proper firewall rules
6. Use HTTPS with proper certificates

## API Documentation

Each service exposes MCP-compatible APIs. See individual service documentation for specific endpoints and schemas.

## Contributing

When adding new MCP tools:

1. Create a new directory under `mcp_tools/`
2. Add `Dockerfile` and `requirements.txt`
3. Update `docker-compose.yml` with the new service
4. Update this README with service details 