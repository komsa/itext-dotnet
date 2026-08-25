#!/usr/bin/env python3
"""Run a scoped `dotnet test` at idle priority under a hard memory cap.

Why this exists: a solution-wide `dotnet test iTextCore.sln` runs all 13 test assemblies in
parallel. On 2026-08-25 that consumed all 64 GB of RAM on a dev machine and took the whole box
down. Idle CPU priority alone does not help - the problem is memory, not scheduling.

This wrapper therefore does three things:

1. Puts the test run into a Windows **job object** carrying `JobMemoryLimit`. The cap is enforced
   by the kernel: once the job as a whole reaches it, further allocations fail inside the test host
   instead of the machine swapping to death.
2. Runs the job at idle priority class, so an accidental long run stays interactive.
3. Sets `KILL_ON_JOB_CLOSE`, so killing this script also reaps every `testhost` it spawned rather
   than leaving them behind.

A solution-wide run is refused unless `--allow-solution` is passed, because that is the exact
command that caused the outage.

Usage:
    python scripts/run_tests.py itext.tests/itext.commons.tests/itext.commons.tests.csproj
    python scripts/run_tests.py <project> --filter "FullyQualifiedName~LazyLogger"
    python scripts/run_tests.py <project> --cap-gb 8 -- --logger "console;verbosity=detailed"

Everything after a bare `--` is forwarded to `dotnet test` untouched.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNSETTINGS = "komsa.runsettings"
DEFAULT_CAP_GB = 16.0

JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOBOBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9

IDLE_PRIORITY_CLASS = 0x00000040
PROCESS_SET_QUOTA = 0x0100
PROCESS_TERMINATE = 0x0001


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _load_kernel32() -> ctypes.WinDLL:
    """kernel32 with explicit prototypes.

    The prototypes are not optional: ctypes defaults a return value to C `int`, which silently
    truncates the 64-bit HANDLE values returned by CreateJobObjectW and OpenProcess.
    """
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    k32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    k32.CreateJobObjectW.restype = wintypes.HANDLE

    k32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    k32.SetInformationJobObject.restype = wintypes.BOOL

    k32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD]
    k32.QueryInformationJobObject.restype = wintypes.BOOL

    k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k32.AssignProcessToJobObject.restype = wintypes.BOOL

    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE

    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.restype = wintypes.BOOL

    return k32


KERNEL32 = _load_kernel32() if os.name == "nt" else None


def create_capped_job(cap_bytes: int) -> wintypes.HANDLE:
    """Create a job object limited to cap_bytes, at idle priority, killed when we exit."""
    job = KERNEL32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())

    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_JOB_MEMORY
        | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        | JOB_OBJECT_LIMIT_PRIORITY_CLASS
    )
    info.BasicLimitInformation.PriorityClass = IDLE_PRIORITY_CLASS
    info.JobMemoryLimit = cap_bytes

    if not KERNEL32.SetInformationJobObject(
        job, JOBOBJECT_EXTENDED_LIMIT_INFORMATION_CLASS, ctypes.byref(info), ctypes.sizeof(info)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return job


def assign_to_job(job: wintypes.HANDLE, pid: int) -> None:
    handle = KERNEL32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not KERNEL32.AssignProcessToJobObject(job, handle):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        KERNEL32.CloseHandle(handle)


def peak_job_memory(job: wintypes.HANDLE) -> int:
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    if not KERNEL32.QueryInformationJobObject(
        job, JOBOBJECT_EXTENDED_LIMIT_INFORMATION_CLASS, ctypes.byref(info),
        ctypes.sizeof(info), None
    ):
        return 0
    return int(info.PeakJobMemoryUsed)


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    forwarded: list[str] = []
    if "--" in argv:
        split = argv.index("--")
        argv, forwarded = argv[:split], argv[split + 1:]

    parser = argparse.ArgumentParser(
        description="Run a scoped dotnet test at idle priority under a hard memory cap.")
    parser.add_argument("target", help="test project (.csproj); a .sln needs --allow-solution")
    parser.add_argument("--filter", help="value for dotnet test --filter")
    parser.add_argument("--configuration", "-c", default="Release")
    parser.add_argument("--cap-gb", type=float, default=DEFAULT_CAP_GB,
                        help=f"hard memory cap for the whole run (default {DEFAULT_CAP_GB:g})")
    parser.add_argument("--no-build", action="store_true",
                        help="skip the build, for when the solution was just built")
    parser.add_argument("--allow-solution", action="store_true",
                        help="permit a solution-wide run (this is what caused the outage)")
    return parser.parse_args(argv), forwarded


def main(argv: list[str]) -> int:
    if os.name != "nt":
        print("This wrapper is Windows-only; the memory cap uses job objects.", file=sys.stderr)
        return 2

    args, forwarded = parse_args(argv)

    if args.target.lower().endswith(".sln") and not args.allow_solution:
        print(
            "Refusing to run a solution-wide test run.\n"
            "All 13 assemblies run in parallel and have already exhausted 64 GB of RAM once.\n"
            "Pass a single test project, or --allow-solution if you really mean it.",
            file=sys.stderr,
        )
        return 2

    command = ["dotnet", "test", args.target, "-c", args.configuration,
               "--settings", RUNSETTINGS]
    if args.no_build:
        command.append("--no-build")
    if args.filter:
        command += ["--filter", args.filter]
    command += forwarded

    cap_bytes = int(args.cap_gb * (1024 ** 3))
    job = create_capped_job(cap_bytes)

    print(f"cap {args.cap_gb:g} GB, idle priority, cwd {REPO_ROOT}")
    print("+ " + " ".join(command), flush=True)

    # dotnet needs several hundred milliseconds before it spawns vstest/testhost, so assigning the
    # parent right after start reliably captures every descendant.
    process = subprocess.Popen(
        command, cwd=str(REPO_ROOT), creationflags=subprocess.IDLE_PRIORITY_CLASS)
    try:
        assign_to_job(job, process.pid)
    except OSError as error:
        process.kill()
        print(f"could not assign the test run to the job object: {error}", file=sys.stderr)
        return 2

    exit_code = process.wait()

    peak = peak_job_memory(job)
    print(f"peak memory for the run: {peak / (1024 ** 3):.2f} GB")
    if peak >= cap_bytes:
        print("the run hit the memory cap - treat failures as resource errors, not regressions",
              file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
