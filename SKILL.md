---
name: mac-system-stat
description: >
  Generate a concise macOS host resource report focused on local-model readiness
  and machine pressure. Use when the user asks about Mac resource usage, current
  machine health, battery, CPU load, memory pressure, swap, disk headroom, GPU
  model/capability, power draw, fan RPM, temperature sensors, or whether the
  machine has enough headroom to run a local model. Triggers include "Mac status",
  "system stats", "how's my machine", "memory pressure", "GPU utilization",
  "power draw", "fan speed", "temperature", "can I run a local model".
  macOS only, Apple Silicon first.
---

# mac-system-stat

Produce a concise macOS host snapshot using small local helpers.

## Quick Start

Run the aggregate report:

```bash
scripts/hoststat
```

For human-readable one-liner:

```bash
scripts/hoststat --text
```

Use the output directly when the user asks for a current system snapshot.

## Available Helpers

| Script | What it reports |
|--------|----------------|
| `scripts/hoststat` | Aggregate JSON host snapshot (calls all others) |
| `scripts/memstat` | RAM, compression, swap, memory pressure |
| `scripts/cpustat` | CPU usage, load average, process counts, top CPU processes |
| `scripts/gpustat` | GPU model, core count, live IOAccelerator utilization via Swift/IOKit |
| `scripts/powerstat` | Apple Silicon IOReport-based power sampler (CPU/GPU/ANE/DRAM watts) |
| `scripts/fanstat` | AppleSMC fan reader (count, RPM, min/max, mode) |
| `scripts/tempstat` | AppleSMC temperature sensors + pmset thermal state |
| `scripts/build-helpers` | Prebuild Swift helpers explicitly (optional; auto-built on first run) |

Each helper outputs structured JSON. `hoststat` aggregates them all.

## Interpretation Rules

Prioritize these signals for local-model readiness:

1. **Memory headroom** — total, available-ish, compressed, swap used. High swap or compressed → call it out.
2. **Current contention** — CPU idle %, load average, top processes. If a few heavy processes dominate, name them.
3. **GPU** — model and core count are reliable. Live utilization (device/renderer/tiler %) comes from IOAccelerator `PerformanceStatistics`.
4. **Power** — CPU/GPU/ANE/DRAM watt draw from IOReport Energy Model. Values are short-window averages, not hardware-meter absolutes.
5. **Temperature** — CPU, battery, ambient from AppleSMC. `pmset -g therm` for system thermal state.
6. **Fans** — RPM from AppleSMC. 0 RPM on Apple Silicon can mean fans are currently stopped, not unreadable.

## Output Style

Keep replies short and decision-oriented:

- 1–2 sentence current state summary
- 3–6 bullets for key numbers or bottlenecks
- Clear conclusion: "ready now" / "usable but memory constrained" / "not ideal because X"

## Build & Prerequisites

- **macOS only**, Apple Silicon first
- **Python 3** (system Python is fine)
- **Xcode Command Line Tools** (`xcode-select --install`) required for Swift-backed helpers (gpustat, powerstat, fanstat, tempstat)
- Swift helpers auto-build into `scripts/bin/` on first run; no manual build step needed
- If `swiftc` is unavailable, Swift-backed helpers fail with structured JSON; `memstat` and `cpustat` still work

## Design Notes

- Default path avoids sudo
- GPU reads IORegistry properties directly via IOKit, not `ioreg` text parsing
- Power uses IOReport Energy Model deltas; non-privileged
- Fan/temp use AppleSMC via IOKit; non-privileged
- For deeper stats: `sudo powermetrics --samplers tasks,cpu_power,gpu_power -n 1` (needs explicit user approval)
- See `references/metrics-notes.md` for detailed metric interpretation guidance
