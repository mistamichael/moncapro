# Dependency Types in moncapro

> Part of the [moncapro documentation](../../README.md#documentation). Deutsch: [doc/de/dependency_types.md](../de/dependency_types.md)

## Overview

moncapro supports four different dependency types for tasks, based on the Critical Path Method (CPM):

1. **EA** - Finish-to-Start - **default**
2. **AA** - Start-to-Start
3. **EE** - Finish-to-Finish
4. **AE** - Start-to-Finish

## 1. EA - Finish-to-Start ✅ default

**Rule:** The successor cannot start until the predecessor has finished.

**Formula:** `ES(successor) >= EF(predecessor)`

**Example:**
```json
{
  "id": 3,
  "name": "Plaster wall",
  "duration": "2d",
  "successors": [2]  // Task 2 must be finished first
}
```

**Use cases:**
- Build wall → plaster wall
- Pour foundation → let foundation cure
- Write code → test code

## 2. AA - Start-to-Start

**Rule:** The successor cannot start until the predecessor has started.

**Formula:** `ES(successor) >= ES(predecessor)`

**Example:**
```json
{
  "id": 1,
  "name": "Dig excavation",
  "duration": "3d",
  "successors_aa": [2]  // Task 2 starts in parallel once task 1 starts
},
{
  "id": 2,
  "name": "Haul away soil",
  "duration": "4d"
}
```

**Use cases:**
- Dig excavation → haul away soil (parallel)
- Build masonry → start electrical work (parallel)
- Collect data → start data analysis (parallel)

## 3. EE - Finish-to-Finish

**Rule:** The successor cannot finish until the predecessor has finished.

**Formula:** `EF(successor) >= EF(predecessor)`

**Example:**
```json
{
  "id": 8,
  "name": "Programming",
  "duration": "8d",
  "successors_ee": [9]  // Task 9 finishes at the same time as task 8
},
{
  "id": 9,
  "name": "Documentation",
  "duration": "8d"
}
```

**Use cases:**
- Programming → documentation (finish together)
- Main project → quality assurance (finish together)
- Production → quality control (finish together)

## 4. AE - Start-to-Finish

**Rule:** The successor cannot finish until the predecessor has started.

**Formula:** `EF(successor) >= ES(predecessor)`

**Example:**
```json
{
  "id": 10,
  "name": "Night watch shift 1",
  "duration": "8h",
  "successors_ae": [11]  // Shift 1 ends when shift 2 starts
},
{
  "id": 11,
  "name": "Night watch shift 2",
  "duration": "8h"
}
```

**Use cases:**
- Shift handover (shift 1 ends when shift 2 starts)
- Handover scenarios
- Just-in-time deliveries

## JSON Syntax

### Simple EA dependency (default)
```json
{
  "id": 5,
  "name": "Task name",
  "duration": "3d",
  "successors": [3, 4]  // Waits for task 3 and 4 (EA)
}
```

### Multiple dependency types combined
```json
{
  "id": 5,
  "name": "Build masonry",
  "duration": "10d",
  "successors": [4],        // EA: after task 4
  "successors_aa": [6, 7],  // AA: tasks 6, 7 start in parallel
  "successors_ee": [8]      // EE: task 8 finishes at the same time
}
```

## Example Projects

### hausbau.json
Demonstrates AA and EE relationships:
- Dig excavation → haul away soil (AA)
- Masonry → electrical/plumbing (AA)
- Programming → documentation (EE)

### tankdesign.json
Classic project with pure EA relationships.

### erdaushub.json
Complex loop-based project with EA relationships and automatic breaks.

## CPM Calculation

### Forward Pass

**EA:** `ES(j) = max(EF(i))` for all predecessors i
**AA:** `ES(j) = max(ES(i))` for all predecessors i
**EE:** `EF(j) = max(EF(i))` for all predecessors i (ES is derived backward)
**AE:** `ES(j) = max(ES(i) - duration(j))` for all predecessors i

### Backward Pass

**EA:** `LF(i) = min(LS(j))` for all successors j
**AA:** `LF(i) = min(LS(j) + duration(i))` for all successors j
**EE:** `LF(i) = min(LF(j))` for all successors j
**AE:** `LF(i) = min(LF(j) + duration(i))` for all successors j

## Notes

- **successors** without a suffix = EA (default, backward compatible)
- Multiple dependency types can be combined
- In case of conflicts, the most restrictive condition always wins (maximum for ES, minimum for LF)
- Weekends are taken into account automatically (ES shifts to Monday)
- All dependencies point to **successors**, not predecessors

## Further Information

- `src/moncapro/models/base.py` - TaskBase with dependency fields
- `src/moncapro/models/cpm.py` - CPMCalculator with forward/backward pass
- `src/moncapro/examples/hausbau.json` - example project with AA/EE
