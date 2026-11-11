# Verification and reproduction

This directory checks the temporary Gauss-reconstruction compiler, its reversible arithmetic and declared register layouts, and a finite Schwinger-quench density calculation with a classical MPS comparator. The scientific task, results and limitations are described in [science/benchmarks.md](../science/benchmarks.md).

The checks do not establish quantum advantage, compile a complete fault-tolerant native simulator, or numerically certify an HHKL block schedule.

## Run the suite

The recorded environment uses Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0. The latter two versions are pinned in [requirements.txt](requirements.txt). From the repository root:

```bash
python -m pip install -r verification/requirements.txt
python verification/run_all.py
python verification/run_all.py --full
```

The runner locates its scripts relative to its own file, so it can also be invoked by its full path from another working directory. It sets `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS` and `MKL_NUM_THREADS` to one for its child processes. Once dependencies are installed, the checks need no network access, quantum package, external data or Hamiltonian oracle.

Both modes print a JSON summary. A failed subprocess, numerical assertion or recorded-result comparison exits with an error. Successful output includes `"status": "pass"`. To save the summary as well as print it:

```bash
python verification/run_all.py --full --output run-report.json
```

`--output` writes the summary report, not the complete raw outputs of every component. Relative output paths are interpreted from the invoking working directory. The runner does not otherwise replace the committed result files. Timings are informational and are not required to reproduce exactly.

### Quick mode

`python verification/run_all.py` runs:

1. Exact streaming block-product checks, including link/prefix cleanup and a failing old-matter uncomputation.
2. Exact conserved-cache checks and a failing retained-internal-prefix construction.
3. The standalone controlled-increment verification: 8,184 clean basis cases across widths one through ten.
4. The reconstruction census, including its own arithmetic checks, with exact equality against the committed deterministic JSON.
5. A small $`N=12`$ quench with several MPS time-step/bond settings, plus the independent small-chain MPS and sparse-exponential implementation checks.

At least one MPS run must attain the declared density tolerance. Norm and sparse-reference consistency checks must also pass.

### Full mode

`python verification/run_all.py --full` includes all the checks above and replaces the pilot quench with the complete $`N=8,12,16,20`$ study. It checks the recorded physical parameters and densities, the separate time-step and bond-dimension sweeps, and the deliberately inadequate bond-four calculation.

The executable acceptance thresholds include:

| Check | Required tolerance or condition |
|---|---|
| Streaming and parallel block-product state error | Less than 1e-11 |
| Exact-construction link/cache garbage | Zero in the tested numerical construction |
| Incorrect old-matter and internal-prefix cleanup controls | Garbage probability greater than 1e-3 |
| MPS versus independent split product | State error less than 1e-11 |
| Sparse exponential versus dense eigendecomposition | State error less than 1e-11 |
| Sparse-reference norm and full-time/two-half-time agreement | Error less than 1e-10 |
| Full-mode reference density versus committed value | Difference less than 1e-10 |
| Full-mode MPS density versus committed value | Difference less than 1e-9 |
| $`N=16`$ time-step error ratios | Between 3.8 and 4.2 under each step doubling |
| $`N=16`$, bond-four negative control | Density error greater than 1e-2 |

These thresholds are implementation checks, not analytic error bounds for arbitrary input states, times or lattice sizes.

## Components

| File | Purpose |
|---|---|
| [run_all.py](run_all.py) | Quick/full entry point, assertions, comparisons and summary report |
| [gauss_streaming_verify.py](gauss_streaming_verify.py) | Independent native-link versus eliminated-basis block products at $`N=3,\ldots,8`$ |
| [gauss_parallel_cache_verify.py](gauss_parallel_cache_verify.py) | Conserved block-total/prefix-tree cache cleanup and an incorrect full-prefix control |
| [verify_controlled_increment.py](verify_controlled_increment.py) | Explicit linear carry-chain increment, staggered charge updates and inverses |
| [reconstruction_resources.py](reconstruction_resources.py) | Exact declared register allocation and X/CNOT/Toffoli census |
| [schwinger_mps.py](schwinger_mps.py) | Neutral-sector sparse Hamiltonian and explicit charge-resolved MPS |
| [schwinger_benchmark.py](schwinger_benchmark.py) | Independent implementation checks and matched-accuracy quench sweeps |
| [results/](results/) | Recorded raw outputs and a compact validation summary |

### Run individual components

Each component prints a JSON document. These commands, from the repository root, write new local records without replacing the committed baselines:

```bash
python verification/gauss_streaming_verify.py > streaming-check.json
python verification/gauss_parallel_cache_verify.py > cache-check.json
python verification/verify_controlled_increment.py > arithmetic-check.json
python verification/reconstruction_resources.py > reconstruction-census.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python verification/schwinger_benchmark.py > quench-benchmark.json
```

The full quench is the default for `schwinger_benchmark.py`; add `--pilot` for its smaller $`N=12`$ configuration. The main runner sets thread limits automatically, while direct benchmark invocations should set them explicitly if reproducible timing conditions matter.

To reproduce the native-workspace sensitivity experiment:

```bash
python verification/reconstruction_resources.py --sites 1024 4096 65536 --native-workspace 1024 > workspace-sensitivity.json
```

Additional census parameters are `--block-sites`, `--left-flux`, `--width-multiple` and `--repetitions`; `--sites` accepts one or more sizes. The default width budget is $`3N`$ bits. The default block length is $`\min(N,8B)`$, chosen to illustrate storage rather than to certify an HHKL accuracy bound. `--native-workspace` is a declared number of auxiliary bits per active native block; it is not inferred from a complete compiled simulator.

The default census is compared with [reconstruction_resource_results.json](results/reconstruction_resource_results.json) by exact JSON equality. Intentional changes to its arithmetic or layout should therefore be reviewed together with new recorded results. Numerical quench comparisons use tolerances instead of exact JSON equality, and timing fields are not compared.

## Scientific scope and controls

The quench starts from the zero-charge Néel product state, changes hopping from zero to one, and holds $`m=0.2`$, $`J=0.5`$, background $`\alpha=0.5`$ and incoming flux $`e_0=0`$ fixed. It estimates the mean staggered excitation density at $`t=2`$ to additive error $`10^{-3}`$. No continuum extrapolation or difficult input-state preparation is hidden in this finite task.

The reference is a floating-point sparse exponential in the explicit neutral sector. Smaller systems are also checked by dense Hermitian eigendecomposition. The MPS has charge-labeled bonds, exact diagonal phases and a second-order hopping product. It records normalized discarded Schmidt weights and independently varies time step and bond dimension. Density is evaluated by MPS contractions; dense conversion is used only for small-system validation. These calculations show that the chosen finite task is easy for a converged classical method. Small-system timing comparisons do not predict a quantum crossover.

The exact block-product checks address a different question: whether reconstruction and updated-matter uncomputation implement the requested local factors. They do not test the accuracy of approximating full Hamiltonian evolution by an HHKL schedule. Intentional wrong implementations must fail, so the suite checks that their garbage probabilities remain nonzero.

The arithmetic census uses an explicit controlled increment with $`2(B-1)`$ Toffoli gates, $`B`$ CNOT gates and $`B-1`$ clean carries. It includes construction and uncomputation, and records cases where the cache cannot fit its declared budget. These are exact counts for the stated arithmetic and layout. They exclude native simulation gates, an accuracy-certified schedule, fault-tolerant synthesis, routing, physical qubits, magic-state production and wall-clock time. Preparation, output estimation and reflection costs must be added for a complete algorithm comparison; see [the finite comparison](../science/finite_resource_comparison.md) and [estimation](../science/estimation.md).

The mathematical compiler argument, finite Boolean checks, floating-point tests and classical task benchmark provide different kinds of evidence. None should be presented as proving the claims outside its stated scope.
