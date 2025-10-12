# ABOUTME: WeaveTraceFetcher retrieves and formats execution traces from Weave for ATC analysis
# ABOUTME: Provides centralized interface for fetching solver traces with filtering and formatting

import weave
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from weave.trace.weave_client import CallsFilter


class WeaveTraceFetcher:
    """Fetches and formats Weave traces for Automatic Tool Creation analysis."""

    def __init__(self, project_name: str):
        """
        Initialize Weave trace fetcher.

        Args:
            project_name: Weave project name (format: 'entity/project')

        Raises:
            ValueError: If project_name is invalid
            Exception: If Weave initialization fails
        """
        if not project_name or '/' not in project_name:
            raise ValueError(
                f"Invalid Weave project name: '{project_name}'. "
                "Expected format: 'entity/project'"
            )

        try:
            self.client = weave.init(project_name)
            self.project_name = project_name
            print(f"✓ WeaveTraceFetcher initialized for {project_name}")
        except Exception as e:
            raise Exception(
                f"Failed to initialize Weave client for {project_name}: {str(e)}"
            ) from e

    @weave.op()
    def fetch_recent_traces(
        self,
        num_traces: int = 20,
        op_name_filter: Optional[str] = "run_react_agent",
        trace_roots_only: bool = True,
        hours_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent traces from Weave project.

        Args:
            num_traces: Maximum number of traces to retrieve
            op_name_filter: Operation name to filter (e.g., 'run_react_agent').
                          Set to None to fetch all operations.
            trace_roots_only: If True, only fetch parent/root traces
            hours_back: Optional time window in hours (None = all time)

        Returns:
            List of formatted trace dictionaries for PatternRecognizer
        """
        print(f"📊 Fetching traces from {self.project_name}...")
        print(f"   Filters: op_name={op_name_filter}, roots_only={trace_roots_only}, limit={num_traces}")

        # Build filter - only set op_names if filter provided
        call_filter = CallsFilter(trace_roots_only=trace_roots_only)
        if op_name_filter:
            # Note: CallsFilter doesn't work well with partial names
            # We'll filter manually after fetching
            pass

        # Build query for time filtering if specified
        query = None
        if hours_back:
            start_time = datetime.now() - timedelta(hours=hours_back)
            query = {"started_at": {"$gte": start_time.isoformat()}}
            print(f"   Time filter: last {hours_back} hours")

        # Fetch calls - specify columns for performance
        try:
            # Fetch more than needed since we'll filter by op_name manually
            # Use 10x multiplier to account for other operations between target traces
            fetch_limit = num_traces * 10 if op_name_filter else num_traces

            calls_iter = self.client.get_calls(
                filter=call_filter,
                columns=['id', 'trace_id', 'op_name', 'inputs', 'output', 'started_at', 'summary'],
                sort_by=[{'field': 'started_at', 'direction': 'desc'}],
                limit=fetch_limit,
                query=query,
                include_costs=True
            )

            # Convert to list and filter by op_name if needed
            all_calls = list(calls_iter)
            print(f"✓ Retrieved {len(all_calls)} calls from Weave")

            # Filter by op_name substring match if specified
            if op_name_filter:
                filtered_calls = [
                    call for call in all_calls
                    if op_name_filter.lower() in call.op_name.lower()
                ]
                calls = filtered_calls[:num_traces]
                print(f"✓ Filtered to {len(calls)} calls matching '{op_name_filter}'")
            else:
                calls = all_calls[:num_traces]

            # Format each call for analysis
            formatted_traces = []
            for call in calls:
                try:
                    trace = self.format_trace_for_analysis(call)
                    if self._validate_trace(trace):
                        formatted_traces.append(trace)
                    else:
                        print(f"⚠️  Skipping invalid trace: {call.id}")
                except Exception as e:
                    print(f"⚠️  Error formatting trace {call.id}: {e}")
                    continue

            print(f"✓ Formatted {len(formatted_traces)} valid traces")
            return formatted_traces

        except Exception as e:
            print(f"❌ Error fetching traces: {e}")
            return []

    def format_trace_for_analysis(self, call) -> Dict[str, Any]:
        """
        Convert Weave Call object to PatternRecognizer format.

        Args:
            call: Weave Call object

        Returns:
            Formatted trace dictionary
        """
        # Extract inputs - handle different formats
        inputs = call.inputs or {}

        # Problem/question can be in different locations
        problem = None
        if 'question' in inputs:
            problem = inputs['question']
        elif 'messages' in inputs and isinstance(inputs['messages'], list):
            # Extract from message format (for chat completions)
            for msg in inputs['messages']:
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    problem = msg.get('content', '')
                    break
        elif 'prompt' in inputs:
            problem = inputs['prompt']

        # Default if not found
        if not problem:
            problem = str(inputs)[:200]

        # Extract output
        output = call.output
        solution = str(output) if output else "No solution recorded"

        # Extract metadata from summary
        summary = call.summary or {}
        weave_metadata = summary.get('weave', {})

        metadata = {
            'latency_ms': weave_metadata.get('latency_ms', 0),
            'status': weave_metadata.get('status', 'unknown'),
            'trace_name': weave_metadata.get('trace_name', ''),
        }

        # Extract usage/cost info if available
        usage = summary.get('usage', {})
        if usage:
            metadata['token_usage'] = usage

        # Build execution flow - simplified for now
        # In future, could fetch child calls for detailed flow
        execution_flow = [{
            'type': 'llm_call',
            'description': f"Executed {call.op_name}"
        }]

        # Tools invoked - extract from child calls if available
        # For now, mark as calculator if it's a math problem
        tools_invoked = []
        if 'calculator' in str(call.op_name).lower() or 'calculator' in solution.lower():
            tools_invoked.append('calculator_tool')

        return {
            'trace_id': call.trace_id,
            'id': call.id,
            'problem': problem,
            'solution': solution,
            'tools_invoked': tools_invoked,
            'execution_flow': execution_flow,
            'metadata': metadata,
            'started_at': str(call.started_at) if call.started_at else None
        }

    def get_child_calls(self, parent_call_id: str) -> List[Dict[str, Any]]:
        """
        Fetch child calls for detailed execution flow analysis.

        Args:
            parent_call_id: Parent call ID to fetch children for

        Returns:
            List of formatted child call dictionaries
        """
        try:
            child_calls_iter = self.client.get_calls(
                filter=CallsFilter(parent_ids=[parent_call_id]),
                columns=['id', 'op_name', 'inputs', 'output', 'started_at']
            )

            child_calls = []
            for call in child_calls_iter:
                child_calls.append({
                    'id': call.id,
                    'op_name': call.op_name,
                    'inputs': call.inputs,
                    'output': call.output,
                    'started_at': str(call.started_at) if call.started_at else None
                })

            return child_calls

        except Exception as e:
            print(f"⚠️  Error fetching child calls for {parent_call_id}: {e}")
            return []

    def _validate_trace(self, trace: Dict[str, Any]) -> bool:
        """
        Validate that trace has minimum required fields.

        Args:
            trace: Formatted trace dictionary

        Returns:
            True if trace is valid, False otherwise
        """
        required_fields = ['trace_id', 'problem']

        for field in required_fields:
            if field not in trace or not trace[field]:
                return False

        # Ensure problem has meaningful content (not just whitespace)
        if len(str(trace['problem']).strip()) < 5:
            return False

        return True

    def fetch_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific trace by its ID.

        Args:
            trace_id: Trace ID to fetch

        Returns:
            Formatted trace dictionary or None if not found
        """
        try:
            call = self.client.get_call(trace_id, include_costs=True)
            if call:
                return self.format_trace_for_analysis(call)
            return None
        except Exception as e:
            print(f"❌ Error fetching trace {trace_id}: {e}")
            return None

    def get_trace_statistics(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for fetched traces.

        Args:
            traces: List of trace dictionaries

        Returns:
            Dictionary with trace statistics
        """
        if not traces:
            return {
                "total_traces": 0,
                "valid_traces": 0,
                "avg_latency_ms": 0,
                "tools_used": [],
                "status_distribution": {}
            }

        total = len(traces)
        total_latency = 0
        tools_set = set()
        status_counts = {}

        for trace in traces:
            # Latency
            if 'metadata' in trace and 'latency_ms' in trace['metadata']:
                total_latency += trace['metadata']['latency_ms']

            # Tools
            if 'tools_invoked' in trace:
                tools_set.update(trace['tools_invoked'])

            # Status
            if 'metadata' in trace and 'status' in trace['metadata']:
                status = trace['metadata']['status']
                status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_traces": total,
            "valid_traces": total,
            "avg_latency_ms": total_latency / total if total > 0 else 0,
            "tools_used": list(tools_set),
            "status_distribution": status_counts
        }
