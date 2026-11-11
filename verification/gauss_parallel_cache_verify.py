"""Check conserved boundary caches for a disjoint Gauss-law block layer.

The useful cache contains complete block charges and functions of those charges.
A full site-by-site prefix cache is generally NOT conserved and cannot be erased
after the block update.  The script compares both cases on finite superpositions.
"""

from collections import defaultdict
import json

import numpy as np
from scipy.sparse.linalg import expm_multiply

from gauss_streaming_verify import E0, charge, native_block, eliminated_block


def blocks_for(n):
    return [(start, min(start + 2, n - 1)) for start in range(0, n, 3)]


def block_charges(matter, blocks):
    return tuple(sum(charge(matter, site) for site in range(a, b + 1)) for a, b in blocks)


def retained_cache(matter, blocks):
    """All cache values are functions of complete block totals only."""
    totals = block_charges(matter, blocks)
    boundaries = tuple(sum(totals[:k]) for k in range(len(totals)))
    # Include every node of a balanced sum tree, not just the leaf totals.
    tree = []
    level = list(totals)
    while level:
        tree.extend(level)
        if len(level) == 1:
            break
        level = [sum(level[k:k+2]) for k in range(0, len(level), 2)]
    return totals, boundaries, tuple(tree)


def internal_prefix_cache(matter, blocks):
    return tuple(sum(charge(matter, site) for site in range(a, j + 1))
                 for a, b in blocks for j in range(a, b))


def evolve_with_cache(initial, blocks, include_internal):
    n = int(np.log2(len(initial)))
    state = defaultdict(complex)
    for matter, amplitude in enumerate(initial):
        if amplitude != 0:
            good = retained_cache(matter, blocks)
            bad = internal_prefix_cache(matter, blocks) if include_internal else ()
            state[(matter, good, bad)] += amplitude
    reference = initial.copy()
    conserved_cache_assertions = 0
    for k, (first, last) in enumerate(blocks):
        time = .17 + .07 * k
        width = last - first + 1
        mask = ((1 << width) - 1) << first
        groups = defaultdict(lambda: np.zeros(1 << width, dtype=complex))
        for (matter, good, bad), amplitude in state.items():
            groups[(matter & ~mask, good, bad)][(matter & mask) >> first] += amplitude
        updated = defaultdict(complex)
        for (outside, good, bad), amplitudes in groups.items():
            _totals, boundaries, _tree = good
            basis, unitary, _ = native_block(first, last, E0 + boundaries[k], n, time)
            for (local, _links), amplitude in zip(basis, unitary @ amplitudes):
                if amplitude == 0:
                    continue
                matter = outside | (local << first)
                assert good == retained_cache(matter, blocks)
                conserved_cache_assertions += 1
                updated[(matter, good, bad)] += amplitude
        state = updated
        reference = expm_multiply(-1j * time * eliminated_block(n, first, last), reference)
    clean_amplitudes = np.zeros_like(reference)
    clean_probability = dirty_probability = 0.0
    for (matter, good, bad), amplitude in state.items():
        good_clears = good == retained_cache(matter, blocks)
        bad_clears = not include_internal or bad == internal_prefix_cache(matter, blocks)
        if good_clears and bad_clears:
            clean_amplitudes[matter] += amplitude
            clean_probability += abs(amplitude) ** 2
        else:
            dirty_probability += abs(amplitude) ** 2
    return {
        'sites': n,
        'blocks': blocks,
        'cache': 'block totals, boundary prefixes, tree, and WRONG internal prefixes'
                 if include_internal else 'block totals, boundary prefixes, and sum tree',
        'conserved_cache_assertions': conserved_cache_assertions,
        'clean_cache_probability': float(clean_probability),
        'dirty_cache_probability': float(dirty_probability),
        'clean_sector_state_l2_error': float(np.linalg.norm(clean_amplitudes-reference)),
    }


def main():
    rng = np.random.default_rng(20261111)
    cases = []
    for n in range(3, 9):
        initial = rng.normal(size=1 << n) + 1j * rng.normal(size=1 << n)
        initial /= np.linalg.norm(initial)
        case = evolve_with_cache(initial, blocks_for(n), False)
        assert case['dirty_cache_probability'] == 0
        assert case['clean_sector_state_l2_error'] < 1e-12
        cases.append(case)
    # Basis input gives a particularly transparent wrong-cache witness.
    initial = np.zeros(1 << 6, dtype=complex)
    initial[0b101010] = 1
    witness = evolve_with_cache(initial, blocks_for(6), True)
    assert witness['dirty_cache_probability'] > 1e-3
    print(json.dumps({
        'claim_tested': 'Complete block charges and their prefix/tree functions survive disjoint native block evolution and erase coherently',
        'cases': cases,
        'max_l2_error': max(case['clean_sector_state_l2_error'] for case in cases),
        'wrong_full_prefix_cache_witness': witness,
        'scope_limit': 'Exact local block matrices; this does not validate HHKL approximation, compiled arithmetic gates, hardware routing, or a classical advantage',
    }, indent=2))


if __name__ == '__main__':
    main()
