"""Small, explicit U(1)-symmetric MPS reference for the open Schwinger chain.

No tensor-network package or Hamiltonian oracle is required.  Bond labels are
integer prefix charges.  Diagonal electric evolution is exact within this
representation; hopping is evolved with charge-preserving two-site gates.
The outer integrator is second-order symmetric splitting.  Truncation occurs
only in a mixed-canonical Schmidt decomposition, and discarded weights are
recorded.  This code is a validation reference, not an optimized MPS package.
"""

from dataclasses import dataclass
from itertools import combinations
from math import cos, sin, sqrt
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import expm_multiply


@dataclass(frozen=True)
class Parameters:
    sites: int
    hopping: float = 1.0
    mass: float = 0.2
    electric: float = 0.5
    background: float = 0.5
    left_flux: int = 0


def exact_problem(p):
    """CSR Hamiltonian in the neutral sector; site zero is the low integer bit."""
    n = p.sites
    if n % 2:
        raise ValueError('The benchmark uses even N and the neutral Neel state.')
    basis = np.array(sorted(sum(1 << j for j in occupied)
                            for occupied in combinations(range(n), n // 2)), dtype=np.int64)
    dimension = len(basis)
    occupations = ((basis[:, None] >> np.arange(n)) & 1).astype(np.int8)
    charges = occupations - (np.arange(n) % 2)
    fluxes = p.left_flux + np.cumsum(charges, axis=1)[:, :-1]
    diagonal = (p.mass * (occupations * ((-1.) ** np.arange(n))).sum(axis=1)
                + p.electric * ((fluxes + p.background) ** 2).sum(axis=1))
    rows, cols, data = [np.arange(dimension)], [np.arange(dimension)], [diagonal]
    for j in range(n - 1):
        selected = np.flatnonzero(occupations[:, j] != occupations[:, j + 1])
        changed = basis[selected] ^ ((1 << j) | (1 << (j + 1)))
        target = np.searchsorted(basis, changed)
        assert np.array_equal(basis[target], changed)
        rows.append(target)
        cols.append(selected)
        data.append(np.full(len(selected), p.hopping))
    hamiltonian = coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
                             shape=(dimension, dimension)).tocsr()
    initial = np.zeros(dimension, dtype=complex)
    initial_integer = sum(1 << j for j in range(1, n, 2))
    initial[np.searchsorted(basis, initial_integer)] = 1
    density_values = np.mean(occupations != (np.arange(n) % 2), axis=1)
    return basis, hamiltonian, initial, density_values


def exact_evolve(hamiltonian, initial, time, split=1):
    state = initial.copy()
    for _ in range(split):
        state = expm_multiply((-1j * time / split) * hamiltonian, state,
                              traceA=(-1j * time / split) * hamiltonian.diagonal().sum())
    return state


class ChargeMPS:
    def __init__(self, parameters, maximum_bond):
        self.p = parameters
        self.n = parameters.sites
        self.maximum_bond = maximum_bond
        self.tensors = []
        self.charges = [np.array([0], dtype=int)]
        for site in range(self.n):
            tensor = np.zeros((1, 2, 1), dtype=complex)
            tensor[0, site % 2, 0] = 1
            self.tensors.append(tensor)
            self.charges.append(np.array([0], dtype=int))
        self.center = 0
        self.two_site_updates = 0
        self.qr_blocks = 0
        self.svd_blocks = 0
        self.discarded_weight_sum = 0.0
        self.discarded_sqrt_sum = 0.0
        self.maximum_discarded_weight = 0.0
        self.maximum_realized_bond = 1
        self.maximum_pre_normalization_error = 0.0

    @staticmethod
    def _block_qr(matrix, row_labels, col_labels):
        """Reduced QR, separately in each conserved charge block."""
        pieces = []
        for charge in np.intersect1d(row_labels, col_labels):
            rows = np.flatnonzero(row_labels == charge)
            cols = np.flatnonzero(col_labels == charge)
            q, r = np.linalg.qr(matrix[np.ix_(rows, cols)], mode='reduced')
            pieces.append((int(charge), rows, cols, q, r))
        dimension = sum(piece[3].shape[1] for piece in pieces)
        q = np.zeros((matrix.shape[0], dimension), dtype=complex)
        r = np.zeros((dimension, matrix.shape[1]), dtype=complex)
        labels = np.empty(dimension, dtype=int)
        start = 0
        for charge, rows, cols, local_q, local_r in pieces:
            end = start + local_q.shape[1]
            q[np.ix_(rows, np.arange(start, end))] = local_q
            r[np.ix_(np.arange(start, end), cols)] = local_r
            labels[start:end] = charge
            start = end
        return q, r, labels, len(pieces)

    def position(self, target):
        while self.center < target:
            i = self.center
            a = self.tensors[i]
            dl, _, dr = a.shape
            rows = (self.charges[i][:, None] + np.arange(2)[None, :] - (i % 2)).ravel()
            q, r, labels, blocks = self._block_qr(a.reshape(dl * 2, dr), rows, self.charges[i + 1])
            self.tensors[i] = q.reshape(dl, 2, len(labels))
            self.tensors[i + 1] = np.einsum('ab,bsr->asr', r, self.tensors[i + 1], optimize=True)
            self.charges[i + 1] = labels
            self.qr_blocks += blocks
            self.center += 1
        while self.center > target:
            i = self.center
            a = self.tensors[i]
            dl, _, dr = a.shape
            cols = (self.charges[i + 1][None, :] - np.arange(2)[:, None] + (i % 2)).ravel()
            q, r, labels, blocks = self._block_qr(a.reshape(dl, 2 * dr).T, cols, self.charges[i])
            self.tensors[i] = q.T.reshape(len(labels), 2, dr)
            self.tensors[i - 1] = np.einsum('lsb,ba->lsa', self.tensors[i - 1], r.T, optimize=True)
            self.charges[i] = labels
            self.qr_blocks += blocks
            self.center -= 1

    def diagonal(self, time):
        for site, tensor in enumerate(self.tensors):
            physical_phase = np.exp(-1j * time * self.p.mass * ((-1) ** site) * np.arange(2))
            if site < self.n - 1:
                electric_phase = np.exp(-1j * time * self.p.electric *
                                        (self.p.left_flux + self.charges[site + 1] + self.p.background) ** 2)
            else:
                electric_phase = np.ones(tensor.shape[-1], dtype=complex)
            self.tensors[site] = tensor * physical_phase[None, :, None] * electric_phase[None, None, :]

    def hopping(self, first, time):
        self.position(first)
        a, b = self.tensors[first:first + 2]
        dl, _, _ = a.shape
        _, _, dr = b.shape
        theta = np.einsum('lsm,mtr->lstr', a, b, optimize=True)
        old01 = theta[:, 0, 1, :].copy()
        old10 = theta[:, 1, 0, :].copy()
        c, s = cos(self.p.hopping * time), -1j * sin(self.p.hopping * time)
        theta[:, 0, 1, :] = c * old01 + s * old10
        theta[:, 1, 0, :] = s * old01 + c * old10
        matrix = theta.reshape(dl * 2, 2 * dr)
        row_labels = (self.charges[first][:, None] + np.arange(2)[None, :] - (first % 2)).ravel()
        col_labels = (self.charges[first + 2][None, :] - np.arange(2)[:, None] + ((first + 1) % 2)).ravel()
        blocks, candidates = [], []
        for charge in np.intersect1d(row_labels, col_labels):
            rows = np.flatnonzero(row_labels == charge)
            cols = np.flatnonzero(col_labels == charge)
            u, singular, vh = np.linalg.svd(matrix[np.ix_(rows, cols)], full_matrices=False)
            block_index = len(blocks)
            blocks.append((int(charge), rows, cols, u, singular, vh))
            candidates.extend((float(value), block_index, k) for k, value in enumerate(singular))
        candidates.sort(key=lambda item: item[0], reverse=True)
        kept = candidates[:self.maximum_bond]
        total_weight = sum(value * value for value, _block, _index in candidates)
        lost_weight = sum(value * value for value, _block, _index in candidates[self.maximum_bond:])
        relative_lost = lost_weight / total_weight
        self.maximum_pre_normalization_error = max(self.maximum_pre_normalization_error, abs(total_weight - 1.))
        self.discarded_weight_sum += relative_lost
        self.discarded_sqrt_sum += sqrt(relative_lost)
        self.maximum_discarded_weight = max(self.maximum_discarded_weight, relative_lost)
        retained_norm = sqrt(total_weight - lost_weight)
        left = np.zeros((dl * 2, len(kept)), dtype=complex)
        right = np.zeros((len(kept), 2 * dr), dtype=complex)
        labels = np.empty(len(kept), dtype=int)
        for output, (value, block, index) in enumerate(kept):
            charge, rows, cols, u, _singular, vh = blocks[block]
            left[rows, output] = u[:, index]
            right[output, cols] = (value / retained_norm) * vh[index, :]
            labels[output] = charge
        self.tensors[first] = left.reshape(dl, 2, len(kept))
        self.tensors[first + 1] = right.reshape(len(kept), 2, dr)
        self.charges[first + 1] = labels
        self.center = first + 1
        self.two_site_updates += 1
        self.svd_blocks += len(blocks)
        self.maximum_realized_bond = max(self.maximum_realized_bond, len(kept))

    def evolve(self, time, steps):
        dt = time / steps
        for _ in range(steps):
            self.diagonal(dt / 2)
            for first in range(0, self.n - 1, 2):
                self.hopping(first, dt / 2)
            for first in reversed(range(1, self.n - 1, 2)):
                self.hopping(first, dt)
            for first in range(0, self.n - 1, 2):
                self.hopping(first, dt / 2)
            self.diagonal(dt / 2)
        return self

    def density(self):
        left = [np.ones((1, 1), dtype=complex)]
        for a in self.tensors:
            left.append(sum(a[:, s, :].conj().T @ left[-1] @ a[:, s, :] for s in range(2)))
        right = [None] * (self.n + 1)
        right[-1] = np.ones((1, 1), dtype=complex)
        for site in reversed(range(self.n)):
            a = self.tensors[site]
            right[site] = sum(a[:, s, :] @ right[site + 1] @ a[:, s, :].conj().T for s in range(2))
        norm = float(left[-1][0, 0].real)
        occupation = []
        for site, a in enumerate(self.tensors):
            value = np.trace(a[:, 1, :].conj().T @ left[site] @ a[:, 1, :] @ right[site + 1]).real / norm
            occupation.append(float(value))
        density = np.mean([value if site % 2 == 0 else 1 - value for site, value in enumerate(occupation)])
        return float(density), occupation, norm

    def dense(self):
        state = self.tensors[0][0, :, :]
        for a in self.tensors[1:]:
            state = np.einsum('am,msr->asr', state, a, optimize=True).reshape(-1, a.shape[-1])
        # Convert site-zero-first tensor order to the exact solver's low-bit order.
        return state[:, 0].reshape([2] * self.n).transpose(tuple(reversed(range(self.n)))).ravel()

    def report(self):
        self.position(self.n // 2)
        a = self.tensors[self.n // 2]
        singular = np.linalg.svd(a.reshape(a.shape[0], -1), compute_uv=False)
        probabilities = singular ** 2 / np.sum(singular ** 2)
        entropy = -float(np.sum(probabilities[probabilities > 0] * np.log(probabilities[probabilities > 0])))
        return {
            'maximum_bond_requested': self.maximum_bond,
            'maximum_bond_realized': self.maximum_realized_bond,
            'final_bond_dimensions': [len(charges) for charges in self.charges],
            'final_tensor_complex_entries': sum(tensor.size for tensor in self.tensors),
            'two_site_updates': self.two_site_updates,
            'svd_charge_blocks': self.svd_blocks,
            'qr_charge_blocks': self.qr_blocks,
            'discarded_weight_sum': self.discarded_weight_sum,
            'discarded_sqrt_sum': self.discarded_sqrt_sum,
            'bounded_observable_truncation_bound': min(1., self.discarded_sqrt_sum),
            'maximum_discarded_weight': self.maximum_discarded_weight,
            'maximum_pre_normalization_error': self.maximum_pre_normalization_error,
            'middle_cut_entropy_nats': entropy,
        }
