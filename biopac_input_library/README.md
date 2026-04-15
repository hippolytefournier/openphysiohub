# biopac_input_library

This directory must contain the InpOut32 parallel-port driver binaries used
to send digital triggers to BIOPAC.

Download the pre-built DLLs from:

> https://www.highrez.co.uk/downloads/inpout32/

Place the following files here:

| File | Description |
|---|---|
| `inpoutx64.dll` | 64-bit parallel port driver (used at runtime) |
| `inpout32.dll`  | 32-bit parallel port driver (kept as fallback reference) |

The BIOPAC `mpdev.dll` is **not** stored here — it is installed system-wide
by the **BIOPAC Hardware API 2.2 Research** installer, available from:

> https://www.biopac.com/ → Software → BIOPAC Hardware API
