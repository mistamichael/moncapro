# Example Projects in moncapro

> Part of the [moncapro documentation](../../README.md#documentation). Deutsch: [doc/de/examples.md](../de/examples.md)

## Overview

The example projects demonstrate different features and use cases of moncapro. They ship with the package in
[`src/moncapro/examples/`](../../src/moncapro/examples) (`moncapro.paths.get_examples_dir()` when installed):

| File                   | Description                  | Features                          |
| ---------------------- | ---------------------------- | --------------------------------- |
| `pizza.json`           | Pizza preparation (minutes)  | Short durations in `m`            |
| `pizzas.json`          | Pizza service with volume    | Loop tasks, resources, machines   |
| `simpleproject.json`   | Machine assembly             | Classic CPM example               |
| `tankdesign.json`      | Tank design project          | Simple engineering project        |
| `hausbau.json`         | Single-family house build    | AA/EE dependencies                |
| `erdaushub.json`       | Excavation                   | Parallel activities               |
| `fassadenbau.json`     | Facade construction          | Section-by-section assembly       |
| `software_simple.json` | Software development         | Persons, resources, costs, scenarios, simulation         |

Pre-computed results: [doc/result_examples/](../result_examples/README.md).

The project files and their task names are in German. The dependency codes are the German abbreviations used in
the JSON format: `EA` (Ende-Anfang, finish-to-start), `AA` (Anfang-Anfang, start-to-start), `EE` (Ende-Ende,
finish-to-finish).

---

## 1. hausbau.json - Different dependency types

### Purpose
Demonstrates all four CPM dependency types in a realistic house-building project.

### Project structure

```
Construction phase:
├── 1. Dig excavation (3d)
│   ├─[EA]→ 3. Pour foundation
│   └─[AA]→ 2. Haul away soil (parallel)
├── 3. Pour foundation (2d)
│   └─[EA]→ 4. Let foundation dry
├── 4. Let foundation dry (7d)
│   └─[EA]→ 5. Build masonry
└── 5. Build masonry (10d)
    ├─[EA]→ 10. Acceptance
    ├─[AA]→ 6. Electrical installation (parallel)
    └─[AA]→ 7. Plumbing installation (parallel)

Software phase:
├── 8. Programming (8d)
│   ├─[EA]→ 10. Acceptance
│   └─[EE]→ 9. Documentation (ends at the same time)
└── 9. Documentation (8d)
    └─[EA]→ 10. Acceptance
```

### Dependency types in detail

#### 1. EA (finish-to-start) - default
```json
{
  "id": 3,
  "name": "Fundament gießen",
  "duration": "2d",
  "successors": [4]  // Task 4 starts AFTER task 3 has finished
}
```
**Use:** Normal sequential order (excavation → foundation → drying → masonry)

#### 2. AA (start-to-start) - parallel work
```json
{
  "id": 1,
  "name": "Grube ausheben",
  "duration": "3d",
  "successors": [3],
  "successors_aa": [2]  // Task 2 starts AS SOON AS task 1 starts
}
```
**Use:**
- **Haul away soil** starts as soon as **dig excavation** starts (parallel)
- **Electrical installation** starts as soon as **masonry** starts (parallel)
- **Plumbing installation** starts as soon as **masonry** starts (parallel)

**Advantage:** Saves time through parallel execution

#### 3. EE (finish-to-finish) - simultaneous end
```json
{
  "id": 8,
  "name": "Programmierung",
  "duration": "8d",
  "successors": [10],
  "successors_ee": [9]  // Task 9 ends WHEN task 8 ends
}
```
**Use:**
- **Documentation** ends when **programming** ends
- Ensures that documentation and code are finished at the same time

**Advantage:** Synchronized completion

### Project results

**Project duration:** 33 days (including weekends)

**Critical path:** Excavation → foundation → drying → masonry → acceptance

**Time saved through AA:**
- Without AA: hauling away soil would start after the excavation → +4 days
- With AA: in parallel with the excavation → 0 additional days

### Usage
```bash
# Create Excel (tabs are controlled via cfg/excel_export.cfg)
moncapro --project src/moncapro/examples/hausbau.json --export xlsx

# HTML report with Mermaid diagrams
moncapro --project src/moncapro/examples/hausbau.json --export html

# All graphics as SVG in a ZIP archive
moncapro --project src/moncapro/examples/hausbau.json --export zip

# View the results
results/hausbau.xlsx
results/hausbau.html
results/hausbau_svg.zip
```

---

## 2. erdaushub.json - Loop tasks with breaks

### Purpose
Realistic construction-site planning with:
- Loop tasks (repeated loading/transport cycles)
- Automatic break calculation (working time law, driving-time interruptions)
- Person model with working hours
- Weekend blockers

### Project structure

```
1. Initialization (15m)
   ↓
2. Loading cycle (loop: 84 iterations)
   ├── Loading (8-12m, depends on excavator capacity)
   │   └── Break after 6h (working time law)
   ├── Transport round trip (40m, truck-specific)
   │   └── Break after 4.5h (driving-time interruption)
   └── Weekend (after Fri 17:00 → Mon 07:00)
```

### Loop task mechanism

```json
{
  "id": 2,
  "name": "Belade-Zyklus",
  "is_loop": true,
  "loop_until": "total_volume <= 0",  // Stop when 1000 m³ have been excavated
  "cycle_prefix": "F",                // Creates: 2-F1, 2-F2, ...
  "successors": [],
  "subtasks": [
    {
      "name": "Beladen",
      "required_resources": ["B1", "any_truck"],
      "resources": ["R_PERS3&B1", "R_PERS1&L1 | R_PERS2&L2"],
      "duration_formula": "resource.truck.capacity / resource.B1.loading_speed_per_min"
    },
    {
      "name": "Transport-Umlauf",
      "required_resources": ["current_truck"],
      "resources": ["R_PERS1&L1 | R_PERS2&L2"],
      "duration": "resource.truck.transport_cycle_fixed"
    }
  ]
}
```

### Automatic break calculation

#### 1. Working time law (§4 ArbZG, Germany)
**Rule:** At least 30 minutes of break after 6 hours of work

```
Person: Bodo Schmidt (excavator operator)
├── Task 2-F1-BEL to 2-F44-BEL (6 hours worked)
├── [BREAK] 2-F44-BEL-BRK-P3 (30 minutes)
│   - is_break: true
│   - Float: 0.0 (no flexibility)
│   - Cost: 0 (the break costs nothing)
└── Task 2-F45-BEL (continue working)
```

#### 2. Driving-time interruptions (German driver working-time rules)
**Rule:** At least 45 minutes of break after 4.5 hours of driving

```
Person: Max Mustermann (truck driver 1)
├── Task 2-F1-TRA to 2-F11-TRA (4.5 hours driven)
├── [BREAK] 2-F11-TRA-BRK-P1 (45 minutes)
│   - is_break: true
│   - EST = LST (fixed start time)
│   - EFT = LFT (fixed end time)
└── Task 2-F12-TRA (continue driving)
```

#### 3. Weekend blocker
**Rule:** No work from Saturday 17:00 to Monday 07:00

```
Friday 17:00:
├── Task 2-F13-TRA (last transport before the weekend)
├── [WEEKEND] WE-2-F13-TRA-2-F14-BEL (2 days)
│   - is_blocker: true
│   - Duration: 2.0 days
│   - Float: 0.0 (critical)
│   - Cost: 0 (no work)
└── Monday 07:00: Task 2-F14-BEL (first loading after the weekend)
```

### Resources & persons

#### Persons (3)
```json
{
  "id": "PERS_MAX",
  "name": "Max Mustermann",
  "role": "LKW-Fahrer",
  "hourly_rate": 35.0,
  "workinghours_override": {
    "days": ["mon", "tue", "wed", "thu", "fri"],
    "start": "07:00",
    "end": "17:00"
  },
  "rest_intervals": "resting_times"  // Reference to the break rules
}
```

#### Machines (3)
- **B1**: Crawler excavator (bucket capacity: 0.9 m³, speed: 12 m³/h)
- **L1**: 18-tonne truck (capacity: 12 m³, round-trip time: 40 min)
- **L2**: 26-tonne truck (capacity: 18 m³, round-trip time: 40 min)

### Dynamic duration calculation

```javascript
// The loading duration depends on the truck size
duration = resource.truck.capacity / resource.B1.loading_speed_per_min

// Example:
// 18 t truck (12 m³) / excavator (12 m³/h) = 60 minutes = 1 hour ❌
// Correct: 12 m³ / (12 m³/60min) = 12 m³ / 0.2 m³/min = 60 min ✓
```

### Project results

**Project duration:** 12.4 days (incl. 2 weekends)
- Pure working time: ~8.4 days
- Weekends: 2x2 = 4 days

**Number of tasks:** 174
- Init: 1
- Loading cycles: 84
- Transport cycles: 84
- Breaks: 5 (3x working time law, 2x driving time)
- Weekends: 2

**Costs:**
- Personnel costs: ~84 hours × €35/h = ~€2,940
- Machine costs: by machine hours

### Usage

```bash
# Full evaluation with Excel
moncapro --project src/moncapro/examples/erdaushub.json --export xlsx

# Text output only
moncapro --project src/moncapro/examples/erdaushub.json --export txt

# All graphics as SVG in a ZIP archive
moncapro --project src/moncapro/examples/erdaushub.json --export zip

# View the results
results/erdaushub.xlsx  # Excel with Gantt (hourly resolution!)
results/erdaushub.txt   # Text report
results/erdaushub_svg.zip  # SVG graphics (Gantt, network diagram, resources)
```

### Special features

#### 1. Hourly resolution in the Gantt chart
Because the minimum task duration is 8 minutes, **hourly resolution** is chosen automatically:
- Timeline: 0-7 o'clock (8-hour working day)
- Weekends: Sat/Sun as individual columns
- Breaks: Visible as short tasks

#### 2. Critical path
The entire loading cycle is critical:
```
Init → F1-BEL → F1-TRA → F2-BEL → ... → F84-TRA
```
Any delay moves the end of the project!

#### 3. Resource utilization
In the resource list you can see:
- Excavator B1: Busy throughout (except breaks)
- Trucks L1/L2: Used alternately
- Persons: Working time vs. breaks visualized

---

## 3. software_simple.json - Scenarios and Monte Carlo simulation

### Purpose
Shows the "what if?" analysis: scenarios (`scenarios`) are compared against the base plan, and the Monte Carlo
simulation draws random uncertainties (`duration_range`, `risk`, scenario `probability`) and returns
probabilities instead of a single end date. Both are already part of `software_simple.json`.

### Uncertainty on tasks

| Task | Plan | `duration_range` | `risk` |
| ---- | ---- | ---------------- | ------ |
| 4 Backend development  | 40h | 32h – 72h | 20 % probability, +16h ("customer API still unstable") |
| 5 Frontend development | 32h | 24h – 48h | – |
| 6 Testing & QA         | 20h | 16h – 40h | – |

```json
{
  "id": 4,
  "name": "Backend Entwicklung",
  "duration": "40h",
  "duration_range": ["32h", "72h"],
  "risk": {"probability": 0.2, "delay": "16h", "note": "API des Kunden noch instabil"}
}
```

### Scenarios

| Scenario | Change | `probability` |
| -------- | ------ | ------------- |
| Alice sick for a week  | `person: DEV1`, vacation 9-13 Mar | 0.15 |
| Backend 50 % more work | `task: 4`, `duration_factor: 1.5` | - (comparison only) |
| Acceptance by 27 Mar   | `task: 8`, `deadline: 2026-03-27` | - (comparison only) |

```json
{
  "name": "Alice eine Woche krank",
  "probability": 0.15,
  "changes": [{"person": "DEV1", "vacation": [{"from": "2026-03-09", "to": "2026-03-13", "description": "krank"}]}]
}
```

Without `probability` a scenario is only compared, it does not enter the simulation. (Names and descriptions in the
JSON file are German.)

### Scenario comparison

```bash
moncapro --project src/moncapro/examples/software_simple.json --scenarios
moncapro --project src/moncapro/examples/software_simple.json --export scenarios   # HTML
```

| Scenario                 | End              | Duration | vs. base plan | Cost     | Deadlines missed |
| ------------------------ | ---------------- | -------- | ------------- | -------- | ---------------- |
| Base plan                | 2026-04-07 17:00 | 192 h    | ±0            | 13,960 € | 0 |
| Alice sick for a week    | 2026-04-14 17:00 | 232 h    | +40 h         | 13,960 € | 0 |
| Backend 50 % more work   | 2026-04-10 13:00 | 212 h    | +20 h         | 15,660 € | 0 |
| Acceptance by 27 Mar     | 2026-04-07 17:00 | 192 h    | ±0            | 13,960 € | 1 |

To calculate and export a single scenario as its own plan: `--scenario "Alice eine Woche krank"`.

### Monte Carlo simulation

```bash
moncapro --project src/moncapro/examples/software_simple.json --simulate 300 --seed 1
moncapro --project src/moncapro/examples/software_simple.json --export simulation --simulate 300 --seed 1
```

With `--seed` the result is reproducible. Typical result (300 runs, seed 1):

| Metric | Value |
| ------ | ----- |
| Plan (no variation)               | 2026-04-07 17:00 (192 h) |
| Plan is kept in                   | 3 % |
| P50 / P80 / P90                   | 13 Apr / 16 Apr / 17 Apr |
| Earliest / latest end             | 31 Mar / 27 Apr |
| Scenario "Alice sick" occurred in | 14 % |
| Most critical tasks               | 6, 7, 8 (100 %), 4, 5 (90 %), 1, 2 (76 %) |

**How to read it:** the 192 h plan holds in only about 3 % of the runs. To commit with 80 % confidence, quote the
P80 date (16 Apr). Criticality shows how often a task determines the end date - here development (4, 5) and
everything after it. If a task's planned duration lies outside `duration_range`, the simulation uses the boundary
and reports the task.

Pre-computed results: [software_simple_scenarios.html](../result_examples/software_simple_scenarios.html),
[software_simple_simulation.html](../result_examples/software_simple_simulation.html). Tested in
[`tests/test_example_analysis.py`](../../tests/test_example_analysis.py).

---

## 4. Other examples (short overview)

### tankdesign.json - Classic project management
**Features:**
- Pure EA dependencies (default)
- 8 tasks, 70 days project duration
- Demonstrates the classic CPM calculation

**Use:** Learning example for standard CPM

### pizzas.json - Production planning
**Features:**
- Instance tasks (several pizzas)
- Very short durations (minutes)
- Shows hourly resolution

**Use:** Production/manufacturing planning

### fassadenbau.json - Resource planning
**Features:**
- PersonProject with 3 persons
- Various materials and machines
- Shows resource reports

**Use:** Construction planning with resources

---

## Running all examples

```bash
# Process all examples at once (without --project, the CLI processes every *.json in the folder)
moncapro --data-dir src/moncapro/examples --export xlsx

# Results in the results/ folder:
results/hausbau.xlsx         # AA/EE dependencies
results/erdaushub.xlsx       # Loop tasks with breaks (hours!)
results/tankdesign.xlsx      # Standard EA
results/pizzas.xlsx          # Instance tasks (hours!)
results/fassadenbau.xlsx     # PersonProject (days)
results/software_simple.xlsx # Scenarios and Monte Carlo simulation
```

---

## Comparison of the examples

| Feature | hausbau | erdaushub | tankdesign | pizzas | fassadenbau | software_simple |
|---------|---------|-----------|------------|--------|-------------|------------------|
| **Dependency types** | EA, AA, EE | EA | EA | EA | EA | EA |
| **Loop tasks** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Breaks** | ❌ | ✅ Auto | ❌ | ❌ | ❌ | ❌ |
| **Weekends** | ✅ | ✅ Blocker | ✅ | ✅ | ✅ | ✅ |
| **Persons** | ❌ | ✅ 3 | ❌ | ❌ | ✅ 3 | ✅ 3 |
| **Machines** | ❌ | ✅ 3 | ❌ | ✅ 1 | ✅ 2 | ❌ |
| **Scenarios** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Monte Carlo simulation** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Gantt resolution** | Days | **Hours** | Days | **Hours** | Days | Hours |
| **Project duration** | 33d | 12.4d | 70d | 1.2h | 6.8d | 192h |
| **Number of tasks** | 10 | 174 | 8 | 4 | 5 | 8 |

---

## Further documentation

- [dependency-types.md](dependency-types.md) - Detailed explanation of all dependency types
- [cfg/defaults.cfg](../../src/moncapro/cfg/defaults.cfg) - Project defaults

---

## Creating your own examples

### Minimal example (EA)
```json
{
  "project": "My project",
  "project_start": "2026-04-01",
  "tasks": [
    {"id": 1, "name": "Task A", "duration": "3d", "successors": [2]},
    {"id": 2, "name": "Task B", "duration": "2d", "successors": []}
  ]
}
```

### With AA dependencies
```json
{
  "id": 1,
  "name": "Main work",
  "duration": "5d",
  "successors": [3],
  "successors_aa": [2]  // Task 2 starts in parallel
}
```

### With PersonProject
```json
{
  "project": "My project",
  "project_start": "2026-04-01",
  "persons": [
    {"id": "P1", "name": "Max", "email": "max@example.com", "role": "Dev", "hourly_rate": 50}
  ],
  "resources": [
    {"id": "PC1", "name": "Laptop", "type": "machine"}
  ],
  "tasks": [
    {"id": 1, "name": "Development", "duration": "5d", "resources": ["P1", "PC1"]}
  ]
}
```

Good luck with project management using moncapro! 🚀
