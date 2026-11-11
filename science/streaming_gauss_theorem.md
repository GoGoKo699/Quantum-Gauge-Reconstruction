# Streaming Gauss reconstruction for one-dimensional gauge dynamics

## Question and result

This note proves a space-efficient implementation of the existing locality-decomposed, interaction-picture quantum algorithm for real-time Schwinger dynamics. It does not introduce a new interaction-picture algorithm or a new electric-field truncation theorem. Its contribution is an exact interface between a matter-only representation and local native-gauge propagators, together with a schedule, coherent workspace-reuse proof, and resource accounting.

The principal result is a resource tradeoff. Under the explicit input-precision assumptions below, the serial implementation uses

```math
N+\operatorname{polylog}\text{ total qubits},\qquad
  \widetilde O\bigl(N(1+|w|t)\bigr)\text{ gates}.
```

A parallel implementation uses $`O(N)+\operatorname{polylog}`$ qubits and $`\widetilde O(1+|w|t)`$ logical depth on an all-to-all architecture. The existing native-gauge implementation already achieves this gate order; the improvement is avoiding permanent storage of all $`N-1`$ gauge links. Relative to the natural matter-only global interaction-picture composition, whose straightforward gate count is $`\widetilde O(N^2|w|t)`$, spatially local reconstruction removes one extensive factor. Neither statement establishes a quantum-versus-classical lower bound or a finite-instance hardware crossover.

All elementary arithmetic below is a reversible circuit. No measurement, postselection, reset, or discarded simulator workspace occurs inside the simulation unitary.

## 1. Model, boundary conditions, and exact encoding

Let $`N\ge 2`$ be the number of matter sites of an open chain, indexed by $`j=0,\ldots,N-1`$. Site $`j`$ has occupation operator $`n_j=|1\rangle\langle1|_j`$. Define occupation-raising and lowering operators by $`\sigma_j^+=|1\rangle\langle0|_j`$ and $`\sigma_j^-=|0\rangle\langle1|_j`$; these definitions fix the hopping sign convention independently of any spin-Z convention. Write

```math
s_j=j\bmod 2,\qquad q_j=n_j-s_j I.
```

Fix the incoming integer flux $`e_{\rm L}\in\mathbb Z`$. A background fractional flux is included in the real parameter $`\theta`$, rather than in the integer register. For a matter basis string $`z`$, define

```math
E_j(z)=e_{\rm L}+\sum_{k=0}^{j}(z_k-s_k),
 \qquad 0\le j\le N-2.
 \tag{1}
```

There are $`N-1`$ dynamical links. The exterior right flux would be

```math
E_{\rm R}(z)=e_{\rm L}+\sum_{k=0}^{N-1}(z_k-s_k).
```

Thus the full $`2^N`$-dimensional matter space fixes the incoming boundary only and is a direct sum of conserved total-charge/right-flux sectors. If both exterior fluxes are prescribed, the matter domain must be restricted to the corresponding total-charge sector. The results below hold on the full direct sum and hence on each such sector.

Put $`F=|e_{\rm L}|+N`$, and choose

```math
b=1+\left\lceil\log_2(F+2)\right\rceil.
 \tag{2}
```

A link register uses two's-complement integers in
$`\mathcal R_b=\{-2^{b-1},\ldots,2^{b-1}-1\}`$. This range contains every value in (1), with a margin at both endpoints. Let

```math
U_j=\sum_{e=-2^{b-1}}^{2^{b-1}-2}|e+1\rangle\langle e|_j
 \tag{3}
```

be the hard-truncated raising operator. It is a contraction, not a cyclic wraparound shift. We use the native Hamiltonian

```math
\begin{split}
 H={}& w\sum_{j=0}^{N-2}
   \left(\sigma_j^+ U_j\sigma_{j+1}^-+
         \sigma_j^- U_j^\dagger\sigma_{j+1}^+\right)\\
 &+m\sum_{j=0}^{N-1}(-1)^j n_j
   +J\sum_{j=0}^{N-2}(E_j+\theta I)^2,
 \end{split}
 \tag{4}
```

where $`w,m,J,\theta`$ are real. A conventional staggered-fermion phase or additive mass constant can be incorporated explicitly; it does not alter the construction. Additive constants must nevertheless be retained when a controlled-unitary or operator-norm contract is claimed.

Define the isometry

```math
\mathcal E|z\rangle
   =|z\rangle\bigotimes_{j=0}^{N-2}|E_j(z)\rangle.
 \tag{5}
```

Every hopping term in (4) maps a valid basis configuration to another valid basis configuration, or annihilates it. It changes the charge at its left endpoint by the same signed unit as its link field and changes the adjacent charge by the opposite unit. Diagonal terms preserve every basis configuration. Consequently $`\operatorname{im}\mathcal E`$ is invariant under $`H`$,

```math
H\mathcal E=\mathcal E H_{\rm red},\qquad
 e^{-itH}\mathcal E=\mathcal E e^{-itH_{\rm red}},
 \tag{6}
```

where $`H_{\rm red}=\mathcal E^\dagger H\mathcal E`$. No physically reachable transition touches a truncation endpoint, so (6) agrees exactly with the untruncated open-chain dynamics on this domain. There is no electric-tail approximation in this theorem.

The finite exact cutoff follows from Gauss's law and bounded matter charge; it is inherited structure. Nguyen et al., *Digital Quantum Simulation of the Schwinger Model and Symmetry Protection with Trapped Ions*, PRX Quantum **3**, 020324 (2022), Sec. II.B, explicitly give the sharper zero-incoming-flux cutoff $`\Lambda=N/2`$ for their convention. Equation (2) is a deliberately conservative uniform cutoff suitable for all incoming fluxes and charge sectors considered here. [Primary source](https://doi.org/10.1103/PRXQuantum.3.020324)

## 2. The local blocks to which the compiler applies

Group matter site $`j`$ and its outgoing link $`j`$ into cell $`j`$; the final cell has only its matter qubit. In this cell geometry, the mass and electric terms in (4) are on-site, and each hopping term acts on two adjacent cells.

For a cell interval $`I=[a,c]`$, define $`H_I`$ to be the sum of **whole terms of (4) whose cell support lies in $`I`$**. Equivalently, it contains:

- mass terms on sites $`a,\ldots,c`$;
- electric terms on links $`a,\ldots,\min(c,N-2)`$;
- hopping terms on bonds $`a,\ldots,c-1`$.

In particular, when $`c<N-1`$, the outgoing link $`c`$ is included for its electric energy even though there is no hopping across the right cut. No hopping crossing either cut is included. This assignment is exactly the restriction convention required by the HHKL decomposition; it avoids changing the Hamiltonian at the interface.

Let

```math
L_I=\max\{0,\min(c,N-2)-a+1\}
```

be the number of represented local links. For every block,

```math
[H_I,Q_I]=0,\qquad Q_I=\sum_{j=a}^{c}q_j.
 \tag{7}
```

The incoming flux $`E_{a-1}`$ is not acted on. The outgoing flux, when represented, is also unchanged: only internal hopping is allowed. Each block propagator preserves the full native physical subspace, even though adjacent blocks in the schedule may overlap.

### Lemma 1: local reconstruction and exact cleanup

Let a $`b`$-bit register $`P`$ contain the current incoming flux

```math
P_a(z)=e_{\rm L}+\sum_{k<a}(z_k-s_k).
 \tag{8}
```

Let $`D_I`$ be the reversible circuit that, into $`L_I`$ initially zero link registers, computes

```math
F_j=P+\sum_{k=a}^{j}(z_k-s_k),
 \qquad j=a,\ldots,\min(c,N-2),
 \tag{9}
```

while preserving the matter and $`P`$ registers. Let
$`U_I(\tau)=e^{-i\tau H_I}`$, with either sign of $`\tau`$. Then

```math
D_I^\dagger U_I(\tau)D_I
 \tag{10}
```

on the subspace (8) realizes the compressed native block action and returns every reconstructed link and every arithmetic carry to zero. It preserves the register $`P`$.

**Proof.** For each physically admissible incoming integer $`p`$ at site $`a`$, (9) defines a local Gauss-law isometry $`\mathcal E_I(p)`$. Internal hopping changes one represented field and its two adjacent charges consistently. The diagonal terms, including the outgoing electric term, preserve the local relation. Since total block charge is conserved, a represented outgoing field remains equal to its value calculated from the updated matter string. Thus

```math
U_I(\tau)\mathcal E_I(p)
   =\mathcal E_I(p)u_I(p,\tau)
```

for a unitary $`u_I(p,\tau)`$ on the matter block. Applying the inverse of the arithmetic circuit evaluates (9) on the **updated** matter, clearing the fields exactly. All omitted global fields are unchanged: those left of the interval depend on unchanged sites, and those right of it depend on the conserved total block charge. This identifies the action with $`\mathcal E^\dagger U_I(\tau)\mathcal E`$.

The proof is an isometry identity for every physically admissible $`p`$. It therefore holds when the incoming flux is a coherent register entangled with other blocks or an arbitrary reference. No classical measurement or selection of a flux sector is made. In particular, the $`p`$-dependent electric phases are retained. Terms such as $`JL_Ip^2`$ are not removable global phases on a superposition of incoming fluxes. ∎

The arithmetic can use modular two's-complement additions on the entire register. On the physical subspace, the range choice (2) makes their values the desired signed integers. The native block simulator is a unitary on its full register space, including invalid gauge configurations; its required approximation guarantee is uniform on that space, as established in the [native-block construction](coherent_native_blocks.md).

## 3. A prefix cursor that follows updated charges

Suppose the next block begins at site $`a`$, and $`P=P_a`$. After that exact block, $`P_a`$ is unchanged. To move to a block beginning at $`a'>a`$, apply

```math
P\longmapsto P+\sum_{j=a}^{a'-1}(z_j-s_j).
 \tag{11}
```

For $`a'<a`$, subtract the current charges on $`[a',a)`$. Equations (8) and (11) use the matter register **at the time of the move**. They do not rely on a record of the input configuration.

### Lemma 2: arbitrary cursor schedules

For any sequence of exact block propagators, possibly overlapping and with either time direction, the cursor update above maintains (8). If the block starts are $`a_1,\ldots,a_M`$, the total number of charge additions needed for initialization, movement, and final cleanup is

```math
O\!\left(N+\sum_{k=1}^{M-1}|a_{k+1}-a_k|\right).
 \tag{12}
```

**Proof.** A block beginning at $`a`$ changes no site strictly left of $`a`$, so it leaves (8) invariant. Adding or subtracting the current crossed charges is the algebraic difference between the two current prefixes. At completion, subtract all charges currently left of the cursor and remove the known bit string for $`e_{\rm L}`$. This returns $`P`$ to zero. The counts follow from the number of crossed sites. ∎

In a layer of disjoint intervals, the exact block propagators commute and can be processed from left to right. The forward cursor movement and its final cleanup cross at most $`2N`$ charges. Reconstruction and its inverse use at most another $`2N`$ charge additions and $`2Nb`$ copying CNOTs in that layer.

## 4. Native locality and the certified HHKL schedule

Let $`A`$ be the complete on-site mass-plus-electric part of (4), and let $`B`$ be its hopping part. In the interaction picture,

```math
B_I(s)=e^{iAs}Be^{-iAs}
```

has the same nearest-neighbor support as $`B`$, and each local term has the same operator norm $`|w|`$. The on-site conjugation also commutes with restricting the set of whole supported terms to a cell interval. Therefore a Lieb–Robinson bound and the HHKL factorization have constants independent of $`b`$, $`\|A\|`$, $`J`$, and $`m`$, after time is measured in units of $`|w|^{-1}`$.

This use of locality is justified by Tong et al., Appendix I, Lemma 13. That lemma explicitly removes an arbitrarily large on-site term from the locality constant. The original HHKL gate theorem is stated for bounded local qubit density; here it is the dimension-independent locality/factorization argument that is applied to cells of dimension $`2^{b+1}`$. Circuit costs depending on $`b`$ are then charged separately. [Tong et al.](https://quantum-journal.org/papers/q-2022-09-22-816/) [HHKL](https://arxiv.org/abs/1801.03922)

For $`w\ne0`$, split the time interval into

```math
r=\max\{1,\lceil |w|t\rceil\}
```

pieces of duration at most $`|w|^{-1}`$. For each piece, HHKL's one-dimensional construction supplies three layers of disjoint interval propagators, including inverse propagators. Its intervals have length $`O(\ell)`$, it has $`O(N/\ell)`$ factors when $`N\gg\ell`$, and its error is bounded by

```math
C(N/\ell)e^{-\mu\ell}
 \tag{13}
```

for universal rescaled-locality constants. Choose

```math
\ell_0=\left\lceil C_0\max\left\{b,\log\frac{Nr}{\delta}\right\}\right\rceil,
 \qquad L=\min\{N,\ell_0\},
 \tag{14}
```

with a sufficiently large constant $`C_0`$. The total factorization error is at most a prescribed fraction of $`\delta`$. If a block would fill the chain, use the whole-chain factor instead; there is then no spatial factorization error. The resulting schedule has at most $`3r`$ layers, maximum factor length $`O(L)`$, and

```math
M=O(rN/L)
 \tag{15}
```

factors, with the single-block convention when $`L=N`$.

The schedule and whole-term block convention are given in HHKL Fig. 1(a), Lemma 6 and the proof of Theorem 1; its Appendix B gives $`2\alpha-1=3`$ layers in one dimension. Choosing a larger overlap to satisfy $`\ell_0\ge b`$ only improves (13) and changes polynomial logarithmic factors. The three-layer claim is not a claim that all approximate circuits can be arbitrarily reordered: choose the spatial order of exact commuting factors first and compile that fixed schedule.

When $`w=0`$, all terms commute and the matter-only diagonal evolution can be implemented directly by a prefix scan and reversible energy arithmetic. This case needs neither HHKL nor Dyson segmentation, and satisfies the stated upper bounds with $`r=1`$.

## 5. Coherent error control with reused workspace

It is not sufficient to know that a simulator's projected top block approximates a desired unitary with error $`\eta`$. A projected error $`\eta`$ can correspond to coherent leakage of order $`\sqrt\eta`$. The following elementary lemma supplies the required interface.

### Lemma 3: top-block error lifts to a clean-input isometry error

Let $`J_0|\psi\rangle=|0\rangle_W|\psi\rangle`$, let $`V`$ be a unitary, and let $`U`$ be a desired system unitary. If

```math
A=J_0^\dagger VJ_0,\qquad \|A-U\|\le\rho,
```

then

```math
\|VJ_0-J_0U\|\le\sqrt{2\rho}.
 \tag{16}
```

**Proof.** Direct expansion gives

```math
(VJ_0-J_0U)^\dagger(VJ_0-J_0U)
  =2I-A^\dagger U-U^\dagger A.
```

Writing $`A=U+E`$, the right-hand side is $`-E^\dagger U-U^\dagger E`$, a positive operator with norm at most $`2\|E\|`$. Taking square roots proves (16). The bound is in operator norm and hence remains valid with an arbitrary reference register. ∎

Low and Wiebe's truncated-Dyson Theorem 3 and Appendix B provide a fixed unitary short-segment circuit whose zero-workspace top block has error $`\rho`$. Their Corollary 4 discusses projections between segments. Here no such projection is performed: retain the fixed OAA circuit and apply (16). If a native block has $`r_I`$ short segments, choose each segment's top-block error at most

```math
\rho=\frac{\eta_I^2}{8r_I^2},
 \tag{17}
```

and give ordinary gate synthesis a further total budget $`\eta_I/2`$. A segment then contributes at most $`\eta_I/(2r_I)`$ before synthesis. Squaring the tolerance in (17) changes only the logarithms in the published query, gate, and workspace bounds. [Low and Wiebe](https://arxiv.org/abs/1805.00675)

### Lemma 4: clean-input errors compose despite dirty actual workspace

Suppose $`W_1,\ldots,W_M`$ are exact unitary extensions of ideal compiled factors. Each ideal prefix, when applied to the specified input subspace, supplies the next factor's required zero workspace and valid prefix data. Suppose the actual unitary factor $`V_j`$ obeys

```math
\|(V_j-W_j)|\phi\rangle\|\le\eta_j
```

on that ideal input subspace. Then the total output error is at most $`\sum_j\eta_j`$.

**Proof.** Expand

```math
V_M\cdots V_1-W_M\cdots W_1
  =\sum_{j=1}^{M}
   V_M\cdots V_{j+1}(V_j-W_j)W_{j-1}\cdots W_1.
 \tag{18}
```

The prefix in each summand is ideal and therefore has the required clean workspace and invariants. The actual suffix is unitary and preserves the norm of that summand. The triangle inequality proves the claim. ∎

For a reconstructed block, take the ideal extension to be the exact unitary $`D_I^\dagger(U_I\otimes I_W)D_I`$, together with the exact cursor operations. The [native-block construction](coherent_native_blocks.md) constructs the actual native block circuit with the required uniform clean-input bound. Lemmas 1 and 2 give the ideal-prefix invariants used by Lemma 4.

The actual state need not have exactly zero links, carries, or Dyson registers after a factor. Those registers are reused as part of the same fixed circuit without resetting them. The proof never assumes correct arithmetic on the actual leakage component; its subsequent evolution is simply part of the unitary suffix in (18). This also permits arithmetic carries and simulator scratch to share the same qubits when their ideal uses occur at different times.

Choose $`\sum_I\eta_I\le\delta/3`$, assign $`\delta/3`$ to HHKL error, and reserve $`\delta/3`$ for parameter and remaining synthesis error. The full compiler then approximates $`e^{-itH_{\rm red}}`$ with state/isometry error at most $`\delta`$, uniformly on the chosen matter domain and any reference.

## 6. Exact arithmetic overhead for a fixed schedule

For a $`b`$-bit register, a controlled increment uses $`b-1`$ clean carry bits, exactly $`2(b-1)`$ Toffoli gates and $`b`$ CNOTs. Compute the carries of the lower unchanged bits, then flip bits and uncompute carries from high to low. The inverse gives controlled decrement. A negative control adds at most two X gates. Since $`q_j=z_j`$ on even sites and $`q_j=-(1-z_j)`$ on odd sites, this implements every needed charge update. This simple construction is chosen for transparent counts, not optimality.

For a factor with $`L_I`$ represented links, reconstruction consists of copying the incoming flux or preceding link into the next clean link, then adding the corresponding charge. Reconstruction and its inverse use $`2L_I`$ charge updates and $`2L_Ib`$ copying CNOTs. Summing over disjoint blocks and including the cursor scan and cleanup gives the following **added** per-layer upper bounds:

| Resource | Added per disjoint layer |
|---|---:|
| Toffoli gates | $`8N(b-1)`$ |
| CNOT gates | $`6Nb`$ |
| X gates from negative controls | $`8N`$ |
| Fixed-prefix initialization and erasure | at most $`2b`$ X gates |

Let $`a`$ be the maximum auxiliary width of the selected coherent native block circuit, excluding its matter and link inputs, and let $`L_{\max}`$ be the maximum represented-link count in the schedule. If factors are serialized on both implementations, their widths are

```math
Q_{\rm native}=N+(N-1)b+a,
 \tag{19}
```

```math
Q_{\rm stream}\le
 N+(L_{\max}+1)b+\max\{a,b-1\}.
 \tag{20}
```

Equation (20) counts a prefix register, temporary links, and shared carry/simulator scratch. It does not silently treat approximate scratch as exactly clean; Lemma 4 justifies its reuse. For $`R`$ layers, multiply the arithmetic overhead table by $`R`$. The native block T-count remains an inherited quantity. If a selected exact Toffoli synthesis has T-count $`T_{\rm Toff}`$, the added T-count is bounded by $`8RN(b-1)T_{\rm Toff}`$. No absolute Schwinger T-count is claimed without compiling the native block circuit, its rotation precision, and the actual HHKL schedule.

## 7. Parallel compilation with linear total width

The following implementation applies separately to each disjoint-block layer.

1. Partition the chain into the simulated block intervals and any unchanged gaps. Compute the total charge of each interval into a $`b`$-bit register. It is sufficient to use a serial controlled-increment scan inside each interval while computing all intervals in parallel. Uncompute every internal carry or site-prefix value before evolution.
2. Build a reversible balanced prefix tree from these interval totals. Copy the appropriate incoming flux into each simulated block's boundary cache. The tree, total registers, and boundary caches contain functions only of whole-interval charges.
3. Allocate a fixed set of complete native-block workspaces. Process the layer in batches of disjoint blocks, using their cached incoming fluxes for reconstruction. A workspace includes its temporary local links, all native simulation/OAA registers, and any carry workspace.
4. Erase the prefix tree and boundary caches, then recompute and erase the whole-interval charge registers using the updated matter.

Every exact block preserves its own interval total, and gaps are unchanged. Therefore every retained cache in step 2 is invariant under the ideal layer, and step 4 is exact on its ideal output. Retaining within-block site prefixes would be incorrect because hopping changes them. Lemma 4 covers approximate leakage while these caches and workspaces are reused; again, no reset is allowed.

There are $`B=O(N/L)`$ intervals/caches. For $`N\ge\ell_0`$, (14) gives $`L\ge b`$, so their total storage is $`O(Bb)=O(N)`$. For an explicit register adder, add each source bit by a controlled increment on the corresponding destination suffix. The charge-increment circuit above gives $`b(b-1)`$ Toffoli gates, $`b(b+1)/2`$ CNOTs, $`b-1`$ reusable carries, and depth $`O(b^2)`$ for a full $`b`$-bit addition. Reversible block-total scans and a prefix tree therefore use $`O(Nb+Bb^2)\subseteq O(Nb^2)`$ gates. A serial scan within each block has depth $`O(Lb)`$, and a balanced tree of these adders has depth $`O(b^2\log B)`$; both are polynomial in the parameter $`P`$ below.

Let $`W`$ bound the additional workspace for one block, including reconstructed fields. Allocate $`p=\max\{1,\lfloor N/W\rfloor\}`$ such workspaces. If $`W>N`$, allocate one and count its width separately. In either case, the number of batches is

```math
O\!\left(1+\frac{W}{L}\right).
 \tag{21}
```

Indeed, when $`N/W\ge2`$, $`p\ge N/(2W)`$; otherwise $`B=O(N/L)=O(W/L)`$. Since the local circuit below has $`W=O(Lb+P)`$, (21) is polynomial logarithmic. The total width is $`O(N)+O(P^2)`$, including the small-instance case. The original native algorithm's fine parallelism may incur additional polynomial-logarithmic batching factors; only the stated asymptotic depth is claimed.

## 8. Resource theorem with explicit precision dependence

Assume the numerical parameters $`w,m,J,\theta,t`$ are supplied as exact dyadic rationals of total bit length at most $`\beta`$, or are rounded to that form with the parameter-error budget in the [native-block construction](coherent_native_blocks.md). They are compiled into known circuit angles; no coherent QRAM oracle or uncharged parameter table is assumed.

Let $`0<\delta<1/4`$, $`t\ge0`$, $`r=\max\{1,\lceil |w|t\rceil\}`$, and define

```math
\begin{split}
 \kappa&=|m|+|J|\bigl(2^{b-1}+|\theta|\bigr)^2+|w|,\\
 P&=2+b+\beta+
  \left\lceil\log_2\frac{Nr}{\delta}\right\rceil+
  \left\lceil\log_2(2+t\kappa)\right\rceil.
 \end{split}
 \tag{22}
```

All gate bounds below count Toffoli, CNOT, and bounded-arity known-angle phase gates as constant-size primitives. Equivalently, one may count arbitrary one-qubit rotations and CNOTs after constant-size decomposition. The companion construction supplies a native block of $`s=O(L)`$ cells with

```math
G_I=O(s^2P^4),\qquad
 a_I=O(P),
 \tag{23}
```

in addition to its $`s`$ matter qubits and $`O(sb)`$ link qubits. These exponents are conservative circuit upper bounds, not optimized finite resource estimates.

### Theorem 5: streaming and batched simulation

There are fixed coherent circuits whose clean-input isometry error relative to $`e^{-itH_{\rm red}}`$ is at most $`\delta`$, with the following primitive resource bounds:

| Compiler | Gates | Qubits | Logical depth |
|---|---:|---:|---:|
| Serial prefix cursor | $`O(NrP^5)`$ | $`N+O(P^2)`$ | at most $`O(NrP^5)`$ |
| Batched disjoint layers | $`O(NrP^5)`$ | $`O(N)+O(P^2)`$ | $`O(rP^7)`$ |

The depth claim assumes all-to-all logical connectivity and parallel execution on disjoint registers. A fixed finite universal gate set adds a polynomial in $`P`$ through standard one-qubit gate synthesis, without changing the width order or the dependence on the extensive factor $`Nr`$.

**Proof.** Equations (14) and (22) give $`L=O(P)`$. There are $`O(rN/L)`$ factors, each costing $`O(L^2P^4)`$, for $`O(NrLP^4)\subseteq O(NrP^5)`$ gates. The added scans, arithmetic, and parallel caches cost at most $`O(Nrb^2)`$. Equation (20), (23), and $`L,b=O(P)`$ give serial width $`N+O(P^2)`$.

For the batched version, $`W=O(Lb+P)`$, so (21) gives $`O(P)`$ batches. A block has depth no greater than its $`O(L^2P^4)`$ gate count. The prefix computation adds $`O(Lb+b^2\log N)`$ depth per layer. With $`L\le O(P)`$, this is at most $`O(P^7)`$ depth per layer and $`O(rP^7)`$ total. Width follows from the invariant-cache construction and the workspace allocation. Lemmas 1–4 and the error allocation prove the isometry guarantee. ∎

The phrase “near-linear spacetime gates” means $`\widetilde O(N(1+|w|t))`$ only when $`b`$, the coefficient-description length, and the relevant magnitude/precision logarithms are themselves polynomial logarithmic in the intended asymptotic family. Arbitrarily long numerical input descriptions are explicitly charged in (22). The theorem makes no nearest-neighbor hardware routing claim and no finite-constant advantage claim. For $`N`$ comparable to the block length or local workspace, the memory benefit can disappear.

## Complete task and comparison

[Density estimation](estimation.md) gives the explicit input, reversible scalar readout, exact inverse/reflection contract, and total preparation-to-output cost. [Resource interpretation](interpretation.md) distinguishes the native storage comparison, the specified global interaction-picture comparator, the classical alternatives, and continuum and architecture limits. [Benchmarks](benchmarks.md) reports the finite quench and reconstruction census.

## Primary theorem dependencies

1. Haah, Hastings, Kothari, and Low, *Quantum algorithm for simulating real time evolution of lattice Hamiltonians*, arXiv:1801.03922: Lemmas 5–6, Fig. 1, Theorem 1 proof, Appendix B. <https://arxiv.org/abs/1801.03922>
2. Tong, Albert, McClean, Preskill, and Su, *Provably accurate simulation of gauge theories and bosonic systems*, Quantum **6**, 816 (2022): Appendix E.1 and Appendix I, Lemma 13. <https://quantum-journal.org/papers/q-2022-09-22-816/>
3. Low and Wiebe, *Hamiltonian Simulation in the Interaction Picture*, arXiv:1805.00675: Theorem 3, Corollary 4, Lemma 6, and Appendix B. The projection-based multi-segment interpretation is replaced here by Lemmas 3–4 and the squared top-block tolerance. <https://arxiv.org/abs/1805.00675>
4. Nguyen et al., *Digital Quantum Simulation of the Schwinger Model and Symmetry Protection with Trapped Ions*, PRX Quantum **3**, 020324 (2022): Sec. II.B exact open-boundary cutoff. <https://doi.org/10.1103/PRXQuantum.3.020324>
5. Nie, Zi, and Sun, *Quantum circuit for multi-qubit Toffoli gate with optimal resource*, arXiv:2402.05053: Sec. 3, Theorem 1. <https://arxiv.org/abs/2402.05053>
6. Brassard, Høyer, Mosca, and Tapp, *Quantum Amplitude Amplification and Estimation*, arXiv:quant-ph/0005055. <https://arxiv.org/abs/quant-ph/0005055>

The arithmetic counts are derived explicitly above and independently checked in the companion finite-resource work. The constants and rotation counts of the complete native block simulator have not been compiled for a physical benchmark; the displayed polynomial resource exponents are asymptotic upper bounds.
