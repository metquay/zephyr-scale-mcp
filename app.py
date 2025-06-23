from typing import Any, Dict, Optional, List
import json
import os
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP
import logging
from enum import Enum

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("zephyr-scale")

# Configuration
ZEPHYR_API_BASE = "https://api.zephyrscale.smartbear.com/v2"
EU_ZEPHYR_API_BASE = "https://eu.api.zephyrscale.smartbear.com/v2"
API_TOKEN = os.getenv("ZEPHYR_API_TOKEN")
USE_EU_REGION = os.getenv("ZEPHYR_USE_EU_REGION", "false").lower() == "true"

if not API_TOKEN:
    raise ValueError("ZEPHYR_API_TOKEN environment variable is not set")

# Use EU region if specified
API_BASE = EU_ZEPHYR_API_BASE if USE_EU_REGION else ZEPHYR_API_BASE

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FolderType(str, Enum):
    TEST_CASE = "TEST_CASE"
    TEST_PLAN = "TEST_PLAN"
    TEST_CYCLE = "TEST_CYCLE"

class StatusType(str, Enum):
    TEST_CASE = "TEST_CASE"
    TEST_PLAN = "TEST_PLAN"
    TEST_CYCLE = "TEST_CYCLE"
    TEST_EXECUTION = "TEST_EXECUTION"

async def make_zephyr_request(
    method: str,
    url: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a request to the Zephyr Scale API with proper error handling."""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, params=params, timeout=30.0)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data, params=params, timeout=30.0)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, params=params, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses for DELETE operations
            if response.status_code == 204 or not response.content:
                return {"success": True}
            
            return response.json()
            
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"API error: {error_msg}")
        return {"error": error_msg, "status_code": e.response.status_code}
    except Exception as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

# =============================================================================
# TEST CASES ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_test_cases(
    project_key: str,
    folder_id: Optional[int] = None,
    max_results: int = 25,
    start_at: int = 0
) -> str:
    """Get test cases from Zephyr Scale.
    
    Args:
        project_key: Project key (e.g. 'SM')
        folder_id: Optional folder ID to filter test cases
        max_results: Maximum number of test cases to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "projectKey": project_key,
        "maxResults": min(max_results, 1000),
        "startAt": start_at
    }
    
    if folder_id:
        params["folderId"] = folder_id
    
    url = f"{API_BASE}/testcases"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    test_cases = data.get("values", [])
    
    if not test_cases:
        return "No test cases found."
    
    result = []
    for tc in test_cases:
        result.append({
            "id": tc.get("id"),
            "key": tc.get("key"),
            "name": tc.get("name"),
            "priority": tc.get("priority", {}).get("id"),
            "status": tc.get("status", {}).get("id"),
            "objective": tc.get("objective"),
            "precondition": tc.get("precondition"),
            "estimatedTime": tc.get("estimatedTime"),
            "createdOn": tc.get("createdOn"),
            "folder": tc.get("folder", {}).get("id") if tc.get("folder") else None,
            "owner": tc.get("owner", {}).get("accountId") if tc.get("owner") else None
        })
    
    return json.dumps({
        "testCases": result,
        "pagination": {
            "startAt": data.get("startAt"),
            "maxResults": data.get("maxResults"),
            "total": data.get("total"),
            "isLast": data.get("isLast")
        }
    }, indent=2)

@mcp.tool()
async def get_test_case(test_case_key: str) -> str:
    """Get a specific test case by key.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
    """
    url = f"{API_BASE}/testcases/{test_case_key}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_test_case(
    project_key: str,
    name: str,
    objective: Optional[str] = None,
    precondition: Optional[str] = None,
    priority_name: Optional[str] = None,
    status_name: Optional[str] = None,
    folder_id: Optional[int] = None,
    owner_id: Optional[str] = None,
    estimated_time: Optional[int] = None,
    component_id: Optional[int] = None,
    labels: Optional[List[str]] = None
) -> str:
    """Create a new test case.
    
    Args:
        project_key: Project key (e.g. 'SM')
        name: Test case name
        objective: Test case objective/description
        precondition: Any preconditions
        priority_name: Priority name (e.g. 'High', 'Normal')
        status_name: Status name (e.g. 'Draft', 'Approved')
        folder_id: ID of folder to place test case in
        owner_id: Jira user account ID
        estimated_time: Estimated duration in milliseconds
        component_id: Jira component ID
        labels: List of labels
    """
    payload = {
        "projectKey": project_key,
        "name": name
    }
    
    if objective:
        payload["objective"] = objective
    if precondition:
        payload["precondition"] = precondition
    if priority_name:
        payload["priorityName"] = priority_name
    if status_name:
        payload["statusName"] = status_name
    if folder_id:
        payload["folderId"] = folder_id
    if owner_id:
        payload["ownerId"] = owner_id
    if estimated_time:
        payload["estimatedTime"] = estimated_time
    if component_id:
        payload["componentId"] = component_id
    if labels:
        payload["labels"] = labels
    
    url = f"{API_BASE}/testcases"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def update_test_case(test_case_key: str, test_case_data: str) -> str:
    """Update an existing test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        test_case_data: JSON string containing the test case data to update
    """
    try:
        payload = json.loads(test_case_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for test_case_data"
    
    url = f"{API_BASE}/testcases/{test_case_key}"
    data = await make_zephyr_request("PUT", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Test case updated successfully"

@mcp.tool()
async def get_test_case_links(test_case_key: str) -> str:
    """Get all links for a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
    """
    url = f"{API_BASE}/testcases/{test_case_key}/links"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_test_case_issue_link(test_case_key: str, issue_id: int) -> str:
    """Create a link between a test case and a Jira issue.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        issue_id: The Jira issue ID
    """
    payload = {"issueId": issue_id}
    url = f"{API_BASE}/testcases/{test_case_key}/links/issues"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_test_case_web_link(test_case_key: str, url_link: str, description: Optional[str] = None) -> str:
    """Create a web link for a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        url_link: The URL to link to
        description: Optional description for the link
    """
    payload = {"url": url_link}
    if description:
        payload["description"] = description
    
    url = f"{API_BASE}/testcases/{test_case_key}/links/weblinks"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_test_case_versions(test_case_key: str, max_results: int = 10, start_at: int = 0) -> str:
    """Get all versions of a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        max_results: Maximum number of versions to return (default: 10)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": max_results,
        "startAt": start_at
    }
    
    url = f"{API_BASE}/testcases/{test_case_key}/versions"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_test_case_version(test_case_key: str, version: int) -> str:
    """Get a specific version of a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        version: Version number to retrieve
    """
    url = f"{API_BASE}/testcases/{test_case_key}/versions/{version}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_test_case_script(test_case_key: str) -> str:
    """Get the test script for a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
    """
    url = f"{API_BASE}/testcases/{test_case_key}/testscript"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_test_case_script(test_case_key: str, script_type: str, text: str) -> str:
    """Create or update a test script for a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        script_type: Type of script ('plain' or 'bdd')
        text: The script content
    """
    payload = {
        "type": script_type,
        "text": text
    }
    
    url = f"{API_BASE}/testcases/{test_case_key}/testscript"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_test_case_steps(test_case_key: str, max_results: int = 10, start_at: int = 0) -> str:
    """Get test steps for a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        max_results: Maximum number of steps to return (default: 10)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": max_results,
        "startAt": start_at
    }
    
    url = f"{API_BASE}/testcases/{test_case_key}/teststeps"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_test_case_steps(test_case_key: str, steps_data: str) -> str:
    """Create test steps for a test case.
    
    Args:
        test_case_key: The test case key (e.g. 'PROJ-T123')
        steps_data: JSON string containing the test steps data
    """
    try:
        payload = json.loads(steps_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for steps_data"
    
    url = f"{API_BASE}/testcases/{test_case_key}/teststeps"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

# =============================================================================
# FOLDERS ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_folders(
    project_key: Optional[str] = None,
    folder_type: Optional[str] = None,
    max_results: int = 25,
    start_at: int = 0
) -> str:
    """Get folders from Zephyr Scale.
    
    Args:
        project_key: Optional project key filter (e.g. 'SM')
        folder_type: Optional folder type filter ('TEST_CASE', 'TEST_PLAN', 'TEST_CYCLE')
        max_results: Maximum number of folders to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": min(max_results, 1000),
        "startAt": start_at
    }
    
    if project_key:
        params["projectKey"] = project_key
    if folder_type:
        params["folderType"] = folder_type
    
    url = f"{API_BASE}/folders"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_folder(folder_id: int) -> str:
    """Get a specific folder by ID.
    
    Args:
        folder_id: The folder ID
    """
    url = f"{API_BASE}/folders/{folder_id}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_folder(
    project_key: str,
    name: str,
    folder_type: str,
    parent_id: Optional[int] = None
) -> str:
    """Create a new folder.
    
    Args:
        project_key: Project key (e.g. 'SM')
        name: Folder name
        folder_type: Folder type ('TEST_CASE', 'TEST_PLAN', 'TEST_CYCLE')
        parent_id: Optional parent folder ID (null for root folders)
    """
    payload = {
        "projectKey": project_key,
        "name": name,
        "folderType": folder_type
    }
    
    if parent_id:
        payload["parentId"] = parent_id
    
    url = f"{API_BASE}/folders"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

# =============================================================================
# TEST CYCLES ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_test_cycles(
    project_key: Optional[str] = None,
    folder_id: Optional[int] = None,
    jira_project_version_id: Optional[int] = None,
    max_results: int = 25,
    start_at: int = 0
) -> str:
    """Get test cycles from Zephyr Scale.
    
    Args:
        project_key: Optional project key filter (e.g. 'SM')
        folder_id: Optional folder ID filter
        jira_project_version_id: Optional Jira project version ID filter
        max_results: Maximum number of test cycles to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": min(max_results, 1000),
        "startAt": start_at
    }
    
    if project_key:
        params["projectKey"] = project_key
    if folder_id:
        params["folderId"] = folder_id
    if jira_project_version_id:
        params["jiraProjectVersionId"] = jira_project_version_id
    
    url = f"{API_BASE}/testcycles"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_test_cycle(test_cycle_id_or_key: str) -> str:
    """Get a specific test cycle by ID or key.
    
    Args:
        test_cycle_id_or_key: The test cycle ID or key (e.g. 'PROJ-R123' or '123')
    """
    url = f"{API_BASE}/testcycles/{test_cycle_id_or_key}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_test_cycle(
    project_key: str,
    name: str,
    description: Optional[str] = None,
    planned_start_date: Optional[str] = None,
    planned_end_date: Optional[str] = None,
    status_name: Optional[str] = None,
    folder_id: Optional[int] = None,
    owner_id: Optional[str] = None,
    jira_project_version_id: Optional[int] = None
) -> str:
    """Create a new test cycle.
    
    Args:
        project_key: Project key (e.g. 'SM')
        name: Test cycle name
        description: Optional description
        planned_start_date: Planned start date (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        planned_end_date: Planned end date (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        status_name: Status name
        folder_id: Optional folder ID
        owner_id: Jira user account ID
        jira_project_version_id: Jira project version ID
    """
    payload = {
        "projectKey": project_key,
        "name": name
    }
    
    if description:
        payload["description"] = description
    if planned_start_date:
        payload["plannedStartDate"] = planned_start_date
    if planned_end_date:
        payload["plannedEndDate"] = planned_end_date
    if status_name:
        payload["statusName"] = status_name
    if folder_id:
        payload["folderId"] = folder_id
    if owner_id:
        payload["ownerId"] = owner_id
    if jira_project_version_id:
        payload["jiraProjectVersion"] = jira_project_version_id
    
    url = f"{API_BASE}/testcycles"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def update_test_cycle(test_cycle_id_or_key: str, test_cycle_data: str) -> str:
    """Update an existing test cycle.
    
    Args:
        test_cycle_id_or_key: The test cycle ID or key (e.g. 'PROJ-R123' or '123')
        test_cycle_data: JSON string containing the test cycle data to update
    """
    try:
        payload = json.loads(test_cycle_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for test_cycle_data"
    
    url = f"{API_BASE}/testcycles/{test_cycle_id_or_key}"
    data = await make_zephyr_request("PUT", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Test cycle updated successfully"

# =============================================================================
# TEST EXECUTIONS ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_test_executions(
    project_key: Optional[str] = None,
    test_cycle: Optional[str] = None,
    test_case: Optional[str] = None,
    actual_end_date_after: Optional[str] = None,
    actual_end_date_before: Optional[str] = None,
    jira_project_version_id: Optional[int] = None,
    only_last_executions: bool = False,
    include_step_links: bool = False,
    max_results: int = 25,
    start_at: int = 0
) -> str:
    """Get test executions from Zephyr Scale.
    
    Args:
        project_key: Optional project key filter (e.g. 'SM')
        test_cycle: Optional test cycle key filter
        test_case: Optional test case key filter
        actual_end_date_after: Filter for actual end date after (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        actual_end_date_before: Filter for actual end date before (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        jira_project_version_id: Optional Jira project version ID filter
        only_last_executions: If true, includes only the last execution of each test cycle item
        include_step_links: If true, execution step issue links will be included
        max_results: Maximum number of test executions to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": min(max_results, 1000),
        "startAt": start_at,
        "onlyLastExecutions": only_last_executions,
        "includeStepLinks": include_step_links
    }
    
    if project_key:
        params["projectKey"] = project_key
    if test_cycle:
        params["testCycle"] = test_cycle
    if test_case:
        params["testCase"] = test_case
    if actual_end_date_after:
        params["actualEndDateAfter"] = actual_end_date_after
    if actual_end_date_before:
        params["actualEndDateBefore"] = actual_end_date_before
    if jira_project_version_id:
        params["jiraProjectVersionId"] = jira_project_version_id
    
    url = f"{API_BASE}/testexecutions"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_test_execution(test_execution_id_or_key: str, include_step_links: bool = False) -> str:
    """Get a specific test execution by ID or key.
    
    Args:
        test_execution_id_or_key: The test execution ID or key (e.g. 'PROJ-E123' or '123')
        include_step_links: If true, execution step issue links will be included
    """
    params = {"includeStepLinks": include_step_links}
    
    url = f"{API_BASE}/testexecutions/{test_execution_id_or_key}"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_test_execution(
    project_key: str,
    test_case_key: str,
    test_cycle_key: str,
    status_name: str,
    environment_name: Optional[str] = None,
    actual_end_date: Optional[str] = None,
    execution_time: Optional[int] = None,
    executed_by_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    comment: Optional[str] = None
) -> str:
    """Create a new test execution.
    
    Args:
        project_key: Project key (e.g. 'SM')
        test_case_key: Test case key (e.g. 'PROJ-T123')
        test_cycle_key: Test cycle key (e.g. 'PROJ-R123')
        status_name: Status name (e.g. 'Pass', 'Fail')
        environment_name: Optional environment name
        actual_end_date: Actual end date (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        execution_time: Actual execution time in milliseconds
        executed_by_id: Jira user account ID of executor
        assigned_to_id: Jira user account ID of assignee
        comment: Optional comment
    """
    payload = {
        "projectKey": project_key,
        "testCaseKey": test_case_key,
        "testCycleKey": test_cycle_key,
        "statusName": status_name
    }
    
    if environment_name:
        payload["environmentName"] = environment_name
    if actual_end_date:
        payload["actualEndDate"] = actual_end_date
    if execution_time:
        payload["executionTime"] = execution_time
    if executed_by_id:
        payload["executedById"] = executed_by_id
    if assigned_to_id:
        payload["assignedToId"] = assigned_to_id
    if comment:
        payload["comment"] = comment
    
    url = f"{API_BASE}/testexecutions"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def update_test_execution(test_execution_id_or_key: str, execution_data: str) -> str:
    """Update an existing test execution.
    
    Args:
        test_execution_id_or_key: The test execution ID or key (e.g. 'PROJ-E123' or '123')
        execution_data: JSON string containing the test execution data to update
    """
    try:
        payload = json.loads(execution_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for execution_data"
    
    url = f"{API_BASE}/testexecutions/{test_execution_id_or_key}"
    data = await make_zephyr_request("PUT", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Test execution updated successfully"

# =============================================================================
# PROJECTS ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_projects(max_results: int = 25, start_at: int = 0) -> str:
    """Get all projects from Zephyr Scale.
    
    Args:
        max_results: Maximum number of projects to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": min(max_results, 1000),
        "startAt": start_at
    }
    
    url = f"{API_BASE}/projects"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_project(project_id_or_key: str) -> str:
    """Get a specific project by ID or key.
    
    Args:
        project_id_or_key: The project ID or key (e.g. 'PROJ' or '123')
    """
    url = f"{API_BASE}/projects/{project_id_or_key}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

# =============================================================================
# PRIORITIES ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_priorities(
    project_key: Optional[str] = None,
    max_results: int = 25,
    start_at: int = 0
) -> str:
    """Get priorities from Zephyr Scale.
    
    Args:
        project_key: Optional project key filter (e.g. 'SM')
        max_results: Maximum number of priorities to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": min(max_results, 1000),
        "startAt": start_at
    }
    
    if project_key:
        params["projectKey"] = project_key
    
    url = f"{API_BASE}/priorities"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_priority(priority_id: int) -> str:
    """Get a specific priority by ID.
    
    Args:
        priority_id: The priority ID
    """
    url = f"{API_BASE}/priorities/{priority_id}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_priority(
    project_key: str,
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None
) -> str:
    """Create a new priority.
    
    Args:
        project_key: Project key (e.g. 'SM')
        name: Priority name
        description: Optional priority description
        color: Optional color in hexadecimal format (e.g. '#FF0000')
    """
    payload = {
        "projectKey": project_key,
        "name": name
    }
    
    if description:
        payload["description"] = description
    if color:
        payload["color"] = color
    
    url = f"{API_BASE}/priorities"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def update_priority(priority_id: int, priority_data: str) -> str:
    """Update an existing priority.
    
    Args:
        priority_id: The priority ID
        priority_data: JSON string containing the priority data to update
    """
    try:
        payload = json.loads(priority_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for priority_data"
    
    url = f"{API_BASE}/priorities/{priority_id}"
    data = await make_zephyr_request("PUT", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Priority updated successfully"

# =============================================================================
# STATUSES ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_statuses(
    project_key: Optional[str] = None,
    status_type: Optional[str] = None,
    max_results: int = 25,
    start_at: int = 0
) -> str:
    """Get statuses from Zephyr Scale.
    
    Args:
        project_key: Optional project key filter (e.g. 'SM')
        status_type: Optional status type filter ('TEST_CASE', 'TEST_PLAN', 'TEST_CYCLE', 'TEST_EXECUTION')
        max_results: Maximum number of statuses to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": min(max_results, 1000),
        "startAt": start_at
    }
    
    if project_key:
        params["projectKey"] = project_key
    if status_type:
        params["statusType"] = status_type
    
    url = f"{API_BASE}/statuses"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_status(status_id: int) -> str:
    """Get a specific status by ID.
    
    Args:
        status_id: The status ID
    """
    url = f"{API_BASE}/statuses/{status_id}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_status(
    project_key: str,
    name: str,
    status_type: str,
    description: Optional[str] = None,
    color: Optional[str] = None
) -> str:
    """Create a new status.
    
    Args:
        project_key: Project key (e.g. 'SM')
        name: Status name
        status_type: Status type ('TEST_CASE', 'TEST_PLAN', 'TEST_CYCLE', 'TEST_EXECUTION')
        description: Optional status description
        color: Optional color in hexadecimal format (e.g. '#FF0000')
    """
    payload = {
        "projectKey": project_key,
        "name": name,
        "type": status_type
    }
    
    if description:
        payload["description"] = description
    if color:
        payload["color"] = color
    
    url = f"{API_BASE}/statuses"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def update_status(status_id: int, status_data: str) -> str:
    """Update an existing status.
    
    Args:
        status_id: The status ID
        status_data: JSON string containing the status data to update
    """
    try:
        payload = json.loads(status_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for status_data"
    
    url = f"{API_BASE}/statuses/{status_id}"
    data = await make_zephyr_request("PUT", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Status updated successfully"

# =============================================================================
# ENVIRONMENTS ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_environments(
    project_key: Optional[str] = None,
    max_results: int = 25,
    start_at: int = 0
) -> str:
    """Get environments from Zephyr Scale.
    
    Args:
        project_key: Optional project key filter (e.g. 'SM')
        max_results: Maximum number of environments to return (default: 25, max: 1000)
        start_at: Zero-indexed starting position (default: 0)
    """
    params = {
        "maxResults": min(max_results, 1000),
        "startAt": start_at
    }
    
    if project_key:
        params["projectKey"] = project_key
    
    url = f"{API_BASE}/environments"
    data = await make_zephyr_request("GET", url, params=params)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_environment(environment_id: int) -> str:
    """Get a specific environment by ID.
    
    Args:
        environment_id: The environment ID
    """
    url = f"{API_BASE}/environments/{environment_id}"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def create_environment(
    project_key: str,
    name: str,
    description: Optional[str] = None
) -> str:
    """Create a new environment.
    
    Args:
        project_key: Project key (e.g. 'SM')
        name: Environment name
        description: Optional environment description
    """
    payload = {
        "projectKey": project_key,
        "name": name
    }
    
    if description:
        payload["description"] = description
    
    url = f"{API_BASE}/environments"
    data = await make_zephyr_request("POST", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def update_environment(environment_id: int, environment_data: str) -> str:
    """Update an existing environment.
    
    Args:
        environment_id: The environment ID
        environment_data: JSON string containing the environment data to update
    """
    try:
        payload = json.loads(environment_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for environment_data"
    
    url = f"{API_BASE}/environments/{environment_id}"
    data = await make_zephyr_request("PUT", url, data=payload)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Environment updated successfully"

# =============================================================================
# LINKS ENDPOINTS
# =============================================================================

@mcp.tool()
async def delete_link(link_id: int) -> str:
    """Delete a link by ID.
    
    Args:
        link_id: The link ID to delete
    """
    url = f"{API_BASE}/links/{link_id}"
    data = await make_zephyr_request("DELETE", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "Link deleted successfully"

# =============================================================================
# ISSUE LINKS ENDPOINTS
# =============================================================================

@mcp.tool()
async def get_issue_link_test_cases(issue_key: str) -> str:
    """Get test case keys and versions linked to a Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g. 'PROJ-123')
    """
    url = f"{API_BASE}/issuelinks/{issue_key}/testcases"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_issue_link_test_cycles(issue_key: str) -> str:
    """Get test cycle IDs linked to a Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g. 'PROJ-123')
    """
    url = f"{API_BASE}/issuelinks/{issue_key}/testcycles"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_issue_link_test_plans(issue_key: str) -> str:
    """Get test plan IDs linked to a Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g. 'PROJ-123')
    """
    url = f"{API_BASE}/issuelinks/{issue_key}/testplans"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

@mcp.tool()
async def get_issue_link_test_executions(issue_key: str) -> str:
    """Get test execution IDs linked to a Jira issue.
    
    Args:
        issue_key: The Jira issue key (e.g. 'PROJ-123')
    """
    url = f"{API_BASE}/issuelinks/{issue_key}/executions"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2)

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@mcp.tool()
async def health_check() -> str:
    """Check the health of the Zephyr Scale API."""
    url = f"{API_BASE}/healthcheck"
    data = await make_zephyr_request("GET", url)
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return "API is healthy"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

@mcp.tool()
async def get_api_info() -> str:
    """Get information about the Zephyr Scale MCP server configuration."""
    info = {
        "api_base": API_BASE,
        "region": "EU" if USE_EU_REGION else "Global",
        "authentication": "JWT Bearer Token" if API_TOKEN else "Not configured",
        "available_endpoints": {
            "test_cases": [
                "get_test_cases", "get_test_case", "create_test_case", "update_test_case",
                "get_test_case_links", "create_test_case_issue_link", "create_test_case_web_link",
                "get_test_case_versions", "get_test_case_version",
                "get_test_case_script", "create_test_case_script",
                "get_test_case_steps", "create_test_case_steps"
            ],
            "folders": [
                "get_folders", "get_folder", "create_folder"
            ],
            "test_cycles": [
                "get_test_cycles", "get_test_cycle", "create_test_cycle", "update_test_cycle"
            ],
            "test_executions": [
                "get_test_executions", "get_test_execution", "create_test_execution", "update_test_execution"
            ],
            "projects": [
                "get_projects", "get_project"
            ],
            "priorities": [
                "get_priorities", "get_priority", "create_priority", "update_priority"
            ],
            "statuses": [
                "get_statuses", "get_status", "create_status", "update_status"
            ],
            "environments": [
                "get_environments", "get_environment", "create_environment", "update_environment"
            ],
            "links": [
                "delete_link"
            ],
            "issue_links": [
                "get_issue_link_test_cases", "get_issue_link_test_cycles", 
                "get_issue_link_test_plans", "get_issue_link_test_executions"
            ],
            "utilities": [
                "health_check", "get_api_info"
            ]
        }
    }
    
    return json.dumps(info, indent=2)

if __name__ == "__main__":
    # Initialize and run the server
    logger.info(f"Starting Zephyr Scale MCP Server")
    logger.info(f"API Base: {API_BASE}")
    logger.info(f"Region: {'EU' if USE_EU_REGION else 'Global'}")
    mcp.run(transport='stdio')