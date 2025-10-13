# Daytona SDK Reference

This document contains reference information for the Daytona SDK used in the Self-Evolving Agent project for isolated code execution and testing.

## Overview

Daytona SDK provides secure, isolated sandbox environments for executing generated code safely. The ATC (Automatic Tool Creation) system uses Daytona to test generated tools before integration.

## Installation

```bash
pip install daytona-sdk
```

## Quick Start

```python
from daytona_sdk import Daytona, DaytonaConfig

# Initialize Daytona client
config = DaytonaConfig(api_key="your-api-key")
daytona = Daytona(config)

# Create a sandbox
sandbox = daytona.create()

# Upload a file
file_content = b"print('Hello from Daytona!')"
sandbox.fs.upload_file(file_content, "hello.py")

# Execute code
response = sandbox.process.code_run('python hello.py')
print(response.result)

# Clean up
sandbox.delete()
```

## Core Concepts

### 1. Sandbox Lifecycle

**Creation**:
```python
sandbox = daytona.create()
sandbox_id = sandbox.id  # Unique identifier
```

**Deletion**:
```python
sandbox.delete()  # Always cleanup in finally block
```

### 2. File Operations

**Upload File**:
```python
# Upload file content
sandbox.fs.upload_file(content_bytes, "filename.py")
```

**Download File**:
```python
file_content = sandbox.fs.download_file("filename.py")
```

### 3. Code Execution

**Execute Command**:
```python
result = sandbox.process.code_run('pip install pytest')
print(result.result)  # Output from command
```

**Run Tests**:
```python
# Upload test file
sandbox.fs.upload_file(test_code.encode('utf-8'), "test_tool.py")

# Run pytest
result = sandbox.process.code_run('python -m pytest test_tool.py -v')
success = "FAILED" not in result.result and "ERROR" not in result.result
```

## Best Practices

### 1. Always Cleanup

```python
sandbox = None
try:
    sandbox = daytona.create()
    # ... do work
finally:
    if sandbox:
        sandbox.delete()
```

### 2. Error Handling

```python
try:
    result = sandbox.process.code_run(command)
    if "error" in result.result.lower():
        print(f"Warning: {result.result}")
except Exception as e:
    print(f"Execution failed: {e}")
```

### 3. Dependency Installation

```python
# Install dependencies before running code
sandbox.process.code_run("pip install pytest numpy pandas")
```

## Integration in ATC System

The Self-Evolving Agent uses Daytona in the following pipeline:

1. **Pattern Recognition**: Identify recurring patterns in solver traces
2. **Tool Ideation**: Generate tool specifications
3. **Code Generation**: LLM generates Python code from specs
4. **Sandbox Testing**: Execute generated code in Daytona sandbox
5. **Validation**: Verify tests pass before tool integration

### Example: DaytonaManager

```python
from sea.daytona_manager import DaytonaManager

manager = DaytonaManager()

# Test generated tool code
result = manager.run_code_with_tests(
    tool_code=generated_code,
    dependencies=["pytest", "langchain-core"],
    timeout=60
)

if result["success"]:
    print("Tool tests passed!")
else:
    print(f"Tests failed: {result['output']}")
```

## API Reference

### DaytonaConfig

**Parameters**:
- `api_key` (str): Daytona API key (required)

### Daytona

**Methods**:
- `create() -> Sandbox`: Create new sandbox
- Configuration options for resources, timeouts, etc.

### Sandbox

**Properties**:
- `id` (str): Unique sandbox identifier
- `fs`: File system operations
- `process`: Process execution

**Methods**:
- `delete()`: Remove sandbox and cleanup resources

### Sandbox.fs

**Methods**:
- `upload_file(content: bytes, path: str)`: Write file to sandbox
- `download_file(path: str) -> bytes`: Read file from sandbox

### Sandbox.process

**Methods**:
- `code_run(command: str) -> Result`: Execute command in sandbox

### Result

**Properties**:
- `result` (str): Combined output from command execution

## Environment Configuration

Add to `.env`:
```bash
DAYTONA_API_KEY=your_daytona_api_key_here
```

Get your API key from: https://www.daytona.io/dashboard

## Troubleshooting

### Common Issues

1. **Module not found**: Ensure `daytona-sdk` is installed
   ```bash
   uv pip install daytona-sdk
   ```

2. **Authentication failed**: Check DAYTONA_API_KEY is set correctly
   ```bash
   echo $DAYTONA_API_KEY
   ```

3. **Sandbox creation timeout**: Increase timeout or check network connectivity

4. **Dependency installation fails**: Verify package names and availability

## Testing

Run the integration tests:
```bash
# Test connection only
python scripts/run_atc_evolution.py --test-daytona

# Full integration tests
python scripts/test_daytona_codegen.py
```

## Resources

- Official Documentation: https://www.daytona.io/docs
- Dashboard: https://www.daytona.io/dashboard
- GitHub: https://github.com/daytonaio/sdk

## Version Information

This reference is based on:
- `daytona-sdk>=0.110.1`
- Last updated: 2025-10-12
- Status: ✅ **Setup Complete & Verified**

### Verification Results (2025-10-12)

All integration tests passed successfully:
- ✅ Connection test: Sandbox creation and basic execution (1.42s)
- ✅ Simple code execution: Python code with pytest (3.05s)
- ✅ Code generation: LLM-generated tool creation (valid syntax)
- ✅ End-to-end pipeline: Specification → Code → Sandbox testing (3.05s)

**Implementation verified against official SDK:**
- API usage matches documentation patterns
- Proper error handling and cleanup
- Weave integration for observability
- Ready for production tool testing

## Notes

- Sandboxes are ephemeral and cleaned up after use
- Each sandbox execution is isolated
- Resource limits can be configured
- Network access can be restricted
- Suitable for testing untrusted code safely
