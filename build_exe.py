import PyInstaller.__main__
import shutil
import os

# Clean previous build
if os.path.exists('dist'):
    print("Cleaning dist folder...")
    shutil.rmtree('dist')
if os.path.exists('build'):
    print("Cleaning build folder...")
    shutil.rmtree('build')

print("🚀 Starting PyInstaller Build...")

args = [
    'start_gui.py',
    '--name=HybridConductor',
    '--onefile',
    '--noconsole',
    '--clean',
    # Include Static Files
    '--add-data=backend/static;backend/static',
    # Include Templates (if any logic uses them, though we serve static index.html)
    '--add-data=backend/dashboard/templates;backend/dashboard/templates',
    # Hidden imports to ensure Flask app is found
    '--hidden-import=backend',
    '--hidden-import=backend.dashboard',
    '--hidden-import=backend.dashboard.app',
]

if os.path.exists('backend/static/favicon.ico'):
    args.append('--icon=backend/static/favicon.ico')

PyInstaller.__main__.run(args)

print("✅ Build Complete! Check dist/HybridConductor.exe")
