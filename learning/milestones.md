# Thirty milestones for understanding gauge reconstruction

This map follows the scientific argument from individual registers to a complete simulation-and-estimation task. Its single educational anchor is Andrew M. Childs, [*Lecture Notes on Quantum Algorithms*, 17 April 2025](https://www.cs.umd.edu/~amchilds/qa/qa.pdf). Page numbers below are the printed Arabic page numbers in that edition; the corresponding one-based PDF page number is eight larger.

The allocation is **12 background/preliminaries milestones and 18 narrative/innovation milestones**. Twelve foundations connect quantum circuits, the lattice model, approximation, and scalar output into one computational contract. Eighteen further milestones are needed because the contribution joins a local encoding identity to native simulation circuits, a chain-wide schedule, coherent error control, and a complete resource comparison. Within each phase, the route moves from local objects to the assembled task. It identifies the central understanding targets without attempting to reproduce every proof or neighboring subject.

The [anchor bridge](anchor_bridge.md) explains the source-to-project connections and gives a four-site example. Full statements and proofs remain in [the scientific account](../science/README.md). Research papers named below supply specific theorem dependencies; they are not additional educational anchors.

## Phase I — Background and preliminaries

### M01. A matter register and a coherent state

**Central question.** What does a string of occupation bits describe, and what changes when several strings occur coherently?

**Understanding target.** Distinguish a basis configuration, its quantum amplitude, and a measurement probability. Recognize that a computed field can remain correlated with the matter rather than becoming classical information.

**Dependencies and story role.** This is the local starting point: one site, then a joint register.

**Conceptual connection.** The field-reconstruction identity is first defined on basis strings and then extends linearly to superpositions.

**Sources.** [Childs §1.1, p. 1](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=9); [model and encoding, §1](../science/streaming_gauss_theorem.md#1-model-boundary-conditions-and-exact-encoding).

### M02. Gates, width, depth, and a generated circuit

**Central question.** Which resources distinguish two circuits that implement the same transformation?

**Understanding target.** Separate gate count, simultaneously occupied qubits, parallel depth, numerical precision, and classical circuit generation. Distinguish logical gates from a physical fault-tolerant implementation.

**Dependencies and story role.** Uses M01 to turn a transformation of registers into a resource-accounting problem.

**Conceptual connection.** The project improves a gate–width tradeoff; its serial and parallel implementations make different depth commitments.

**Sources.** [Childs §§1.2–1.7, pp. 1–4](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=9); [resource theorem, §8](../science/streaming_gauss_theorem.md#8-resource-theorem-with-explicit-precision-dependence).

### M03. Compute, use, and uncompute

**Central question.** How can a circuit calculate a useful function without permanently storing its intermediate work?

**Understanding target.** Explain reversible function evaluation with a preserved input and a zero target, and why running the computation backward clears its work. Distinguish reversible cleanup from measurement or reset.

**Dependencies and story role.** Uses M01–M02 to introduce the local circuit pattern underlying temporary field storage.

**Conceptual connection.** Reconstruction computes a charge prefix; its inverse will later be evaluated against the updated matter configuration.

**Sources.** [Childs §1.4, pp. 2–3](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=10); [explicit charge arithmetic](../science/finite_resource_comparison.md#explicit-bounded-charge-arithmetic).

### M04. A Hamiltonian as a rule for real-time evolution

**Central question.** What is being simulated when a circuit approximates Hamiltonian dynamics?

**Understanding target.** Interpret $`H`$ as the generator of $`e^{-itH}`$, distinguish the prepared initial state from the evolution, and identify the requested final observable.

**Dependencies and story role.** Uses M01–M02 to connect circuit transformations to a physical time-dependent state.

**Conceptual connection.** The concrete task begins with a specified product-state quench, without an uncharged interacting-ground-state preparation.

**Sources.** [Childs §§27.1–27.2, pp. 133–134](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=141); [estimation input and output](../science/estimation.md#input-and-output).

### M05. Occupation, staggered charge, and one hopping bond

**Central question.** Why is occupation not identical to electric charge at every lattice site?

**Understanding target.** Interpret the fixed alternating background $`s_j=j\bmod2`$, the charge $`q_j=z_j-s_j`$, and the transfer of one occupation between adjacent sites. Track the equal and opposite charge changes at a hopping bond.

**Dependencies and story role.** Uses M01 and M04 to introduce the model's local physical variables.

**Conceptual connection.** A consistent hopping operation changes the link field together with the adjacent charges; this is the mechanism later used for cleanup.

**Sources.** [model, §1 and Eq. (4)](../science/streaming_gauss_theorem.md#1-model-boundary-conditions-and-exact-encoding); [one-bond native circuit](../science/coherent_native_blocks.md#21-each-bond-is-a-partial-matching). The model-specific definitions are supplied locally, not attributed to the anchor.

### M06. Gauss's law, a boundary condition, and a prefix sum

**Central question.** When does matter determine every electric field on the chain?

**Understanding target.** Derive the prefix relation from successive local charge balances and a known incoming flux. Distinguish fixing the incoming flux alone from also fixing the outgoing flux and hence total charge. Understand why a sufficiently large finite integer range is exact here.

**Dependencies and story role.** Uses M05 to assemble local charge conservation into a global encoding constraint.

**Conceptual connection.** The field registers contain reconstructible information, but the constraint does not by itself prescribe an efficient simulation circuit.

**Sources.** [model, encoding, and cutoff, §1](../science/streaming_gauss_theorem.md#1-model-boundary-conditions-and-exact-encoding); [Nguyen et al., Sec. II.B](https://doi.org/10.1103/PRXQuantum.3.020324).

### M07. Locality depends on the representation

**Central question.** Why can deleting redundant registers make the Hamiltonian harder to implement?

**Understanding target.** Distinguish geometric locality, the number of qubits in a local term, matrix sparsity, and the gate cost of accessing a term. Explain why substituting a charge prefix into electric energy produces nonlocal matter interactions.

**Dependencies and story role.** Uses M02 and M04–M06 to expose the central gate–width tension.

**Conceptual connection.** The compiler stores matter alone between factors while applying the locality decomposition in the redundant native representation.

**Sources.** [Childs §§27.3–27.4, pp. 134–136](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=142); [resource interpretation](../science/interpretation.md#why-the-asymptotic-comparison-matters).

### M08. Approximation as a uniform operational promise

**Central question.** What does a small simulation error guarantee for an unknown input state?

**Understanding target.** Interpret operator-norm error, accumulation of errors through unitary circuits, and the separate approximation of elementary rotations. Recognize the distinction between an all-input guarantee and a guarantee restricted to clean workspace inputs.

**Dependencies and story role.** Uses M02–M04 to establish the language needed to compose approximate local factors.

**Conceptual connection.** The project will strengthen a projected matrix-block guarantee and then use an ideal-prefix hybrid to reuse workspace.

**Sources.** [Childs §1.3, p. 2](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=10), [§2.1, pp. 7–8](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=15), and [§3.4, p. 14](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=22); [coherent error, §5](../science/streaming_gauss_theorem.md#5-coherent-error-control-with-reused-workspace).

### M09. An encoded matrix is an interface with a cost

**Central question.** How can a unitary circuit represent a matrix that is not itself unitary?

**Understanding target.** Identify the selected ancillary matrix block and its normalization, and distinguish the number of oracle calls from the gates implementing each call. Explain the roles of term preparation and selection in a linear combination of unitaries.

**Dependencies and story role.** Uses M03, M07, and M08 to connect Hamiltonian descriptions to executable subroutines.

**Conceptual connection.** Native hopping is encoded by explicit reversible circuits; neither its normalization nor its SELECT operation is free.

**Sources.** [Childs §§21.1–21.2, pp. 97–98](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=105), [§28.3, pp. 140–142](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=148), and [§29.1, pp. 143–144](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=151); [native hopping encoding](../science/coherent_native_blocks.md#2-an-explicit-hopping-block-encoding).

### M10. Coherent control, phases, and an inverse circuit

**Central question.** Why does a phase or discarded register that seems harmless in one experiment matter in a controlled computation?

**Understanding target.** Track a relative phase between controlled branches, distinguish a circuit inverse from a new approximation to reverse-time physics, and identify the registers retained by phase estimation.

**Dependencies and story role.** Uses M01–M03 and M08 to connect local reversible circuits to a coherent algorithm using them repeatedly.

**Conceptual connection.** Flux-dependent diagonal phases and all active workspace must survive until the implemented circuit is reversed.

**Sources.** [Childs §4.3, p. 19](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=27); [controlled use and exact inverse](../science/coherent_native_blocks.md#8-controlled-use-and-exact-inverse).

### M11. From a bounded observable to an acceptance probability

**Central question.** How does a simulation produce a useful number instead of a complete state description?

**Understanding target.** Relate an expectation value to a flag probability, distinguish direct sampling from coherent amplitude estimation, and identify the preparation, inverse, and reflection operations needed by the latter.

**Dependencies and story role.** Uses M03–M04 and M10 to close the elementary preparation–evolution–measurement chain.

**Conceptual connection.** A reversible excitation count and a uniform threshold register supply the project's bounded density flag.

**Sources.** [Childs §19.3, pp. 88–89](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=96) and [§27.5, pp. 136–137](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=144); [exact flag construction](../science/estimation.md#an-exact-reversible-flag-for-every-n).

### M12. One complete comparison contract

**Central question.** What must be held fixed before two simulation procedures can be compared fairly?

**Understanding target.** State the Hamiltonian, boundary sector, initial preparation, time, observable, accuracy, confidence, access model, and counted resources together. Separate a simulation improvement from an established quantum–classical advantage.

**Dependencies and story role.** Integrates M01–M11 into the global problem specification that the innovation phase will implement.

**Conceptual connection.** The strongest relevant comparison charges preparation, oracle construction, execution, output, and classical preprocessing for the same scalar task.

**Sources.** [Childs §§1.5–1.6, p. 3](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=11) and [§27.2, pp. 133–134](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=141); [complete estimation contract](../science/estimation.md); [comparison meaning](../science/interpretation.md).

## Phase II — Narrative and innovation

### M13. Cut a native block without changing its Hamiltonian

**Central question.** Which terms belong to a local interval, and what happens at its boundaries?

**Understanding target.** Group each matter site with its outgoing link, include only whole supported terms, retain the outgoing diagonal electric energy, and omit hopping across either cut. Explain the resulting conservation of block charge.

**Dependencies and story role.** Uses M05–M07 to begin the innovation at one correctly defined local factor.

**Conceptual connection.** The restriction convention is what lets the reconstruction identity and the later HHKL decomposition refer to the same unitary.

**Sources.** [local block assignment, §2](../science/streaming_gauss_theorem.md#2-the-local-blocks-to-which-the-compiler-applies); [HHKL, Lemma 6 and Theorem 1 proof](https://arxiv.org/abs/1801.03922).

### M14. Reconstruct a block from a coherent incoming flux

**Central question.** How can one block recover its fields when the incoming flux is quantum data?

**Understanding target.** Explain the local Gauss-law isometry, its admissible incoming-flux domain, and its linear action on entangled superpositions. Identify the matter, prefix, field, and arithmetic registers.

**Dependencies and story role.** Uses M01, M03, M06, and M13 to construct the local encoding interface.

**Conceptual connection.** The native simulator receives ordinary field registers without measuring which flux sector is present.

**Sources.** [Childs §1.4, pp. 2–3](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=10); [Lemma 1 and Eqs. (8)–(10)](../science/streaming_gauss_theorem.md#lemma-1-local-reconstruction-and-exact-cleanup).

### M15. Erase fields using the matter after it moves

**Central question.** Why does the inverse reconstruction still work after hopping changes its apparent input?

**Understanding target.** Follow the four-site factor through its two coherent configurations and explain why Gauss's law makes the evolved fields equal to prefixes of the updated charges. Identify why stale input charges would leave garbage.

**Dependencies and story role.** Uses M13–M14 to complete the exact local compute–evolve–uncompute mechanism.

**Conceptual connection.** Block-charge conservation preserves the exterior fields while internal Gauss relations make local cleanup possible.

**Sources.** [four-site bridge example](anchor_bridge.md#four-sites-a-complete-reconstruction-and-readout-example); [Lemma 1](../science/streaming_gauss_theorem.md#lemma-1-local-reconstruction-and-exact-cleanup); [compiler verification](../verification/README.md).

### M16. Open the native hopping oracle

**Central question.** What circuit implements one hopping term and its normalization?

**Understanding target.** View a bond as a partial matching of basis states, handle the hard field endpoints, embed the matching in a unitary, and combine bonds through a padded uniform term index. Charge the explicit selection circuit.

**Dependencies and story role.** Uses M05, M09, and M13 to supply the first executable ingredient of a local native propagator.

**Conceptual connection.** A small block's oracle has polynomial-logarithmic cost in the full problem parameters without QRAM.

**Sources.** [Childs §29.1, pp. 143–144](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=151); [native hopping encoding, §2](../science/coherent_native_blocks.md#2-an-explicit-hopping-block-encoding).

### M17. Apply electric phases without an energy table

**Central question.** How is a large quadratic electric energy implemented at low workspace cost?

**Understanding target.** Express a signed field through its bits, expand its square into bounded-degree bit products, and control the resulting phases on clock bits. Retain constants that depend on a coherent flux or an outer control.

**Dependencies and story role.** Uses M03, M06, M10, and M13 to supply the diagonal part of the native block circuit.

**Conceptual connection.** A large energy scale affects angle and clock precision without requiring a table for every time or field value.

**Sources.** [Childs §27.2, pp. 133–134](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=141); [diagonal fast-forwarding, §3](../science/coherent_native_blocks.md#3-explicit-diagonal-fast-forwarding-including-a-quantum-clock).

### M18. Combine local ingredients in the interaction picture

**Central question.** Which part of the Hamiltonian controls the number of short simulation segments?

**Understanding target.** Distinguish the exactly accessible on-site part from the residual hopping, the time-dependent interaction-picture oracle, and the compressed Dyson/OAA circuit. Explain why the selected compressed implementation's workspace matters.

**Dependencies and story role.** Uses M09–M10 and M16–M17 to assemble one approximate native propagator.

**Conceptual connection.** The anchor's LCU framework supplies the language; Low–Wiebe supplies the required time-dependent theorem and compressed coherent circuit.

**Sources.** [Childs §28.3, pp. 140–142](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=148); [native blocks, §§4–6](../science/coherent_native_blocks.md#4-interaction-picture-oracle-and-short-segment-parameters); [Low–Wiebe, Theorem 3 and Appendix B](https://arxiv.org/abs/1805.00675).

### M19. Projected accuracy is not clean-input accuracy

**Central question.** Why can a small error in a matrix block coexist with larger coherent leakage?

**Understanding target.** Distinguish a selected zero-ancilla block from the whole output state, interpret the square-root lifting bound, and explain why squared short-segment tolerances change precision logarithms rather than the extensive scaling.

**Dependencies and story role.** Uses M08–M09 and M18 to establish the exact interface needed before local work can be reused.

**Conceptual connection.** This is the missing step between a projected simulation theorem and a fixed coherent compiler with no reset.

**Sources.** [Childs §29.1, pp. 143–144](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=151); [Lemma 3](../science/streaming_gauss_theorem.md#lemma-3-top-block-error-lifts-to-a-clean-input-isometry-error); [coherent native lifting, §5](../science/coherent_native_blocks.md#5-from-the-published-top-block-to-a-fixed-coherent-block-unitary).

### M20. Move the prefix instead of recomputing it from the beginning

**Central question.** How can many local factors obtain their incoming flux without an entire-chain scan for every factor?

**Understanding target.** Maintain a cursor prefix, update it using current crossed charges, and relate its cost to total spatial movement. Explain the linear scan cost of a monotone disjoint-block layer.

**Dependencies and story role.** Uses M14–M15 to extend the exact local mechanism along the chain.

**Conceptual connection.** Amortizing prefix movement prevents a hidden extensive factor from returning through input preparation.

**Sources.** [cursor and Lemma 2, §3](../science/streaming_gauss_theorem.md#3-a-prefix-cursor-that-follows-updated-charges); [finite prefix overhead](../science/finite_resource_comparison.md#prefix-movement-and-per-layer-overhead).

### M21. Separate rapid on-site phases from propagation

**Central question.** Does a large electric energy imply proportionally faster transmission along the chain?

**Understanding target.** Explain why on-site interaction-picture conjugation preserves the support and norm of hopping terms, and why the locality velocity depends on hopping rather than the electric cutoff. Keep the hopping strength and physical time visible.

**Dependencies and story role.** Uses M07, M13, and M17–M18 to connect one native block to a controlled spatial approximation.

**Conceptual connection.** A cutoff-independent locality bound is necessary before the reconstructed block length can be logarithmic.

**Sources.** [native locality, §4](../science/streaming_gauss_theorem.md#4-native-locality-and-the-certified-hhkl-schedule); [Tong et al., Appendix I, Lemma 13](https://quantum-journal.org/papers/q-2022-09-22-816/).

### M22. Assemble a certified locality schedule

**Central question.** How do overlapping forward and backward interval evolutions approximate the full chain?

**Understanding target.** Identify the overlap that controls factorization error, the three disjoint layers in one dimension, the time chunks, and the small-system whole-chain fallback. Distinguish this schedule from an arbitrary product formula.

**Dependencies and story role.** Uses M13, M20, and M21 to produce the chain-wide sequence that the streaming compiler implements.

**Conceptual connection.** The decomposition is inherited; the contribution is executing its native factors without permanent field storage.

**Sources.** [HHKL, Fig. 1(a), Lemma 6, Theorem 1 proof, Appendix B](https://arxiv.org/abs/1801.03922); [certified schedule, §4](../science/streaming_gauss_theorem.md#4-native-locality-and-the-certified-hhkl-schedule).

### M23. Reuse imperfect workspace coherently

**Central question.** Why does residual garbage from an approximate factor not force a reset or a new workspace for every factor?

**Understanding target.** Explain the ideal-prefix/actual-suffix hybrid: the input on which a factor error is evaluated is ideal and clean, while its subsequent actual evolution is unitary. Do not assume that actual scratch is exactly zero.

**Dependencies and story role.** Uses M08, M15, M19, and M22 to extend local clean-input guarantees to the complete scheduled circuit.

**Conceptual connection.** This composition argument makes the low-width implementation compatible with both approximation and a later exact circuit inverse.

**Sources.** [Childs §2.1, pp. 7–8](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=15); [Lemma 4 and its application](../science/streaming_gauss_theorem.md#lemma-4-clean-input-errors-compose-despite-dirty-actual-workspace).

### M24. Read the finite gate–width tradeoff

**Central question.** Which registers are removed, and what exact arithmetic is added for the same factors?

**Understanding target.** Compare permanent links with temporary links plus one prefix, include shared carry/simulator scratch, and interpret the positive-saving condition. Separate counted reconstruction gates from uncompiled native T-counts.

**Dependencies and story role.** Uses M02, M16–M20, and M23 to give the serial construction an auditable finite resource consequence.

**Conceptual connection.** The improvement is a specified compilation tradeoff, even before a full fault-tolerant benchmark exists.

**Sources.** [finite resource comparison](../science/finite_resource_comparison.md); [arithmetic overhead, §6](../science/streaming_gauss_theorem.md#6-exact-arithmetic-overhead-for-a-fixed-schedule).

### M25. Parallelism from invariant coarse charge data

**Central question.** Which cached values can safely survive parallel evolution inside disjoint blocks?

**Understanding target.** Retain only whole-interval charge totals and their prefix functions, erase internal partial sums before evolution, and batch complete local workspaces under a linear-width budget. Identify the all-to-all connectivity assumption.

**Dependencies and story role.** Uses M02, M13, M22–M24 to turn the serial chain implementation into a global depth–width tradeoff.

**Conceptual connection.** Conservation makes coarse boundary data reusable; it does not make every intermediate prefix invariant.

**Sources.** [parallel compilation, §7](../science/streaming_gauss_theorem.md#7-parallel-compilation-with-linear-total-width); [parallel-cache verification](../verification/README.md).

### M26. Charge numerical precision and classical compilation

**Central question.** What does the soft-O notation conceal, and when is it justified?

**Understanding target.** Interpret the parameter $`P`$, distinguish exact reversible arithmetic from coefficient and rotation approximation, and include classical generation and control memory. Read the primitive-gate theorem separately from a finite Clifford+T estimate.

**Dependencies and story role.** Uses M08, M18–M19, and M24–M25 to assemble the rigorous global simulation resource statement.

**Conceptual connection.** The near-linear spacetime claim holds under explicit bit-length and magnitude assumptions; numerical input is not free.

**Sources.** [Childs §1.5, p. 3](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=11), [Theorem 2.1, p. 7](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=15), and [§3.4, p. 14](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=22); [Theorem 5](../science/streaming_gauss_theorem.md#8-resource-theorem-with-explicit-precision-dependence); [precision accounting](../science/coherent_native_blocks.md#7-numerical-input-errors-and-gate-synthesis); [classical preprocessing](../science/estimation.md#classical-preprocessing-and-output-processing).

### M27. Attach a prepared quench and an exact density flag

**Central question.** How is the bounded scalar task implemented for every chain length?

**Understanding target.** Count deviations from the staggered vacuum, compare the count with a uniform power-of-two threshold, retain the coherent flag/index state, and apply the known final rescaling. Distinguish count width from threshold width.

**Dependencies and story role.** Uses M04–M06, M11, and M26 to turn the simulation into one concrete executable experiment.

**Conceptual connection.** The four-site example exposes preparation, dynamics, cleanup, and readout in the same register calculation.

**Sources.** [four-site example](anchor_bridge.md#four-sites-a-complete-reconstruction-and-readout-example); [exact reversible flag](../science/estimation.md#an-exact-reversible-flag-for-every-n); [Childs §27.5, pp. 136–137](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=144).

### M28. Estimate the implemented circuit's probability

**Central question.** Which errors and resources enter when amplitude estimation repeatedly uses an approximate simulation?

**Understanding target.** Separate the fixed circuit's physical bias from estimation error, use its exact implemented inverse, reflect over all its active registers, and reserve a genuinely clean reflection ancilla. Compare coherent estimation with direct sampling.

**Dependencies and story role.** Uses M10–M11, M19, M23, and M27 to complete the preparation-to-output algorithm.

**Conceptual connection.** Full-simulation error of order $`\epsilon`$ suffices; squared short-segment tolerances serve the different purpose established in M19.

**Sources.** [Childs §19.3, pp. 88–89](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=96); [simulation bias and estimation](../science/estimation.md#simulation-bias-and-amplitude-estimation); [Nie–Zi–Sun, Sec. 3, Theorem 1](https://arxiv.org/abs/2402.05053).

### M29. Compare the same output with strong classical methods

**Central question.** What evidence would distinguish a better quantum implementation from a quantum–classical crossover?

**Understanding target.** Include charge-resolved MPS, local causal regions, symmetry, observable accuracy, and self-averaging. Interpret the committed short-time benchmark as a validated classical comparator, not a hardness result.

**Dependencies and story role.** Uses M12 and M26–M28 to test the complete quantum contract against actual classical structure and finite evidence.

**Conceptual connection.** Gauss's law benefits classical representations too; large state dimension or entanglement alone does not prove that the density is difficult.

**Sources.** [classical comparison](../science/interpretation.md#the-correct-classical-competitors); [benchmark account](../science/benchmarks.md); [related work](../references/RELATED_WORK.md).

### M30. State the contribution and its limits together

**Central question.** What has changed after preparation, execution, precision, and output are all counted?

**Understanding target.** Synthesize the retained native gate order, reduced persistent field storage, and improvement over the specified global interaction-picture comparator. Preserve the finite-block, small-cutoff, architecture, continuum, boundary, and classical-comparison qualifications.

**Dependencies and story role.** Integrates M13–M29 with the complete contract of M12 into the project's global scientific meaning.

**Conceptual connection.** A useful proved resource frontier can matter without being an unrestricted optimality theorem or a demonstrated hardware advantage.

**Sources.** [complete cost](../science/estimation.md#complete-cost); [lattice precision and continuum limits](../science/estimation.md#lattice-precision-and-continuum-limits); [resource interpretation and scope](../science/interpretation.md); [Childs §28.1, p. 139](https://www.cs.umd.edu/~amchilds/qa/qa.pdf#page=147) for the distinction between structured simulation and a generic fast-forwarding claim.
