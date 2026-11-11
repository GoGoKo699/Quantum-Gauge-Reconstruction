"""Reproduce matched-accuracy classical Schwinger-quench validation.

Usage: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python schwinger_benchmark.py
The output is a JSON document.  The default finite benchmark is deliberately
tractable; its timings are not evidence of a quantum/classical crossover.
"""

import argparse
from dataclasses import asdict
import json
import platform
import time
import numpy as np
import scipy

from schwinger_mps import Parameters, ChargeMPS, exact_problem, exact_evolve


def split_reference(p, basis, hamiltonian, initial, duration, steps):
    """Independent state-vector implementation of the same symmetric product."""
    state = initial.copy()
    dt = duration / steps
    diagonal = hamiltonian.diagonal()
    def hopping(first, gate_time):
        nonlocal state
        selected = np.flatnonzero(((basis >> first) & 1) == 0)
        selected = selected[((basis[selected] >> (first + 1)) & 1) == 1]
        target = np.searchsorted(basis, basis[selected] ^ ((1 << first) | (1 << (first + 1))))
        old01, old10 = state[selected].copy(), state[target].copy()
        c, s = np.cos(p.hopping * gate_time), -1j * np.sin(p.hopping * gate_time)
        state[selected], state[target] = c * old01 + s * old10, s * old01 + c * old10
    for _ in range(steps):
        state *= np.exp(-1j * dt * diagonal / 2)
        for first in range(0, p.sites - 1, 2):
            hopping(first, dt / 2)
        for first in reversed(range(1, p.sites - 1, 2)):
            hopping(first, dt)
        for first in range(0, p.sites - 1, 2):
            hopping(first, dt / 2)
        state *= np.exp(-1j * dt * diagonal / 2)
    return state


def implementation_validation():
    cases = []
    for n in (4, 6, 8):
        for steps in (1, 4):
            p = Parameters(n)
            basis, h, initial, observable = exact_problem(p)
            values, vectors = np.linalg.eigh(h.toarray())
            spectral = vectors @ (np.exp(-1j * .73 * values) * (vectors.conj().T @ initial))
            exponential = exact_evolve(h, initial, .73)
            independent_reference_error = float(np.linalg.norm(spectral-exponential))
            assert independent_reference_error < 1e-12
            split = split_reference(p, basis, h, initial, .73, steps)
            mps = ChargeMPS(p, 2 ** (n // 2)).evolve(.73, steps)
            dense = mps.dense()
            density, occupations, norm = mps.density()
            error = float(np.linalg.norm(dense[basis] - split))
            expectation_error = float(abs(density - np.dot(abs(split) ** 2, observable)))
            assert error < 1e-12
            assert expectation_error < 1e-12
            cases.append({'sites': n, 'steps': steps, 'state_l2_error_against_independent_split': error,
                          'sparse_exponential_vs_dense_eigendecomposition_error': independent_reference_error,
                          'density_error_against_independent_split': expectation_error,
                          'norm_error': abs(norm - 1),
                          'total_occupation_error': abs(sum(occupations) - n / 2)})
    return cases


def run_case(n, duration, configurations, target_error):
    p = Parameters(n)
    before = time.perf_counter()
    basis, h, initial, observable = exact_problem(p)
    setup_seconds = time.perf_counter() - before
    before = time.perf_counter()
    reference = exact_evolve(h, initial, duration)
    exact_seconds = time.perf_counter() - before
    before = time.perf_counter()
    split_check = exact_evolve(h, initial, duration, split=2)
    exact_validation_seconds = time.perf_counter() - before
    norm = float(np.linalg.norm(reference))
    exact_density = float(np.dot(abs(reference) ** 2, observable))
    reference_agreement = float(np.linalg.norm(reference-split_check))
    assert reference_agreement < 1e-10
    assert abs(norm - 1) < 1e-10
    runs = []
    for steps, bond in configurations:
        before = time.perf_counter()
        mps = ChargeMPS(p, bond).evolve(duration, steps)
        evolution_seconds = time.perf_counter() - before
        before = time.perf_counter()
        density, occupations, mps_norm = mps.density()
        dense = mps.dense()
        amplitudes = dense[basis]
        report = mps.report()
        readout_seconds = time.perf_counter() - before
        density_error = abs(density - exact_density)
        state_error = float(np.linalg.norm(amplitudes - reference))
        sector_probability = float(np.sum(abs(amplitudes) ** 2))
        total_probability = float(np.sum(abs(dense) ** 2))
        report.update({
            'steps': steps, 'time_step': duration / steps,
            'density': density, 'density_absolute_error': density_error,
            'meets_density_target': density_error <= target_error,
            'state_l2_error': state_error,
            'state_fidelity': float(abs(np.vdot(reference, amplitudes)) ** 2),
            'charge_sector_leakage_probability': max(0., total_probability - sector_probability),
            'norm_error': abs(mps_norm - 1),
            'total_occupation_error': abs(sum(occupations) - n / 2),
            'site_occupations': occupations,
            'evolution_seconds': evolution_seconds,
            'density_dense_validation_and_report_seconds': readout_seconds,
        })
        runs.append(report)
    return {
        'parameters': asdict(p), 'time': duration, 'target_density_additive_error': target_error,
        'neutral_sector_dimension': len(basis), 'hamiltonian_nonzeros': h.nnz,
        'csr_array_bytes': h.data.nbytes + h.indices.nbytes + h.indptr.nbytes,
        'exact_state_array_bytes': reference.nbytes,
        'exact_density': exact_density, 'exact_norm_error': abs(norm - 1),
        'exact_direct_vs_two_half_steps_state_error': reference_agreement,
        'exact_hamiltonian_setup_seconds': setup_seconds,
        'exact_evolution_seconds': exact_seconds,
        'exact_half_step_validation_seconds': exact_validation_seconds,
        'mps_runs': runs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args()
    validations = implementation_validation()
    if args.pilot:
        cases = [run_case(12, 2., [(32, 8), (64, 8), (64, 16), (128, 16)], 1e-3)]
    else:
        cases = [
            run_case(8, 2., [(128, 16)], 1e-3),
            run_case(12, 2., [(128, 32)], 1e-3),
            run_case(16, 2., [(16, 64), (32, 64), (64, 64), (128, 64),
                             (128, 4), (128, 8), (128, 16), (128, 32)], 1e-3),
            run_case(20, 2., [(64, 32), (128, 32), (128, 64)], 1e-3),
        ]
    print(json.dumps({
        'task': 'Mean staggered excitation density after a finite open-chain hopping quench',
        'hamiltonian': 'w sum_j (sigma+_j sigma-_j+1 + h.c.) + m sum_j (-1)^j b_j + J sum_(j=0)^(N-2) (e0 + sum_(k<=j)(b_k-k mod 2) + alpha)^2',
        'input': 'Pure Neel product state b_j = j mod 2, fixed left flux e0=0, zero total charge; exact ground state at pre-quench hopping w=0 for the specified m>0,J>0,alpha=1/2',
        'quench': 'At time zero change only the hopping from w=0 to w=1; hold mass, electric coupling, and background fixed',
        'observable': 'R = (1/N) sum_j 1{b_j != j mod 2}, in [0,1]',
        'units': 'hbar=1 and hopping w=1; no continuum extrapolation',
        'exact_method': 'SciPy expm_multiply on explicit neutral-sector CSR Hamiltonian, checked against two half-time applications and against dense Hermitian eigendecomposition at N=4,6,8',
        'mps_method': 'Explicit charge-resolved mixed-canonical MPS; exact diagonal electric/mass phases and second-order D/2-even/2-odd-even/2-D/2 hopping splitting',
        'mps_error_controls': 'Separate time-step and bond-dimension sweeps; normalized Schmidt truncation weights; independent full-state split-product validation and exact sparse comparison',
        'truncation_bound_scope': 'Sum of square roots of normalized discarded Schmidt weights bounds a [0,1] observable error against the same untruncated split product, in exact arithmetic; it excludes splitting and floating-point error',
        'timing_scope': 'Single local CPU runs including stated phases; no hardware/runtime crossover inference; code is a validation reference, not an optimized MPS implementation',
        'dependencies': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
        'primary_method_references': ['https://doi.org/10.1103/PhysRevLett.93.040502',
                                      'https://doi.org/10.1103/PhysRevLett.113.091601',
                                      'https://doi.org/10.1103/PhysRevD.96.114501'],
        'implementation_validation': validations,
        'cases': cases,
    }, indent=2))


if __name__ == '__main__':
    main()
