# Resource meaning and the classical comparison

The central result concerns the cost of storing and reconstructing a constrained quantum state. Gauss's law makes the electric field a function of matter charges on an open chain. The compiler uses geometric locality in the native representation while storing the matter-only representation between local factors.

## The finite consequence

For one fixed certified local-factor schedule, let $`b`$ be the common field-register width, $`L_{\max}`$ the largest number of links used by a factor, and $`a`$ its maximum auxiliary simulator width. Serial execution in the native representation uses

```math
Q_{\mathrm{native}}=N+(N-1)b+a.
```
The reconstructed implementation uses at most

```math
Q_{\mathrm{reconstruct}}
\le N+(L_{\max}+1)b+\max(a,b-1).
```
The extra $`b`$-bit register is the streamed incoming flux; the $`b-1`$ carry bits share storage with the simulator workspace. The exact finite saving is positive when

```math
(N-2-L_{\max})b>\max(0,b-1-a).
```
For each disjoint spatial layer, the chosen arithmetic adds at most $`8N(b-1)`$ Toffoli gates, $`6Nb`$ CNOT gates and $`8N+2b`$ X gates. Native block costs remain explicit inputs to the comparison. See [the finite resource theorem](finite_resource_comparison.md) for the construction and counting convention.

This statement is useful even when a complete fault-tolerant gate count is unavailable: it identifies exactly which persistent registers are removed and exactly which additional arithmetic is required for the same target factors and accuracy. It does not assume an uncharged oracle or a guessed locality constant.

## Why the asymptotic comparison matters

The native HHKL/interaction-picture algorithm already has near-linear spacetime gate complexity. This compiler preserves that scaling with $`N+\operatorname{polylog}`$ serial width, or $`O(N)+\operatorname{polylog}`$ width with the stated parallel construction. The nearest stored-field encoding requires $`\Theta(N\log\Lambda)`$ qubits for matter and fields when each link has range $`\Lambda`$.

The strongest published or applicable quantum comparator depends on the parameter regime. A concrete eliminated global interaction-picture construction has near-$`N^2|w|t`$ gates and low width. The spatial compiler removes one extensive factor relative to that construction. Product formulas, state-dependent truncation and other encodings may improve particular regimes; no universal low-width lower bound is asserted.

If a small fixed field cutoff is already accurate, native storage is itself linear in $`N`$. The asymptotic logarithmic storage improvement then becomes a finite constant comparison. If a certified HHKL interval fills most of the chain, temporary reconstruction may save little or no width. The finite inequality above exposes both cases.

## The correct classical competitors

The input/output contract is a specified quench and a bounded scalar density. Relevant classical methods include charge-resolved matrix product states, time-dependent variational methods, structured matrix product operators for the eliminated interaction, observable-focused contraction, finite causal windows, and controlled semiclassical limits. Dense state-vector evolution supplies a small-system reference, not a universal classical baseline.

The gauge constraint is useful classically too. In a charge-resolved MPS, virtual bond labels identify prefix charges. Electric phases can then be applied from those labels without expanding an independent field Hilbert space. This established structure is used by the [finite benchmark](benchmarks.md), following the gauge-MPS and real-time Schwinger literature cited in [Related work](../references/RELATED_WORK.md).

At fixed time after a homogeneous product quench, a local bulk observable can often be approximated using only its causal region. Spatial averaging can exploit translation symmetry or self-averaging. Increasing the total chain length alone therefore does not establish increasing classical difficulty for this output.

Large state entanglement is likewise insufficient to prove that a particular density is hard to compute. The required bond dimension is determined by the actual evolution, observable and error target. A state-norm approximation can be much more demanding than one accurate expectation value.

## What the benchmark establishes

The committed benchmark specifies an open chain, a bare staggered-vacuum input, lattice couplings and a single output. It compares a charge-resolved MPS with sparse matrix-exponential evolution in the complete neutral sector. Separate step-size and bond-dimension sweeps test the relevant numerical errors.

The tested short-time regime is classically tractable. This is positive evidence for a usable comparator and a verified finite task, and provides no evidence of a quantum–classical crossover. Small-system timings are not extrapolated into a hardness statement.

For a prospective advantage test, let $`C_{\mathrm{cl}}(N,t,\epsilon)`$ denote the best validated classical cost under the same access and output contract. Under the low-width quantum implementation constraint, the compiler changes one quantum candidate's cost from near $`N^2|w|t/\epsilon`$ to near $`N|w|t/\epsilon`$. A crossover claim still needs the constants, a certified block schedule, a fault-tolerant architecture and an appropriate classical benchmark. The present result establishes the changed quantum resource comparison.

## Scope

The simple reconstruction uses a one-dimensional open chain and known incoming flux. Fixing the outgoing flux as well selects a conserved total-charge sector. Periodic boundaries have an additional global flux degree of freedom, and higher dimensions have independent transverse gauge degrees of freedom.

The depth result assumes all-to-all logical connectivity. Routing and error correction have not been folded into the asymptotic logical gate count. The finite reconstruction census separately states whether native simulator workspace is included.

The model, proof and error budgets are authoritative for the stated compiler. The numerical checks validate their specified finite circuits and benchmark; they do not certify priority, unrestricted optimality, physical runtime or publication significance.
