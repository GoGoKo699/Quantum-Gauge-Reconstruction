# Benchmarks and the limits of the evidence

The verification suite supports three distinct conclusions: temporary Gauss reconstruction implements the specified native block factors correctly; its declared register layouts and reversible arithmetic can be counted explicitly; and a small, completely specified Schwinger quench is accurately solvable by a classical matrix product state (MPS). **The finite quench is a classically tractable control, not evidence of a quantum advantage.**

The mathematical compiler statement is in [the streaming theorem](streaming_gauss_theorem.md), its coherent implementation requirements are in [coherent native blocks](coherent_native_blocks.md), and its finite symbolic costs are in [the resource comparison](finite_resource_comparison.md). Numerical agreement does not replace those arguments. Reproduction instructions and the executable checks are in [verification](../verification/README.md).

## A fully specified finite task

Take an even number $`N`$ of staggered matter sites with open boundaries. Occupations are $`b_j\in\{0,1\}`$, and the incoming electric flux is fixed to $`e_0=0`$. Define

```math
q_j=b_j-(j\bmod 2),\qquad
E_j=e_0+\sum_{k=0}^{j}q_k,\qquad j=0,\ldots,N-2.
```

The Hamiltonian below is the matter-only representation after exact Gauss-law elimination for this open chain and fixed incoming flux. A native hopping term also shifts its electric link. In this physical basis, that shift is determined by the change in matter occupations, so the displayed hopping term has no independent link operator.

```math
\begin{split}
H={}&w\sum_{j=0}^{N-2}
  \bigl(\sigma_j^+\,\sigma_{j+1}^-+\sigma_j^-\,\sigma_{j+1}^+\bigr)\\
  &+m\sum_{j=0}^{N-1}(-1)^j b_j
  +J\sum_{j=0}^{N-2}(E_j+\alpha)^2.
\end{split}
```

The benchmark fixes the following inputs:

| Quantity | Value |
|---|---|
| Sizes | $`N=8,12,16,20`$ |
| Initial matter state | Néel product, $`b_j=j\bmod2`$ |
| Charge sector | Zero total charge |
| Quench at time zero | Hopping changes from $`w=0`$ to $`w=1`$ |
| Parameters held fixed | $`m=0.2`$, $`J=0.5`$, $`\alpha=0.5`$, $`e_0=0`$ |
| Evolution time | $`t=2`$, with $`\hbar=1`$ |
| Required output accuracy | Additive error $`10^{-3}`$ |

The initial state is an exact ground state before the quench. The positive staggered mass is uniquely minimized by occupying every odd site, and each integer-flux electric term is at least $`J/4`$, attained by $`E_j=0`$. Preparing this state from zero matter bits takes exactly $`N/2`$ X gates. No ground-state preparation oracle is assumed.

The output is the bounded staggered excitation density

```math
R(t)=\frac1N\sum_{j=0}^{N-1}
\Pr\!\left[b_j(t)\ne j\bmod2\right],\qquad 0\le R(t)\le1.
```

This is a finite-lattice task in the stated units. The error target does not include a continuum or thermodynamic extrapolation. The benchmark does not estimate an entire state vector as its scientific output.

## Matched classical methods

### Sparse numerical reference

The reference explicitly constructs the Hamiltonian in the neutral occupation sector, whose dimension is $`\binom{N}{N/2}`$. SciPy's `expm_multiply` applies the matrix exponential to the Néel state. A full-time application is compared with two half-time applications. For smaller chains, an independent dense Hermitian eigendecomposition checks the same exponential.

This is a high-accuracy floating-point reference, not an interval-arithmetic certificate. The recorded state norm and independent checks quantify its observed numerical consistency.

### Charge-resolved MPS

The comparator stores integer prefix-charge labels on MPS bonds. Its tensor entries obey

```math
q_{\mathrm{right}}=q_{\mathrm{left}}+q_{\mathrm{site}}.
```

The electric phase for a link is therefore a phase on the corresponding outgoing bond-charge sector. Mass and electric evolution are applied exactly within this representation without increasing the bond dimension. Hopping uses explicit two-site number-preserving gates. The time step is a symmetric second-order product of diagonal evolution and disjoint even/odd hopping layers:

```math
U_{\Delta t}
=D(\Delta t/2)\,
 E(\Delta t/2)\,
 O(\Delta t)\,
 E(\Delta t/2)\,
 D(\Delta t/2).
```

Each truncation is a Schmidt decomposition in mixed-canonical form, performed separately in each charge sector. The largest singular values across sectors are retained up to the chosen bond limit. The implementation separately varies time step and bond dimension.

If $`w_k`$ is the normalized discarded Schmidt weight at truncation $`k`$, then, in exact arithmetic,

```math
\min\!\left(1,\sum_k\sqrt{w_k}\right)
```

bounds the error of a $`[0,1]`$ observable relative to the same untruncated split product. This follows from the pure-state trace distance of each normalized truncation and the triangle inequality. It does not include splitting or floating-point error. The suite records this bound and also compares the actual density directly with the sparse reference.

Density evaluation contracts MPS environments. It neither calls the exact solver nor requires conversion to a dense state. The benchmark additionally performs dense conversion at these small sizes to check state fidelity and charge conservation; that conversion is validation work, not part of the scalar MPS estimator.

Gauge-resolved MPS and real-time Schwinger calculations have substantial prior work. They are an essential comparator here, rather than an unexplored classical alternative: see [Vidal (2004)](https://doi.org/10.1103/PhysRevLett.93.040502), [Buyens et al. (2014)](https://doi.org/10.1103/PhysRevLett.113.091601), and [Buyens et al. (2017)](https://doi.org/10.1103/PhysRevD.96.114501).

## Recorded matched-accuracy results

The complete data, including all parameter sweeps, numerical diagnostics and separately labeled timing fields, are in [schwinger_benchmark_results.json](../verification/results/schwinger_benchmark_results.json).

| $`N`$ | Neutral-sector dimension | Reference density | MPS bond limit | Steps | Density absolute error |
|---:|---:|---:|---:|---:|---:|
| 8 | 70 | 0.294514779012 | 16 | 128 | 1.010e-5 |
| 12 | 924 | 0.320641462959 | 32 | 128 | 8.504e-6 |
| 16 | 12,870 | 0.333631328606 | 64 | 128 | 7.755e-6 |
| 20 | 184,756 | 0.341425277272 | 64 | 128 | 7.306e-6 |

At $`N=16`$ and bond limit 64, using 16, 32, 64 and 128 steps gives density errors 4.957e-4, 1.241e-4, 3.102e-5 and 7.755e-6. The approximately fourfold improvement under each step doubling is consistent with second-order convergence.

The bond sweep is a meaningful failure control. At $`N=16`$ and 128 steps, bond limit four gives density error 0.1361. Bond limits 8, 16, 32 and 64 give errors 7.479e-4, 6.305e-6, 7.755e-6 and 7.755e-6. Limits 32 and 64 differ in density by about 4.03e-10. A single acceptable scalar at bond limit eight would not establish convergence: its state error is about 0.186 and its cumulative truncation bound is about 0.656.

At $`N=20`$, bond limit 32 with 64 steps already reaches density error 2.922e-5. With 128 steps, increasing the limit from 32 to 64 changes the density by only 2.72e-10. The bond-64 truncation-only bound is 2.621e-6, below the task tolerance.

Independent checks give:

| Check | Recorded maximum state error |
|---|---:|
| Untruncated MPS versus independently implemented split product, six small-chain cases | 6.58e-15 |
| Sparse exponential versus independent dense eigendecomposition | 4.38e-15 |
| Full-time versus two half-time sparse exponential applications | 4.24e-15 |

These results show that the chosen task is classically tractable and that the observable can converge much more readily than the full state. They do not justify extrapolating a classical exponential cost from the state-vector dimension, or predicting a quantum crossover from small-system runtimes.

## Exact block-product and cache checks

The compiler checks are separate from the quench benchmark. They compare independently constructed native-link block matrices, with explicit electric-link shifts, against the corresponding eliminated-basis block matrices. They test an exact product of specified blocks; they do not numerically certify the HHKL approximation to the full Hamiltonian.

- **Streaming:** twelve cases at $`N=3,\ldots,8`$, with random complex states in neutral and unrestricted charge sectors, overlapping and nonmonotone block orders, and positive and negative evolution times. Maximum final state error is 5.60e-16, with zero link and final-prefix garbage in the tested exact construction.
- **Conserved cache:** disjoint block layers at $`N=3,\ldots,8`$ retain complete block charges, boundary prefixes and sum-tree nodes. Maximum state error is 3.65e-16; the cache clears.
- **Incorrect old-matter uncomputation:** a two-site example leaves garbage probability 0.06189937.
- **Incorrect retained internal prefixes:** a six-site Néel example leaves garbage probability 0.06643694. Within-block partial prefixes must be erased before the block evolves.

The failing constructions are intentional negative controls. Passing finite examples supports implementation consistency; the general cleanup claim rests on the charge-conservation and isometry arguments in the theorem.

## What the arithmetic census measures

[reconstruction_resources.py](../verification/reconstruction_resources.py) counts the actual register allocation and X/CNOT/Toffoli operations of a specified reconstruction layout. It uses the common explicit controlled increment: $`2(B-1)`$ Toffoli, $`B`$ CNOT and $`B-1`$ clean carry bits. The general register adder is constructed from suffix increments and is not claimed optimal. Both construction and uncomputation are counted.

For this staggered chain, every prefix and contiguous-interval charge is bounded in magnitude by $`\lceil N/2\rceil`$. The census chooses a signed width whose positive range contains $`\lceil N/2\rceil+|e_0|`$. Thus $`B=13`$ is safe at $`N=4096,e_0=0`$; the coarser bound using $`N`$ would request another bit.

The default block size is $`\min(N,8B)`$. This illustrates storage scaling and is **not an HHKL error-certified choice**. Native block-simulator workspace is an explicit input, defaulting to zero to isolate reconstruction overhead. Under that default, the recorded examples are:

| $`N`$ | $`B`$ | Block size | Persistent matter+links | Streaming layout bits | Conserved-cache layout bits | Cache batches |
|---:|---:|---:|---:|---:|---:|---:|
| 128 | 8 | 64 | 1,144 | 655 | 695 minimum; exceeds 3N | Does not fit |
| 1,024 | 11 | 88 | 12,277 | 2,013 | 2,508 | 12 |
| 4,096 | 13 | 104 | 57,331 | 5,473 | 11,606 | 10 |
| 65,536 | 17 | 136 | 1,179,631 | 67,881 | 196,054 | 12 |

At $`N=4096`$, one streaming reconstruction layer uses 391,248 Toffoli, 318,396 CNOT and 16,300 X gates. The cache layout uses 417,504 Toffoli, 336,674 CNOT and 16,380 X gates. These are added arithmetic costs, not complete simulation counts. The general per-layer streaming bounds and native-width comparison are derived in [finite_resource_comparison.md](finite_resource_comparison.md).

The [workspace sensitivity record](../verification/results/reconstruction_workspace_sensitivity.json) adds an allowance of 1,024 native-workspace bits per active block. At $`N=4096`$, streaming then uses 6,485 bits; the cache requires 20 batches with 10,902 peak bits. At $`N=1024`$, the cache cannot fit its declared $`3N`$ budget: even one active block requires 3,522 bits. These finite-size failures are retained in the data.

The census excludes native simulation gates, an error-certified factor schedule, logical synthesis, fault-tolerant T counts, physical routing, magic-state supply, and wall-clock runtime. It also excludes preparation, scalar readout and amplitude-estimation repetitions unless those costs are added separately. The `--repetitions` option repeats only the declared reconstruction layer; it does not establish a simulation-accuracy guarantee.

## Evidence boundary

The exact arithmetic and invariant arguments establish the compiler's stated representation change under its assumptions. The numerical checks test independent implementations and concrete failure cases. The quench study supplies a strong classical comparator at matched accuracy. None of these experiments demonstrates quantum advantage or identifies a classically difficult long-time regime. A practical complete comparison still needs the certified native simulator and schedule, coherent error accounting, output-estimation costs, and a converged classical method for the same physical task.
