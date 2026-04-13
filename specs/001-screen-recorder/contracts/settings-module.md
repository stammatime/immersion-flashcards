# Contract: Settings Module

**Module**: `src/settings/`
**Consumer**: UI layer, Recorder module
**Date**: 2026-04-12

---

## SettingsManager (class)

Manages reading, writing, and validating application settings. Singleton per application run.

### Constructor

```python
SettingsManager(config_dir: Path | None = None)
```

- `config_dir`: Override for the config directory (used in tests). If None, resolves the
  OS-appropriate user config directory automatically.
- Does NOT raise on missing file — missing config is treated as defaults.

---

### Properties

| Property | Type | Description |
|---|---|---|
| `settings` | `Settings` | Current settings snapshot (read-only view) |
| `config_path` | `Path` | Full path to the settings JSON file |

---

### Methods

#### `load() -> Settings`

Reads settings from disk. If file is missing or malformed, returns defaults and logs a warning.
Validates loaded values:
- `save_directory`: resets to OS default if path does not exist or is not writable.
- `selected_display_id`: resets to None if ID not present in current display list.

**Returns**: Validated `Settings` object.

---

#### `save(settings: Settings) -> None`

Persists settings to disk atomically (write to temp file, then rename).

**Raises**:
- `PermissionError` — if config directory is not writable.

---

#### `default_save_directory() -> Path`

Returns the OS-appropriate default video save directory:
- Windows: `%USERPROFILE%\Videos`
- macOS: `~/Movies`

---

### Signals

| Signal | Payload | Emitted when |
|---|---|---|
| `settings_changed` | `Settings` | Any setting is saved |
