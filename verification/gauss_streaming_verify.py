"""Independent finite-chain check of local Gauss decompression and prefix scans.

This tests equality to an explicitly specified product of native gauge-invariant
block unitaries, not the approximation error of HHKL itself. The native block
matrix is assembled by explicit matter flips and electric-link shifts. The
reference matrix is assembled independently in the globally eliminated basis.
"""

from collections import defaultdict
from functools import lru_cache
import json
from math import ceil, log2

import numpy as np
from scipy.linalg import expm
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import expm_multiply


E0, THETA, W, MASS, J = -1, 0.21, 0.63, 0.37, 0.29


def bit(matter, site):
    return (matter >> site) & 1


def charge(matter, site):
    return bit(matter, site) - (site % 2)


def prefix_charge(matter, stop):
    return sum(charge(matter, site) for site in range(stop))


def links_from_local(local, first, last, left_flux, total_sites):
    flux = left_flux
    links = []
    for site in range(first, last + 1):
        flux += ((local >> (site - first)) & 1) - (site % 2)
        if site < total_sites - 1:
            links.append(flux)
    return tuple(links)


@lru_cache(maxsize=None)
def native_block(first, last, left_flux, total_sites, time):
    width = last - first + 1
    basis = [
        (local, links_from_local(local, first, last, left_flux, total_sites))
        for local in range(1 << width)
    ]
    indices = {state: index for index, state in enumerate(basis)}
    hamiltonian = np.zeros((len(basis), len(basis)), dtype=complex)
    checked_shifts = 0
    for index, (local, links) in enumerate(basis):
        diagonal = sum(
            MASS * (-1) ** site * ((local >> (site - first)) & 1)
            for site in range(first, last + 1)
        )
        diagonal += J * sum((flux + THETA) ** 2 for flux in links)
        hamiltonian[index, index] = diagonal
        for offset in range(width - 1):
            left = (local >> offset) & 1
            right = (local >> (offset + 1)) & 1
            if left == right:
                continue
            changed = local ^ (1 << offset) ^ (1 << (offset + 1))
            changed_links = list(links)
            # Moving a fermion left (01 -> 10) raises this electric link.
            changed_links[offset] += right - left
            native_target = (changed, tuple(changed_links))
            assert native_target in indices, ('Gauss violation', native_target)
            hamiltonian[indices[native_target], index] += W
            checked_shifts += 1
    assert np.max(np.abs(hamiltonian - hamiltonian.conj().T)) == 0
    return basis, expm(-1j * time * hamiltonian), checked_shifts


def eliminated_block(total_sites, first, last):
    dimension = 1 << total_sites
    hamiltonian = lil_matrix((dimension, dimension), dtype=complex)
    for matter in range(dimension):
        diagonal = sum(
            MASS * (-1) ** site * bit(matter, site)
            for site in range(first, last + 1)
        )
        for link in range(first, min(last, total_sites - 2) + 1):
            flux = E0 + prefix_charge(matter, link + 1)
            diagonal += J * (flux + THETA) ** 2
        hamiltonian[matter, matter] = diagonal
        for site in range(first, last):
            if bit(matter, site) != bit(matter, site + 1):
                changed = matter ^ (1 << site) ^ (1 << (site + 1))
                hamiltonian[changed, matter] += W
    return hamiltonian.tocsr()


def move_prefix(state, old_start, new_start):
    result = defaultdict(complex)
    scanned_sites = abs(new_start - old_start)
    for (matter, prefix), amplitude in state.items():
        if new_start >= old_start:
            prefix += sum(charge(matter, i) for i in range(old_start, new_start))
        else:
            prefix -= sum(charge(matter, i) for i in range(new_start, old_start))
        assert prefix == prefix_charge(matter, new_start)
        result[(matter, prefix)] += amplitude
    return dict(result), scanned_sites


def streamed_block(state, total_sites, first, last, time):
    mask = ((1 << (last - first + 1)) - 1) << first
    groups = defaultdict(lambda: np.zeros(1 << (last - first + 1), dtype=complex))
    for (matter, prefix), amplitude in state.items():
        outside = matter & ~mask
        local = (matter & mask) >> first
        groups[(outside, prefix)][local] += amplitude
    result = defaultdict(complex)
    garbage_probability = 0.0
    checked_shifts = 0
    for (outside, prefix), amplitudes in groups.items():
        basis, unitary, shifts = native_block(first, last, E0 + prefix, total_sites, time)
        checked_shifts += shifts
        evolved = unitary @ amplitudes
        for (local, stored_links), amplitude in zip(basis, evolved):
            matter = outside | (local << first)
            # Inverse decompression uses the UPDATED matter occupations.
            expected_links = links_from_local(local, first, last, E0 + prefix, total_sites)
            residual = tuple(a - b for a, b in zip(stored_links, expected_links))
            if any(residual):
                garbage_probability += abs(amplitude) ** 2
            assert prefix == prefix_charge(matter, first)
            result[(matter, prefix)] += amplitude
    return dict(result), garbage_probability, checked_shifts


def schedule(total_sites):
    n = total_sites
    return [
        (0, min(2, n - 1), 0.19),
        (1, min(3, n - 1), -0.11),
        (max(0, n - 3), n - 1, 0.23),
        (0, 1, 0.07),
        (max(0, n // 2 - 1), min(n - 1, n // 2 + 1), -0.13),
        (n - 2, n - 1, 0.17),
    ]


def check_chain(total_sites, neutral_only, seed):
    rng = np.random.default_rng(seed)
    initial = rng.normal(size=1 << total_sites) + 1j * rng.normal(size=1 << total_sites)
    if neutral_only:
        for matter in range(1 << total_sites):
            if prefix_charge(matter, total_sites) != 0:
                initial[matter] = 0
    initial /= np.linalg.norm(initial)
    state = {(matter, 0): amplitude for matter, amplitude in enumerate(initial) if amplitude != 0}
    reference = initial.copy()
    start = 0
    scanned_sites = checked_shifts = 0
    garbage = maximum_intermediate_error = 0.0
    for first, last, time in schedule(total_sites):
        state, moved = move_prefix(state, start, first)
        scanned_sites += moved
        state, local_garbage, shifts = streamed_block(state, total_sites, first, last, time)
        garbage += local_garbage
        checked_shifts += shifts
        reference = expm_multiply(-1j * time * eliminated_block(total_sites, first, last), reference)
        actual = np.zeros_like(reference)
        for (matter, _prefix), amplitude in state.items():
            actual[matter] += amplitude
        maximum_intermediate_error = max(maximum_intermediate_error, float(np.linalg.norm(actual-reference)))
        start = first
    # Clean the prefix register using current, not original, matter.
    state, moved = move_prefix(state, start, 0)
    scanned_sites += moved
    assert all(prefix == 0 for _matter, prefix in state)
    actual = np.zeros_like(reference)
    for (matter, _prefix), amplitude in state.items():
        actual[matter] += amplitude
    occupations = np.array([sum(bit(matter, i) != (i % 2) for i in range(total_sites)) / total_sites
                            for matter in range(1 << total_sites)])
    electric_energy = np.array([sum((E0 + prefix_charge(matter, j + 1) + THETA) ** 2
                                    for j in range(total_sites - 1))
                               for matter in range(1 << total_sites)])
    return {
        'sites': total_sites,
        'input_sector': 'neutral_fixed_right_flux' if neutral_only else 'all_charge_sectors',
        'block_count': len(schedule(total_sites)),
        'maximum_block_matter_sites': max(last-first+1 for first,last,_time in schedule(total_sites)),
        'maximum_block_links': max(min(last,total_sites-2)-first+1 for first,last,_time in schedule(total_sites)),
        'prefix_sites_scanned_including_cleanup': scanned_sites,
        'explicit_native_hop_shifts_checked': checked_shifts,
        'link_garbage_probability': garbage,
        'final_prefix_nonzero_probability': 0.0,
        'state_l2_error': float(np.linalg.norm(actual-reference)),
        'max_intermediate_state_l2_error': maximum_intermediate_error,
        'norm_error': float(abs(np.linalg.norm(actual)-1)),
        'pair_density_error': float(abs(np.dot(abs(actual)**2, occupations)-np.dot(abs(reference)**2, occupations))),
        'electric_energy_error': float(abs(np.dot(abs(actual)**2,electric_energy)-np.dot(abs(reference)**2,electric_energy))),
    }


def wrong_old_matter_uncompute_witness():
    first, last, n, left_flux, time = 0, 1, 3, E0, 0.4
    basis, unitary, _ = native_block(first, last, left_flux, n, time)
    initial_local = 2  # occupations 01 in site order, so left hopping is possible
    initial_links = basis[initial_local][1]
    amplitudes = unitary[:, initial_local]
    garbage = sum(abs(amplitude)**2 for (_local, links), amplitude in zip(basis, amplitudes)
                  if links != initial_links)
    assert garbage > 1e-4
    return {'case': 'Subtracting old rather than updated matter flux',
            'nonzero_link_garbage_probability': float(garbage)}


def run_checks():
    cases = [check_chain(n, neutral, 20261111+n+100*neutral)
             for n in range(3,9) for neutral in (False, True)]
    assert max(case['state_l2_error'] for case in cases) < 1e-11
    return {
        'claim_tested': 'Exact streaming implementation of a given overlapping block-unitary product',
        'not_tested': ['HHKL decomposition error', 'logical or physical hardware runtime', 'classical advantage'],
        'parameters': {'left_flux': E0, 'theta': THETA, 'hopping': W, 'mass': MASS, 'electric': J},
        'convention': 'q_j = occupation_j - (j mod 2); E_j = e0 + sum_(k<=j) q_k',
        'block_assignment': 'mass on [a,b], outgoing electric links a..min(b,N-2), internal hopping a..b-1',
        'cases': cases,
        'diagnostic_bad_uncompute': wrong_old_matter_uncompute_witness(),
        'max_l2_error': max(case['state_l2_error'] for case in cases),
    }


if __name__ == '__main__':
    print(json.dumps(run_checks(), indent=2))
