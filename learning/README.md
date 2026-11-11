# Learning route

The question is how a quantum simulation can use a local gauge-field description while keeping only the matter data between local factors. The route begins with registers and reversible computation, follows one reconstructed block, and ends with the complete density-estimation cost and its classical comparison.

The single educational anchor is Andrew M. Childs, [*Lecture Notes on Quantum Algorithms*, 17 April 2025](https://www.cs.umd.edu/~amchilds/qa/qa.pdf). Its circuit, simulation, block-encoding, and counting sections supply the foundations. The Schwinger constraint and compiler are explained here and in the scientific account; the specific locality and interaction-picture theorems are attributed to their research sources.

## Choose a reading route

| Purpose | Route |
|---|---|
| Understand the mechanism through a small calculation | [Anchor bridge and four-site example](anchor_bridge.md) |
| Follow the complete conceptual argument | [Thirty milestones](milestones.md) |
| Check the exact assumptions and proof | [Compiler theorem](../science/streaming_gauss_theorem.md) and [native block circuits](../science/coherent_native_blocks.md) |
| Follow preparation, computation, and output costs | [Density estimation](../science/estimation.md) and [finite resource comparison](../science/finite_resource_comparison.md) |
| Assess what the result establishes | [Resource interpretation](../science/interpretation.md), [benchmarks](../science/benchmarks.md), and [related work](../references/RELATED_WORK.md) |

## The two phases

The settled map has exactly **M01–M30**. **M01–M12, background/preliminaries**, connect individual quantum registers and local physical variables to a complete input–output contract. **M13–M30, narrative/innovation**, connect the local reconstruction identity, native circuits, approximation guarantees, and schedule to the complete resource comparison. Each phase progresses from local objects to global understanding. The allocation reflects the number of interfaces the compiler must make compatible, rather than the chapter order of the anchor.

The anchor's principal entry points are §§1.1–1.7, §2.1, §3.4, §4.3, §19.3, §§21.1–21.2, §§27.1–27.5, §28.3, and §29.1. [The bridge](anchor_bridge.md#the-selected-anchor-and-the-project-boundary) gives verified page locations and explains what each contributes. The complete notes need not be read before the project makes sense.

## Keep the scientific distinction in view

The existing native algorithm already has near-linear spacetime gate complexity. This compiler reduces persistent field storage while retaining that gate order, and improves a specified matter-only global interaction-picture construction. It supplies a scalar-output algorithm with charged preparation, precision, inverse, reflection, and classical preprocessing costs. Its primitive logical-gate bounds are not finite T-count or physical-runtime forecasts.

The parallel depth assumes all-to-all logical connectivity. A useful finite width gain requires blocks sufficiently smaller than the chain. The committed classical benchmark is tractable and does not establish a quantum–classical crossover. The [final milestone](milestones.md#m30-state-the-contribution-and-its-limits-together) connects these qualifications to the result rather than treating them as a separate afterthought.
