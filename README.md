# Zephyr Scale MCP Server

A comprehensive Model Context Protocol (MCP) server for SmartBear Zephyr Scale test management platform. This server provides seamless integration with Zephyr Scale's REST API, enabling automated test management workflows through Claude and other MCP-compatible tools.

## Table of Contents

- [Features](#features)
- [Code Structure](#code-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Setup with Claude Desktop](#setup-with-claude-desktop)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Complete API Coverage**: All major Zephyr Scale endpoints
- **Region Support**: Global and EU region APIs
- **Comprehensive Error Handling**: Detailed error messages and status codes
- **Type Safety**: Proper type hints and enums
- **Pagination Support**: Handle large datasets efficiently
- **Flexible Authentication**: JWT token-based authentication
- **Logging**: Comprehensive logging for debugging

## Code Structure

```
zephyr-scale-mcp/
├── .venv/                    # UV virtual environment
├── zephyr_mcp_server.py      # Main MCP server implementation
├── .env                      # Environment variables (create this)
├── pyproject.toml           # UV project configuration
├── uv.lock                  # UV lock file
├── .gitignore               # Git ignore file
└── README.md                # This file
```

### Core Components

```python
# Main server initialization
mcp = FastMCP("zephyr-scale")

# HTTP client with error handling
async def make_zephyr_request(method, url, data=None, params=None)

# Tool categories:
# - Test Cases (13 tools)
# - Folders (3 tools) 
# - Test Cycles (4 tools)
# - Test Executions (4 tools)
# - Projects (2 tools)
# - Priorities (4 tools)
# - Statuses (4 tools)
# - Environments (4 tools)
# - Links (1 tool)
# - Issue Links (4 tools)
# - Utilities (2 tools)
```

## Prerequisites

- Python 3.8+
- Zephyr Scale account with API access
- Jira instance connected to Zephyr Scale
- Valid Zephyr Scale API token

## Installation

1. **Initialize UV project**
   ```bash
   # Create project directory
   mkdir zephyr-scale-mcp
   cd zephyr-scale-mcp
   
   # Initialize uv project
   uv init
   
   # Save the zephyr_mcp_server.py file in this directory
   ```

2. **Install dependencies with UV**
   ```bash
   uv add fastmcp python-dotenv httpx
   ```

3. **Your pyproject.toml should look like**
   ```toml
   [project]
   name = "zephyr-scale-mcp"
   version = "0.1.0"
   description = "Zephyr Scale MCP Server"
   dependencies = [
       "fastmcp>=0.1.0",
       "dotenv>=1.0.0",
       "httpx>=0.25.0",
   ]
   requires-python = ">=3.8"
   ```

## Configuration

1. **Generate Zephyr Scale API Token**
   - Log into your Jira instance
   - Click on your profile picture (bottom left)
   - Select "Zephyr API keys"
   - Generate a new API key
   - Copy the token for configuration

2. **Create Environment File**
   Create a `.env` file in the project directory:
   ```env
   # Required: Your Zephyr Scale API token
   ZEPHYR_API_TOKEN=your_jwt_token_here
   
   # Optional: Set to true for EU region (default: false)
   ZEPHYR_USE_EU_REGION=false
   ```

3. **Test Configuration**
   ```bash
   uv run python zephyr_mcp_server.py
   ```

## Setup with Claude Desktop

1. **Locate Claude Desktop Config**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add MCP Server Configuration**
   ```json
   {
     "mcpServers": {
       "zephyr-scale": {
         "command": "uv",
         "args": ["run", "python", "app.py"],
         "cwd": "/path/to/your/zephyr-scale-mcp",
         "env": {
           "ZEPHYR_API_TOKEN": "your_jwt_token_here",
           "ZEPHYR_USE_EU_REGION": "false"
         }
       }
     }
   }
   ```

3. **Alternative: Using .env file (Recommended)**
   ```json
   {
     "mcpServers": {
       "zephyr-scale": {
         "command": "uv",
         "args": ["run", "python", "zephyr_mcp_server.py"],
         "cwd": "/path/to/your/zephyr-scale-mcp"
       }
     }
   }
   ```

4. **Restart Claude Desktop**
   - Close Claude Desktop completely
   - Restart the application
   - The Zephyr Scale tools should now be available

## Available Tools

### 📝 Test Cases (13 tools)
- `get_test_cases` - List test cases with filtering
- `get_test_case` - Get specific test case details
- `create_test_case` - Create new test case
- `update_test_case` - Update existing test case
- `get_test_case_links` - Get all links for a test case
- `create_test_case_issue_link` - Link test case to Jira issue
- `create_test_case_web_link` - Create web link for test case
- `get_test_case_versions` - Get all versions of test case
- `get_test_case_version` - Get specific version
- `get_test_case_script` - Get test script content
- `create_test_case_script` - Create/update test script
- `get_test_case_steps` - Get test steps
- `create_test_case_steps` - Create test steps

### 📁 Folders (3 tools)
- `get_folders` - List folders with filtering
- `get_folder` - Get specific folder details
- `create_folder` - Create new folder

### 🔄 Test Cycles (4 tools)
- `get_test_cycles` - List test cycles
- `get_test_cycle` - Get specific test cycle
- `create_test_cycle` - Create new test cycle
- `update_test_cycle` - Update existing test cycle

### ▶️ Test Executions (4 tools)
- `get_test_executions` - List test executions
- `get_test_execution` - Get specific execution
- `create_test_execution` - Create new execution
- `update_test_execution` - Update execution results

### 🏗️ Projects (2 tools)
- `get_projects` - List all projects
- `get_project` - Get specific project details

### 🔺 Priorities (4 tools)
- `get_priorities` - List priorities
- `get_priority` - Get specific priority
- `create_priority` - Create new priority
- `update_priority` - Update existing priority

### 📊 Statuses (4 tools)
- `get_statuses` - List statuses
- `get_status` - Get specific status
- `create_status` - Create new status
- `update_status` - Update existing status

### 🌍 Environments (4 tools)
- `get_environments` - List environments
- `get_environment` - Get specific environment
- `create_environment` - Create new environment
- `update_environment` - Update existing environment

### 🔗 Links (1 tool)
- `delete_link` - Delete any link by ID

### 🎯 Issue Links (4 tools)
- `get_issue_link_test_cases` - Get test cases linked to Jira issue
- `get_issue_link_test_cycles` - Get test cycles linked to Jira issue
- `get_issue_link_test_plans` - Get test plans linked to Jira issue
- `get_issue_link_test_executions` - Get executions linked to Jira issue

### 🛠️ Utilities (2 tools)
- `health_check` - Check API health
- `get_api_info` - Get server configuration info

## Usage Examples

### 1. Create a Test Case
```
Create a test case named "User Login Validation" for project "DEMO" with high priority and objective "Validate user authentication flow"
```

### 2. Organize Tests with Folders
```
Create a folder structure for organizing regression tests in project "DEMO"
```

### 3. Execute Test Cycles
```
Create a test cycle for Sprint 1 testing in project "DEMO" and show me all test executions
```

### 4. Link Tests to Issues
```
Link test case DEMO-T123 to Jira issue DEMO-456
```

### 5. Manage Test Environments
```
Create testing environments for Chrome, Firefox, and Safari browsers in project "DEMO"
```

### 6. Generate Test Reports
```
Get all test executions for project "DEMO" from the last 7 days and summarize the results
```

### 7. Bulk Operations
```
Get all test cases in folder ID 100 and update their priority to "High"
```

### 8. Integration Workflows
```
For each failed test execution, create a Jira issue and link it to the test case
```

## Error Handling

The server includes comprehensive error handling:

- **HTTP Errors**: Detailed status codes and messages
- **Authentication Errors**: Clear token validation feedback
- **Validation Errors**: Parameter validation with helpful messages
- **Network Errors**: Timeout and connection error handling
- **JSON Parsing**: Graceful handling of malformed responses

Example error response:
```json
{
  "error": "HTTP 401: Unauthorized - Invalid API token",
  "status_code": 401
}
```

## Troubleshooting

### Common Issues

1. **"API token not set" error**
   - Ensure `ZEPHYR_API_TOKEN` is set in `.env` file
   - Verify token is valid and not expired

2. **"Connection timeout" errors**
   - Check network connectivity
   - Verify API base URL (Global vs EU region)

3. **"Project not found" errors**
   - Ensure project key exists and is accessible
   - Check user permissions in Jira/Zephyr Scale

4. **Tools not appearing in Claude**
   - Verify `claude_desktop_config.json` syntax
   - Check file paths are absolute
   - Restart Claude Desktop after config changes

### Debug Mode

Enable debug logging by modifying the server:
```python
logging.basicConfig(level=logging.DEBUG)
```

## API Rate Limits

Zephyr Scale has rate limits. The server handles these gracefully:
- Automatic retry for rate limit errors
- Exponential backoff strategy
- Clear error messages when limits are exceeded

## Security Considerations

- Store API tokens securely in environment variables
- Use `.env` files for local development only
- Consider using secrets management for production
- Regularly rotate API tokens
- Monitor API usage and access logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues related to:
- **This MCP Server**: Create an issue in this repository
- **Zephyr Scale API**: Contact SmartBear support
- **Claude Desktop**: Contact Anthropic support

## Changelog

### v1.0.0
- Initial release with complete API coverage
- Support for all major Zephyr Scale endpoints
- Comprehensive error handling
- Region support (Global/EU)
- Claude Desktop integration