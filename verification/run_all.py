"""Reproduce the checks supporting the compiler and its finite comparison.

Default: exact compiler/arithmetic checks and a small matched quench.
--full: the complete N=8,12,16,20 benchmark and accuracy sweeps.
Run from any working directory. No network access or quantum package is used.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def run_json(name: str, *arguments: str) -> dict:
    environment = os.environ.copy()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        environment[key] = "1"
    result = subprocess.run(
        [sys.executable, str(ROOT / name), *arguments],
        cwd=ROOT, env=environment, text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    start = time.perf_counter()

    streaming = run_json("gauss_streaming_verify.py")
    require(streaming["max_l2_error"] < 1e-11, "Streaming state mismatch")
    require(all(c["link_garbage_probability"] == 0
                and c["final_prefix_nonzero_probability"] == 0
                for c in streaming["cases"]), "Exact compiler left garbage")
    require(streaming["diagnostic_bad_uncompute"]["nonzero_link_garbage_probability"] > 1e-3,
            "Old-matter negative control did not fail")

    parallel = run_json("gauss_parallel_cache_verify.py")
    require(parallel["max_l2_error"] < 1e-11, "Parallel cache state mismatch")
    require(all(c["dirty_cache_probability"] == 0 for c in parallel["cases"]),
            "Invariant cache left garbage")
    require(parallel["wrong_full_prefix_cache_witness"]["dirty_cache_probability"] > 1e-3,
            "Internal-prefix negative control did not fail")

    arithmetic = run_json("verify_controlled_increment.py")
    require(arithmetic["status"] == "pass" and arithmetic["clean_basis_cases"] == 8184,
            "Controlled-increment exhaustive check changed")
    resources = run_json("reconstruction_resources.py")
    saved_resources = json.loads((ROOT / "results/reconstruction_resource_results.json").read_text())
    require(resources == saved_resources, "Deterministic reconstruction census changed")

    benchmark = run_json("schwinger_benchmark.py", *([] if options.full else ["--pilot"]))
    validations = benchmark["implementation_validation"]
    require(max(c["state_l2_error_against_independent_split"] for c in validations) < 1e-11,
            "MPS disagrees with independent split-product circuit")
    require(max(c["sparse_exponential_vs_dense_eigendecomposition_error"] for c in validations) < 1e-11,
            "Sparse reference disagrees with dense diagonalization")
    summary_cases = []
    for case in benchmark["cases"]:
        require(case["exact_norm_error"] < 1e-10, "Reference state lost norm")
        require(case["exact_direct_vs_two_half_steps_state_error"] < 1e-10,
                "Sparse reference failed its time-splitting check")
        best = min(case["mps_runs"], key=lambda run: run["density_absolute_error"])
        require(best["density_absolute_error"] < case["target_density_additive_error"],
                "No MPS run achieved the specified density accuracy")
        summary_cases.append({
            "sites": case["parameters"]["sites"],
            "reference_density": case["exact_density"],
            "best_density_error": best["density_absolute_error"],
        })

    if options.full:
        saved_benchmark = json.loads((ROOT / "results/schwinger_benchmark_results.json").read_text())
        for current, saved in zip(benchmark["cases"], saved_benchmark["cases"], strict=True):
            require(current["parameters"] == saved["parameters"], "Benchmark input changed")
            require(abs(current["exact_density"] - saved["exact_density"]) < 1e-10,
                    "Reference density changed")
            for actual_run, saved_run in zip(current["mps_runs"], saved["mps_runs"], strict=True):
                require(abs(actual_run["density"] - saved_run["density"]) < 1e-9,
                        "Recorded MPS density changed beyond numerical tolerance")
        case16 = next(c for c in benchmark["cases"] if c["parameters"]["sites"] == 16)
        step_runs = sorted(
            (r for r in case16["mps_runs"] if r["maximum_bond_requested"] == 64),
            key=lambda r: r["steps"],
        )
        for coarse, fine in zip(step_runs, step_runs[1:]):
            ratio = coarse["density_absolute_error"] / fine["density_absolute_error"]
            require(3.8 < ratio < 4.2, "Second-order step-size convergence was lost")
        bad = next(r for r in case16["mps_runs"] if r["maximum_bond_requested"] == 4)
        require(bad["density_absolute_error"] > 1e-2, "Low-bond negative control changed")

    report = {
        "status": "pass",
        "mode": "full" if options.full else "quick",
        "python": platform.python_version(),
        "streaming_max_state_error": streaming["max_l2_error"],
        "parallel_max_state_error": parallel["max_l2_error"],
        "controlled_increment_basis_cases": arithmetic["clean_basis_cases"],
        "resource_census_matches_committed_output": True,
        "matched_quench_cases": summary_cases,
        "elapsed_seconds": time.perf_counter() - start,
        "scope": (
            "Finite exact-block identities, reversible arithmetic, declared reconstruction "
            "layouts, and classical quench accuracy. Does not test the HHKL asymptotic "
            "proof, a complete fault-tolerant block implementation, routing, or quantum advantage."
        ),
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
