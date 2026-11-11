# References and comparison of simulation resources

Machine-readable entries for the sources below and the numerical-method references used in the science notes are in [references.bib](references.bib). Journal versions are preferred where available; theorem locations refer to the linked paper versions.

## Conventions and claim boundary

N denotes staggered matter sites, t denotes evolution time in fixed lattice units, and delta denotes coherent simulation error. Couplings and boundary-flux magnitudes must be included explicitly if they scale; a continuum limit is not obtained by silently keeping the fixed-lattice constants unchanged. A tilde suppresses logarithmic factors only. Published upper bounds are not lower bounds on the corresponding formulations.

The resource result studied here is a compiler for an existing native HHKL factorization. It combines compact storage between factors with the native local simulation algorithm inside each factor. Its finite claim compares **the same certified factor schedule and inherited block simulator**. It does not prove a globally optimal width/gate frontier or a speedup over every possible low-width algorithm.

## Quantum comparisons

| Construction | Simulation gate scaling in the stated fixed-coupling regime | Principal storage | Status and comparison |
|---|---|---|---|
| Native gauge HHKL plus interaction picture, Tong et al. | N t polylog(Lambda_0 N t / delta) | Matter plus all link registers, approximately N+(N−1)b before simulator workspace | Published near-spacetime-linear algorithm; supplies the local simulator being compiled |
| Eliminated global block encoding, Sakamoto et al. | Leading N^4 t, with additional precision-dependent logarithmic terms | N matter qubits plus O(log N) simulation ancillas | Published explicit low-width algorithm; useful motivation, but not the strongest simple comparator |
| Eliminated global interaction picture with prefix-based diagonal fast-forwarding | Approximately N^2 t up to logarithms | N+polylog(Nt/delta) | Explicit derived comparator from known ingredients, not presented as a published optimal bound |
| Serial temporary reconstruction of native HHKL blocks | N t polylog(Nt/delta) | N+polylog(Nt/delta) | Present compiler result; arithmetic overhead and coherent reuse must be counted |
| Coarse-prefix batching of the same compiler | N t polylog(Nt/delta) | O(N), when N dominates the local polylogarithmic workspace | Parallel resource variant in an abstract logical connectivity model; not a concrete hardware-depth estimate |

Here b is the actual link-register width. On the physical subspace with fixed open-boundary incoming flux, b=O(log(N+|E_left|)) suffices exactly. A smaller certified state-dependent cutoff can be used by a competing native implementation and should be included in any numerical comparison.

### The stronger global interaction-picture comparator

After gauge elimination, write H=A+V, where A is the diagonal electric-plus-mass term and V is nearest-neighbor hopping. The complete diagonal energy can be computed by scanning the matter occupations, maintaining the electric prefix and accumulating its square. Reversible arithmetic, phase application, and uncomputation implement exp(−i A s) using N polylogarithmic-cost work and only polylogarithmic extra space. At fixed hopping strength the normalization of V is O(N). Applying the standard global interaction-picture construction therefore gives O(Nt polylog) queries, each with O(N polylog) gates, for approximately N^2t gates.

This removes two powers of N from a comparison made only against Sakamoto's leading N^4t cost. Consequently, the compiler's factor-N improvement is relative to this **specified** global interaction-picture implementation. It is not a lower bound on global simulation or a claim that no more efficient eliminated algorithm exists.

### Stronger alternatives that must remain in the comparison

- Product-formula costs depend on the order, couplings, nested commutators, accessible flux range, time, and accuracy. Nguyen et al.'s eliminated-Hamiltonian bounds and the explicit native implementations of Shaw et al., Rajput et al., and Kan et al. are meaningful competitors. Prefix arithmetic can also improve their implementation of diagonal electric evolution; comparisons should not force those competitors to expand every Coulomb pair into a separate rotation.
- State-dependent flux bounds and low-energy restrictions can reduce practical costs. The exact full-physical-space bound |E_j|<=|E_left|+N is a safe encoding guarantee, not a claim that a native simulator must allocate that maximum in every task.
- A persistent dyadic charge/rank data structure is a possible alternative implementation. Classical rank-query time alone does not establish a cheap quantum-selected oracle: construction, coherent addressing, updates under hopping, storage, and gate connectivity must all be charged. We have not proved a lower bound excluding such a better implementation.
- Interaction-picture hopping terms have more commutation structure than their long Pauli support suggests: a hop changes only the intervening flux, and separated hopping terms commute even at different interaction-picture times. An algebraic local-block formulation may express the present compiler without explicitly materializing every link. This observation does not invalidate the resource construction, but it makes a broad uniqueness or mechanism-priority claim inappropriate.

## Verified primary-source anchors

### 1. Tong et al., Quantum 6, 816 (2022)

Y. Tong, V. V. Albert, J. R. McClean, J. Preskill, Y. Su, *Provably accurate simulation of gauge theories and bosonic systems*.

[arXiv:2110.06942](https://arxiv.org/pdf/2110.06942), [journal DOI](https://doi.org/10.22331/q-2022-09-22-816).

**Verified locations:** Appendix E.1, especially E.1.1–E.1.2; Appendix I, Lemma13. E.1 explicitly gives O(N T polylog(Lambda_0 N T epsilon^−1)) gates for U(1)/SU(2), using HHKL and the Low–Wiebe interaction-picture algorithm. It defines the block Hamiltonian by including local terms acting entirely on sites/links within the block. E.1.2 assigns inverse-polynomial per-block error and uses electric-energy fast-forwarding. Lemma13 makes the locality velocity independent of large on-site electric terms.

**Relation:** inherited simulation and locality ingredients. The present contribution concerns how those factors are stored and implemented on the Gauss-law subspace, not a new HHKL or Dyson-series algorithm.

### 2. Haah, Hastings, Kothari, Low, SIAM Journal on Computing 52(6), FOCS18-250–FOCS18-284

J. Haah, M. B. Hastings, R. Kothari, G. H. Low, *Quantum algorithm for simulating real time evolution of lattice Hamiltonians*.

[arXiv:1801.03922](https://arxiv.org/pdf/1801.03922), [journal DOI](https://doi.org/10.1137/18M1231511). The journal article appeared online in January 2021 and was assigned to the December 2023 issue; the initial preprint and conference version date from 2018.

**Verified locations:** Fig.1(a); Lemma6; proof of Theorem1; Appendix B. The one-dimensional layout consists of three layers of disjoint interval evolutions with forward/backward factors. Appendix B states a 2 alpha−1 layer decomposition for an alpha-colorable tessellation; alpha=2 gives the one-dimensional case. A footnote near the theorem proof already discusses serial reuse of simulation ancillas.

**Relation:** schedule and local-unitary factorization are inherited. Serial ancilla reuse by itself is not claimed as new. The added step is temporary reconstruction and erasure of constrained **system** link registers.

### 3. Sakamoto et al., Quantum 8, 1474 (2024)

K. Sakamoto, H. Morisaki, J. Haruna, E. Itou, K. Fujii, K. Mitarai, *End-to-end complexity for simulating the Schwinger model on quantum computers*.

[arXiv:2311.17388v3](https://arxiv.org/html/2311.17388v3), [journal DOI](https://doi.org/10.22331/q-2024-09-17-1474).

**Verified locations:** Introduction pp.2–3; Result1 / Table1; Result2 and Eqs.(39)–(40); Result3. The introduction explicitly contrasts Tong's fast native representation with the qubit savings and nonlocal interactions after elimination. The eliminated block encoding has normalization O(N^3), T-cost O(N+log^2(N/epsilon)), and O(log N) ancillary width. The displayed simulation cost has leading N^4t. Result2 specifies a near-unitary block encoding and its simulation ancillas. Result3 is expressly based on an empirical amplitude-estimation assumption and uses an additional Theta(N)-ancilla implementation of its reflection.

**Relation:** documented motivating tradeoff and explicit low-width baseline. Its 1.72×10^13 T-gate example estimates a vacuum-persistence amplitude for a particular N=128 problem; it is not a directly comparable numerical cost for pair density, a different time/coupling point, or the current compiler. Simulation-only and end-to-end widths must not be conflated.

### 4. Rhodes, Kreshchuk, Pathak, PRX Quantum 5, 040347 (2024)

M. L. Rhodes, M. Kreshchuk, S. Pathak, *Exponential Improvements in the Simulation of Lattice Gauge Theories Using Near-Optimal Techniques*.

[primary PDF](https://journals.aps.org/prxquantum/pdf/10.1103/PRXQuantum.5.040347), [DOI](https://doi.org/10.1103/PRXQuantum.5.040347).

**Verified locations:** Section II.C; Section IV resource discussion, pp.19–20; Section V, Eq.(76). The paper develops explicit native block encodings and fault-tolerant resource counts. Eq.(76) retains a gauge-register contribution proportional to the number of links times log Lambda. Its finite U(1) comparisons explicitly note that HHKL blocks can be too large for the asymptotic size advantage to be realized.

**Relation:** important current source of native circuit costs; does not provide temporary Gauss reconstruction in the examined text. It also supplies a direct warning against substituting an asymptotic block size for a certified finite one.

### 5. Kan et al., Physical Review D 113, 114503 (2026)

A. Kan, J. Lemieux, O. Okrut, B. Sahinoglu, *Optimized quantum algorithms for simulating the Schwinger effect*.

[arXiv:2508.16831v2](https://arxiv.org/abs/2508.16831v2), [DOI](https://doi.org/10.1103/ps29-tshk).

**Verified locations:** Introduction; Section II; Section IV and Table II; Appendices VII–VIII. The v2 text treats product-state quenches and Gaussian-state scattering/splitting, chooses physical parameters for pair production, and explicitly compiles second-order product formulas and interaction-picture Dyson evolution. Its electric subroutine operates on each stored bosonic register, with eta=log2(2Lambda). It compares finite T and qubit costs, and observes that the preferred method depends on parameters.

**Relation:** a strong physical-task and native-circuit comparator. Its detailed constants may be inherited only after matching conventions, cutoff, coherent accuracy, and the actual block simulator. No absolute total-T claim is inferred here.

### 6. Rajput, Roggero, Wiebe, Quantum 6, 780 (2022)

A. Rajput, A. Roggero, N. Wiebe, *Hybridized Methods for Quantum Simulation in the Interaction Picture*.

[arXiv:2109.03308](https://arxiv.org/pdf/2109.03308), [DOI](https://doi.org/10.22331/q-2022-08-17-780).

**Verified locations:** Section5, Corollaries5.3–5.4, Eqs.(65)–(69); Section7. Their native Schwinger constructions give the stated approximately N^3 t^2/(a^2 epsilon) and N^2 t^2/(a^2 epsilon) gate dependences with logarithmic cutoff factors. Section7 treats dynamical constraints through penalty terms and interaction pictures.

**Relation:** native low-ancilla alternatives and evidence that cutoff, time, accuracy, and lattice spacing must be compared together. Constraint enforcement is distinct from removing permanent gauge storage.

### 7. Pardo et al., Physical Review Research 5, 023077 (2023)

G. Pardo, T. Greenberg, A. Fortinsky, N. Katz, E. Zohar, *Resource-efficient quantum simulation of lattice gauge theories in arbitrary dimensions: Solving for Gauss's law and fermion elimination*.

[arXiv:2206.00685](https://arxiv.org/pdf/2206.00685), [DOI](https://doi.org/10.1103/PhysRevResearch.5.023077).

**Verified locations:** Introduction; Section II discussion of eliminating gauge fields; Section III, eliminating matter. The paper demonstrates how local constraints can eliminate matter while retaining a local gauge description, with explicit Z2 examples.

**Relation:** Gauss-law redundancy removal is established prior art. Its examined construction is not the same temporary U(1)-link reconstruction around a native HHKL factor.

### 8. Low and Wiebe, interaction-picture simulation

G. H. Low, N. Wiebe, *Hamiltonian Simulation in the Interaction Picture*.

[arXiv:1805.00675](https://arxiv.org/abs/1805.00675).

**Relevant source anchors:** Definition2 and Corollary4 are the ingredients explicitly invoked by Tong Appendix E.1.2. Theorem3 and Appendix B, particularly the compression gadget in Lemma13 and robust oblivious amplitude amplification in Lemma14, supply the selected low-workspace implementation. Corollary4 Eq.(11) explicitly identifies the underlying fixed unitary and its projected top block. The present compiler converts that top-block guarantee to a clean-input isometry guarantee; squaring per-segment top-block tolerance suffices and changes only logarithmic scaling. See the dedicated coherent-reuse lemma rather than treating postselection success as exact cleanup.

### 9. Nie, Zi, Sun, low-width reflections

J. Nie, W. Zi, X. Sun, *Quantum circuit for multi-qubit Toffoli gate with optimal resource*.

[arXiv:2402.05053](https://arxiv.org/pdf/2402.05053).

**Verified locations:** Section3, Theorem1; introduction pp.1–2. A linear-size, logarithmic-depth multi-controlled Toffoli uses one ancillary qubit. The Section3 construction uses bounded-size Toffoli primitives. This is the relevant low-width option for amplitude-estimation reflections; the separate ancilla-free construction involves high-precision gates and is not the one being invoked.

### 10. Nguyen et al., PRX Quantum 3, 020324 (2022)

N. H. Nguyen, M. C. Tran, Y. Zhu, A. M. Green, C. Huerta Alderete, Z. Davoudi, N. M. Linke, *Digital Quantum Simulation of the Schwinger Model and Symmetry Protection with Trapped Ions*.

[arXiv:2112.14262](https://arxiv.org/abs/2112.14262), [journal DOI](https://doi.org/10.1103/PRXQuantum.3.020324).

**Verified locations:** Section II.B, “Gate complexity,” printed p.4, gives the exact open-boundary cutoff Lambda=N/2 for zero incoming flux in its convention. Eq.(15) and the following discussion give the eliminated-Hamiltonian product-formula bounds. Section I defines the bare-vacuum quench and the particle-number density in Eq.(4).

**Relation:** the exact finite physical flux range and the bare-vacuum density task are established ingredients. Neither is a new contribution of this compiler. Its product-formula estimates are formulation-specific upper bounds, not lower bounds for all matter-only algorithms.

### 11. Shaw et al., Quantum 4, 306 (2020)

A. F. Shaw, P. Lougovski, J. R. Stryker, N. Wiebe, *Quantum Algorithms for Simulating the Lattice Schwinger Model*.

[arXiv:2002.11146](https://arxiv.org/abs/2002.11146), [journal DOI](https://doi.org/10.22331/q-2020-08-10-306).

**Verified locations:** Corollary9 gives asymptotic simulation resources; Corollary11 gives a finite resource bound. The paper also develops and costs measurement of mean pair density, explicitly identifying this bounded output in its abstract.

**Relation:** an explicit native product-formula and observable-estimation comparator. Its electric cutoff, dimensionless time, coupling conventions, and error target must be matched before using its finite counts. Mean pair density is an established useful output rather than an application novelty here.

### 12. Brassard, Høyer, Mosca, Tapp, Contemporary Mathematics 305, 53–74 (2002)

G. Brassard, P. Høyer, M. Mosca, A. Tapp, *Quantum Amplitude Amplification and Estimation*, in *Quantum Computation and Quantum Information*, edited by S. J. Lomonaco, Jr.

[arXiv:quant-ph/0005055](https://arxiv.org/abs/quant-ph/0005055), [published chapter DOI](https://doi.org/10.1090/conm/305/05215).

**Verified locations:** Section4, Theorem12. The additive amplitude-estimation guarantee gives O(1/epsilon) uses at constant success probability; independent confidence amplification supplies the logarithmic failure-probability factor.

**Relation:** inherited output-estimation algorithm. The compiler must supply the implemented circuit, its exact gate inverse, success marking, and a reflection over the full initialized register. A probability oracle with uncharged preparation or reflection costs is not assumed.

## Classical comparison

The baseline must include tensor-network and observable-specific algorithms, not only exponentially large state vectors or sign-problem-limited Monte Carlo. Relevant primary demonstrations include:

- G. Vidal, *Efficient Simulation of One-Dimensional Quantum Many-Body Systems*, [Physical Review Letters 93, 040502 (2004)](https://doi.org/10.1103/PhysRevLett.93.040502), [arXiv:quant-ph/0310089](https://arxiv.org/abs/quant-ph/0310089). This supplies the time-evolving block-decimation method used as a numerical-method anchor in the benchmark account.
- B. Buyens, J. Haegeman, K. Van Acoleyen, H. Verschelde, F. Verstraete, *Matrix Product States for Gauge Field Theories*, [Physical Review Letters 113, 091601 (2014)](https://doi.org/10.1103/PhysRevLett.113.091601). This is an early gauge-invariant MPS formulation for the Schwinger model.
- B. Buyens, J. Haegeman, F. Hebenstreit, F. Verstraete, K. Van Acoleyen, *Real-time simulation of the Schwinger effect with matrix product states*, [Physical Review D 96, 114501 (2017)](https://doi.org/10.1103/PhysRevD.96.114501), [arXiv:1612.00739](https://arxiv.org/abs/1612.00739). Section II.B and Appendix A describe gauge-invariant MPS and real-time evolution. Appendix A.1, Eq.(A.2b), resolves virtual indices into electric-flux sectors; Appendix A.3 uses iTEBD with truncation of Schmidt values. Its electric quench starts from an interacting vacuum and is studied in the thermodynamic limit, so its numerical results are not automatically the same task as this repository's finite bare-vacuum quench.
- T. Pichler et al., *Real-Time Dynamics in U(1) Lattice Gauge Theories with Tensor Networks*, [Physical Review X 6, 011023 (2016)](https://doi.org/10.1103/PhysRevX.6.011023).
- A. Florio, D. Frenklakh, K. Ikeda, D. E. Kharzeev, V. Korepin, S. Shi, K. Yu, *Quantum real-time evolution of entanglement and hadronization in jet production: Lessons from the massive Schwinger model*, [Physical Review D 110, 094029 (2024)](https://doi.org/10.1103/PhysRevD.110.094029), [arXiv:2404.00087](https://arxiv.org/abs/2404.00087). The work uses classical MPS/TDVP for real-time dynamics and entanglement. The linked preprint has an earlier title beginning “Quantum simulation of entanglement”; the journal title is used here.
- K. Ikeda, Z.-B. Kang, D. E. Kharzeev, W. Qian, *Quantum simulation of real-time current correlators and DIS-inspired observables in the Schwinger model*, [JHEP07(2026)242](https://doi.org/10.1007/JHEP07(2026)242), [arXiv:2512.18062](https://arxiv.org/abs/2512.18062). Both quantum circuits and tensor-network methods are used for the same physical observables.

For a homogeneous product-state quench and fixed-time local density, causal-region restriction can eliminate dependence on the total chain length. Conversely, long-time entanglement growth motivates difficult instances but does not prove that their scalar observable is hard to calculate. Classical convergence and matched-error work must be measured instance by instance. No quantum–classical crossover is established in this repository solely from the gate theorem.

## Scope of this literature comparison

These sources establish the inherited simulation, gauge-constraint, estimation, and classical numerical ingredients, and identify concrete competing resource bounds. The comparison does not establish first priority or exhaust all low-width simulation constructions. A source providing a comparable compiler should be incorporated and the claimed distinction narrowed accordingly.
