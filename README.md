# Quantum Gauge Reconstruction

**Can a quantum simulation keep the locality of an explicit gauge field without storing that field throughout the computation?** For an open one-dimensional Schwinger chain, Gauss's law makes each electric field a prefix sum of the matter charges. This repository constructs those fields only while a local simulation block needs them, then reversibly erases them using the updated matter state.

The result is a compiler for the existing HHKL and interaction-picture simulation algorithm. It preserves near-linear spacetime gate scaling while reducing serial storage to the matter qubits plus polynomial-logarithmic workspace. Preparation and a scalar density readout fit the same scaling. A matched classical benchmark is included; it does **not** demonstrate a quantum–classical crossover.

## Main result

For N matter sites, fixed incoming flux and an open boundary, the physical electric field is

```math
E_j=e_{\mathrm L}+\sum_{k=0}^{j}(z_k-s_k),\qquad s_k=k\bmod 2.
```

Apply the locality decomposition in the native matter-and-gauge representation. For each factor, reconstruct its local links, run the native block circuit, and uncompute the links. A streaming prefix cursor or an invariant coarse-prefix cache supplies the incoming flux coherently. All flux-dependent phases are retained.

Let $`r=\max\{1,\lceil |w|t\rceil\}`$ and let P be the explicit bit-length and precision parameter in [Theorem 5](science/streaming_gauss_theorem.md#8-resource-theorem-with-explicit-precision-dependence). The proved conservative bounds are:

| Implementation | Primitive gates | Total logical qubits | Logical depth |
|---|---:|---:|---:|
| Serial prefix cursor | $`O(NrP^5)`$ | $`N+O(P^2)`$ | $`O(NrP^5)`$ |
| Batched local layers | $`O(NrP^5)`$ | $`O(N)+O(P^2)`$ | $`O(rP^7)`$ |

The primitives are Toffoli, CNOT and bounded-arity known-angle phase gates. Finite universal gate synthesis adds precision factors. Parallel depth assumes all-to-all logical connectivity. The exponents are explicit upper bounds, not optimized finite T-count forecasts.

For a specified product-state quench and normalized excitation density to additive error $`\epsilon`$, coherent amplitude estimation gives the complete logical gate bound

```math
\widetilde O\!\left(\frac{N(1+|w|t)}{\epsilon}\right),
```

including product-state preparation, reversible counting, inverse circuits, reflections and output. The soft-O notation suppresses precision and confidence logarithms under the stated input assumptions. [The complete task and error budget](science/estimation.md) specify exactly what is estimated.

## What changes in the comparison

The fastest native algorithm already has near-linear spacetime gates. The compiler removes permanent link storage while using the same native block simulator. For a fixed certified factor schedule, common b-bit field representation, largest local link count $`L_{\max}`$ and native workspace a,

```math
\begin{aligned}
Q_{\mathrm{native}}&=N+(N-1)b+a,\\
Q_{\mathrm{stream}}&\le N+(L_{\max}+1)b+\max(a,b-1).
\end{aligned}
```

Each disjoint layer adds at most $`8N(b-1)`$ Toffoli gates, $`6Nb`$ CNOTs and $`8N+2b`$ X gates. These are explicit reconstruction costs; native simulation costs remain part of the total. [Finite comparison and arithmetic](science/finite_resource_comparison.md)

A straightforward matter-only global interaction-picture construction uses approximately $`N^2|w|t`$ gates up to logarithms. The compiler removes one extensive factor relative to that specified construction, while retaining low width. This is not a lower bound on every eliminated-Hamiltonian algorithm. Product formulas, state-dependent cutoffs and other structured encodings remain relevant competitors. [Comparison and limitations](science/interpretation.md) · [Primary literature](references/RELATED_WORK.md)

## Evidence

The repository separates the mathematical construction from its finite numerical checks:

- **Proofs:** exact Gauss reconstruction and cleanup, the correct whole-term block boundaries, native hopping and electric-phase circuits, coherent approximation with reused scratch, serial and batched resource bounds, and preparation-to-output estimation costs.
- **Compiler checks:** exact small-system block products, overlapping and reverse-time factors, coherent incoming-flux sectors, and an invariant-cache implementation. Deliberately stale prefixes and inappropriate retained caches are negative controls.
- **Arithmetic:** exhaustive controlled-increment and cleanup checks for widths 1 through 10, covering 8,184 basis cases.
- **Classical benchmark:** charge-resolved MPS evolution against sparse exact evolution for open chains with 8, 12, 16 and 20 sites, separate time-step and bond-dimension sweeps, and independent dense/split checks. The reported short-time regime is classically tractable.

[Benchmark parameters, results and caveats](science/benchmarks.md) · [Verification commands and committed outputs](verification/README.md)

## Read and reproduce

| Question | Authoritative source |
|---|---|
| What is the model, and why does cleanup work? | [Compiler theorem](science/streaming_gauss_theorem.md) |
| What are the actual native circuit ingredients? | [Coherent native blocks](science/coherent_native_blocks.md) |
| What are the finite width and arithmetic savings? | [Finite resource comparison](science/finite_resource_comparison.md) |
| What is prepared and measured, and how is error allocated? | [Density estimation](science/estimation.md) |
| What does this establish against quantum and classical alternatives? | [Resource interpretation](science/interpretation.md) |
| What was numerically tested? | [Benchmarks](science/benchmarks.md) |
| Which prior results are inherited? | [Related work](references/RELATED_WORK.md) and [BibTeX](references/references.bib) |

From the repository root, using Python 3.12 and the pinned numerical dependencies:

```bash
python -m pip install -r verification/requirements.txt
python verification/run_all.py --full
```

The default command without `--full` uses a smaller quench case while retaining the exact compiler, arithmetic and census checks. The [verification guide](verification/README.md) describes dependencies, individual scripts and the meaning of each check.

## Learning route

The educational anchor is **Andrew M. Childs, [Lecture Notes on Quantum Algorithms](https://www.cs.umd.edu/~amchilds/qa/qa.pdf), 17 April 2025**. The [source bridge](learning/anchor_bridge.md) translates its circuit, error and simulation foundations into this project's gauge-constrained setting, including a four-site worked example. The [30-milestone map](learning/milestones.md) connects those foundations to the compiler, its complete scalar-output contract and the classical comparison. [Start the learning route](learning/README.md).

## Scope and open work

The result is for a one-dimensional open chain with known incoming flux. Fixing outgoing flux as well selects a total-charge sector. The theorem includes numerical input precision and coherent error; it does not assume a supplied interacting ground state or QRAM.

No classical lower bound, hardware crossover, complete finite fault-tolerant T-count, nearest-neighbor routing result, or periodic/higher-dimensional/non-Abelian extension is established. A useful finite width gain needs a certified block length substantially below the chain length. A fixed small physical flux cutoff can already make native storage linear in N. At fixed physical volume, lattice spacing changes the hopping strength and therefore the apparent N scaling. These limitations are part of the result.

## Purpose and contact

This repository serves as a record of the work and a guide for the author’s self-directed learning. For discussion or potential collaboration, please contact Ruge Lin at [gogoko699@gmail.com](mailto:gogoko699@gmail.com).

The repository is distributed under the [MIT License](LICENSE).
