# mac-system-stat

A concise macOS system report tool for AI agents. Produces structured JSON snapshots of CPU, memory, GPU, power, fans, and temperature — designed for [OpenClaw](https://github.com/openclaw/openclaw) skills and local-model readiness checks.

## What it reports

| Helper | Metrics |
|--------|---------|
| **hoststat** | Aggregate snapshot (calls all helpers below) |
| **memstat** | RAM total/used/compressed/available, swap, memory pressure |
| **cpustat** | CPU usage, load average, process counts, top processes |
| **gpustat** | GPU model, core count, live utilization (device/renderer/tiler %) |
| **powerstat** | CPU/GPU/ANE/DRAM power draw in watts (IOReport Energy Model) |
| **fanstat** | Fan count, RPM, min/max, mode (AppleSMC) |
| **tempstat** | Temperature sensors + thermal state (AppleSMC + pmset) |

## Requirements

- **macOS** (Apple Silicon first, Intel partial support)
- **Python 3** (system Python works)
- **Xcode Command Line Tools** for Swift-backed helpers (gpustat, powerstat, fanstat, tempstat)

```bash
xcode-select --install  # if not already installed
```

## Quick start

```bash
# Full JSON report
./scripts/hoststat

# Human-readable one-liner
./scripts/hoststat --text

# Individual helpers
./scripts/memstat
./scripts/cpustat
./scripts/gpustat
./scripts/powerstat
./scripts/fanstat
./scripts/tempstat
```

Swift helpers auto-build on first run into `scripts/bin/`. To prebuild explicitly:

```bash
./scripts/build-helpers
```

## Install as OpenClaw skill

Via [ClawHub](https://clawhub.com):

```bash
clawhub install mac-system-stat
```

Or manually:

```bash
cp -R . ~/.agents/skills/mac-system-stat
```

## How it works

- **memstat/cpustat**: Pure Python, uses `vm_stat`, `sysctl`, `top`, `ps`
- **gpustat**: Python + Swift helper reading `IOAccelerator` via IOKit (non-privileged). Utilization is a point-in-time private registry snapshot; for bursty workloads, sample repeatedly or cross-check GPU watts from `powerstat`.
- **powerstat**: Python + Swift helper sampling `IOReport` Energy Model channels (non-privileged)
- **fanstat/tempstat**: Python + Swift helpers reading `AppleSMC` via IOKit (non-privileged)

All helpers run without sudo. For deeper stats: `sudo powermetrics --samplers tasks,cpu_power,gpu_power -n 1`

## GPU interpretation

For MLX/oMLX and other Metal compute workloads, read `gpustat` and `powerstat` together:

- `gpustat` `device` is the useful IOAccelerator activity counter.
- `renderer` and `tiler` can stay near 0 for compute workloads.
- `powerstat` `gpu` watts is the cross-check for sustained GPU activity.

Typical idle/light desktop: `device=0%`, `gpu~0.005W`.
Typical active Metal/MLX compute: `device=93-100%`, `gpu~45-70W`.

## Example output

```
CPU 3.2% used, load 2.41/2.90/3.56 | Memory 42.1% used est (52.8GB/128.0GB),
pressure normal/low | Apple M4 Max/40c dev 0%, render 0% | Temp CPU 38.2C,
hottest 42.0C (Efficiency cluster) | Power CPU 7.29W, DRAM 1.35W |
Fans fan0 0rpm, fan1 0rpm | Top proc WindowServer pid 312 @ 5.2% CPU
```

## License

[MIT](LICENSE)
