# File Editing Rules

When modifying files, always use Python.

Requirements:

- MUST use Python for all text file reading and writing.
- MUST NOT use PowerShell Set-Content, Add-Content, Out-File, shell redirection (>, >>), or Get-Content for text manipulation.
- MUST NOT touch binary files (images, archives, compiled artifacts).

Editing rules:

- Modify only the necessary lines; do not rewrite entire files unless required.
- Preserve original encoding, UTF-8 BOM presence, and line endings (LF/CRLF).
- Preserve indentation, whitespace, and formatting.

Always use this exact idiom; nothing else guarantees the above:

```python
from pathlib import Path
p = Path("...")
b = p.read_bytes()
bom = b[:3] == b"ï»¿"
s = b.decode("utf-8-sig") if bom else b.decode("utf-8", "surrogateescape")
crlf = "\r\n" in s
# edit s ...
p.write_bytes(s.encode("utf-8-sig") if bom else s.encode("utf-8"))
```

Use pathlib only.
