"""Apply the bounded FSR4 reference-precision patch to the pinned converter."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PIN = "4096eb8d2872922951ec7bf6ceca7a8e74032e19"


def prepare(source):
    source = source.resolve()
    if subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() != PIN:
        raise RuntimeError("Unexpected dxil-spirv revision")
    patch = ROOT / "tools/dxil-spirv-fsr4-fp16.patch"
    command = ["git", "-C", str(source), "apply"]
    if subprocess.run(command + ["--reverse", "--check", str(patch)], capture_output=True).returncode == 0:
        return
    subprocess.run(command + ["--check", str(patch)], check=True)
    subprocess.run(command + [str(patch)], check=True)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]))
