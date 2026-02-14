# Spec for: write pi to 20dp into tests/test.txt
## Requirements
1. Functional adherence to Windows-native constraints.
2. UTF-8+BOM encoding for all file outputs.
3. Path normalization via pathlib.

## Constraints
- NO WSL or Docker dependencies.
- Absolute path handling for all system calls.
