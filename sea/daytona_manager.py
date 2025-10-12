# ABOUTME: DaytonaManager handles sandbox creation and code execution for tool testing
# ABOUTME: Provides isolated environments to run generated code safely with proper cleanup

import os
import time
import weave
from typing import Dict, Any, List, Optional
from daytona_sdk import Daytona, DaytonaConfig
from dotenv import load_dotenv

load_dotenv()


class DaytonaManager:
    """Manages Daytona sandbox creation, code execution, and cleanup."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Daytona manager.

        Args:
            api_key: Daytona API key. If None, reads from DAYTONA_API_KEY env var
        """
        self.api_key = api_key or os.getenv("DAYTONA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Daytona API key required. Set DAYTONA_API_KEY environment variable "
                "or pass api_key parameter"
            )

        # Initialize Daytona client with config
        config = DaytonaConfig(api_key=self.api_key)
        self.daytona = Daytona(config)

    @weave.op()
    def run_code_with_tests(
        self,
        tool_code: str,
        dependencies: Optional[List[str]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Execute tool code with tests in isolated Daytona sandbox.

        Args:
            tool_code: Complete Python code including tool and test functions
            dependencies: List of pip packages to install (e.g., ['pytest', 'numpy'])
            timeout: Maximum execution time in seconds

        Returns:
            Dictionary with execution results:
            {
                "success": bool,  # True if tests passed
                "exit_code": int,  # Process exit code (0 = success)
                "output": str,  # Combined stdout + stderr
                "stdout": str,  # Standard output
                "stderr": str,  # Standard error
                "test_results": str,  # Pytest output if tests ran
                "sandbox_id": str,  # Sandbox identifier
                "execution_time": float  # Time taken in seconds
            }
        """
        sandbox = None
        start_time = time.time()

        try:
            # Create sandbox
            print(f"Creating Daytona sandbox...")
            sandbox = self.daytona.create()
            sandbox_id = sandbox.id if hasattr(sandbox, 'id') else "unknown"
            print(f"  Sandbox created: {sandbox_id}")

            # Install dependencies if provided
            if dependencies:
                print(f"  Installing dependencies: {', '.join(dependencies)}")
                # Use subprocess to run pip install
                dep_list_str = str(dependencies)  # Convert to string for interpolation
                dep_install_code = f"""
import subprocess
result = subprocess.run(['pip', 'install'] + {dep_list_str}, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)
"""
                install_result = sandbox.process.code_run(dep_install_code)

                if install_result.exit_code != 0:
                    print(f"  Warning: Dependency installation exit code: {install_result.exit_code}")
                    if install_result.result:
                        print(f"  Output: {install_result.result[:300]}")

            # Write code to file in sandbox
            code_filename = "generated_tool.py"
            print(f"  Writing code to {code_filename}...")
            sandbox.fs.upload_file(tool_code.encode('utf-8'), code_filename)

            # Execute tests with pytest
            print(f"  Running tests...")
            # Use subprocess to run pytest
            test_code = f"""
import subprocess
result = subprocess.run(['python', '-m', 'pytest', '{code_filename}', '-v', '--tb=short'],
                       capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)
print(f'PYTEST_EXIT_CODE: {{result.returncode}}')
"""
            result = sandbox.process.code_run(test_code)

            execution_time = time.time() - start_time

            # Parse results
            output = result.result if hasattr(result, 'result') else ""

            # Extract pytest exit code from output
            pytest_exit_code = 1  # Default to failure
            if "PYTEST_EXIT_CODE: 0" in output:
                pytest_exit_code = 0
            elif "PYTEST_EXIT_CODE:" in output:
                try:
                    import re
                    match = re.search(r'PYTEST_EXIT_CODE: (\d+)', output)
                    if match:
                        pytest_exit_code = int(match.group(1))
                except:
                    pass

            success = pytest_exit_code == 0 and result.exit_code == 0
            stdout = output
            stderr = ""

            print(f"  Test execution completed: {'✓ PASS' if success else '✗ FAIL'}")
            print(f"  Pytest exit code: {pytest_exit_code}")
            print(f"  Execution time: {execution_time:.2f}s")

            return {
                "success": success,
                "exit_code": pytest_exit_code,
                "output": output,
                "stdout": stdout,
                "stderr": stderr,
                "test_results": output,
                "sandbox_id": sandbox_id,
                "execution_time": execution_time,
                "error": None
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Sandbox execution failed: {str(e)}"
            print(f"  ✗ ERROR: {error_msg}")

            return {
                "success": False,
                "exit_code": -1,
                "output": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "test_results": "",
                "sandbox_id": sandbox.id if sandbox and hasattr(sandbox, 'id') else "unknown",
                "execution_time": execution_time,
                "error": error_msg
            }

        finally:
            # Always cleanup sandbox
            if sandbox:
                try:
                    print(f"  Cleaning up sandbox...")
                    sandbox.delete()
                    print(f"  Sandbox removed")
                except Exception as e:
                    print(f"  Warning: Failed to cleanup sandbox: {e}")

    @weave.op()
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Daytona connection with a simple hello world execution.

        Returns:
            Dictionary with test results and connection status
        """
        print("Testing Daytona connection...")

        sandbox = None
        start_time = time.time()

        try:
            # Create sandbox
            print(f"Creating Daytona sandbox...")
            sandbox = self.daytona.create()
            sandbox_id = sandbox.id if hasattr(sandbox, 'id') else "unknown"
            print(f"  Sandbox created: {sandbox_id}")

            # Test simple Python execution
            print(f"  Running test code...")
            simple_code = """
import sys
print("Hello from Daytona!")
print(f"Python version: {sys.version}")
"""
            result = sandbox.process.code_run(simple_code)

            execution_time = time.time() - start_time
            success = result.exit_code == 0

            print(f"  Test execution completed: {'✓ PASS' if success else '✗ FAIL'}")
            print(f"  Execution time: {execution_time:.2f}s")

            return {
                "success": success,
                "exit_code": result.exit_code,
                "output": result.result,
                "execution_time": execution_time,
                "error": None
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Sandbox connection test failed: {str(e)}"
            print(f"  ✗ ERROR: {error_msg}")

            return {
                "success": False,
                "exit_code": -1,
                "output": error_msg,
                "execution_time": execution_time,
                "error": error_msg
            }

        finally:
            # Always cleanup sandbox
            if sandbox:
                try:
                    print(f"  Cleaning up sandbox...")
                    sandbox.delete()
                    print(f"  Sandbox removed")
                except Exception as e:
                    print(f"  Warning: Failed to cleanup sandbox: {e}")
