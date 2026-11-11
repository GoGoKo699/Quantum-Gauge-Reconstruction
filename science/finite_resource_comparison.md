# A finite resource comparison for a fixed block schedule

This comparison concerns the **same native local-block simulation factors, target unitary, cutoff encoding, and factor accuracy**. It isolates the cost of replacing permanent gauge-link storage with temporary reconstruction. It is not a numerical forecast for a chosen physical instance, and it does not claim a lower bound on competing encodings.

## Inputs to the comparison

Let the open chain have N matter sites and N−1 dynamical gauge links. Use the same b-bit integer representation for every link in both implementations. The valid range must contain all physical fluxes; for fixed incoming flux E_left it suffices that it contains [−(|E_left|+N), |E_left|+N].

Assume a certified HHKL factor schedule has R layers, with disjoint intervals inside each layer. Let L_max be the largest number of link registers reconstructed for one factor, including its outgoing diagonal-only link if the cell convention includes it. Let a be the maximum auxiliary width of the chosen coherent native block simulator, excluding its matter and link inputs. Its gate counts remain symbolic and are denoted G_native and T_native. The comparison serializes factors within each layer on both sides, so a single block workspace suffices.

The original HHKL one-dimensional construction supplies three such layers per constant-time segment. The analysis here also applies to any other certified schedule with these properties; it does not assume a numerical block size without a locality-error calculation.

## Explicit bounded-charge arithmetic

Write the staggered charge as q_j=z_j−s_j, where z_j is the matter occupation bit and s_j∈{0,1} is a known background. A charge update is either a controlled increment, or a controlled decrement conditioned on the occupation being zero.

For a b-bit register x, a controlled increment by c can be implemented using b−1 clean carry bits:

1. For k=1,...,b−1, compute c_k=c AND x_0 AND ... AND x_(k−1) into a fresh carry, using one Toffoli per k.
2. For k=b−1,...,1, flip x_k controlled on c_k, then erase c_k with its original Toffoli. The lower input bit x_(k−1) is still unchanged at this point.
3. Flip x_0 controlled on c.

This circuit uses exactly **2(b−1) Toffoli gates, b CNOT gates, and b−1 clean carry ancillas**. Reversing the gates implements controlled decrement. Conjugating the control with X implements the negative control, adding two X gates. Arithmetic is modular on the entire register, and agrees with signed addition on the valid physical range. No measurement or nonunitary reset is used.

The accompanying [controlled-increment check](../verification/verify_controlled_increment.py) exhaustively checks both staggered-charge cases for widths 1 through 10 against modular arithmetic, including cleanup and inverse operation. This is a deliberately simple circuit for transparent finite counts; it is not a claim of optimal arithmetic.

## Reconstructing a block

Retain the incoming flux P in a b-bit prefix register. For the first link of a block, copy P into a clean link register and add the first matter charge. For every subsequent link, copy the preceding link value into the next clean register and add the next charge.

For L reconstructed links, this is exactly L charge-update circuits plus Lb CNOTs. After the ideal restricted native block evolution, Gauss's law relates the new link values to the **updated** matter charges. Reversing this reconstruction therefore clears all L link registers. Reconstruction and erasure together cost 2L charge updates and 2Lb CNOTs.

## Prefix movement and per-layer overhead

At the start of a layer, initialize the prefix register to E_left. Process its disjoint intervals from left to right. Before the next interval, add each intervening current matter charge once to move the prefix to the next left boundary. No later block in that layer changes matter to the left of the cursor.

At the end of the layer, reverse this prefix scan using the current matter charges and erase the known E_left bit pattern. The forward and reverse scans use at most 2N charge updates. Since the intervals are disjoint, their reconstructed link counts sum to at most N. Therefore reconstruction and erasure use at most another 2N charge updates and 2Nb CNOTs.

An explicit upper bound for the **added** cost per layer is thus:

| Resource | Added upper bound |
|---|---:|
| Toffoli gates | 8N(b−1) |
| CNOT gates | 6Nb |
| X gates for negative controls | 8N |
| X gates initializing/erasing the fixed prefix | 2b |

For R layers multiply these bounds by R. If a particular fault-tolerant gate library assigns a cost tau_Toffoli to the exact Toffoli circuit, the corresponding additional T-count is at most 8RN(b−1) tau_Toffoli. The total T-count is **T_native plus this inherited-library overhead**, not a newly compiled absolute T-count for Schwinger simulation. More efficient adders can improve these constants.

## Width comparison

The serial native representation uses

```math
Q_{\mathrm{native}}=N+(N-1)b+a.
```

Temporary reconstruction uses

```math
Q_{\mathrm{reconstruct}}\le N+(L_{\max}+1)b+\max(a,b-1).
```

The b−1 carry bits and native simulation workspace can share physical qubits because they are used at different stages. This sharing is interpreted coherently: approximate leakage is covered by the clean-isometry hybrid argument, not by resetting the shared register.

Thus the finite width saving is at least

```math
(N-2-L_{\max})b-\max(0,b-1-a).
```

It is positive whenever that expression is positive. This is an auditable finite comparison for any supplied certified schedule. It does not require a guessed HHKL constant or an invented native T-count. If L_max approaches N, the saving can disappear; the asymptotic theorem alone does not certify a useful finite-instance saving.

## Coherent simulation accuracy

The inherited simulator must satisfy a **clean-isometry** guarantee, not merely a bound on its all-zero-to-all-zero matrix block. Let $`J_0`$ embed a system state with clean workspace, let V be the actual unitary, and let $`A=J_0^\dagger VJ_0`$. For a desired unitary U,

```math
\|A-U\|\le\eta
\quad\Longrightarrow\quad
\|VJ_0-J_0U\|\le\sqrt{2\eta}.
```

The squared error operator is $`2I-A^\dagger U-U^\dagger A`$, whose norm is at most $`2\eta`$. A target coherent error $`\delta`$ can therefore be obtained by choosing $`\eta=O(\delta^2)`$. See [the exact lemma and composition proof](streaming_gauss_theorem.md#5-coherent-error-control-with-reused-workspace).

This squares per-factor top-block tolerances when necessary but changes only logarithmic factors in the inherited interaction-picture gate bounds. It is essential when repeatedly reusing link and simulator ancillas without measurement. All actual operations remain unitary, and the total clean-input error is bounded by a telescoping comparison against the ideal clean trajectory.

## Preparation and output workspace

For a computational-basis quench input, preparation takes O(N) gates and no extensive additional workspace. Measuring the matter occupation string directly yields a density sample with no coherent readout workspace; classical processing takes O(N) operations per sample.

For amplitude estimation of a density, a k=ceil(log2(N+1))-bit population count can be computed by N of the explicit controlled increments above. Computing and uncomputing the count costs 4N(k−1) Toffolis and 2Nk CNOTs, plus the chosen comparator and uniform-index preparation. The count, carry, and comparator registers require O(log N) additional qubits. For arbitrary N, use q=ceil(log2 N) Hadamard bits for a threshold uniform on [0,2^q). The flag r<c has probability E[c]/2^q. Multiplication by the known factor 2^q/N, which is less than two, returns the desired density. No approximate uniform-[0,N) state is needed; see [the full readout construction](estimation.md).

The reflection about the full initial state also needs a low-width implementation. A linear-size multi-controlled reflection with one ancillary qubit follows from Nie, Zi, and Sun, arXiv:2402.05053, Section 3 / Theorem 1. Their one-ancilla construction uses bounded-size Toffoli primitives, unlike the distinct ancilla-free construction involving increasingly precise rotations. This keeps the readout/reflection overhead at N+polylogarithmic width. This is the reflection selected in [the end-to-end construction](estimation.md); a finite total cost must include it and the native block costs.

For a fair finite comparison, use the same readout and reflection construction on both native and reconstructed simulations. If it has r persistent extra qubits and a_read temporary workspace, replace a on both sides by max(a,a_read) and add r. Do not inherit Sakamoto et al.'s simulation-only N+O(log N) width as the width of its particular end-to-end estimator: its Result 3 explicitly adds a Theta(N)-ancilla reflection implementation.

## References

- Haah, Hastings, Kothari, Low, [arXiv:1801.03922](https://arxiv.org/pdf/1801.03922), Fig.1(a), proof of Theorem1, and Appendix B.
- Tong et al., [arXiv:2110.06942](https://arxiv.org/pdf/2110.06942), Appendix E.1 (native block simulation), Appendix I (cutoff-independent locality).
- Sakamoto et al., [arXiv:2311.17388v3](https://arxiv.org/html/2311.17388v3), Results 2–3 and Eq.(40) (simulation versus estimator workspace).
- Nie, Zi, Sun, [arXiv:2402.05053](https://arxiv.org/pdf/2402.05053), Section 3 / Theorem1 (low-width multi-controlled operations).
