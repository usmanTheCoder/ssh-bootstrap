# PyInstaller hook for paramiko
# This ensures all paramiko components are included

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect everything from paramiko
datas, binaries, hiddenimports = collect_all('paramiko')

# Add all paramiko submodules
hiddenimports += collect_submodules('paramiko')

# Add cryptography dependencies
hiddenimports += [
    'cryptography',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.asymmetric',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
]

# Add other required modules
hiddenimports += [
    'nacl',
    'nacl.bindings',
    'bcrypt',
    '_cffi_backend',
]
