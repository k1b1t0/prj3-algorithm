# prj3-algorithm

---

## 1. Problem Formulation

### 1.1 Scope & Assumptions
- Single-Sprint Snapshot
- $N$ backlog tasks $\mathcal{V} = \{1, \dots, N\}$ with a DAG precedence graph $G = (\mathcal{V}, \mathcal{E})$ must be assigned and sequenced across $|T|$ cross-functional teams.
- Each task $i \in \mathcal{V}$ has:
  - Risk score $r_i$ (CVSS severity)
  - Estimated effort $e_i$ (Story Points - SP)
  - Required domain skill $\text{skill}_i$
  - Target microservice module $\text{mod}_i$
- Each team $t \in T$ has:
  - Sprint capacity limit $\text{cap}_t$ (SP)
  - Skill competency matrix $k_{t, s} \in [0, 1]$

### 1.2 Mathematical Model
- **Context-Switch Distance between task $i$ and $j$ ($C_{ij}$)**:
  $$C_{ij} = 0.6 \cdot \mathbb{I}(\text{mod}_i \neq \text{mod}_j) + 0.4 \cdot \mathbb{I}(\text{skill}_i \neq \text{skill}_j) \in [0, 1]$$

- **Multi-Objective Criteria**:
  1. **Maximize Risk Resolved**: $\max \sum_{i \in \text{Scheduled}} r_i \iff \min \sum_{i \in \text{Deferred}} r_i$
  2. **Minimize Context-Switch Cost**: $\min F_{\text{Switch}} = \sum_{t \in T} \sum_{k=1}^{|\pi_t|-1} C_{\pi_t(k), \pi_t(k+1)}$
  3. **Maximize Skill Match Score (SMS)**: $\max \text{SMS} = \frac{1}{|\text{Scheduled}|} \sum_{t \in T} \sum_{i \in \pi_t} k_{t, \text{skill}_i}$

- **Hard Constraints**:
  1. **Sprint Capacity**: $\sum_{i \in \pi_t} e_i \le \text{cap}_t, \quad \forall t \in T$
  2. **Competency Threshold**: $k_{t, \text{skill}_i} \ge 0.5, \quad \forall i \in \pi_t$
  3. **DAG Precedence Integrity**: If $(u, v) \in \mathcal{E}$ and $v \in \pi_t$, then $u \in \text{Scheduled}$ and $u$ must be executed before $v$.

---

## 2. Experimental Scenarios & Baselines

### 2.1 Benchmark Scenarios
- **`demo-1`**: $N=20$, $|T|=2$, Capacity $= 60$ SP, Backlog $= 76$ SP.
- **`demo-2`**: $N=40$, $|T|=3$, Capacity $= 90$ SP, Backlog $= 158$ SP.
- **`demo-3`**: $N=60$, $|T|=4$, Capacity $= 120$ SP, Backlog $= 238$ SP.

### 2.2 Comparison Baselines
- **`Google OR-Tools CP-SAT (Exact Baseline)`**: Exact constraint programming & Mixed-Integer Linear Programming (MILP) solver. Formulates the exact mathematical model with capacity constraints, MTZ subtour elimination for context switches, skill thresholds, and DAG precedence. Solves for theoretical global optimum up to a specified time limit (30s–60s).
- **`Greedy-CVSS (Industry Standard)`**: Sorts tasks descending by CVSS risk ($r_i$); greedily assigns each task to the first eligible team with remaining capacity and $k_{t, s} \ge 0.5$. Reflects standard industry practice (Jira / security triage queues).

---

## 3. Proposed 4-Phase Algorithm

```text
       [Backlog Tasks]
              │
              ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Phase 1: Context Clustering (Spectral Clustering)       │
  │ • Affinity A_ij = exp(-C_ij^2 / 2σ^2)                   │
  │ • DAG Affinity Boost: Force A_uv = 1.0 for u -> v       │
  │ • Partitions tasks into k = |T| cohesive clusters.      │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Phase 2: Team Assignment (Hungarian Matching)           │
  │ • Cost matrix: Cost(t, j) = 1.0 - AvgSkill(t, Cluster_j)│
  │ • Linear sum assignment solves globally optimal 1-to-1  │
  │   bipartite matching in O(|T|^3).                       │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Phase 3: Capacity Trimming (PCKP Leaf Pruning)          │
  │ • Prune tasks with skill < 0.5 & cascade orphan children│
  │ • While sum(e_i) > cap_t: iteratively prune LEAF tasks  │
  │   (out-degree = 0 in current set) with lowest r_i / e_i.│
  │ • Guarantees 0 DAG violations mathematically.           │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Phase 4: Intra-Team Sequencing (Topological Bitmask DP) │
  │ • State: dp(mask, last_u) over team's assigned tasks.   │
  │ • Transition requires (mask & req_mask[v]) == req[v].   │
  │ • Finds globally minimal context-switch tour in         │
  │   O(2^L * L^2), taking < 0.005s per team.               │
  └─────────────────────────────────────────────────────────┘
```

1. **Phase 1 (Spectral Clustering + DAG Boost)**: Builds affinity using Gaussian RBF $A_{ij} = \exp(-C_{ij}^2 / 2\sigma^2)$. Forces $A_{uv} = 1.0$ for direct dependencies to prevent cross-team blocking.
2. **Phase 2 (Hungarian Matching)**: Solves globally optimal bipartite matching between teams and task clusters based on average skill compatibility.
3. **Phase 3 (PCKP Leaf Pruning)**: Eliminates tasks failing skill thresholds, then trims overload by iteratively pruning leaf nodes with lowest $r_i / e_i$. Because only leaves are pruned, DAG integrity is 100% preserved.
4. **Phase 4 (Topological Bitmask DP)**: Formulates intra-team sequencing as a TSP tour over context distances $C_{ij}$ constrained by topological bitmasks. Guarantees global optimality within milliseconds.

---

## 4. Benchmark Results & Evaluation

The proposed method was benchmarked against the Exact baseline (OR-Tools CP-SAT) and Industry standard (Greedy-CVSS) on all 3 scenarios.

### Scenario 1: `demo-1` (Small & Dense DAG: $N=20$ Tasks, $|T|=2$ Teams)

| Method | Risk Resolved $\uparrow$ | Switch Cost $\downarrow$ | SMS (0-1) $\uparrow$ | Opt. Gap (%) $\downarrow$ | Runtime (s) $\downarrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. OR-Tools CP-SAT (OPTIMAL)** | **106.0** | 2.40 | **0.739** | **0.0% (Exact)** | 1.581s |
| **2. Proposed (ESSC+DP)** | 103.0 | **1.60** | 0.675 | **2.87%** | **0.0753s** |
| 3. Greedy CVSS | **106.0** | 5.00 | **0.739** | 2.22% | 0.0001s |

---

### Scenario 2: `demo-2` (Standard Sprint & Trimming: $N=40$ Tasks, $|T|=3$ Teams)

| Method | Risk Resolved $\uparrow$ | Switch Cost $\downarrow$ | SMS (0-1) $\uparrow$ | Opt. Gap (%) $\downarrow$ | Runtime (s) $\downarrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. OR-Tools CP-SAT (FEASIBLE)** | **163.5** | 3.80 | **0.766** | **0.0% (Exact)** | 30.158s |
| **2. Proposed (ESSC+DP)** | **163.5** | **2.00** | 0.670 | **0.50%** | **0.0500s** |
| 3. Greedy CVSS | 157.5 | 7.00 | 0.725 | 6.51% | 0.0003s |

---

### Scenario 3: `demo-3` (Stress Test & High Contention: $N=60$ Tasks, $|T|=4$ Teams)

| Method | Risk Resolved $\uparrow$ | Switch Cost $\downarrow$ | SMS (0-1) $\uparrow$ | Opt. Gap (%) $\downarrow$ | Runtime (s) $\downarrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. OR-Tools CP-SAT (FEASIBLE)** | **224.0** | 9.20 | **0.696** | **0.0% (Exact)** | 60.788s |
| **2. Proposed (ESSC+DP)** | 200.0 | **3.60** | 0.694 | **9.36%** | **0.0391s** |
| 3. Greedy CVSS | 191.0 | 9.60 | 0.687 | 16.22% | 0.0003s |

---


## 5. Repository Structure & Quickstart

### 5.1 Project Structure
```text
prj3-algorithm/
├── src/                          # Core Algorithm & Models
│   ├── models.py                 # Task, Team, Schedule data classes
│   ├── metrics.py                # Multi-objective metrics evaluation
│   ├── proposed/                 # Proposed 4-stage pipeline
│   │   ├── pipeline.py
│   │   ├── affinity.py
│   │   ├── clustering.py
│   │   ├── assignment.py
│   │   ├── trimmer.py
│   │   └── dp_sequencing.py
│   └── baselines/                # CP-SAT Exact & Greedy-CVSS baselines
├── dataset/                      # Benchmark inputs (demo-1, demo-2, demo-3.json)
├── outputs/                      # Generated results & HTML dashboards (Git-ignored)
├── scripts/                      # Standalone execution scripts
│   ├── run_proposed.py
│   ├── run_exact.py
│   ├── run_benchmark.py
│   └── generate_visualizer.py
├── tests/                        # Unit tests for DP and PCKP trimmer
├── main.py                       # Unified CLI runner
├── pyproject.toml
└── README.md
```

### 5.2 Installation & Usage

#### Setup Environment
```bash
# Using uv (recommended)
uv sync

# Or standard pip
pip install -e .
```

#### Running Experiments via Unified CLI
```bash
# Run proposed algorithm on demo scenarios
uv run main.py proposed

# Run full comparative benchmark vs baselines
uv run main.py benchmark

# Generate interactive visualizer dashboard
uv run main.py visualizer

# All-in-one: Run benchmark and generate HTML visualizer
uv run main.py all
```

#### Running Individual Scripts
```bash
uv run scripts/run_proposed.py
uv run scripts/run_benchmark.py
uv run scripts/generate_visualizer.py
```

#### Running Unit Tests
```bash
uv run python -m unittest discover tests
```
