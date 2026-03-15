# Metrics Notes

## Why some numbers are approximate

macOS memory accounting is not as straightforward as Linux `free -h`.
The script uses practical approximations:

- **app-ish used**: active + wired pages
- **available-ish**: free + inactive + speculative pages
- **compressed**: pages occupied by compressor
- **used estimate**: active + wired + compressed

These are good enough for quick capacity judgment, especially for local-model work.

## Memory pressure risk levels

- **low**: used ratio < 82%, compressed ratio < 6%, swap ratio < 1%
- **medium**: used ratio 82–92%, compressed ratio 6–12%, swap ratio 1–5%
- **high**: used ratio > 92%, compressed ratio > 12%, swap ratio > 5%, or free percent < 10%

## Strong warning signs for local-model runs

- Swap used is non-trivial and rising
- Compressed memory is large relative to total memory
- Memory pressure free percentage is low
- CPU idle is low and load average stays elevated
- Another large app already dominates RAM or CPU

## GPU on Apple Silicon

- GPU model and core count are reliably read from IORegistry
- Live utilization (device/renderer/tiler %) comes from `IOAccelerator` `PerformanceStatistics`
- These are Apple-private registry properties, not a documented public API
- Non-privileged built-ins do not expose a clean GPU utilization percentage like `nvidia-smi`
- For deeper live stats, use `powermetrics` with user approval

## Power sampling

- Uses `IOReport` Energy Model channels (non-privileged)
- Samples twice over a configurable interval (default 1000ms)
- Converts cumulative energy counters to joules using unit labels (mJ, uJ, nJ)
- Computes average watts over the sample window
- Subsystem rollups: cpu, gpu, ane, dram, pci
- Values are delta-based averages, not instantaneous hardware-meter readings

## Fan readout

- Reads AppleSMC `FNum` and per-fan keys (`F*Ac`, `F*Mn`, `F*Mx`, `F*Tg`, `F*Md`)
- 0 RPM on Apple Silicon legitimately means fans are currently stopped
- Read-only; no fan control is attempted

## Temperature sensors

- Curated AppleSMC key list: Tp0P, Tp0T, Te0T, Ts0P, TB0T, TW0P, Ta0P
- Values outside -40°C to 140°C filtered as invalid
- Ambient sensor (Ta0P) measures internal intake point, not room temperature
- `pmset -g therm` complements raw temps with system-level thermal state
- Future SoCs may expose different key names
