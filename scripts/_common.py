#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import platform
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

ZSH = "/bin/zsh"


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


@dataclass
class CommandResult:
    cmd: Union[List[str], str]
    stdout: str = ""
    stderr: str = ""
    returncode: Optional[int] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.returncode == 0

    @property
    def text(self) -> str:
        return (self.stdout or self.stderr or "").strip()

    def error_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "command": self.cmd,
            "returncode": self.returncode,
        }
        if self.error:
            payload["error"] = self.error
        if self.stderr:
            payload["stderr"] = self.stderr.strip()[:1000]
        if self.stdout:
            payload["stdout"] = self.stdout.strip()[:1000]
        return payload


def run_result(cmd: List[str], timeout: int = 15) -> CommandResult:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return CommandResult(cmd=cmd, stdout=_text(e.stdout), stderr=_text(e.stderr), error=f"timeout after {timeout}s")
    except Exception as e:
        return CommandResult(cmd=cmd, error=str(e))
    return CommandResult(cmd=cmd, stdout=p.stdout or "", stderr=p.stderr or "", returncode=p.returncode)


def run_shell_result(cmd: str, timeout: int = 20) -> CommandResult:
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, executable=ZSH)
    except subprocess.TimeoutExpired as e:
        return CommandResult(cmd=cmd, stdout=_text(e.stdout), stderr=_text(e.stderr), error=f"timeout after {timeout}s")
    except Exception as e:
        return CommandResult(cmd=cmd, error=str(e))
    return CommandResult(cmd=cmd, stdout=p.stdout or "", stderr=p.stderr or "", returncode=p.returncode)


def run(cmd: List[str], timeout: int = 15) -> str:
    return run_result(cmd, timeout=timeout).text


def run_shell(cmd: str, timeout: int = 20) -> str:
    return run_shell_result(cmd, timeout=timeout).text


def json_dump(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def bytes_human(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    n = float(value)
    idx = 0
    while abs(n) >= 1024 and idx < len(units) - 1:
        n /= 1024.0
        idx += 1
    return f"{n:.1f}{units[idx]}"


def parse_size_to_bytes(value: str) -> Optional[int]:
    text = value.strip()
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([KMGTP]?)(?:i?B?)?$", text, re.IGNORECASE)
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2).upper()
    scale = {"": 0, "K": 1, "M": 2, "G": 3, "T": 4, "P": 5}[unit]
    return int(amount * (1024 ** scale))


def now_iso() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def machine_meta() -> Dict[str, Any]:
    return {
        "hostname": platform.node(),
        "machine": platform.machine(),
        "macos_version": platform.mac_ver()[0],
        "timestamp": now_iso(),
    }


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def clamp_percent(value: Optional[float]) -> Optional[float]:
    if value is None or math.isnan(value):
        return None
    return max(0.0, min(100.0, value))
