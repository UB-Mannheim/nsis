# -*- coding: utf-8 -*-
# =============================================================================
# access_test.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Access test for API endpoints simulating multiple concurrent accesses.

A single access comprises calling following endpoints in order:
1. /research-compass + /research-compass.css + /research-compass.js + /research-compass-settings.js (static files)
2. /api/v1/query-expansion
3. /api/v1/perform-vufind-search
4. /api/v1/query-judge-quality (with previous results from /perform-vufind-search)
5. /api/v1/query-transformation

Usage:
    uv run python tests/access_test.py

Configuration:
    See CONFIG section below to adjust test parameters.
"""

import asyncio
import json
import os
import random
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
import httpx


# =============================================================================
# CONFIGURATION (copy from app/config.py: host, port, vufind_base_url, supported_versions, log_dir)
# =============================================================================

CONFIG = {
    # Base URL of the API server (from app/config.py: host, port)
    "base_url": "http://localhost:8000",

    "vufind_base_url": 'https://karma.bib.uni-mannheim.de',

    # API version prefix (from app/config.py: supported_versions[0])
    "api_version": "v1",

    # Number of concurrent accesses to simulate
    "num_concurrent_accesses": 3,

    # Number of times to repeat the test (for more reliable averages)
    "num_repetitions": 3,

    # Delay between repetitions in seconds
    "repetition_delay": 2.0,

    # Timeout for each HTTP request in seconds
    "request_timeout": 120.0,

    # Limit for titles retrieval
    "test_titles_limit": 10,

    # Log directory for performance stats (from app/config.py: log_dir)
    "log_dir": "/data/log/nsis",
}


# Test queries and VuFind URLs for access testing (10 total)
TEST_DATA = [
    {
        "query": "machine learning artificial intelligence",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=machine+learning+artificial+intelligence&type=AllFields&sort=relevance",
    },
    {
        "query": "climate change environmental science",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=climate+change+environmental+science&type=AllFields&sort=relevance",
    },
    {
        "query": "quantum physics relativity theory",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=quantum+physics+relativity+theory&type=AllFields&sort=relevance",
    },
    {
        "query": "world war history 20th century",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=world+war+history+20th+century&type=AllFields&sort=relevance",
    },
    {
        "query": "shakespeare literature drama",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=shakespeare+literature+drama&type=AllFields&sort=relevance",
    },
    {
        "query": "renewable energy solar wind power",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=renewable+energy+solar+wind+power&type=AllFields&sort=relevance",
    },
    {
        "query": "data science statistics analysis",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=data+science+statistics+analysis&type=AllFields&sort=relevance",
    },
    {
        "query": "philosophy ethics moral theory",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=philosophy+ethics+moral+theory&type=AllFields&sort=relevance",
    },
    {
        "query": "neural networks deep learning",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=neural+networks+deep+learning&type=AllFields&sort=relevance",
    },
    {
        "query": "biodiversity ecosystem conservation",
        "vufind_url": f"{CONFIG["vufind_base_url"]}/Search/Results?lookfor=biodiversity+ecosystem+conservation&type=AllFields&sort=relevance",
    },
]

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EndpointTiming:
    """Timing information for a single endpoint call."""
    endpoint: str
    duration_ms: float
    status_code: int
    success: bool
    error_message: Optional[str] = None
    cost_usd: Optional[float] = None


@dataclass
class AccessTiming:
    """Timing information for a complete access (all endpoints in sequence)."""
    access_id: int
    repetition: int
    endpoint_timings: List[EndpointTiming] = field(default_factory=list)
    total_duration_ms: float = 0.0
    total_cost_usd: float = 0.0
    success: bool = False

    @property
    def successful_endpoints(self) -> List[str]:
        return [e.endpoint for e in self.endpoint_timings if e.success]


@dataclass
class TestResults:
    """Aggregated results from access test."""
    total_accesses: int
    successful_accesses: int
    failed_accesses: int
    total_duration_seconds: float
    accesses_per_second: float
    endpoint_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    cost_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)


# =============================================================================
# COST LOGGING
# =============================================================================

def parse_llm_cost_stats(
    log_dir: str,
    start_time: datetime,
    end_time: datetime
) -> Dict[str, Dict[str, float]]:
    """
    Parse the performance log file and extract cost data for LLM operations.

    Args:
        log_dir: Directory containing nsis_stats_performance.log
        start_time: Start of test window (UTC aware datetime)
        end_time: End of test window (UTC aware datetime)

    Returns:
        Dict mapping function_name to cost statistics (count, min, max, mean, total)
    """
    perf_log_path = os.path.join(log_dir, "nsis_stats_performance.log")

    if not os.path.exists(perf_log_path):
        return {}

    # Collect all costs per function_name
    function_costs: Dict[str, List[float]] = {}

    try:
        with open(perf_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                # Filter by type = "performance" and operation_type in ("llm_inference", "embedding")
                if entry.get("type") != "performance":
                    continue
                operation_type = entry.get("operation_type")
                if operation_type not in ("llm_inference", "embedding"):
                    continue

                # Parse timestamp
                timestamp_str = entry.get("timestamp")
                if not timestamp_str:
                    continue

                try:
                    entry_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    continue

                # Check if within time window
                if not (start_time <= entry_time <= end_time):
                    continue

                # Extract cost
                cost = entry.get("cost_usd")
                if cost is None:
                    continue

                # Get function name
                function_name = entry.get("function_name", "unknown")

                if function_name not in function_costs:
                    function_costs[function_name] = []
                function_costs[function_name].append(float(cost))

    except Exception as e:
        print(f"Warning: Could not parse performance logs: {e}")

    # Calculate statistics per function
    result: Dict[str, Dict[str, float]] = {}
    for fname, costs in function_costs.items():
        if costs:
            result[fname] = {
                "count": len(costs),
                "min_usd": min(costs),
                "max_usd": max(costs),
                "mean_usd": statistics.mean(costs),
                "total_usd": sum(costs),
            }

    return result


# =============================================================================
# API CLIENT
# =============================================================================

class AccessTestClient:
    """HTTP client for access testing the API."""

    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def fetch_static_file(self, path: str) -> EndpointTiming:
        """Fetch a static file and measure timing."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=self.timeout)
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=path,
                duration_ms=duration_ms,
                status_code=response.status_code,
                success=response.status_code == 200
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=path,
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error_message=str(e)
            )

    async def call_query_expansion(self, query: str) -> EndpointTiming:
        """Call /api/v1/query-expansion endpoint."""
        url = f"{self.base_url}/api/{CONFIG["api_version"]}/query-expansion"
        payload = {"query": query}
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=self.timeout)
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/query-expansion",
                duration_ms=duration_ms,
                status_code=response.status_code,
                success=response.status_code == 200
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/query-expansion",
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error_message=str(e)
            )

    async def call_perform_vufind_search(self, url: str, limit: int = 10) -> tuple:
        """
        Call /api/v1/perform-vufind-search endpoint.

        Returns tuple of (EndpointTiming, titles_data) where titles_data is a list of titles
        to pass to query-judge-quality, or None if the call failed.
        """
        api_url = f"{self.base_url}/api/{CONFIG["api_version"]}/perform-vufind-search"
        payload = {"url": url, "limit": limit}
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, json=payload, timeout=self.timeout)
            duration_ms = (time.perf_counter() - start) * 1000
            timing = EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/perform-vufind-search",
                duration_ms=duration_ms,
                status_code=response.status_code,
                success=response.status_code == 200
            )
            # Parse response to extract titles
            titles_data = None
            if response.status_code == 200:
                try:
                    data = response.json()
                    titles_data = data.get("titles", [])
                except Exception:
                    pass
            return (timing, titles_data)
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            timing = EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/perform-vufind-search",
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error_message=str(e)
            )
            return (timing, None)

    async def call_query_judge_quality(self, query: str, url: str,
                                       titles: Optional[List[dict]] = None) -> EndpointTiming:
        """Call /api/v1/query-judge-quality endpoint."""
        api_url = f"{self.base_url}/api/{CONFIG["api_version"]}/query-judge-quality"
        payload = {"query": query, "url": url, "titles": None}
        if titles:
            payload["titles"] = titles
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, json=payload, timeout=self.timeout)
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/query-judge-quality",
                duration_ms=duration_ms,
                status_code=response.status_code,
                success=response.status_code == 200
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/query-judge-quality",
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error_message=str(e)
            )

    async def call_query_transformation(self, query: str) -> EndpointTiming:
        """Call /api/v1/query-transformation endpoint."""
        api_url = f"{self.base_url}/api/{CONFIG["api_version"]}/query-transformation"
        payload = {"query": query}
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, json=payload, timeout=self.timeout)
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/query-transformation",
                duration_ms=duration_ms,
                status_code=response.status_code,
                success=response.status_code == 200
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return EndpointTiming(
                endpoint=f"/api/{CONFIG["api_version"]}/query-transformation",
                duration_ms=duration_ms,
                status_code=0,
                success=False,
                error_message=str(e)
            )


# =============================================================================
# ACCESS TEST RUNNER
# =============================================================================

def print_access_progress(completed: int, total: int, access_id: int,
                         endpoint: str, duration_ms: float, success: bool) -> None:
    """Print progress for a single endpoint call."""
    status = "✓" if success else "✗"
    print(f"  [{completed}/{total}] Access #{access_id:3d} | {endpoint:45s} | {duration_ms:8.2f}ms | {status}")


def print_access_start(access_id: int) -> None:
    """Print when an access starts."""
    print(f"[START] Access #{access_id} beginning sequence...")


def print_access_complete(access_id: int, total_ms: float, success: bool) -> None:
    """Print when an access completes."""
    status = "SUCCESS" if success else "FAILED"
    print(f"[DONE ] Access #{access_id} completed in {total_ms:.2f}ms | {status}")
    print()


async def run_single_access(client: AccessTestClient, access_id: int, repetition: int,
                           query: str, vufind_url: str, titles_limit: int,
                           verbose: bool = True) -> AccessTiming:
    """
    Run a single complete access through all endpoints in order.

    Sequence (matching actual browser behavior):
    1. /research-compass + /research-compass.css + /research-compass.js + /research-compass-settings.js (static files)
    2. /api/v1/query-expansion
       - On success, immediately triggers:
         3. /api/v1/perform-vufind-search
         4. /api/v1/query-judge-quality (with VuFind titles)
    5. /api/v1/query-transformation
       - On success, rebuilds URL (but skipFetch=true, no additional fetch)
    """
    timing = AccessTiming(access_id=access_id, repetition=repetition)
    overall_start = time.perf_counter()

    if verbose:
        print_access_start(access_id)

    # Step 1: Fetch static files (research-compass + css + js + settings.js)
    # Note: Static files are served at /static/{filename} (see app/main.py: serve_static_file)
    static_files = ["research-compass", "static/research-compass.css", "static/research-compass.js", "static/research-compass-settings.js"]
    for static_file in static_files:
        endpoint_timing = await client.fetch_static_file(static_file)
        timing.endpoint_timings.append(endpoint_timing)
        if verbose:
            print(f"         → GET {static_file} → {endpoint_timing.duration_ms:.2f}ms ({endpoint_timing.status_code})")

    # Step 2: Query expansion (QE)
    # In the browser, QE completes first and immediately triggers VuFind search + quality
    endpoint_timing = await client.call_query_expansion(query)
    timing.endpoint_timings.append(endpoint_timing)
    if verbose:
        print(f"         → POST /api/{CONFIG["api_version"]}/query-expansion → {endpoint_timing.duration_ms:.2f}ms ({endpoint_timing.status_code})")

    # Step 3: Perform VuFind search (triggered immediately after QE returns in browser)
    endpoint_timing, vufind_titles = await client.call_perform_vufind_search(vufind_url, titles_limit)
    timing.endpoint_timings.append(endpoint_timing)
    if verbose:
        titles_count = len(vufind_titles) if vufind_titles else 0
        print(f"         → POST /api/{CONFIG["api_version"]}/perform-vufind-search → {endpoint_timing.duration_ms:.2f}ms ({endpoint_timing.status_code}) [{titles_count} titles]")

    # Step 4: Query judge quality (triggered immediately after VuFind results in browser)
    endpoint_timing = await client.call_query_judge_quality(query, vufind_url, titles=vufind_titles)
    timing.endpoint_timings.append(endpoint_timing)
    if verbose:
        print(f"         → POST /api/{CONFIG["api_version"]}/query-judge-quality → {endpoint_timing.duration_ms:.2f}ms ({endpoint_timing.status_code})")

    # Step 5: Query transformation (QT)
    # In the browser, QT runs after QE and rebuilds URL with skipFetch=true
    # (VuFind search already triggered by QE's immediate rebuildUrl)
    endpoint_timing = await client.call_query_transformation(query)
    timing.endpoint_timings.append(endpoint_timing)
    if verbose:
        print(f"         → POST /api/{CONFIG["api_version"]}/query-transformation → {endpoint_timing.duration_ms:.2f}ms ({endpoint_timing.status_code})")

    timing.total_duration_ms = (time.perf_counter() - overall_start) * 1000
    timing.success = all(e.success for e in timing.endpoint_timings)

    if verbose:
        print_access_complete(access_id, timing.total_duration_ms, timing.success)

    return timing


async def run_concurrent_accesses(num_accesses: int, titles_limit: int, base_url: str,
                                  timeout: float, verbose: bool = True) -> List[AccessTiming]:
    """Run multiple concurrent accesses, each with randomly selected test data."""
    client = AccessTestClient(base_url, timeout)

    print(f"\n{'='*80}")
    print(f"Running {num_accesses} concurrent accesses (each with random test data)...")
    print(f"{'='*80}\n")

    tasks = []
    for i in range(num_accesses):
        # Each concurrent access gets different random test data
        test_entry = random.choice(TEST_DATA)
        task = run_single_access(client, access_id=i, repetition=0,
                                query=test_entry['query'],
                                vufind_url=test_entry['vufind_url'],
                                titles_limit=titles_limit,
                                verbose=verbose)
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    timings = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Handle unexpected exceptions
            timing = AccessTiming(access_id=i, repetition=0)
            timing.endpoint_timings.append(EndpointTiming(
                endpoint="[unknown]",
                duration_ms=0,
                status_code=0,
                success=False,
                error_message=str(result)
            ))
            timing.success = False
            timings.append(timing)
            print(f"[ERROR] Access #{i} failed with exception: {result}")
        else:
            timings.append(result)

    return timings


def calculate_statistics(timings: List[AccessTiming]) -> TestResults:
    """Calculate aggregated statistics from access timings."""
    total_duration_start = time.perf_counter()

    successful = [t for t in timings if t.success]
    failed = [t for t in timings if not t.success]

    # Calculate per-endpoint statistics
    endpoint_durations: Dict[str, List[float]] = {}
    for timing in timings:
        for et in timing.endpoint_timings:
            if et.endpoint not in endpoint_durations:
                endpoint_durations[et.endpoint] = []
            if et.success:
                endpoint_durations[et.endpoint].append(et.duration_ms)

    endpoint_stats = {}
    for endpoint, durations in endpoint_durations.items():
        if durations:
            endpoint_stats[endpoint] = {
                "count": len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "mean_ms": statistics.mean(durations),
                "median_ms": statistics.median(durations),
                "stdev_ms": statistics.stdev(durations) if len(durations) > 1 else 0.0,
            }

    total_duration = time.perf_counter() - total_duration_start

    return TestResults(
        total_accesses=len(timings),
        successful_accesses=len(successful),
        failed_accesses=len(failed),
        endpoint_stats=endpoint_stats,
        total_duration_seconds=total_duration,
        accesses_per_second=len(timings) / total_duration if total_duration > 0 else 0
    )


def format_results(results: TestResults, config: dict) -> str:
    """Format test results as a readable string."""
    lines = []
    lines.append("=" * 80)
    lines.append("API ACCESS TEST RESULTS")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Test Configuration:")
    lines.append(f"  Base URL:            {config['base_url']}")
    lines.append(f"  Concurrent accesses: {config['num_concurrent_accesses']}")
    lines.append(f"  Repetitions:         {config['num_repetitions']}")
    lines.append(f"  Request timeout:     {config['request_timeout']}s")
    lines.append(f"  Test data entries:   {len(TEST_DATA)}")
    lines.append("")
    lines.append("-" * 80)
    lines.append("OVERALL RESULTS")
    lines.append("-" * 80)
    lines.append(f"Total accesses:       {results.total_accesses}")
    lines.append(f"Successful accesses:  {results.successful_accesses}")
    lines.append(f"Failed accesses:      {results.failed_accesses}")
    success_rate = (results.successful_accesses / results.total_accesses * 100
                   if results.total_accesses > 0 else 0)
    lines.append(f"Success rate:         {success_rate:.1f}%")
    lines.append("")

    lines.append("-" * 80)
    lines.append("ENDPOINT TIMINGS (in milliseconds)")
    lines.append("-" * 80)

    # Sort endpoints by mean time (slowest first)
    sorted_endpoints = sorted(results.endpoint_stats.items(),
                             key=lambda x: x[1]["mean_ms"],
                             reverse=True)

    for endpoint, stats in sorted_endpoints:
        lines.append(f"\n  {endpoint}")
        lines.append(f"    Count:   {stats['count']}")
        lines.append(f"    Min:     {stats['min_ms']:.2f}ms")
        lines.append(f"    Max:     {stats['max_ms']:.2f}ms")
        lines.append(f"    Mean:    {stats['mean_ms']:.2f}ms")
        lines.append(f"    Median:  {stats['median_ms']:.2f}ms")
        lines.append(f"    StdDev:  {stats['stdev_ms']:.2f}ms")

    lines.append("")
    lines.append("-" * 80)
    lines.append("PER-ACCESS TOTAL TIMES")
    lines.append("-" * 80)

    # Calculate total per-access time from individual access timings
    total_mean = sum(s["mean_ms"] for s in results.endpoint_stats.values()
                     if "mean_ms" in s)
    lines.append(f"\n  Estimated mean total time per access: ~{total_mean:.2f}ms")

    # Cost statistics section
    if results.cost_stats:
        lines.append("")
        lines.append("-" * 80)
        lines.append("LLM COST STATISTICS (USD)")
        lines.append("-" * 80)

        # Calculate totals
        total_cost = sum(s.get("total_usd", 0) for s in results.cost_stats.values())
        total_count = sum(s.get("count", 0) for s in results.cost_stats.values())
        num_accesses = config.get("num_concurrent_accesses", 1) * config.get("num_repetitions", 1)
        cost_per_access = total_cost / num_accesses if num_accesses > 0 else 0

        lines.append(f"\n  Total LLM cost:          ${total_cost:.6f}")
        lines.append(f"  Total LLM calls:         {total_count}")
        lines.append(f"  Total accesses:          {num_accesses}")
        lines.append(f"  Approx cost per access:  ${cost_per_access:.6f}")

        lines.append("\n  Cost by function:")
        sorted_cost_funcs = sorted(results.cost_stats.items(),
                                       key=lambda x: x[1].get("total_usd", 0),
                                       reverse=True)
        for func_name, cost_data in sorted_cost_funcs:
            lines.append(f"    {func_name}")
            lines.append(f"      Count:     {cost_data['count']}")
            lines.append(f"      Mean:      ${cost_data['mean_usd']:.6f}")
            lines.append(f"      Min:       ${cost_data['min_usd']:.6f}")
            lines.append(f"      Max:       ${cost_data['max_usd']:.6f}")
            lines.append(f"      Total:     ${cost_data['total_usd']:.6f}")
    else:
        lines.append("")
        lines.append("-" * 80)
        lines.append("LLM COST STATISTICS")
        lines.append("-" * 80)
        lines.append("\n  No cost data available (log file not found or no LLM calls)")

    lines.append("")
    lines.append("=" * 80)
    lines.append(f"Test completed at: {datetime.now().isoformat()}")
    lines.append("=" * 80)

    return "\n".join(lines)


async def run_access_test(config: dict, log_dir: str, verbose: bool = True) -> TestResults:
    """Run the complete access test."""
    print(f"\n{'='*80}")
    print("nsis API ACCESS TEST")
    print(f"{'='*80}")
    print("\nConfiguration:")
    print(f"  Target URL:            {config['base_url']}")
    print(f"  Concurrent accesses:  {config['num_concurrent_accesses']}")
    print(f"  Repetitions:           {config['num_repetitions']}")
    print(f"  Request timeout:      {config['request_timeout']}s")
    print(f"  Test data entries:     {len(TEST_DATA)}")
    print(f"  Verbose output:       {verbose}")
    print(f"  Log directory:        {log_dir}")
    print()

    all_timings: List[AccessTiming] = []
    test_start = time.perf_counter()
    test_start_dt = datetime.now(timezone.utc)

    for rep in range(config['num_repetitions']):
        if config['num_repetitions'] > 1:
            print(f"\n{'='*80}")
            print(f"REPETITION {rep + 1}/{config['num_repetitions']}")
            print(f"{'='*80}\n")

        timings = await run_concurrent_accesses(
            num_accesses=config['num_concurrent_accesses'],
            titles_limit=config['test_titles_limit'],
            base_url=config['base_url'],
            timeout=config['request_timeout'],
            verbose=verbose
        )

        # Update access_ids to be unique across repetitions
        for t in timings:
            t.repetition = rep

        all_timings.extend(timings)

        if config['num_repetitions'] > 1 and rep < config['num_repetitions'] - 1:
            if verbose:
                print(f"\nPausing {config['repetition_delay']}s before next repetition...\n")
            await asyncio.sleep(config['repetition_delay'])

    test_end_dt = datetime.now(timezone.utc)
    total_test_duration = time.perf_counter() - test_start

    # Parse performance logs for cost statistics
    if verbose:
        print("\nParsing performance logs for cost data...")

    # Calculate statistics
    results = calculate_statistics(all_timings)
    results.total_duration_seconds = total_test_duration

    # Parse cost stats from log file
    results.cost_stats = parse_llm_cost_stats(log_dir, test_start_dt, test_end_dt)

    if verbose:
        print(f"\n{'='*80}")
        print("ALL ACCESSES COMPLETED")
        print(f"{'='*80}")

    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point for the access test."""
    # Run the async access test with verbose output
    results = asyncio.run(run_access_test(
        CONFIG,
        log_dir=CONFIG["log_dir"],
        verbose=True,
    ))

    # Format and print summary results
    output = format_results(results, CONFIG)
    print("\n" + output)

    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("tests/access_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"access_test_results_{timestamp}.txt"
    output_file.write_text(output)
    print(f"\nResults saved to: {output_file}")

    # Exit with appropriate code
    if results.failed_accesses > 0:
        print(f"\nWARNING: {results.failed_accesses} accesses failed!")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())