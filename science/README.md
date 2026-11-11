# Scientific reading route

The central question is whether a locality-based gauge simulation can retain its favorable gate scaling while storing only matter between local factors. The construction is specific to a one-dimensional open chain with a known incoming flux.

Read [the compiler theorem](streaming_gauss_theorem.md) first. Sections 1–3 define the physical subspace, whole-term blocks and moving prefix. Sections 4–5 connect the native locality decomposition to coherent error composition. Sections 6–8 count the serial and parallel resources.

The theorem depends on [coherent native block circuits](coherent_native_blocks.md). That note opens the hopping block encoding, electric-energy fast-forwarding, compressed Dyson circuit and precision budget; these are charged circuit ingredients, not abstract cost-free oracles.

For a finite certified block schedule, [the resource comparison](finite_resource_comparison.md) gives width savings and exact arithmetic overhead without guessing an HHKL block constant or total T-count. [Density estimation](estimation.md) then fixes the preparation, scalar output and full error contract.

[Resource interpretation](interpretation.md) distinguishes the native storage comparison, the specified global interaction-picture baseline, and the best relevant classical alternatives. [Benchmarks](benchmarks.md) reports the finite checks and a classically tractable quench. Numerical agreement supports those finite implementations; the asymptotic theorem is supported by its proof and cited dependencies.

Return to the [repository overview](../README.md), [primary-source comparison](../references/RELATED_WORK.md), or [reproduction instructions](../verification/README.md).
