# File Editing Rules

When modifying files, always use Python.

Requirements:

- MUST use Python for all text file reading and writing.
- MUST NOT use PowerShell Set-Content.
- MUST NOT use Add-Content.
- MUST NOT use Out-File.
- MUST NOT use shell redirection (>, >>) to modify files.
- MUST NOT use Get-Content for text manipulation.

Editing rules:

- Modify only the necessary lines.
- Do not rewrite entire files unless required.
- Preserve the original encoding.
- Preserve UTF-8 BOM if present.
- Preserve line endings (LF/CRLF).
- Preserve indentation.
- Preserve whitespace.
- Preserve formatting.

Use pathlib or open() in Python.