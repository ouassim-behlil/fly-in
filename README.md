*This project has been created as part of the 42 curriculum by obehlil.*

# fly-in

A high-performance autonomous drone routing and scheduling simulation system.

---

## Description

**fly-in** solves the multi-drone routing problem across a dynamic graph network. The primary goal is to compute the schedule that transports all drones from a designated starting zone (`start_hub`) to a target destination (`end_hub`) in the **minimum total number of discrete turns**, while strictly adhering to physical network capacities and zone safety constraints:

- **Zone Capacities (`max_drones`)**: Each hub limits the maximum number of drones that can simultaneously occupy it during any given turn.
- **Connection Capacities (`max_link_capacity`)**: Each bidirectional link restricts how many drones can traverse it concurrently per turn.
- **Zone Types & Movement Costs**:
  - `normal`: Standard hub taking 1 turn to enter.
  - `priority`: High-priority routing waypoint (1 turn).
  - `restricted`: Hazardous zone requiring **2 turns** to traverse (1 turn in transit occupying the link, 1 turn entering the destination). Drones cannot wait on the connection or wait for destination space.
  - `blocked`: Impassable zone that cannot be entered or traversed under any condition.
- **Feasibility Verification**: Fast pre-solve reachability analysis that detects blocked or disconnected topologies before initiating path search.

---

## Instructions

### Requirements

- **Python**: `>= 3.12`
- **Package Manager**: [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip` / `make`

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/ouassim-behlil/fly-in.git
cd fly-in
make install
```

*(Alternatively with `uv` directly)*:
```bash
uv sync
```

### Execution

Run the simulation on a map file:

```bash
make run MAP=map.txt
```

Or execute directly with Python / `uv`:

```bash
uv run python main.py maps/maps/easy/01_linear_path.txt
```

To disable colored terminal output:
```bash
uv run python main.py map.txt --no-color
```

### Debugging

Launch the simulation with Python's interactive debugger (`pdb`):

```bash
make debug MAP=map.txt
```

### Testing

Run the automated test suite using `pytest`:

```bash
make test
```

### Linting & Type Checking

Execute standard code style and static type analysis:

```bash
make lint
```

Execute strict type checking (`mypy --strict`):

```bash
make lint-strict
```

### Cleaning Cache Files

Remove temporary artifacts, compiled bytecode, and cache directories:

```bash
make clean
```

---

## Algorithm Choices and Implementation Strategy

The routing and scheduling problem is modeled as a **Max-Flow problem on a Time-Expanded Network** solved via **Dinic's Algorithm** and optimized with **Binary Search**:

```
[ Map Parser ]
      │
      ▼
[ Feasibility Pre-Check (BFS) ]
      │ (Pass)
      ▼
[ Binary Search on Turns T ∈ [1, max_turns] ]
      │
      ├──> Build Time-Expanded Graph (T layers)
      │      ├── Zone split: IN[t] --(max_drones)--> OUT[t]
      │      ├── Temporal hold: OUT[t] --(∞)--> IN[t+1]
      │      └── Movement / Transit: OUT[t] --(link_cap)--> IN[t+cost]
      │
      ├──> Dinic Max-Flow (Source -> Sink)
      │
      └──> Converge on minimal T where Max-Flow ≥ nb_drones
      │
      ▼
[ Flow Decomposition into Drone Paths ]
      │
      ▼
[ Colorized Terminal Timeline Output ]
```

### 1. Map Parsing & Topological Validation
- `MapParser` reads the scenario specification, validating zone coordinates, connections, capacities, and metadata syntax.
- Initial graph validation ensures proper declaration of start/end hubs and basic structural integrity.

### 2. Upfront Feasibility Analysis
- Before executing expensive multi-turn flow evaluations, `Solver.check_feasibility()` conducts a breadth-first search (BFS) starting from `start_hub` to `end_hub`.
- Nodes marked as `ZoneType.BLOCKED` are excluded from traversal. If no valid path exists, an `InfeasibleMapError` is immediately raised and handled gracefully.

### 3. Time-Expanded Network Construction
To incorporate time and capacity constraints simultaneously, the static graph is expanded across $T$ discrete time layers ($t \in [0, T]$):
- **Node Splitting**: Every zone $u$ at turn $t$ is split into an ingress node $u_{\text{in}}[t]$ and egress node $u_{\text{out}}[t]$ with directed capacity `max_drones(u)`.
- **Temporal Waiting**: Edges $u_{\text{out}}[t] \to u_{\text{in}}[t+1]$ with capacity $\infty$ allow drones to hold position in a zone across turns.
- **Normal Movement**: For adjacent hubs $u$ and $v$ with cost 1, directed edges $u_{\text{out}}[t] \to v_{\text{in}}[t+1]$ carry capacity `max_link_capacity(u, v)`.
- **Multi-Turn Transit (Restricted Zones)**: When moving to a restricted zone ($cost = 2$), the movement spans two time steps:
  $$u_{\text{out}}[t] \xrightarrow{\text{capacity}} \text{transit}[t+1] \xrightarrow{\text{capacity}} v_{\text{in}}[t+2]$$
  Transit nodes have no temporal waiting edges, strictly preventing drones from hovering indefinitely on the connection.

### 4. Dinic's Maximum Flow Algorithm
- Dinic's algorithm computes the maximum deliverable flow from a virtual super-source to a virtual super-sink in $O(V^2 E)$ time.
- Uses BFS to construct level graphs and DFS with pointer elimination to push blocking flows along admissible edges.

### 5. Binary Search on Minimum Turns
- Rather than sequentially checking $T = 1, 2, 3, \dots$, the solver performs binary search over the turn budget `[1, max_turns]` (with `max_turns = 100` by default) to pinpoint the optimal minimum turn count $T^*$.

### 6. Flow Decomposition & Path Extraction
- Once the minimal turn graph is determined, unit flow paths are iteratively extracted via DFS to reconstruct the exact timestamped itinerary for each individual drone ($D_1, D_2, \dots, D_N$).

---


## Visual Representation Features (UX)

The simulation provides clear, informative visual feedback designed to enhance understanding and inspection of complex scheduling dynamics:

### 1. ANSI Color-Coded Terminal Output
- Each zone name is dynamically colorized in the terminal according to its configured color metadata (e.g. `green` for start, `red` for goal, `orange` for bottlenecks, `cyan` for priority paths, or custom 24-bit hex RGB `#RRGGBB`).
- This makes bottlenecks, multi-path branching, and destination arrivals instantly recognizable at a glance.

### 2. Step-by-Step Simulation Timeline
- **Turn Representation**: Each simulation turn outputs a single line listing all drone movements that occur during that turn.
- **Movement Format**: Standard movements appear as `D<id>-<zone>` (e.g. `D1-bottleneck`).
- **Transit Representation**: Drones traversing restricted zones explicitly show their intermediate link state on turn 1 (`D1-start-trap_loop1`) before arriving on turn 2 (`D1-trap_loop1`), clearly explaining transit latency.
- **Omission of Stationary Drones**: Drones waiting in place are omitted from turn output lines to reduce visual noise.
- **Automatic Delivery Un-tracking**: Drones reaching `end_hub` are marked delivered and no longer clutter subsequent turn lines.

---

## Project Structure

```text
fly-in/
├── flyin/
│   ├── algorithm/
│   │   ├── __init__.py
│   │   ├── dinic.py               # Dinic's maximum flow algorithm
│   │   ├── solver.py              # Feasibility check, binary search, timeline formatter
│   │   └── time_expanded_graph.py # Dynamic multi-turn graph builder
│   ├── model/
│   │   ├── __init__.py
│   │   ├── connection.py          # Edge link model & capacity
│   │   ├── drone.py               # Drone entity definition
│   │   ├── graph.py               # Top-level graph data container
│   │   ├── metadata.py            # Zone types, costs, color definitions
│   │   └── zone.py                # Hub node definition
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── colors.py              # ANSI colorizer & hex/name parser
│   │   ├── decorators.py          # Performance & memory profilers
│   │   └── errors.py              # ParseError and InfeasibleMapError
│   ├── parser.py                  # Map parser and syntax validator
│   └── __init__.py
├── maps/                          # Test scenarios (easy, medium, hard, challenger)
├── tests/
│   ├── test_colors.py             # Unit tests for color formatting
│   ├── test_feasibility.py        # Unit tests for blocked paths & feasibility
│   └── test_parser.py             # Unit tests for map parsing & validations
├── .flake8                        # Flake8 linter configuration
├── Makefile                       # Build automation (install, run, debug, clean, lint, test)
├── pyproject.toml                 # Project metadata & dependency definitions
├── main.py                        # CLI entry point
└── README.md
```

---

## Resources

### Classic References

1. **Dinic, E. A. (1970)**. *Algorithm for solution of a problem of maximum flow in networks with power estimation*. Soviet Math. Doklady, 11: 1277–1280.
2. **Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2009)**. *Introduction to Algorithms* (3rd ed.). MIT Press (Chapters 26: Maximum Flow).
3. **Ford, L. R., & Fulkerson, D. R. (1956)**. *Maximal flow through a network*. Canadian Journal of Mathematics, 8: 399–404.
4. **Time-Expanded Graphs in Network Flow Modeling**: Ahuja, R. K., Magnanti, T. L., & Orlin, J. B. (1993). *Network Flows: Theory, Algorithms, and Applications*. Prentice Hall.
5. **Python Standard Documentation**:
   - `unittest` & `pytest` documentation: https://docs.pytest.org/
   - `pdb` interactive debugger: https://docs.python.org/3/library/pdb.html

### AI Usage Statement

In accordance with the 42 AI usage guidelines, artificial intelligence was utilized as a development and pair-programming assistant during this project:

- **Tools Used**:
  - Google Antigravity / Gemini 3.7 Flash
- **Tasks Assisted**:
  - **Feasibility Verification**: Designing the upfront BFS reachability filter and custom exception hierarchy (`InfeasibleMapError`) to reject impassable maps before turn expansion.
  - **Color Formatting & UX**: Implementing the terminal ANSI/RGB colorization module in `flyin/utils/colors.py` and integrating it with `Solver.print_output`.
  - **Makefile & Linter Compliance**: Creating the automated `Makefile` and resolving all PEP 8 / `flake8` formatting issues and strict `mypy` type annotations across the codebase.
  - **Unit Testing**: Expanding `pytest` coverage with test suites for feasibility edge cases, custom color parsing, and parser error validation.
- **Validation Performed by Authors**:
  - Line-by-line manual code review of all algorithms and data structures.
  - Verification of network flow correctness against all benchmark scenarios (`easy`, `medium`, `hard`, `challenger`).
  - Strict static type enforcement (`mypy --strict`) and 100% passing test suite execution (`pytest`).
