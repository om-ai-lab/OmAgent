# MCP Server for Milvus

> The Model Context Protocol (MCP) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you're building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

This repository contains a MCP server that provides access to [Milvus](https://milvus.io/) vector database functionality.

![MCP with Milvus](Claude_mcp+1080.gif)

## Prerequisites

Before using this MCP server, ensure you have:

- Python 3.10 or higher
- A running [Milvus](https://milvus.io/) instance (local or remote)
- [uv](https://github.com/astral-sh/uv) installed (recommended for running the server)

## Usage

The recommended way to use this MCP server is to run it directly with `uv` without installation. This is how both Claude Desktop and Cursor are configured to use it in the examples below.

If you want to clone the repository:

```bash
git clone https://github.com/zilliztech/mcp-server-milvus.git
cd mcp-server-milvus
```

Then you can run the server directly:

```bash
uv run src/mcp_server_milvus/server.py --milvus-uri http://localhost:19530
```

Alternatively you can change the .env file in the `src/mcp_server_milvus/` directory to set the environment variables and run the server with the following command:

```bash
uv run src/mcp_server_milvus/server.py
```

### Important: the .env file will have higher priority than the command line arguments.

### Running Modes

The server supports two running modes: **stdio** (default) and **SSE** (Server-Sent Events).

### Stdio Mode (Default)

- **Description**: Communicates with the client via standard input/output. This is the default mode if no mode is specified.

- Usage:

  ```bash
  uv run src/mcp_server_milvus/server.py --milvus-uri http://localhost:19530
  ```

### SSE Mode

- **Description**: Uses HTTP Server-Sent Events for communication. This mode allows multiple clients to connect via HTTP and is suitable for web-based applications.

- **Usage:**

  ```bash
  uv run src/mcp_server_milvus/server.py --sse --milvus-uri http://localhost:19530 --port 8000
  ```

  - `--sse`: Enables SSE mode.
  - `--port`: Specifies the port for the SSE server (default: 8000).

- **Debugging in SSE Mode:**

  If you want to debug in SSE mode, after starting the SSE service, enter the following command:

  ```bash
  mcp dev src/mcp_server_milvus/server.py
  ```

  The output will be similar to:

  ```plaintext
  % mcp dev src/mcp_server_milvus/merged_server.py
  Starting MCP inspector...
  ⚙️ Proxy server listening on port 6277
  🔍 MCP Inspector is up and running at http://127.0.0.1:6274 🚀
  ```

  You can then access the MCP Inspector at `http://127.0.0.1:6274` for testing.

## Supported Applications

This MCP server can be used with various LLM applications that support the Model Context Protocol:

- **Claude Desktop**: Anthropic's desktop application for Claude
- **Cursor**: AI-powered code editor with MCP support
- **Custom MCP clients**: Any application implementing the MCP client specification

## Usage with Claude Desktop

### Configuration for Different Modes

#### SSE Mode Configuration

Follow these steps to configure Claude Desktop for SSE mode:

1. Install Claude Desktop from https://claude.ai/download.
2. Open your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Add the following configuration for SSE mode:

```json
{
  "mcpServers": {
    "milvus-sse": {
      "url": "http://your_sse_host:port/sse",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

4. Restart Claude Desktop to apply the changes.

#### Stdio Mode Configuration

For stdio mode, follow these steps:

1. Install Claude Desktop from https://claude.ai/download.
2. Open your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Add the following configuration for stdio mode:

```json
{
  "mcpServers": {
    "milvus": {
      "command": "/PATH/TO/uv",
      "args": [
        "--directory",
        "/path/to/mcp-server-milvus/src/mcp_server_milvus",
        "run",
        "server.py",
        "--milvus-uri",
        "http://localhost:19530"
      ]
    }
  }
}
```

4. Restart Claude Desktop to apply the changes.

## Usage with Cursor

[Cursor also supports MCP](https://docs.cursor.com/context/model-context-protocol) tools. You can integrate your Milvus MCP server with Cursor by following these steps:

### Integration Steps

1. Open `Cursor Settings` > `MCP`
2. Click on `Add new global MCP server`
3. After clicking, it will automatically redirect you to the `mcp.json` file, which will be created if it doesn’t exist

### Configuring the `mcp.json` File

#### For Stdio Mode:

Overwrite the `mcp.json` file with the following content:

```json
{
  "mcpServers": {
    "milvus": {
      "command": "/PATH/TO/uv",
      "args": [
        "--directory",
        "/path/to/mcp-server-milvus/src/mcp_server_milvus",
        "run",
        "server.py",
        "--milvus-uri",
        "http://127.0.0.1:19530"
      ]
    }
  }
}
```

#### For SSE Mode:

1. Start the service by running the following command:

   ```bash
   uv run src/mcp_server_milvus/server.py --sse --milvus-uri http://your_sse_host --port port
   ```

   > **Note**: Replace `http://your_sse_host` with your actual SSE host address and `port` with the specific port number you’re using.

2. Once the service is up and running, overwrite the `mcp.json` file with the following content:

   ```json
   {
       "mcpServers": {
         "milvus-sse": {
           "url": "http://your_sse_host:port/sse",
           "disabled": false,
           "autoApprove": []
         }
       }
   }
   ```

### Completing the Integration

After completing the above steps, restart Cursor or reload the window to ensure the configuration takes effect.

## Verifying the Integration

To verify that Cursor has successfully integrated with your Milvus MCP server:

1. Open `Cursor Settings` > `MCP`
2. Check if "milvus" or "milvus-sse" appear in the list（depending on the mode you have chosen）
3. Confirm that the relevant tools are listed (e.g., milvus_list_collections, milvus_vector_search, etc.)
4. If the server is enabled but shows an error, check the Troubleshooting section below

## Available Tools

The server provides the following tools:

### Search and Query Operations

- `milvus_text_search`: Search for documents using full text search

  - Parameters:
    - `collection_name`: Name of collection to search
    - `query_text`: Text to search for
    - `limit`: The maximum number of results to return (default: 5)
    - `output_fields`: Fields to include in results
    - `drop_ratio`: Proportion of low-frequency terms to ignore (0.0-1.0)
- `milvus_vector_search`: Perform vector similarity search on a collection
  - Parameters:
    - `collection_name`: Name of collection to search
    - `vector`: Query vector
    - `vector_field`: Field name for vector search (default: "vector")
    - `limit`: The maximum number of results to return (default: 5)
    - `output_fields`: Fields to include in results
    - `filter_expr`: Filter expression
    - `metric_type`: Distance metric (COSINE, L2, IP) (default: "COSINE")
- `milvus_hybrid_search`: Perform hybrid search on a collection
  - Parameters:
    - `collection_name`: Name of collection to search
    - `query_text`: Text query for search
    - `text_field`: Field name for text search
    - `vector`: Vector of the text query
    - `vector_field`: Field name for vector search
    - `limit`: The maximum number of results to return
    - `output_fields`: Fields to include in results
    - `filter_expr`: Filter expression
- `milvus_query`: Query collection using filter expressions
  - Parameters:
    - `collection_name`: Name of collection to query
    - `filter_expr`: Filter expression (e.g. 'age > 20')
    - `output_fields`: Fields to include in results
    - `limit`: The maximum number of results to return (default: 10)

### Collection Management

- `milvus_list_collections`: List all collections in the database

- `milvus_create_collection`: Create a new collection with specified schema

  - Parameters:
    - `collection_name`: Name for the new collection
    - `collection_schema`: Collection schema definition
    - `index_params`: Optional index parameters

- `milvus_load_collection`: Load a collection into memory for search and query

  - Parameters:
    - `collection_name`: Name of collection to load
    - `replica_number`: Number of replicas (default: 1)

- `milvus_release_collection`: Release a collection from memory
  - Parameters:
    - `collection_name`: Name of collection to release

- `milvus_get_collection_info`: Lists detailed information like schema, properties, collection ID, and other metadata of a specific collection.
  - Parameters:
    - `collection_name`:  Name of the collection to get detailed information about

### Data Operations

- `milvus_insert_data`: Insert data into a collection

  - Parameters:
    - `collection_name`: Name of collection
    - `data`: Dictionary mapping field names to lists of values

- `milvus_delete_entities`: Delete entities from a collection based on filter expression
  - Parameters:
    - `collection_name`: Name of collection
    - `filter_expr`: Filter expression to select entities to delete

## Environment Variables

- `MILVUS_URI`: Milvus server URI (can be set instead of --milvus-uri)
- `MILVUS_TOKEN`: Optional authentication token
- `MILVUS_DB`: Database name (defaults to "default")

## Development

To run the server directly:

```bash
uv run server.py --milvus-uri http://localhost:19530
```

## Examples

### Using Claude Desktop

#### Example 1: Listing Collections

```
What are the collections I have in my Milvus DB?
```

Claude will then use MCP to check this information on your Milvus DB.

```
I'll check what collections are available in your Milvus database.

Here are the collections in your Milvus database:

1. rag_demo
2. test
3. chat_messages
4. text_collection
5. image_collection
6. customized_setup
7. streaming_rag_demo
```

#### Example 2: Searching for Documents

```
Find documents in my text_collection that mention "machine learning"
```

Claude will use the full-text search capabilities of Milvus to find relevant documents:

```
I'll search for documents about machine learning in your text_collection.

> View result from milvus-text-search from milvus (local)

Here are the documents I found that mention machine learning:
[Results will appear here based on your actual data]
```

### Using Cursor

#### Example: Creating a Collection

In Cursor, you can ask:

```
Create a new collection called 'articles' in Milvus with fields for title (string), content (string), and a vector field (128 dimensions)
```

Cursor will use the MCP server to execute this operation:

```
I'll create a new collection called 'articles' with the specified fields.

Collection 'articles' has been created successfully with the following schema:
- title: string
- content: string
- vector: float vector[128]
```

## Troubleshooting

### Common Issues

#### Connection Errors

If you see errors like "Failed to connect to Milvus server":

1. Verify your Milvus instance is running: `docker ps` (if using Docker)
2. Check the URI is correct in your configuration
3. Ensure there are no firewall rules blocking the connection
4. Try using `127.0.0.1` instead of `localhost` in the URI

#### Authentication Issues

If you see authentication errors:

1. Verify your `MILVUS_TOKEN` is correct
2. Check if your Milvus instance requires authentication
3. Ensure you have the correct permissions for the operations you're trying to perform

#### Tool Not Found

If the MCP tools don't appear in Claude Desktop or Cursor:

1. Restart the application
2. Check the server logs for any errors
3. Verify the MCP server is running correctly
4. Press the refresh button in the MCP settings (for Cursor)

### Getting Help

If you continue to experience issues:

1. Check the [GitHub Issues](https://github.com/zilliztech/mcp-server-milvus/issues) for similar problems
2. Join the [Zilliz Community Discord](https://discord.gg/zilliz) for support
3. File a new issue with detailed information about your problem
