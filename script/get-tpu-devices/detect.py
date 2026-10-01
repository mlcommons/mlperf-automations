"""TPU detection for `mlcr get,tpu-devices`.

Fill in `get_tpu_info()` so it returns one dict per TPU chip on this node.
How you obtain the values is up to you:

  * pure Python, if a library exposes them (e.g. jax, libtpu bindings)
  * `subprocess` to run a CLI (e.g. `tpu-info`, `lspci`) and parse its output
  * put the commands in `run.sh` instead, write their output to a file, and
    just parse that file here

The only thing that matters is the shape of what this script writes to
`tmp-run.out` -- `customize.py` parses that into the `MLC_TPU_*` env vars.
See info.md for the full key list and value formats, and
../get-xpu-devices/detect.py for a working example.
"""


def get_tpu_info():
    """Return a list of dicts, one per TPU chip.

    "TPU Device ID" must come first in each dict -- customize.py uses it as
    the marker that starts a new device block.
    """
    # TODO(tpu): implement. Expected shape:
    #
    #   return [
    #       {
    #           "TPU Device ID": "0",
    #           "TPU Name": "TPU v5e",
    #           "Memory Type": "HBM2e",
    #           "Global memory": "16 GiB",
    #           "Host Interconnect Type": "PCIe 4.0 x16",
    #           "libtpu version": "0.0.11",
    #       },
    #       ...
    #   ]
    raise NotImplementedError(
        "get-tpu-devices: get_tpu_info() is not implemented yet")


if __name__ == "__main__":
    try:
        tpu_info_list = get_tpu_info()
    except Exception as exc:
        raise SystemExit(f"[ERROR] Failed to collect TPU info: {exc}")

    with open("tmp-run.out", "w", encoding="utf-8") as f:
        for tpu_info in tpu_info_list:
            for key, value in tpu_info.items():
                f.write(f"{key}: {value}\n")
