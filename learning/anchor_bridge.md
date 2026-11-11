# From quantum-algorithm foundations to temporary gauge fields

The useful task is concrete: prepare a specified lattice state, let it evolve, and estimate how many particle and antiparticle excitations have appeared. A quantum computer can represent that evolving state with matter and electric-field registers. On an open one-dimensional chain, however, the field at a link is already determined by the charges to its left and the incoming boundary flux.

Deleting the field registers saves memory but makes electric energy a nonlocal function of the matter bits. Keeping every field makes the interactions local but spends extra qubits throughout the simulation. The compiler combines the two representations: calculate the fields needed by one local factor, run that factor, then erase the fields using the matter after it has evolved.

This bridge supplies the connections between the selected educational source and that mechanism. [The thirty milestones](milestones.md) organize the complete route. Exact statements, proofs, and detailed resource accounting have their authoritative homes in [the scientific account](../science/README.md).

## The selected anchor and the project boundary

The educational anchor is Andrew M. Childs, [*Lecture Notes on Quantum Algorithms*, dated 17 April 2025](https://www.cs.umd.edu/~amchilds/qa/qa.pdf). The title-page date, section headings, and page locations below are verified against that PDF. Page numbers are the printed Arabic numbers; a direct PDF page link uses the printed number plus eight.

| Foundation in the anchor | Verified location | Connection to this project |
|---|---|---|
| Registers, circuits, gate sets, reversibility, uniformity, and resource measures | [§§1.1–1.7, pp. 1–4](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=9) | Matter and field registers are explicit circuit data; classical circuit generation and workspace are charged. |
| Accumulation of approximation errors | [§2.1, pp. 7–8](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=15) | The project adapts the unitary hybrid argument to factors guaranteed only on clean-workspace inputs. |
| Approximate gate synthesis | [§3.4, p. 14](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=22) | Known phase gates must eventually be synthesized at a chosen precision; a primitive gate count is not an absolute T-count. |
| Phase estimation and coherent counting | [§4.3, p. 19](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=27); [§19.3, pp. 88–89](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=96) | A flag probability becomes a scalar estimate using the implemented circuit, its inverse, and reflections. |
| Queries as an access model | [§§21.1–21.2, pp. 97–98](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=105) | A Hamiltonian query must be opened into actual preparation, selection, arithmetic, and phase gates. |
| Hamiltonian evolution, simulation, and measurement | [§§27.1–27.5, pp. 133–137](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=141) | The output contract specifies a prepared state and one bounded density, rather than a complete classical description of the state. |
| Linear combinations of unitaries and block encoding | [§28.3, pp. 140–142](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=148); [§29.1, pp. 143–144](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=151) | These give the language for the native hopping oracle and the distinction between a selected matrix block and a full coherent output. |

The Schwinger model, its Gauss-law constraint, the locality factorization, and the chosen compressed Dyson implementation are not results imported from this educational anchor. Their definitions and proof dependencies are supplied below and in the linked scientific pages. In particular, the project's quantitative block costs come from its explicit circuits and the selected Low–Wiebe theorem, not from a generic appeal to the anchor's simulation chapter.

## Translate the notation before using the algorithms

A computational basis string names a definite occupation pattern. A quantum state assigns amplitudes to many such strings; a measurement samples probabilities determined by those amplitudes. Reversible arithmetic acts on all these branches coherently. Computing a field value therefore need not mean observing it.

| Object | Meaning here |
|---|---|
| $`N`$ | Number of matter sites. It is not the exponentially large matrix dimension that the same letter can denote in generic matrix-algorithm statements. |
| $`z_j`$ and $`s_j`$ | The occupation bit at site $`j`$ and the fixed staggered background $`s_j=j\bmod2`$. |
| $`q_j=z_j-s_j`$ | Charge relative to that background. An occupied odd site has zero charge in the chosen bare vacuum. |
| $`E_j`$ and $`P`$ | Electric field on link $`j`$ and the incoming-field register for the current local interval. Both use explicit signed integer encodings. |
| $`H_I=A_I+B_I`$ | The restricted native block Hamiltonian, split into on-site mass/electric energy and hopping. The symbol $`A_I`$ here is a Hamiltonian term, not the generic matrix called A in a block-encoding definition. |
| $`U_j`$ versus a circuit unitary | The finite link-raising operator $`U_j`$ is a hard-truncated shift and a contraction. Its hopping contribution is embedded in a larger actual unitary circuit. |
| $`\alpha_B`$ | Normalization of the hopping block encoding. Both this normalization and the gates per query enter the cost. |
| Clean workspace | Ancillas in their specified zero input state. An approximate factor can leave a small coherent component outside that state. |

With known incoming flux $`e_{\rm L}`$, Gauss's law gives

```math
E_j=e_{\rm L}+\sum_{k=0}^{j}(z_k-s_k).
```

The equation is a running charge balance. Knowing the left boundary determines each successive field. Fixing only that boundary allows several total-charge sectors; prescribing the right boundary as well selects one of them. A sufficiently wide finite field register is exact for the full physical domain because each matter charge is bounded. The [model and cutoff statement](../science/streaming_gauss_theorem.md#1-model-boundary-conditions-and-exact-encoding) makes the range and boundary quantifiers explicit.

## Four sites: a complete reconstruction and readout example

Write site 0 at the left of each four-bit string. Set $`e_{\rm L}=0`$ and use the background $`s=0101`$. Preparing the bare vacuum $`0101`$ takes X gates on sites 1 and 3. Its charges and all three dynamical fields are zero.

Consider just the native interval $`I=[1,2]`$. It contains matter sites 1 and 2, links 1 and 2 for their electric energy, and the hopping bond between sites 1 and 2. It contains no hopping across either cut. Link 2 is the outgoing diagonal-only link; link 0 supplies the incoming flux $`P=E_0`$.

For a transparent exact factor, set $`m=J=0`$ and evolve only this restricted hopping term for duration $`\tau_f`$. This is an isolated factor illustrating the compiler, not the full four-site chain evolution at those parameters.

| Configuration | Matter string | Charges at sites 0–3 | Fields on links 0–2 | Excitation count |
|---|---|---|---|---:|
| Bare vacuum | `0101` | $`(0,0,0,0)`$ | $`(0,0,0)`$ | 0 |
| One allowed hop within the interval | `0011` | $`(0,-1,+1,0)`$ | $`(0,-1,0)`$ | 2 |

### Calculate the two local fields

Start a prefix register at $`P=0`$ and two field registers at zero. Reversible additions compute

```math
F_1=P+q_1,
\qquad
F_2=P+q_1+q_2.
```

On the vacuum both values are zero. The native hopping term moves the occupation from site 1 to site 2 and lowers link 1 by one. In the reverse transition it raises link 1 by one. Link 2 remains zero because the total charge of sites 1 and 2 has not changed.

Put $`\lambda=w\tau_f`$. Starting in the vacuum, the exact reconstructed state after this factor is

```math
\cos\lambda\,|0101\rangle|0,0\rangle_F
-i\sin\lambda\,|0011\rangle|-1,0\rangle_F.
```

The two coefficients are amplitudes: their squared magnitudes, $`\cos^2\lambda`$ and $`\sin^2\lambda`$, are the probabilities of the two configurations. The factor $`-i`$ records their relative phase, and the field label $`-1`$ denotes its signed binary encoding. The matter and field registers are generally entangled. Erasing the field registers by observation would alter that state; the circuit instead reverses the arithmetic.

### Erase the fields against the updated charges

On the hopped branch the current charges are $`q_1=-1`$ and $`q_2=+1`$. Recomputing their fields gives exactly the stored pair $`(-1,0)`$. On the other branch it gives $`(0,0)`$. The inverse reconstruction therefore produces

```math
\left(
\cos\lambda\,|0101\rangle
-i\sin\lambda\,|0011\rangle
\right)|0,0\rangle_F.
```

The arithmetic has removed the redundant field record while preserving the coherent matter state. It works because the native evolution preserved the relation between fields and charges. Reusing the old vacuum charges would fail to clear link 1 on the hopped branch.

This also illustrates a genuinely coherent incoming flux. If the next interval begins at site 2, the cursor advances by adding the **current** $`q_1`$. Its incoming field becomes zero on the vacuum branch and minus one on the hopped branch. The register must carry that superposition into the next factor. At the end of a sweep it is cleared by reversing its relation to the current matter, rather than by resetting it.

Restoring electric energy adds phases determined by these reconstructed fields. Terms involving the incoming flux, including an outgoing boundary electric contribution, must remain in the circuit. A phase that varies between coherent incoming-flux branches is not a removable global phase.

### Produce a density flag

The excitation count $`c`$ is the number of bits that differ from $`0101`$. Here it is zero or two. The normalized density is $`d=c/4`$, so the exact expectation after the isolated factor is

```math
\nu=\frac12\sin^2\lambda.
```

The general four-site readout uses a **three-bit count register**, which can represent every possible count from zero through four. It also uses a separate **two-bit threshold register**, prepared by two Hadamard gates, with values $`r=0,1,2,3`$ equally likely. A flag is flipped when $`r\lt c`$; the count and comparator scratch are then uncomputed.

On the vacuum branch the flag never succeeds. On the hopped branch it succeeds for $`r=0,1`$, hence with probability one half. Its total success probability is therefore exactly $`\sin^2\lambda/2=\nu`$. The threshold and flag can remain entangled with matter; they are part of the preparation circuit and its inverse. No square-root amplitude loading or uniform-state preparation over an irregular set is needed.

The resources are visible: four matter qubits, two temporary local field registers, one incoming-flux register, native/arithmetic work, and the stated count/threshold/flag registers when readout is performed. The precise reuse of scratch is accounted for in [the finite comparison](../science/finite_resource_comparison.md). This four-site calculation does not demonstrate a width gain: one prefix and two local field registers already equal the number of permanent links. The gain requires local factors substantially smaller than the chain, as the finite width inequality makes explicit.

## The missing steps between the anchor and the compiler

### Reversible arithmetic needs a conserved relation

The anchor's reversible-computation pattern explains how to calculate and erase a function. Here the matter changes between those operations. The additional fact is a physical invariant: native hopping changes fields and charges consistently, while the block's total charge is conserved. That is why the inverse computation evaluated on the new matter can erase the new fields. The [local reconstruction lemma](../science/streaming_gauss_theorem.md#lemma-1-local-reconstruction-and-exact-cleanup) gives the precise isometry identity, including coherent incoming flux and exterior fields.

### A local factor needs an explicit simulator

The anchor's LCU and block-encoding sections describe an interface, not the cost of every implementation of it. The project opens that interface in two steps. A hopping bond is a reversible partial matching of matter-and-field basis states, embedded in a unitary. Electric energy is a quadratic polynomial of signed field bits, so its exponential is implemented by bounded-arity phase gates, including coherent control by clock bits.

Low–Wiebe's interaction-picture construction then combines the two pieces. The selected version uses a compressed Dyson circuit with shared time and oracle registers. Its normalization counts hopping strength; large electric energy still enters clock and phase precision. The [native-block account](../science/coherent_native_blocks.md) states the full-space oracle definitions and the exact primary theorem used. The anchor's static LCU construction does not, by itself, supply this time-dependent circuit or its workspace bound.

### A selected matrix block does not guarantee clean work

Let $`J_0`$ mean “attach zero workspace,” let $`V`$ be the actual unitary, and let $`U`$ be the desired system evolution. If the selected block $`J_0^\dagger VJ_0`$ differs from $`U`$ by at most $`\rho`$ in operator norm, the complete clean-input error is bounded by

```math
\|VJ_0-J_0U\|\le\sqrt{2\rho}.
```

The square root matters: a probability-scale loss can correspond to a larger amplitude outside the clean-workspace state. The compiler therefore selects squared short-segment tolerances. This changes logarithmic precision factors and avoids treating a projected simulation guarantee as an exactly clean output.

To compose factors, compare their product using an ideal prefix and an actual unitary suffix. The ideal prefix supplies clean work at the factor where the error is evaluated; the actual suffix preserves the norm of that error. The actual computation can retain a small coherent residue throughout. It is never measured, discarded, or reset. This is the project-specific extension of the anchor's error-accumulation argument; [the error lemmas](../science/streaming_gauss_theorem.md#5-coherent-error-control-with-reused-workspace) contain the proof.

### Chain-wide locality is a research dependency

The prefix cursor avoids rescanning the entire chain before every local factor. A monotone layer crosses only linearly many sites; arbitrary movement has a cost proportional to its total distance. This arithmetic statement must be combined with a certified schedule of factors.

HHKL provides a locality-based factorization into overlapping interval evolutions, including backward factors, arranged in three disjoint layers per short chunk in one dimension. Tong et al. provide the needed locality bound after removing arbitrarily large on-site terms: on-site phases do not change the support or norm of the hopping interactions. Those results justify the logarithmic block scale. They are separate from the anchor's product-formula discussion.

For parallel execution, only coarse interval totals and their prefix functions are retained across a disjoint layer. Individual site prefixes inside an evolving interval are not invariant. A bounded number of complete local workspaces processes the layer in batches, producing the stated all-to-all depth bound at linear total width. The [schedule and parallel construction](../science/streaming_gauss_theorem.md) make these distinctions explicit.

### A simulation becomes an algorithm only after output is charged

For arbitrary $`N`$, prepare a power-of-two threshold of size $`M=2^{\lceil\log_2N\rceil}`$. The flag has probability $`p=\mathbb E[c]/M`$, and the requested density is $`(M/N)p`$, with a rescaling smaller than two. Computing and erasing the count costs $`O(N\log N)`$ gates and $`O(\log N)`$ extra serial width.

Amplitude estimation acts on one fixed implemented circuit $`A`$: state preparation, approximate coherent simulation, and flag construction together. It uses the gate-by-gate inverse $`A^\dagger`$ and a reflection over every active input register, including simulator scratch. The selected multi-controlled reflection reserves one clean qubit outside $`A`$; leaked simulator scratch cannot silently serve that role.

The estimator learns the acceptance probability of this fixed circuit. Its sampling error is separate from the circuit's physical bias, so full-simulation error of order $`\epsilon`$ suffices. This is compatible with the squared *short-segment* tolerances above: the two statements refer to different levels of the error analysis. [The complete estimation account](../science/estimation.md) also charges classical circuit generation, confidence amplification, and output processing.

## Assemble the cost and keep its qualifications

Let $`r=\max\{1,\lceil |w|t\rceil\}`$ and let $`P`$ be the explicit bit-length and precision parameter in [Theorem 5](../science/streaming_gauss_theorem.md#8-resource-theorem-with-explicit-precision-dependence). The conservative simulation bounds are

```math
G_{\rm sim}=O(NrP^5),
\qquad
Q_{\rm serial}=N+O(P^2),
```

and the batched version has

```math
Q_{\rm parallel}=O(N)+O(P^2),
\qquad
D_{\rm parallel}=O(rP^7).
```

The primitives are Toffoli, CNOT, and bounded-arity known-angle phase gates. Synthesis into a fixed finite gate set adds precision factors. The depth statement assumes all-to-all logical connectivity; neither formula is a physical-runtime or complete finite T-count estimate. Classical generation of a $`G_0`$-gate program costs at most $`G_0\mathrm{poly}(P)`$ under the stated constructive compilation assumptions, and the program is reused across estimation calls. Its ordinary classical storage is separate from the quantum-width count.

When the specified input descriptions and magnitude/precision logarithms have the required polynomial-logarithmic size, density estimation to additive error $`\epsilon`$ has complete logical gate cost

```math
\widetilde O\!\left(\frac{N(1+|w|t)}{\epsilon}\right),
```

including preparation, inverse circuits, reflections, readout, and confidence logarithms. Direct sampling is also available, with worst-case repetition order $`\epsilon^{-2}`$ and potentially smaller cost when variance or spatial self-averaging helps.

The native algorithm already has near-linear spacetime gates; its comparison with reconstruction concerns persistent field storage. A specified matter-only global interaction-picture construction gives the stronger low-width comparator

```math
\widetilde O\!\left(\frac{N+N^2|w|t}{\epsilon}\right).
```

Removing one extensive factor relative to that construction is not a lower bound on all matter-only algorithms. A small accurate field cutoff can already make native storage linear in $`N`$, and a certified local block that fills the chain can erase the temporary-storage benefit.

The strongest classical comparison includes charge-resolved MPS, observable-focused methods, local causal regions, symmetry, and self-averaging. The repository's finite quench benchmark is classically tractable. Neither a large Hilbert-space dimension nor state entanglement alone proves that this scalar density is difficult. Finally, $`w=1/(2a)`$ in a common physical convention: changing lattice spacing changes the time scale, and fixed dimensionless density error need not mean fixed continuum-density error. These are part of [the result's interpretation](../science/interpretation.md), not qualifications removed by the learning route.

## Research dependencies beyond the educational anchor

| Imported ingredient | Primary research source | Authoritative project connection |
|---|---|---|
| Exact open-boundary field range from Gauss's law | [Nguyen et al., Sec. II.B](https://doi.org/10.1103/PRXQuantum.3.020324) | [Model and encoding](../science/streaming_gauss_theorem.md#1-model-boundary-conditions-and-exact-encoding) |
| Locality factorization and one-dimensional layer schedule | [HHKL, Lemma 6, Fig. 1, Theorem 1 proof, Appendix B](https://arxiv.org/abs/1801.03922) | [Certified schedule](../science/streaming_gauss_theorem.md#4-native-locality-and-the-certified-hhkl-schedule) |
| Locality independent of large on-site electric terms | [Tong et al., Appendix I, Lemma 13](https://quantum-journal.org/papers/q-2022-09-22-816/) | [Native locality](../science/streaming_gauss_theorem.md#4-native-locality-and-the-certified-hhkl-schedule) |
| Compressed time-dependent Dyson/OAA circuit | [Low–Wiebe, Theorem 3 and Appendix B](https://arxiv.org/abs/1805.00675) | [Coherent native simulation](../science/coherent_native_blocks.md#5-from-the-published-top-block-to-a-fixed-coherent-block-unitary) |
| Amplitude estimation and the selected low-workspace reflection | [Brassard et al.](https://arxiv.org/abs/quant-ph/0005055); [Nie–Zi–Sun, Sec. 3, Theorem 1](https://arxiv.org/abs/2402.05053) | [Preparation-to-output cost](../science/estimation.md) |

These citations identify imported results and the places where their assumptions are used. The local reconstruction, cursor, cache, and coherent-reuse arguments are explained and proved in the repository. The [milestone map](milestones.md) joins these ingredients into the complete scientific story without requiring a second educational source.
