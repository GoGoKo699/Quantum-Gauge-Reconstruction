"""Exact arithmetic census for specified Gauss-reconstruction layouts.

Counts are in X/CNOT/Toffoli, for an explicit carry-chain increment and a simple
register adder built from it. They are not a fault-tolerant T count and do not include local native
Hamiltonian simulation, amplitude estimation, preparation, or readout.
The register allocation is exact for the stated layout and configurable native
workspace allowance.  Small-size basis-state tests validate every arithmetic
primitive used in the census.
"""

import argparse
from collections import Counter
import json
from math import ceil


def controlled_increment(target, control, scratch):
    """Compute carries, then update high-to-low and erase each carry early.

    The carry feeding target[k] is erased before target[k-1] changes. This
    gives exactly 2(B-1) Toffoli, B CNOT and B-1 clean scratch bits. The same
    primitive was independently verified by the alternative_algorithm worker.
    """
    assert len(scratch) >= len(target) - 1
    circuit = []
    for bit in range(1, len(target)):
        previous = control if bit == 1 else scratch[bit - 2]
        circuit.append(('ccx', (previous, target[bit - 1], scratch[bit - 1])))
    for bit in reversed(range(1, len(target))):
        previous = control if bit == 1 else scratch[bit - 2]
        circuit.append(('cx', (scratch[bit - 1], target[bit])))
        circuit.append(('ccx', (previous, target[bit - 1], scratch[bit - 1])))
    circuit.append(('cx', (control, target[0])))
    return circuit


def register_add(target, source, scratch):
    circuit = []
    for bit, control in enumerate(source):
        circuit.extend(controlled_increment(target[bit:], control, scratch))
    return circuit


def execute(circuit, integer):
    for gate, wires in circuit:
        if gate == 'x':
            integer ^= 1 << wires[0]
        elif all((integer >> control) & 1 for control in wires[:-1]):
            integer ^= 1 << wires[-1]
    return integer


def primitive_validation():
    results = []
    for bits in range(1, 7):
        target = list(range(bits))
        control = bits
        scratch = list(range(bits + 1, bits + 1 + max(0, bits - 1)))
        circuit = controlled_increment(target, control, scratch)
        counts = Counter(gate for gate, _wires in circuit)
        assert counts['cx'] == bits and counts['ccx'] == 2 * (bits - 1)
        for value in range(1 << bits):
            for flag in (0, 1):
                encoded = value | (flag << bits)
                expected = ((value + flag) % (1 << bits)) | (flag << bits)
                result = execute(circuit, encoded)
                assert result == expected
                assert execute(list(reversed(circuit)), result) == encoded
        results.append({'primitive': 'controlled modular increment', 'bits': bits,
                        'inputs_checked': 2 ** (bits + 1), 'counts': dict(counts),
                        'clean_scratch_bits': max(0, bits - 1)})
    for bits in range(1, 6):
        target, source = list(range(bits)), list(range(bits, 2 * bits))
        scratch = list(range(2 * bits, 2 * bits + max(0, bits - 1)))
        circuit = register_add(target, source, scratch)
        counts = Counter(gate for gate, _wires in circuit)
        expected_toffoli = (bits - 1) * bits
        assert counts['cx'] == bits * (bits + 1) // 2 and counts['ccx'] == expected_toffoli
        for x in range(1 << bits):
            for y in range(1 << bits):
                encoded = x | (y << bits)
                expected = ((x + y) % (1 << bits)) | (y << bits)
                result = execute(circuit, encoded)
                assert result == expected
                assert execute(list(reversed(circuit)), result) == encoded
        results.append({'primitive': 'in-place modular register addition', 'bits': bits,
                        'inputs_checked': 4 ** bits, 'counts': dict(counts),
                        'clean_scratch_bits': max(0, bits - 1)})
    return results


def signed_width(n, left_flux):
    # This bound covers every staggered matter basis state and every contiguous
    # block charge, including sum-tree nodes, not merely the chosen Neel quench.
    magnitude = ceil(n / 2) + abs(left_flux)
    bits = 1
    while (1 << (bits - 1)) - 1 < magnitude:
        bits += 1
    return bits


def multiply_counts(counts, times):
    return {name: value * times for name, value in counts.items()}


def count_gates(bits, charge_updates, register_adds, copied_bits, negative_control_x, initialization_x):
    return {
        'toffoli': charge_updates * 2 * (bits - 1)
                    + register_adds * (bits - 1) * bits,
        'cnot': charge_updates * bits + register_adds * bits * (bits + 1) // 2 + copied_bits,
        'x': negative_control_x + initialization_x,
    }


def one_layer(n, block_size, left_flux=0, native_workspace=0, width_multiple=3,
              repetitions=1):
    bits = signed_width(n, left_flux)
    blocks = [(first, min(first + block_size, n)) for first in range(0, n, block_size)]
    links = [max(0, min(last, n - 1) - first) for first, last in blocks]
    k = len(blocks)
    carry = max(0, bits - 1)
    initial_x = 2 * ((left_flux % (1 << bits)).bit_count())
    last_start = blocks[-1][0]

    # Each outgoing link is reconstructed once and cleaned once.  Moving the
    # incoming register right then cleaning it scans the final prefix twice.
    stream_updates = 2 * (n - 1) + 2 * last_start
    stream_copy = 2 * (n - 1) * bits
    stream_negative_x = 4 * ((n - 1) // 2 + last_start // 2)
    stream_registers = {'matter': n, 'incoming_flux': bits,
                        'temporary_links': max(links) * bits,
                        'shared_carry_or_native_work': max(carry, native_workspace)}
    stream_counts = count_gates(bits, stream_updates, 0, stream_copy,
                               stream_negative_x, initial_x)

    # Explicit balanced binary tree, K leaves and K-1 internal nodes.  Retain
    # every sum node and every prefix node.  Two register banks each have 2K-1
    # B-bit entries.  This layout is conservative but has a fully specified
    # reverse: prefix tree, sum tree, leaf totals from updated matter.
    cache_bits = (4 * k - 2) * bits
    cache_charge_updates = 2 * n + 2 * (n - 1)
    cache_adds = 4 * (k - 1)
    cache_copy = (6 * (k - 1) + 2 * (n - 1)) * bits
    cache_negative_x = 4 * (n // 2 + (n - 1) // 2)
    cache_counts = count_gates(bits, cache_charge_updates, cache_adds, cache_copy,
                              cache_negative_x, initial_x)
    build_carries = k * carry
    workspace_per_block = [link_count * bits + max(carry, native_workspace) for link_count in links]
    budget = width_multiple * n
    available = budget - n - cache_bits
    feasible = []
    if build_carries <= available:
        for active in range(1, k + 1):
            peak_batch_workspace = max(sum(workspace_per_block[start:start + active])
                                       for start in range(0, k, active))
            if peak_batch_workspace <= available:
                feasible.append((active, peak_batch_workspace))
    if feasible:
        active, simulation_workspace = feasible[-1]
        peak_workspace = max(build_carries, simulation_workspace)
        parallel = {'fits_declared_width_budget': True, 'active_blocks': active,
                    'batches': ceil(k / active), 'matter_bits': n,
                    'retained_conserved_cache_bits': cache_bits,
                    'shared_peak_workspace_bits': peak_workspace,
                    'peak_total_bits': n + cache_bits + peak_workspace,
                    'cache_build_carry_bits': build_carries,
                    'local_batch_workspace_bits': simulation_workspace}
    else:
        minimum_workspace = max(build_carries, max(workspace_per_block))
        parallel = {'fits_declared_width_budget': False, 'active_blocks': None, 'batches': None,
                    'minimum_one_block_total_bits': n + cache_bits + minimum_workspace,
                    'matter_bits': n, 'retained_conserved_cache_bits': cache_bits,
                    'minimum_shared_workspace_bits': minimum_workspace}

    # Synchronous depth at the level of the chosen arithmetic primitives;
    # these are not elementary-gate depth numbers.  Prefix/sum tree height is
    # at most ceil(log2 K), with separately allocated carries at each level.
    tree_height = (k - 1).bit_length()
    return {
        'parameters': {'sites': n, 'nominal_block_sites': block_size,
                       'left_flux': left_flux, 'bits_per_flux_or_total': bits,
                       'native_simulator_workspace_bits_per_active_block': native_workspace,
                       'parallel_total_width_budget_bits': budget,
                       'complete_layer_repetitions_counted': repetitions},
        'block_count': k, 'largest_block_sites': max(last - first for first, last in blocks),
        'largest_temporary_link_count': max(links),
        'persistent_native_system_bits': n + (n - 1) * bits,
        'persistent_native_plus_one_workspace_bits': n + (n - 1) * bits + native_workspace,
        'streaming': {'register_bits': stream_registers, 'total_bits': sum(stream_registers.values()),
                      'charge_controlled_unit_updates_per_layer': stream_updates,
                      'copied_bits_per_layer': stream_copy,
                      'register_additions_per_layer': 0,
                      'elementary_gates_per_layer': stream_counts,
                      'elementary_gates_all_repetitions': multiply_counts(stream_counts, repetitions)},
        'conserved_cache': {**parallel,
                            'charge_controlled_unit_updates_per_layer': cache_charge_updates,
                            'copied_bits_per_layer': cache_copy,
                            'register_additions_per_layer': cache_adds,
                            'tree_height': tree_height,
                            'elementary_gates_per_layer': cache_counts,
                            'elementary_gates_all_repetitions': multiply_counts(cache_counts, repetitions)},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sites', nargs='*', type=int, default=[64, 128, 256, 1024, 4096, 16384, 65536, 1048576])
    parser.add_argument('--block-sites', type=int)
    parser.add_argument('--left-flux', type=int, default=0)
    parser.add_argument('--native-workspace', type=int, default=0)
    parser.add_argument('--width-multiple', type=int, default=3)
    parser.add_argument('--repetitions', type=int, default=1)
    args = parser.parse_args()
    validation = primitive_validation()
    cases = [one_layer(n, min(n, args.block_sites or 8 * signed_width(n, args.left_flux)),
                       args.left_flux, args.native_workspace, args.width_multiple, args.repetitions)
             for n in args.sites]
    print(json.dumps({
        'scope': 'Reconstruction and conserved-cache bookkeeping for a specified disjoint block layer, with exact register allocation and explicit reversible arithmetic',
        'not_a_full_quantum_resource_estimate': ['Local native block simulation gates and ancillas are not derived here; a workspace allowance is an input',
                                               'No HHKL block length or repetition count is certified to a target simulation error by this census',
                                               'No logical synthesis, T count, code distance, routing, physical qubits, magic-state supply, or wall-clock estimate',
                                               'Input preparation, scalar readout, and amplitude-estimation repetitions are excluded unless explicitly added externally'],
        'arithmetic_implementation': {'controlled_increment': 'Compute B-1 carries ascending; descending, flip each target bit then erase its carry BEFORE the lower target bit changes; finally flip target bit zero',
                                      'controlled_increment_counts': 'B CNOT plus 2(B-1) Toffoli and B-1 clean carries; inverse has the same count',
                                      'register_add': 'For each source bit i, controlled increment target suffix i..B-1; B(B+1)/2 CNOT plus B(B-1) Toffoli; carries are reused',
                                      'charge_update': 'Even site: increment conditioned on b=1. Odd site: decrement conditioned on b=0, using two X gates to negate the control',
                                      'copy': 'B parallel CNOT gates into a clean B-bit register',
                                      'optimality': 'Explicit exact increment; the generic register adder is simple and is not claimed to be optimal'},
        'cache_layout': 'K complete block totals plus K-1 internal sum nodes; 2K-1 boundary-prefix tree nodes. All retained quantities depend only on conserved complete block totals. No within-block partial sum is retained.',
        'parallel_connectivity_assumption': 'Disjoint arithmetic and native blocks may run simultaneously with logical connectivity sufficient for the stated prefix tree; routing is uncounted',
        'width_choice': 'B is the smallest signed width with positive range at least ceil(N/2)+|e0|, conservatively covering all staggered basis states and tree totals',
        'default_block_choice': 'min(N,8B), chosen to illustrate an O(N) cache, not derived as an HHKL accuracy bound',
        'primitive_validation': validation,
        'cases': cases,
    }, indent=2))


if __name__ == '__main__':
    main()
