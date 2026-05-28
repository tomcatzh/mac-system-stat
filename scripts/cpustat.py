#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from _common import json_dump, machine_meta, run_result


TOP = "/usr/bin/top"
PS = "/bin/ps"
SYSCTL = "/usr/sbin/sysctl"


def probe_error(probe: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"probe": probe, "error": message}
    if details:
        payload.update(details)
    return payload


def parse_top_summary() -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    result = run_result([TOP, "-l", "1", "-n", "0"])
    if not result.ok:
        return {"raw_excerpt": result.text.splitlines()[:30]}, probe_error("top", "top failed", result.error_dict())
    out = result.text
    result: Dict[str, Any] = {"raw_excerpt": out.splitlines()[:30]}
    for line in out.splitlines():
        if line.startswith("Load Avg:"):
            match = re.search(r"Load Avg:\s*([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)", line)
            if match:
                result["load_avg"] = [float(match.group(1)), float(match.group(2)), float(match.group(3))]
        elif line.startswith("CPU usage:"):
            match = re.search(r"CPU usage:\s*([0-9.]+)% user,\s*([0-9.]+)% sys,\s*([0-9.]+)% idle", line)
            if match:
                result["cpu_percent"] = {
                    "user": float(match.group(1)),
                    "system": float(match.group(2)),
                    "idle": float(match.group(3)),
                    "used": float(match.group(1)) + float(match.group(2)),
                }
        elif line.startswith("Processes:"):
            match = re.search(r"Processes:\s*(\d+) total,\s*(\d+) running,\s*(\d+) sleeping", line)
            if match:
                result["process_counts"] = {
                    "total": int(match.group(1)),
                    "running": int(match.group(2)),
                    "sleeping": int(match.group(3)),
                }
            thread_match = re.search(r"(\d+) threads", line)
            if thread_match:
                result["thread_count"] = int(thread_match.group(1))
    if "cpu_percent" not in result or "load_avg" not in result:
        return result, probe_error("top", "failed to parse CPU summary", {"raw": out[:1000]})
    return result, None


def top_processes() -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    try:
        proc = subprocess.run([PS, "-A", "-r", "-o", "pid=,%cpu=,%mem=,comm="], capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired as e:
        return [], probe_error("ps", "ps timed out", {"stdout": (e.stdout or "")[:500] if isinstance(e.stdout, str) else "", "stderr": (e.stderr or "")[:500] if isinstance(e.stderr, str) else ""})
    except Exception as e:
        return [], probe_error("ps", "ps failed", {"error": str(e)})
    if proc.returncode != 0:
        return [], probe_error("ps", "ps failed", {"returncode": proc.returncode, "stderr": (proc.stderr or "").strip()[:1000], "stdout": (proc.stdout or "").strip()[:1000]})

    out = proc.stdout
    rows: List[Dict[str, Any]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"\s+", line, maxsplit=3)
        if len(parts) != 4:
            continue
        pid, cpu, mem, command = parts
        try:
            rows.append({
                "pid": int(pid),
                "cpu_percent": float(cpu),
                "mem_percent": float(mem),
                "command": command,
            })
        except ValueError:
            continue
    return rows[:5], None


def sysctl_int(name: str) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    result = run_result([SYSCTL, "-n", name])
    if not result.ok:
        return None, probe_error(name, "sysctl failed", result.error_dict())
    text = result.text
    if not text.isdigit():
        return None, probe_error(name, "failed to parse sysctl integer", {"raw": text[:500]})
    return int(text), None


def physical_cpu_count() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    errors: List[Dict[str, Any]] = []
    logical, error = sysctl_int("hw.logicalcpu")
    if error:
        errors.append(error)
    physical, error = sysctl_int("hw.physicalcpu")
    if error:
        errors.append(error)
    return {
        "logical": logical,
        "physical": physical,
    }, errors


def main() -> int:
    errors: List[Dict[str, Any]] = []
    top, error = parse_top_summary()
    if error:
        errors.append(error)
    processes, error = top_processes()
    if error:
        errors.append(error)
    cores, core_errors = physical_cpu_count()
    errors.extend(core_errors)
    supported = "cpu_percent" in top and top.get("load_avg") is not None

    payload = {
        **machine_meta(),
        "kind": "cpustat",
        "supported": supported,
        "cpu": {
            **top.get("cpu_percent", {}),
            "cores": cores,
            "load_avg": top.get("load_avg"),
        },
        "scheduler": {
            "process_counts": top.get("process_counts"),
            "thread_count": top.get("thread_count"),
        },
        "top_processes": processes,
        "source": {
            "top_excerpt": top.get("raw_excerpt", []),
        },
        "errors": errors,
    }
    json_dump(payload)
    return 0 if supported and not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
