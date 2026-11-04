"""Execute the project notebook and preserve every successful cell output."""

from pathlib import Path
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT.parent / "fcc_predict_health_costs_with_regression.ipynb"
for name, folder in (("IPYTHONDIR", "ipython"), ("JUPYTER_RUNTIME_DIR", "jupyter"),
                     ("MPLCONFIGDIR", "matplotlib")):
    os.environ.setdefault(name, str(PROJECT / ".cache" / folder))
    Path(os.environ[name]).mkdir(parents=True, exist_ok=True)

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

notebook = nbformat.read(NOTEBOOK, as_version=4)
manager = KernelManager(kernel_name="python3")
manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]


def checkpoint(cell, cell_index, **kwargs):
    nbformat.write(notebook, NOTEBOOK)
    if cell.cell_type == "code":
        print(f"Completed: {cell.id}", flush=True)
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                print(output.text, end="", flush=True)


client = NotebookClient(notebook, km=manager, timeout=1200,
                        resources={"metadata": {"path": str(PROJECT)}},
                        on_cell_executed=checkpoint)
try:
    client.execute()
finally:
    nbformat.write(notebook, NOTEBOOK)
    if manager.has_kernel:
        manager.shutdown_kernel(now=True)
print("Complete notebook execution passed.")
