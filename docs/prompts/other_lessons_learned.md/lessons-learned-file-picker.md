# Lessons Learned: File Picker Implementation

## Problem Encountered
The native Windows folder selection dialog (via Electron's `dialog.showOpenDialog`) has significant performance issues:
- **60+ second delays** when browsing network shares
- Dialog appears frozen during enumeration of large directories
- User experience is severely degraded for network-heavy workflows

## Root Cause
1. Windows Explorer shell integration performs full directory enumeration before displaying folders
2. Network latency compounds with each subfolder access
3. No way to cancel or timeout the native dialog once opened

## Alternative Solutions Considered

### 1. Custom Folder Picker (Implemented Partially)
**File:** `FolderPicker.tsx`

A custom React component that:
- Uses lazy-loading tree view
- Expands folders on-demand via IPC
- Provides immediate feedback with loading states

**IPC Handlers Required:**
```typescript
// main.ts
ipcMain.handle('list-directory', async (_, dirPath) => {
    const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
    return entries.map(e => ({
        name: e.name,
        isDirectory: e.isDirectory(),
        path: path.join(dirPath, e.name)
    }));
});

ipcMain.handle('get-drives', async () => {
    // PowerShell: Get-PSDrive -PSProvider FileSystem
    // Returns: ['C:\\', 'D:\\', 'Z:\\']
});
```

**Pros:** Fast, responsive, full control
**Cons:** More code to maintain, edge cases (permissions, symlinks)

### 2. Text Paste Only (Current Implementation)
Simply let users paste paths directly into text fields.

**Pros:** Immediate, zero latency, works with any path format
**Cons:** No validation until run, typo-prone

### 3. Recent Paths Dropdown
Store last 10 used paths and offer quick-select dropdown.

**Implementation:**
```typescript
// store in localStorage or electron-store
const recentPaths = JSON.parse(localStorage.getItem('recentPaths') || '[]');
```

### 4. QuickStart Presets
Offer buttons for common locations:
- `+ Local Temp` → `%LOCALAPPDATA%\Temp\BenchTest`  
- `+ Desktop` → `%USERPROFILE%\Desktop\BenchTest`
- `+ Network Share` → Opens minimal path input dialog

## Recommendation for Future
Implement a **hybrid approach**:
1. Text input as primary (instant, flexible)
2. "Browse" button that opens custom picker in a modal
3. Recent paths dropdown for quick re-selection
4. Validate paths asynchronously with visual feedback (green check / red X)

## Related Files
- `components/FolderPicker.tsx` - Custom folder picker component
- `preload.ts` - IPC bridge for `list-directory`, `get-drives`
- `main.ts` - Handlers for filesystem operations
