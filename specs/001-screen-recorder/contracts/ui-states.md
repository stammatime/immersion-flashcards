# Contract: UI State Machine

**Component**: Main Window (`src/ui/main_window.py`)
**Date**: 2026-04-12

Defines the UI states and the widget enable/disable/label rules that MUST be enforced
in the main window. The UI is a single window with no navigation.

---

## UI States

| State | Condition | Start Button | Stop Button | Choose Folder Button | Display Selector |
|---|---|---|---|---|---|
| **IDLE** | Recorder is IDLE | Enabled, label "Start Recording" | Disabled | Enabled | Enabled |
| **RECORDING** | Recorder is RECORDING or STOPPING | Disabled | Enabled, label "Stop Recording" | Disabled | Disabled |
| **ERROR** | Last operation failed | Enabled, label "Start Recording" | Disabled | Enabled | Enabled |

Transitions between UI states are driven exclusively by `ScreenRecorder.status_changed` signal.
The UI MUST NOT poll the recorder.

---

## Always-Visible Elements

The following elements are visible in all UI states:

| Element | Content |
|---|---|
| Status indicator | Text + color dot: "Idle" (grey), "Recording" (red), "Stopping…" (orange) |
| Elapsed timer | `MM:SS` format; resets to `00:00` when IDLE; counts up while RECORDING |
| Save folder path | Absolute path of current `settings.save_directory`; truncated with ellipsis if too long |
| Display selector | Hidden if only 1 display connected; dropdown otherwise |

---

## Error Display

When `ScreenRecorder.error_occurred` is emitted:
- Show a modal dialog with the error message.
- UI transitions to ERROR state (same controls as IDLE).
- Log the error with structured fields: `event`, `message`, `recording_id`, `timestamp`.

---

## Folder Picker Behavior

When "Choose Folder" is pressed:
1. Open `QFileDialog.getExistingDirectory` with the current save directory pre-selected.
2. If user confirms a selection:
   a. Validate the directory is writable.
   b. If valid: update settings, update displayed path.
   c. If not writable: show inline warning label ("This folder is not writable — choose another").
3. If user cancels: no change.

The dialog is always the OS-native folder picker (Qt default behavior on both platforms).
