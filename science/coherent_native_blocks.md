# Constructive coherent native-block simulation and precision accounting

This companion to [the streaming theorem](streaming_gauss_theorem.md) establishes the local circuit interface used there. It opens the required Hamiltonian oracle, counts temporary registers, specifies how a projected simulator is made into a coherent clean-input approximation, and accounts for numerical parameter and gate-synthesis errors. The selected primary simulation theorem is Low and Wiebe, *Hamiltonian Simulation in the Interaction Picture*, arXiv:1805.00675, Theorem 3 and Appendix B. It is not assumed to provide a clean-output unitary with the same error as its projected top block.

## 1. Local input and target

Consider an interval of $`s\ge1`$ matter cells, with $`L_I\le s`$ represented outgoing links, each stored in $`b`$ bits. Use the whole-term block convention of the main theorem. Write

```math
H_I=A_I+B_I,
```

where

**Equation (1).**

```math
A_I=m\sum_{j\in I}(-1)^j n_j+
 J\sum_{j\in\mathrm{links}(I)}(E_j+\theta I)^2
```

contains all on-site terms, including the outgoing boundary electric term, and

**Equation (2).**

```math
B_I=w\sum_{j=a}^{c-1}T_j,
 \quad
 T_j=\sigma_j^+U_j\sigma_{j+1}^-+
       \sigma_j^-U_j^\dagger\sigma_{j+1}^+.
```

The field range and hard-truncated shifts are those of the main theorem. Bounds valid on the **entire native register space**, not only the physical subspace, are

**Equation (3).**

```math
\|A_I\|\le
 s\left[|m|+|J|\bigl(2^{b-1}+|\theta|\bigr)^2\right]
 =:\alpha_A,
 \qquad \|T_j\|\le1.
```

Let $`|\tau|\le |w|^{-1}`$, as in a rescaled HHKL chunk, and let $`\eta`$ be the desired block clean-input isometry error. The diagonal cases $`w=0`$, $`s=1`$, or no internal hopping are implemented directly from (1); below assume that $`s\ge2`$ and $`w\ne0`$.

The circuit must satisfy, for every native input and every reference register,

**Equation (4).**

```math
\left\|V_I\bigl(|0\rangle_W|\psi\rangle\bigr)
       -|0\rangle_W e^{-i\tau H_I}|\psi\rangle\right\|
 \le\eta.
```

It need not return its work register exactly to zero, and it need not approximate $`I_W\otimes e^{-i\tau H_I}`$ on arbitrary nonzero work inputs. The main theorem's hybrid proof uses precisely (4), with no intermediate reset.

## 2. An explicit hopping block encoding

### 2.1 Each bond is a partial matching

For a fixed link field $`e`$, the bond operator exchanges

**Equation (5).**

```math
|0,1,e\rangle\longleftrightarrow|1,0,e+1\rangle
```

whenever both fields are in range. All other basis states are annihilated. Thus $`T_j^2=P_j`$, where $`P_j`$ is the projector onto the active endpoints of these disjoint pairs. Explicitly, the active predicate is

**Equation (6).**

```math
p_j(x,y,e)=
 [x=0,y=1,e\lt e_{\max}]
 \ \lor\ 
 [x=1,y=0,e>e_{\min}].
```

Let $`F_j`$ be the reversible permutation that performs the exchange (5) on active states and fixes inactive states. It is implementable in $`O(b)`$ elementary reversible gates and $`O(b)`$ scratch:

1. Compute (6) into one active flag with a clean reversible predicate subroutine: compute constant-endpoint comparisons, copy their Boolean combination to the flag, and uncompute all comparison scratch before changing any field or matter bit.
2. Conditioned on the active flag and the current left occupation being zero, increment the link. Conditioned on the active flag and the current left occupation being one, decrement it. The matter bits have not yet changed, so these mutually exclusive controls use the original direction.
3. Swap the two matter bits conditioned on the active flag.
4. Run the same clean predicate subroutine on the updated state to XOR (6) out of the active flag. The predicate itself is invariant under the matching exchange, so this clears the flag. Intermediate endpoint-comparison values need not be invariant; they were already uncomputed in step 1 and are freshly recomputed and erased within this final subroutine.

Controlled increments, decrements, and comparison with a known $`b`$-bit endpoint have linear gate and scratch cost. The exact charge-adder counts in the main theorem are one available implementation; extra constant controls change only a constant factor. No table lookup is needed.

Introduce one signal qubit $`a`$. The operator

**Equation (7).**

```math
V_j=P_jF_j\otimes I_a+(I-P_j)\otimes X_a
```

is a Hermitian unitary with

**Equation (8).**

```math
(\langle0|_a\otimes I)V_j(|0\rangle_a\otimes I)=T_j.
```

Implement it by applying the matching on active states and flipping the signal qubit on inactive states while the predicate is available. Because $`F_j`$ commutes with $`P_j`$, the same cleanup is valid. Equation (7) specifies a unitary on every native basis state, including endpoint and gauge-violating configurations.

### 2.2 Uniform padded LCU

Let $`Q=2^{\lceil\log_2(s-1)\rceil}`$, so $`s-1\le Q\lt 2(s-1)`$, with the natural equality case when $`s-1`$ is a power of two. Prepare a uniform $`\log_2Q`$-bit term index with Hadamards. For the $`s-1`$ real terms, select (7). For padded terms, select $`X_a`$, whose zero-signal top block is zero. Unprepare the index.

This gives an exact block encoding of $`B_I/\alpha_B`$ with

**Equation (9).**

```math
\alpha_B=Q|w|\le2s|w|.
```

The sign of $`w`$ is a known overall sign in the block encoding and is retained in controlled uses. It can equivalently be absorbed by a known alternating matter phase convention. Its implementation has constant gate overhead.

A direct SELECT implementation loops over the $`s-1`$ hard-coded neighboring bonds, computes equality of the index with the bond label, applies the corresponding controlled local circuit, and erases the equality flag. This uses

**Equation (10).**

```math
G_{B}=O\bigl(s(b+\log s)\bigr),\qquad
 a_B=O(b+\log s)
```

gates and auxiliary qubits. Matter and link wires have ordinary compiled addresses; no coherent random-access memory is assumed. A term register selects a short circuit on an interval of length $`s`$, rather than querying a database of the whole chain.

## 3. Explicit diagonal fast-forwarding, including a quantum clock

Let $`x_0,\ldots,x_{b-1}`$ be a link's two's-complement bits, and put

```math
\lambda_u=2^u\quad(u\lt b-1),\qquad
 \lambda_{b-1}=-2^{b-1},\qquad
 E=\sum_{u=0}^{b-1}\lambda_u x_u.
```

The exact quadratic expansion is

**Equation (11).**

```math
(E+\theta)^2
 =\theta^2+
   \sum_u(\lambda_u^2+2\theta\lambda_u)x_u
   +2\sum_{u\lt v}\lambda_u\lambda_v x_ux_v.
```

Consequently $`e^{-i\xi A_I}`$ is a product of $`O(sb^2)`$ known one- or two-bit phase gates, together with the known global scalar phase from the $`L_I\theta^2`$ term. In a controlled use that scalar becomes a relative phase and must be implemented. For an uncontrolled factor with an operator-norm phase convention, it can be implemented by a known phase on a reserved clean qubit; its constant workspace and gates are included in the bounds.

Let $`M`$ be a power of two, and let the time-index register encode $`v=\sum_{r=0}^{d-1}2^rv_r`$, with $`d=\log_2M`$. The coherent diagonal oracle

**Equation (12).**

```math
D_{h,M}=\sum_{v=0}^{M-1}|v\rangle\langle v|
        \otimes e^{-i A_I h v/M}
```

is constructed by multiplying each phase coefficient in (11) by $`h2^r/M`$ and controlling it on bit $`v_r`$. It uses

**Equation (13).**

```math
G_D=O(sb^2d)
```

bounded-arity phase gates and constant additional workspace. A quadratic field term controlled on a clock bit acts on at most three qubits. The mass term and scalar $`\theta^2`$ phase need at most two and one clock-controlled qubits, respectively. Each such gate has a constant-size decomposition into CNOTs and one-qubit rotations; adding a single outer control also changes the cost by only a constant factor.

This construction neither stores a table of $`M`$ phases nor explicitly computes a large energy integer. The number of time values may be large, but only $`d=\log_2M`$ clock bits and $`O(d)`$ copies of the bitwise phase pattern are used. The coefficients of these gates are classically computed from the specified finite numerical inputs.

In the streaming compiler, the native field registers already contain the incoming flux contribution. Thus (11) retains every phase that depends on the coherent incoming flux, including the outgoing boundary energy. No flux-dependent term is silently dropped as a global phase.

## 4. Interaction-picture oracle and short-segment parameters

Using (8)–(13), the Hamiltonian oracle required by Low–Wiebe is

**Equation (14).**

```math
\mathrm{HAM\!-\!T}
   =D_{h,M}^\dagger O_B D_{h,M},
```

whose zero-signal/index top block is

**Equation (15).**

```math
\sum_{v=0}^{M-1}|v\rangle\langle v|
 \otimes \frac{e^{i A_I h v/M}B_Ie^{-i A_I h v/M}}{\alpha_B}.
```

Its circuit cost is

**Equation (16).**

```math
G_{\rm HAM-T}=O\bigl(sb^2d+s(b+\log s)\bigr).
```

The time-dependent interaction Hamiltonian has

**Equation (17).**

```math
\max_u\|H_I^{\rm int}(u)\|\le\alpha_B,
 \qquad
 \left\|\frac{dH_I^{\rm int}(u)}{du}\right\|
   \le2\alpha_A\alpha_B.
```

For a block duration $`|\tau|`$, choose

**Equation (18).**

```math
r_I=\max\{1,\lceil2\alpha_B|\tau|\rceil\},
 \qquad h=|\tau|/r_I.
```

Then $`h\alpha_B\le1/2`$, and because $`|\tau|\le|w|^{-1}`$, $`r_I=O(s)`$. Each exact full-Hamiltonian segment is a short interaction-picture propagator followed by $`e^{-ihA_I}`$. Negative-time blocks use the signs reversed, or the inverse of a positive-time compiled circuit. If $`\|VJ_0-J_0U\|\le\eta`$ for a full system domain, then

**Equation (19).**

```math
\|V^\dagger J_0-J_0U^\dagger\|
 =\|J_0-VJ_0U^\dagger\|\le\eta,
```

so taking the inverse preserves the same clean-input guarantee.

Low–Wiebe Lemma 5 permits a Dyson truncation order

```math
K=O\!\left(\frac{\log(1/\rho)}{\log\log(1/\rho)}\right)
```

and a discretization satisfying, for an absolute constant $`C`$,

**Equation (20).**

```math
M\ge C\max\left\{
 K^2,\frac{h^2}{\rho}
       \left(2\alpha_A\alpha_B+\alpha_B^2\right)
 \right\}.
```

Round $`M`$ upward to a power of two. Since $`h\alpha_B\le1/2`$, a choice with

**Equation (21).**

```math
M=O\!\left(K^2+\frac{1+h\alpha_A}{\rho}\right)
```

is sufficient. All such quantities are determined classically from explicit couplings, duration, and the requested error; they are not problem-dependent oracles.

## 5. From the published top block to a fixed coherent block unitary

### The precise primary-theorem interface

Low–Wiebe Theorem 3 constructs a short-time truncated-Dyson operation with projected operator error $`\rho`$. The proof of their Corollary 4, Eq. (11), explicitly identifies its underlying unitary circuit $`V_j`$ and the projected operation

**Equation (22).**

```math
W_j=(\langle0|\otimes I)V_j(|0\rangle\otimes I).
```

Appendix B provides the controlled-product construction and robust oblivious amplitude amplification. The **compressed implementation in that theorem**, including the compression gadget of Lemma 13 and the OAA step of Lemma 14, is the one selected here. Its auxiliary-width bound is

**Equation (23).**

```math
O\!\left(a_B+
  \log\left[\frac{h^2}{\rho}
   \left(\langle\|\dot H\|\rangle+\max_u\|H(u)\|^2\right)\right]
 \right),
```

with harmless constants/lower bounds inside the logarithm. In particular, this does **not** use $`K`$ independently stored time registers of $`\log M`$ bits. Selecting an uncompressed Dyson implementation would change the width and depth polynomials and must not be substituted while retaining (23).

The published multi-segment discussion bounds projected error and failure probability after projection. For the present application, keep the entire fixed unitary OAA circuit and make **no measurement at all**. There is neither repeat-until-success control nor a fresh segment-environment register left behind at each step.

### Coherent lifting

For $`J_0|\psi\rangle=|0\rangle|\psi\rangle`$, if

```math
\|J_0^\dagger V_jJ_0-U_j\|\le\rho,
```

then the main theorem's Lemma 3 gives

**Equation (24).**

```math
\|V_jJ_0-J_0U_j\|\le\sqrt{2\rho}.
```

Choose

**Equation (25).**

```math
\rho=\eta^2/(8r_I^2).
```

Each short segment then has clean-input error at most $`\eta/(2r_I)`$. The ideal segment prefix has zero work, so the coherent hybrid argument composes all $`r_I`$ segments using the **same** work register and gives block error at most $`\eta/2`$. Exact on-site exponential factors preserve the norm and keep ideal work zero. Budget the other $`\eta/2`$ for ordinary gate synthesis of the full fixed circuit.

This proves (4). The actual short-segment outputs may contain nonzero workspace amplitude. It is neither measured nor erased; the next segment acts unitarily on it. The ideal-prefix/actual-suffix hybrid proves the bound without assuming correct behavior on this leakage component.

The square in (25) is essential to a coherent implementation with reusable scratch. It increases $`\log(1/\rho)`$ only by a constant factor relative to $`\log(r_I/\eta)`$. It therefore does not change the claimed soft asymptotic scaling.

## 6. Explicit conservative local gate and workspace bounds

Use the parameter $`P`$ of the main theorem. For its error assignment $`\eta=\Theta(\delta/M_{\rm factors})`$, all of the following hold:

```math
s=O(P),\quad b=O(P),\quad
 \log(1/\eta)=O(P),\quad r_I=O(s).
```

Equations (3), (21), and (25), together with $`h\le t`$, give

**Equation (26).**

```math
d=\log_2M=O(P),\qquad K=O(P),\qquad a_B=O(P).
```

Theorem 3 makes $`O(K)`$ queries to (14) per short segment, so there are $`O(sP)`$ such queries per block. Equation (16) costs at most $`O(sP^3)`$ primitive gates per query. The remaining theorem-provided gates use at most $`O(r_I(a_B+d)K)=O(sP^2)`$ primitives, and the $`r_I`$ outer diagonal exponentials cost at most $`O(s^2b^2)`$. Therefore a conservative total is

**Equation (27).**

```math
G_I=O(s^2P^4).
```

The native-system width is $`s+L_Ib`$. The selected compressed Dyson circuit and the explicitly opened oracle use only

**Equation (28).**

```math
a_I=O(a_B+d+\log K)=O(P)
```

additional qubits. In a streaming implementation, the complete local extra width, including links and prefix, is therefore $`O(sb+P)`$, as used in the main theorem.

Equations (27)–(28) are constructive asymptotic upper bounds, not finite T-counts. They deliberately avoid optimizing parallel phase layers, term-index selection, arithmetic constants, truncation degree, or OAA coefficients. The exact added reconstruction overhead is independently counted in the main theorem and the finite-resource comparison.

## 7. Numerical input errors and gate synthesis

### 7.1 Exact finite inputs versus physical parameters

The algorithm may take exact dyadic $`w,m,J,\theta,t`$ as its problem definition. If the desired physical values are real and rounded to $`\widetilde w,\widetilde m,\widetilde J,\widetilde\theta,\widetilde t`$, that approximation must be included in the error budget.

On the physical domain, all fields satisfy $`|E_j|\le F=|e_{\rm L}|+N`$. Let $`\Delta w=\widetilde w-w`$, and similarly for the other parameters. A direct triangle bound gives

**Equation (29).**

```math
\begin{split}
 \|H_{\rm red}-\widetilde H_{\rm red}\|
 \le{}&(N-1)|\Delta w|+N|\Delta m|\\
 &+(N-1)\left[
 |\Delta J|(F+|\theta|)^2
 +|\widetilde J|\,|\Delta\theta|
    (2F+|\theta|+|\widetilde\theta|)
 \right].
\end{split}
```

For time error as well,

**Equation (30).**

```math
\|e^{-itH_{\rm red}}-e^{-i\widetilde t\widetilde H_{\rm red}}\|
 \le t\|H_{\rm red}-\widetilde H_{\rm red}\|
    +|t-\widetilde t|\,\|\widetilde H_{\rm red}\|,
```

where a valid norm bound for the second term is

**Equation (31).**

```math
\|\widetilde H_{\rm red}\|
 \le (N-1)|\widetilde w|+N|\widetilde m|
 +(N-1)|\widetilde J|(F+|\widetilde\theta|)^2.
```

These are Duhamel/unitary perturbation bounds. They show explicitly how many coefficient fractional bits suffice. For bounded or polynomially scaling parameters, precision grows logarithmically in $`Nt/\delta`$ and the field magnitude. If input magnitudes or description lengths scale faster, the $`\beta`$ and logarithmic magnitude terms in $`P`$ charge them. The integer incoming flux and reversible charge arithmetic are exact.

### 7.2 Compilation of the fixed circuit

First define the ideal fixed circuit selected by the truncated-Dyson construction, with exact known one-qubit rotation angles. This circuit has the top-block and clean-input error established above. Then approximate each elementary rotation of a block to operator-norm error at most $`\eta/(2G_{\rm rot})`$, where $`G_{\rm rot}`$ bounds its total rotation count. A unitary circuit hybrid gives a further total error of at most $`\eta/2`$. Thus synthesis is not incorrectly fed through the square-root lifting bound a second time.

The bit expansion (11) can contain large angle coefficients. Reduction modulo $`2\pi`$ must be performed to the required **absolute angle error**, retaining enough classical precision for the coefficient magnitudes, the time numerator/denominator, and the synthesis target. Those bit lengths are $`O(P)`$ for the stated parameter family. Approximate preparation angles used inside the Dyson/OAA circuit are included in the same fixed-circuit synthesis budget.

For a chosen finite universal gate set, standard approximate one-qubit synthesis multiplies (27) by a polynomial in $`\log(G_{\rm rot}/\eta)`$, hence by a polynomial in $`P`$, with no extensive additional workspace. The theorem does not assert a finite T-count or a particular synthesis constant. A finite-resource claim must specify the gate library, angle compiler, exact HHKL intervals and durations, every local tolerance, and the selected Dyson/OAA implementation.

## 8. Controlled use and exact inverse

Every component above is a specified finite unitary circuit. Adding a single control to each bounded-arity elementary gate changes its decomposition cost by a constant factor; term-selection equality checks and sign phases must be controlled consistently. In particular, the $`\theta^2`$ phases and any Hamiltonian constant must not be omitted in such controlled use.

The inverse used by amplitude estimation is the gate-by-gate inverse of the **implemented** circuit, with its implemented rotation angles. It has exactly the same gate count and width. It is not a fresh approximation to the inverse target Hamiltonian. Therefore amplitude estimation has exact access, within the circuit model, to its own $`A`$ and $`A^\dagger`$, even though $`A`$ approximates the desired physical evolution and may coherently populate scratch registers.

Reflection about the input basis state must include every active register of $`A`$. The one clean ancilla used to synthesize that reflection is reserved outside $`A`$, or a separately justified dirty-ancilla construction is required. Treating potentially leaked simulator scratch as an actually clean reflection ancilla would invalidate exact amplitude amplification of the implemented $`A`$. This is why the main theorem explicitly reserves that extra qubit.

## 9. Dependency and scope record

The following pieces are inherited:

- native block locality and interaction-picture simulation of gauge dynamics: Tong et al., Appendix E.1 and Appendix I;
- the compressed truncated-Dyson/OAA circuit, its top-block approximation, and its workspace bound: Low–Wiebe Theorem 3 and Appendix B;
- standard finite-gate approximation of fixed one-qubit rotations.

The explicit hard-shift partial-matching dilation and quadratic-bit phase expansion above are elementary circuit constructions opening the required oracle for this theorem. They show that the oracle has polynomial-logarithmic cost on a small block and that coherent incoming flux does not require a data table. They are not presented as standalone novelty claims.

The new compiler uses these native blocks only temporarily, with exact local Gauss reconstruction, a moving incoming-flux cursor or invariant interval caches, and the coherent reuse proof. The principal result does not rely on a separate direct implementation of a fully gauge-eliminated local block. Such an alternative may be possible but is unnecessary for the theorem and its parallel batching bound.

### Primary sources

1. G. H. Low and N. Wiebe, *Hamiltonian Simulation in the Interaction Picture*, arXiv:1805.00675. Theorem 3, Corollary 4 Eq. (11), Lemmas 5–6, Appendix B including the compression gadget and robust OAA. <https://arxiv.org/abs/1805.00675>
2. Y. Tong, V. V. Albert, J. R. McClean, J. Preskill, and Y. Su, *Provably accurate simulation of gauge theories and bosonic systems*, Quantum **6**, 816 (2022), Appendix E.1 and Appendix I. <https://quantum-journal.org/papers/q-2022-09-22-816/>

