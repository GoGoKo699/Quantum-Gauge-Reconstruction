# From a specified quench to a density estimate

The simulation theorem becomes a complete computational task when its input and output are fixed. This page uses classical lattice parameters, an explicitly prepared product state, and one bounded scalar observable. The quantum and classical procedures receive the same Hamiltonian, boundary data, initial state, time and accuracy target.

## Input and output

Take an even open chain of $`N`$ staggered matter sites with the Hamiltonian and boundary convention in [the model and compiler theorem](streaming_gauss_theorem.md). The classical input specifies $`w,m,J,\theta,e_0,t`$ to finite precision. The initial occupations are $`z_j=j\bmod 2`$, so every staggered charge is zero and both exterior fluxes equal $`e_0`$ in this neutral sector. Preparation requires at most $`N/2`$ Pauli X gates on matter. It does not assume a supplied interacting ground state.

For a basis string $`z`$, define its excitation count and normalized density by

```math
c(z)=\sum_{j=0}^{N-1}\mathbf 1\{z_j\ne j\bmod 2\},
\qquad
d(z)=\frac{c(z)}{N}.
```
The requested output is an estimate of

```math
\nu(t)=
\langle\psi_0|e^{iHt}d(\hat z)e^{-iHt}|\psi_0\rangle
```
to additive error $`\epsilon`$ with success probability at least $`1-\eta`$. Here $`0\le d\le1`$. In the neutral sector, $`c`$ counts particles and antiparticles, so $`d`$ is twice the number of created pairs divided by the number of staggered sites.

The output is one number. Full-state tomography and a list of all site-resolved observables are different output contracts.

## An exact reversible flag for every N

Let

```math
k=\lceil\log_2(N+1)\rceil,\qquad
q=\lceil\log_2 N\rceil,\qquad
M=2^q.
```
Compute $`c(z)`$ into a $`k`$-bit counter using one controlled increment per site. Prepare a $`q`$-bit threshold register with Hadamard gates, giving a uniform integer $`r\in\{0,\ldots,M-1\}`$. Reversibly flip a flag when $`r\lt c(z)`$, then uncompute the count and comparator scratch.

Conditional on $`z`$, the acceptance probability is exactly $`c(z)/M`$. Therefore, for an arbitrary superposition of matter strings,

```math
p=\frac{\mathbb E[c]}{M},
\qquad
\nu=\frac{M}{N}p,
\qquad
1\le\frac{M}{N}\lt 2.
```
For powers of two the scale is exactly one. Power-of-two padding makes the construction exact for other $`N`$ as well; only a known final classical rescaling is needed.

Using the explicit increment circuit in [the finite resource comparison](finite_resource_comparison.md), computing and uncomputing the count costs

```math
4N(k-1)\ \text{Toffoli gates}
\quad\text{and}\quad
2Nk\ \text{CNOT gates},
```
plus the occupation-control X gates. The counter, carry chain, threshold register, flag and a standard reversible comparator use $`O(\log N)`$ qubits. Comparator gate cost is polynomial in $`\log N`$. The retained threshold register can remain entangled with matter and the flag: it is part of the fixed preparation circuit and its inverse.

All input access is implemented by explicit gates on the matter qubits. No quantum random-access memory is assumed.

## Simulation bias and amplitude estimation

Let $`A`$ be the complete fixed compiled unitary: product-state preparation, the reconstructed simulation, and the flag circuit. It includes every scratch register, even when approximate block simulation leaves a small coherent residue. Use the exact gate-reversed circuit $`A^\dagger`$.

Amplitude estimation estimates the acceptance probability of this implemented $`A`$. With probability at least $`1-\eta`$, an estimate of that probability to error $`\epsilon N/(2M)`$ requires

```math
O\!\left(\epsilon^{-1}\log(1/\eta)\right)
```
uses of $`A`$, $`A^\dagger`$, and the associated reflections, up to the selected estimation variant's logarithmic factors. Rescaling by $`M/N`$ contributes at most $`\epsilon/2`$ to the output error.

Choose the simulation's clean-input state error, including decomposition, local approximation and synthesis, to be at most $`\epsilon/8`$. For normalized pure states, their trace distance is at most their vector-norm difference. A bounded flag probability therefore changes by at most that state error, and the known rescaling is less than two. This leaves a conservative margin for the remaining input-rounding and synthesis errors.

The bias of one fixed compiled $`A`$ is bounded separately from the estimation error. Its compilation tolerance need not be reduced to $`\epsilon^2`$ merely because amplitude estimation invokes it many times. The exact circuit inverse is essential to this statement. Stochastic physical gate failures belong to a separate fault-tolerance error budget for the complete computation.

The reflection about the full initial state must include the matter, threshold and simulation-workspace registers. A linear-size multi-controlled reflection with one ancillary qubit is available from [Nie, Zi and Sun, Theorem 1](https://arxiv.org/abs/2402.05053). Reserve this one clean ancillary qubit outside A; potentially leaked simulation scratch cannot supply the clean-ancilla contract. Their selected construction uses bounded-size Toffoli primitives and preserves low workspace. A reflection implementation that allocates one new ancilla per system qubit would not establish the stated $`N+\mathrm{polylog}`$ width.

## Complete cost

Write $`\tau=1+|w|t`$ and let the logarithmic precision parameter include $`N,\tau,\epsilon^{-1},\eta^{-1}`$, the incoming-flux bit length and the precision of the supplied coefficients. Under the assumptions of the [simulation theorem](streaming_gauss_theorem.md), one $`A`$ or $`A^\dagger`$ costs

```math
\widetilde O(N\tau)+\widetilde O(N)
=\widetilde O(N\tau)
```
logical gates. Preparation, counting, comparison and the reflection fit within that order. The serial construction therefore gives

```math
G_{\mathrm{total}}
=\widetilde O\!\left(\frac{N(1+|w|t)}{\epsilon}\right),
\qquad
Q_{\mathrm{total}}=N+\mathrm{polylog}.
```
Confidence logarithms are included in the soft-O notation. The parallel construction uses $`O(N)+\mathrm{polylog}`$ qubits and has total logical depth $`\widetilde O((1+|w|t)/\epsilon)`$ in the stated all-to-all circuit model. A parallel count and reflection may use linear workspace, which is allowed in that variant.

For the explicitly constructed global interaction-picture comparator, the same output contract gives

```math
G_{\mathrm{global,total}}
=\widetilde O\!\left(\frac{N+N^2|w|t}{\epsilon}\right).
```
The factor-$`N`$ comparison in the evolution-dominated regime refers to that concrete comparator. It is not a lower bound on every low-width algorithm.

## Classical preprocessing and output processing

The classical input is the finite list of lattice parameters and the size, time and accuracy specification. It is not an amplitude table or a supplied quantum data structure. The block schedule, circuit addresses and quadratic phase coefficients are explicit functions of these inputs. The compressed Dyson circuit uses only polynomially many precision bits and order coefficients; it does not enumerate all possible clock values.

Let $`G_0`$ be the number of gates in one compiled A and let P be the theorem's precision parameter. Generating the schedule and gate descriptions requires at most $`G_0\mathrm{poly}(P)`$ classical work when coefficient evaluation and finite-set gate synthesis use constructive polynomial-time precision algorithms. Standard Solovay–Kitaev compilation suffices for this conservative claim; see [Dawson and Nielsen's constructive algorithm](https://arxiv.org/abs/quant-ph/0505030). An efficient specialized rotation compiler can improve the constants. The compiled program is reused for the repeated A and inverse calls in amplitude estimation. Storing the classical program can take $`O(G_0\mathrm{poly}(P))`$ bits; the theorem's quantum-width count does not count this ordinary classical control memory as qubits.

Consequently, charged preprocessing changes only the suppressed precision factors in the stated total work bound. Reading the phase-estimation result, confidence aggregation and rescaling by $`M/N`$ require polynomial-logarithmic classical processing for the selected scalar estimator. Direct sampling instead processes N measured occupation bits per repetition, as counted below.

## Direct sampling

An alternative is to evolve, measure all matter occupations, and compute $`c/N`$ classically. Hoeffding's inequality gives $`O(\epsilon^{-2}\log(1/\eta))`$ repetitions for the worst-case bounded-output guarantee. Each repetition includes preparation, evolution, $`N`$ measured bits and $`O(N)`$ classical processing. Actual variance or spatial self-averaging can reduce the repetition requirement; a practical comparison should use the observed variance when justified.

Coherent amplitude estimation reduces the worst-case repetition exponent while increasing the coherent circuit depth and adding inverse/reflection operations. The finite hardware choice depends on those costs.

## Lattice precision and continuum limits

Input rounding is charged through the Hamiltonian perturbation bound $`t\|H-\widehat H\|`$. For fixed finite lattice parameters, a polynomial bound on this norm requires only logarithmically increasing coefficient precision as $`N,t,\epsilon^{-1}`$ grow. The native block implementation gives the corresponding synthesis and clock precision explicitly.

The hopping parameter remains visible because $`w=1/(2a)`$ in a common lattice convention. At fixed physical volume, $`a\propto1/N`$ makes $`N|w|t`$ scale as $`N^2`$ at fixed physical time. Fixed error in $`d`$, a dimensionless density per staggered site, need not be fixed error in a continuum density per unit length. This result is a finite-lattice simulation and estimation bound.

## Sources and comparison route

Amplitude amplification and estimation are established ingredients: see [Brassard et al., Quantum Amplitude Amplification and Estimation](https://arxiv.org/abs/quant-ph/0005055). The selected low-width reflection is [Nie, Zi and Sun (2024)](https://arxiv.org/abs/2402.05053). The physical and quantum simulation comparisons are collected in [Related work](../references/RELATED_WORK.md); the finite classical calculation is in [the benchmark account](benchmarks.md).
