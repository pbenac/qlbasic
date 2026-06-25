#!/usr/bin/env kpython3
"""
KTL-triggered QuickLook wrapper using OUTDIR + LASTFILE.

- Watches scifs:LASTFILE and scimager:LASTFILE
- Builds full path as:  <OUTDIR>/<LASTFILE>   when LASTFILE is relative
- Robust to services not yet initialized (not connected to traffic)
"""

import os
import time
import threading
from time import sleep, strftime

import ktl
from astropy.io import fits

# QuickLook module (assumed to be importable already)
import QuickLook as quicklook


# -----------------------------
# Config
# -----------------------------
SERVICES = ("scifs", "scimager")
KEY_LASTFILE = "LASTFILE"
KEY_OUTDIR   = "DATADIR"

RETRY_SLEEP_S = 2.0
FILE_READY_TIMEOUT_S = 20.0
FILE_READY_POLL_S = 0.1

# Leave empty to process everything
ALLOWED_CAMERA = set()   # e.g. {"IFS", "Im"}


# -----------------------------
# Helpers
# -----------------------------
def _ts():
    return strftime("%Y-%m-%d %H:%M:%S")


def _is_traffic_not_connected(err):
    s = str(err).lower()
    return ("not connected to traffic" in s) or ("get_dispatcher_traddr" in s)


def wait_for_file_ready(path, timeout_s=FILE_READY_TIMEOUT_S):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return True
        except OSError:
            pass
        sleep(FILE_READY_POLL_S)
    return False


def camera_from_fits(path):
    try:
        with fits.open(path, memmap=False) as hdul:
            return str(hdul[0].header.get("CAMERA", "")).strip()
    except Exception:
        return ""


def build_fullpath(outdir, lastfile):
    """
    Construct full path from OUTDIR and LASTFILE.
    """
    lastfile = (lastfile or "").strip()
    outdir   = (outdir or "").strip()

    if not lastfile:
        return ""

    if os.path.isabs(lastfile):
        return lastfile

    if outdir:
        #print(os.path.join(outdir, lastfile))
        return os.path.join(outdir, lastfile)

    return lastfile


def run_quicklook_on_file(path, source_service):
    print(f"{_ts()}  Triggered by {source_service}: {path}")

    if not wait_for_file_ready(path):
        print(f"{_ts()}  File not ready (timeout): {path}")
        return

    cam = camera_from_fits(path)
    if cam:
        print(f"{_ts()}  FITS CAMERA={cam!r}")
    else:
        print(f"{_ts()}  FITS CAMERA missing")

    if ALLOWED_CAMERA and cam not in ALLOWED_CAMERA:
        print(f"{_ts()}  Skipping (CAMERA={cam!r})")
        return

    try:
        quicklook.run_quicklook(path)
        print(f"{_ts()}  QuickLook DONE : {path}")
    except Exception as e:
        print(f"{_ts()}  QuickLook FAILED for {path}: {e}")


# -----------------------------
# Watchers
# -----------------------------
def watcher(service_name, seen, lock):
    print(f"{_ts()}  Watching {service_name}:{KEY_LASTFILE}")

    svc = ktl.Service(service_name)

    while True:
        try:
            kw_last = svc[KEY_LASTFILE]
            kw_out  = svc[KEY_OUTDIR]
            kw_last.wait()

            lastfile = str(kw_last.read()).strip()
            outdir   = str(kw_out.read()).strip()

            fullpath = build_fullpath(outdir, lastfile)

        except Exception as e:
            if _is_traffic_not_connected(e):
                print(f"{_ts()}  {service_name}: not connected to traffic yet. Retrying...")
                sleep(RETRY_SLEEP_S)
                continue
            print(f"{_ts()}  {service_name}: KTL error ({e}). Retrying...")
            sleep(1.0)
            continue

        if not fullpath.lower().endswith(".fits"):
            continue

        with lock:
            if fullpath in seen:
                continue
            seen.add(fullpath)

        print(f"{_ts()}  {service_name}: OUTDIR={outdir!r}, LASTFILE={lastfile!r}")
        run_quicklook_on_file(fullpath, service_name)


def main():
    seen = set()
    lock = threading.Lock()

    threads = []
    for svc in SERVICES:
        t = threading.Thread(target=watcher, args=(svc, seen, lock), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()

