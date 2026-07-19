*This project has been created as part of the 42 curriculum by obehlil.*

# fly-in

## Description

`fly-in` is a drone routing project that computes how to move multiple drones from a start hub to an end hub in the **minimum number of turns**, while respecting:

- zone capacities (`max_drones`)
- connection capacities (`max_link_capacity`)
- zone travel costs (notably `restricted` zones with extra travel time)

The project parses a map file into a graph, builds a time-expanded network, and solves the scheduling problem with maximum flow.

## Instructions

### Requirements

- Python `>= 3.12`

### Installation

```bash
git clone https://github.com/ouassim-behlil/fly-in.git
cd fly-in
```

Optional virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Execution

Current entry point:

```bash
python3 main.py
```

By default, `main.py` runs the solver on `test_map.txt`.

### Run tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Algorithm choices and implementation strategy

The implementation uses a **time-expanded graph + Dinic max-flow** approach:

1. Parse the map into a base graph (`MapParser`):
   - zones (`start_hub`, `hub`, `end_hub`)
   - metadata (`zone`, `color`, `max_drones`)
   - connections and optional `max_link_capacity`
2. Expand the graph over time:
   - each zone is split into `IN` and `OUT` nodes per turn
   - `IN -> OUT` edges enforce zone capacity
   - temporal waiting edges allow drones to stay in place
   - movement edges encode connection capacities and travel cost
3. Compute max-flow for a given turn budget using **Dinic**.
4. Find the minimal feasible number of turns by binary-searching the turn budget.
5. Reconstruct one path per drone from the resulting unit flows.

### Why this strategy

- Capacity and timing constraints are naturally modeled as flow capacities in a time-expanded network.
- Dinic performs well for repeated max-flow computations.
- Binary search avoids checking every turn sequentially and reduces total solve time.

## Visual representation features (UX)

The project currently provides a **textual visual timeline** of drone movements:

- one output line per simulation turn
- per-drone movement tokens (e.g., `D3-zoneA-zoneB` / `D3-zoneB`)
- explicit 2-step rendering for restricted-zone traversal to make delays understandable

Map files also carry visual metadata (`x`, `y`, `color`) that improve readability and support richer displays.  
A minimal Pygame prototype exists in `vis.py` as a starting point for graphical visualization.

These elements improve UX by making scheduling decisions, bottlenecks, and delayed transitions easier to inspect during debugging and demonstrations.

## Project structure

```text
flyin/
  algorithm/    # solver, Dinic max-flow, time-expanded graph
  model/        # graph, zones, metadata, connections, drone models
  parser.py     # map parsing and validation
tests/
maps/           # easy/medium/hard/challenger scenarios
main.py         # run solver on a map file
```

## Resources

### Classic references

- Dinic, E. A. (1970). Algorithm for solution of a problem of maximum flow in networks.
- CLRS – *Introduction to Algorithms*, chapters on network flow.
- Time-expanded network modeling (operations research and scheduling literature).
- Python `unittest` documentation: https://docs.python.org/3/library/unittest.html

### AI usage statement (to be completed by authors)

Use this section to document AI assistance clearly, for example:

- **Tools used:** GitHub Copilot / ChatGPT / other
- **Tasks assisted:** documentation drafting, map idea generation, test case brainstorming, refactoring suggestions
- **Validation performed by authors:** manual review, unit tests, behavior checks

