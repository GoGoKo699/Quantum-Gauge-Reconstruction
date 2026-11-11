"""Exhaustively verify the explicitly counted clean-carry increment circuit.

No external dependencies. This verifies arithmetic, cleanup, inverse, and gate
counts; it does not verify a Hamiltonian simulator or a fault-tolerant layout.
"""

import json


def controlled_increment_gates(width):
    """Indices: control 0, data 1..b, clean carries b+1..2b-1."""
    if width < 1:
        raise ValueError("width must be positive")
    gates = []
    for k in range(1, width):
        previous = 0 if k == 1 else width + k - 1
        gates.append(("ccx", previous, k, width + k))
    for k in range(width - 1, 0, -1):
        gates.append(("cx", width + k, k + 1))
        previous = 0 if k == 1 else width + k - 1
        gates.append(("ccx", previous, k, width + k))
    gates.append(("cx", 0, 1))
    return gates


def charge_gates(width, background):
    inc = controlled_increment_gates(width)
    if background == 0:
        return inc
    if background == 1:
        return [("x", 0)] + list(reversed(inc)) + [("x", 0)]
    raise ValueError("staggered background must be 0 or 1")


def apply(gates, state):
    for gate in gates:
        if gate[0] == "x":
            state ^= 1 << gate[1]
        elif gate[0] == "cx":
            _, control, target = gate
            if state >> control & 1:
                state ^= 1 << target
        elif gate[0] == "ccx":
            _, c1, c2, target = gate
            if state >> c1 & 1 and state >> c2 & 1:
                state ^= 1 << target
        else:
            raise ValueError(gate)
    return state


def main():
    rows = []
    total = 0
    for width in range(1, 11):
        cases = 0
        modulus = 1 << width
        for background in (0, 1):
            gates = charge_gates(width, background)
            counts = {kind: sum(g[0] == kind for g in gates)
                      for kind in ("ccx", "cx", "x")}
            assert counts == {"ccx": 2 * (width - 1),
                              "cx": width, "x": 2 * background}
            for occupation in (0, 1):
                for value in range(modulus):
                    initial = occupation | value << 1
                    actual = apply(gates, initial)
                    expected_value = (value + occupation - background) % modulus
                    expected = occupation | expected_value << 1
                    assert actual == expected, (width, background, occupation, value)
                    assert apply(list(reversed(gates)), actual) == initial
                    cases += 1
        total += cases
        rows.append({"width": width, "cases": cases,
                     "toffoli_per_charge_update": 2 * (width - 1),
                     "cnot_per_charge_update": width,
                     "clean_carries": width - 1})
    print(json.dumps({"status": "pass", "clean_basis_cases": total,
                      "widths": rows}, indent=2))


if __name__ == "__main__":
    main()
