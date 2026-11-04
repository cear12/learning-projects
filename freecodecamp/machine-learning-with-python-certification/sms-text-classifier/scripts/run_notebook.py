"""Execute the SMS project notebook and preserve cell outputs."""

from pathlib import Path
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
# Keras saves the learned Unicode vocabulary using the kernel's text encoding.
os.environ["PYTHONUTF8"] = "1"
PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT.parent / "fcc_sms_text_classification.ipynb"
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
