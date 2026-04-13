---

description: "Task list for Screen Recorder feature implementation"
---

# Tasks: Screen Recorder

**Input**: Design documents from `specs/001-screen-recorder/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅, research.md ✅, quickstart.md ✅

**Tests**: Included per Constitution Principle III (Test-First is NON-NEGOTIABLE). Tests are
written first, confirmed to fail, then implementation follows.

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. No story label — required by all stories.

- [x] T001 Create pyproject.toml with Python 3.11 project metadata, pytest configuration (testpaths, python_files), and ruff linting settings in pyproject.toml
- [x] T002 [P] Create requirements.txt with pinned dependencies: PyQt6>=6.6, ffmpeg-python>=0.2 in requirements.txt
- [x] T003 [P] Create requirements-dev.txt with development dependencies: pytest>=8, pytest-qt>=4, ruff>=0.4 in requirements-dev.txt
- [x] T004 [P] Create src/ package hierarchy with empty __init__.py files: src/__init__.py, src/recorder/__init__.py, src/settings/__init__.py, src/ui/__init__.py
- [x] T005 [P] Create tests/ directory hierarchy with empty __init__.py files: tests/__init__.py, tests/unit/__init__.py, tests/unit/recorder/__init__.py, tests/unit/settings/__init__.py, tests/unit/app/__init__.py, tests/integration/__init__.py
- [x] T006 [P] Create tests/conftest.py with a session-scoped QApplication fixture required by all PyQt widget tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared data models and settings persistence that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Write failing unit tests for RecordingStatus enum (all 6 states), Recording dataclass (field defaults, state invariants), and Display dataclass in tests/unit/recorder/test_models.py
- [x] T008 Implement RecordingStatus enum (IDLE, RECORDING, STOPPING, COMPLETE, PARTIAL, FAILED) and Recording, Display dataclasses in src/recorder/models.py — verify T007 tests fail before starting, pass after
- [x] T009 [P] Implement RecorderStateError, DiskSpaceError, FFmpegNotFoundError exception classes in src/recorder/exceptions.py
- [x] T010 [P] Write failing unit tests for Settings dataclass (default values, save_directory defaults to None, selected_display_id defaults to None) in tests/unit/settings/test_models.py
- [x] T011 [P] Implement Settings dataclass with save_directory (Path | None), selected_display_id (str | None), app_version (str) fields in src/settings/models.py — verify T010 tests fail before starting, pass after
- [x] T012 Write failing unit tests for SettingsManager: load() returns defaults on missing file, load() resets invalid save_directory, save() writes valid JSON to tmp_path, default_save_directory() returns platform path in tests/unit/settings/test_settings_manager.py
- [x] T013 Implement SettingsManager with load() (defaults on missing/malformed file, resets invalid paths), save() (atomic write via temp file + rename), and default_save_directory() (Videos on Windows, Movies on macOS) in src/settings/settings_manager.py — verify T012 tests fail before starting, pass after

**Checkpoint**: Foundation ready — models, exceptions, and settings persistence are all tested and passing. User story implementation can now begin.

---

## Phase 3: User Story 1 — Start and Stop a Screen Recording (Priority: P1) 🎯 MVP

**Goal**: User can open the app, press Start, record their screen, press Stop, and find a valid
MP4 in their save folder.

**Independent Test**: `python -m src.main` → press Start → wait 5s → press Stop → verify
`recording_YYYYMMDD_HHMMSS.mp4` appears in the save folder and plays in a media player.

### Tests for User Story 1 ⚠️ Write these first — they MUST FAIL before implementation

- [x] T014 [P] [US1] Write failing unit tests for ScreenRecorder with mocked FFmpeg subprocess: start() builds correct platform args (gdigrab on Windows / avfoundation on macOS), transitions to RECORDING state, stop() terminates process and transitions to COMPLETE state in tests/unit/recorder/test_screen_recorder.py
- [x] T015 [P] [US1] Write failing integration test: instantiate ScreenRecorder with real FFmpeg, call start() on primary display, sleep 2s, call stop(), assert returned Recording has status COMPLETE and save_path points to a readable MP4 with duration > 1s in tests/integration/test_recording_flow.py

### Implementation for User Story 1

- [x] T016 [US1] Implement DisplayEnumerator.list_displays() — query QApplication.screens(), map each QScreen to a Display model (id=screen.name(), label, width, height, x, y, is_primary, scale_factor) in src/recorder/display_enumerator.py
- [x] T017 [US1] Implement ScreenRecorder.__init__(settings), status (RecordingStatus property), current_recording (Recording | None property), elapsed_seconds (float property) in src/recorder/screen_recorder.py
- [x] T018 [US1] Implement ScreenRecorder.start(display: Display): validate save_directory writable, build FFmpeg args for platform (gdigrab offset+size on Windows; avfoundation display index on macOS), spawn subprocess, set Recording with start_time, transition to RECORDING, emit status_changed in src/recorder/screen_recorder.py
- [x] T019 [US1] Implement ScreenRecorder.stop(): send SIGTERM to FFmpeg subprocess, await exit, set end_time, transition to COMPLETE (exit 0) or FAILED (exit non-zero) or PARTIAL (file > 0 bytes on unexpected termination), emit status_changed and recording_completed in src/recorder/screen_recorder.py
- [x] T020 [US1] Implement elapsed timer: QTimer(interval=1000) started on RECORDING, stopped on any terminal state, emitting elapsed_updated(float) signal each tick in src/recorder/screen_recorder.py
- [x] T021 [US1] Implement unexpected-termination handler: monitor FFmpeg subprocess exit while in RECORDING state (QTimer or QProcess), transition to PARTIAL if file > 0 bytes, emit error_occurred with message in src/recorder/screen_recorder.py
- [x] T022 [US1] Implement MainWindow skeleton in src/ui/main_window.py: status indicator (QLabel with colored dot — grey=Idle, red=Recording, orange=Stopping), elapsed timer label (QLabel, MM:SS format, resets to 00:00 on IDLE), Start/Stop QPushButton following UI state machine from contracts/ui-states.md
- [x] T023 [US1] Wire ScreenRecorder Qt signals to MainWindow: status_changed → update indicator label + button text/enabled state; elapsed_updated → update timer label; recording_completed → log completion in src/ui/main_window.py
- [x] T024 [US1] Implement error dialog handler in MainWindow: on error_occurred signal, show QMessageBox.critical with the message, log structured event (event, message, recording_id, timestamp) in src/ui/main_window.py
- [x] T025 [US1] Implement src/main.py: acquire SingleInstanceLock (exit with warning dialog if already running), create QApplication, instantiate SettingsManager and call load(), bootstrap default save_directory if none is set, instantiate ScreenRecorder(settings), instantiate MainWindow(recorder, settings_manager), show window, call app.exec(), release lock on exit

**Checkpoint**: User Story 1 is fully functional. Launch the app, record, stop — MP4 file appears. Both unit and integration tests pass.

---

## Phase 4: User Story 2 — Select Save Location (Priority: P2)

**Goal**: User can choose the folder where recordings are saved, see the current path at all
times, and have their choice persist across app restarts.

**Independent Test**: Open app → click "Choose Folder" → pick a new directory → close app →
reopen → verify the chosen folder path is shown and a new recording saves there.

### Tests for User Story 2 ⚠️ Write these first — they MUST FAIL before implementation

- [x] T026 [P] [US2] Write failing unit tests for save location: SettingsManager correctly persists and restores a custom save_directory path; SettingsManager resets to default when saved path no longer exists in tests/unit/settings/test_settings_manager.py

### Implementation for User Story 2

- [x] T027 [US2] Add "Choose Folder" QPushButton and save path QLabel to MainWindow layout; disable "Choose Folder" button when status is RECORDING per UI state machine in src/ui/main_window.py
- [x] T028 [US2] Implement folder picker handler in MainWindow: on "Choose Folder" click, open QFileDialog.getExistingDirectory pre-seeded with current save_directory; if user confirms and path is writable, accept; if not writable, show inline QLabel warning "This folder is not writable — choose another" in src/ui/main_window.py
- [x] T029 [US2] On valid folder selection, call settings_manager.save(updated_settings) and update the save path QLabel to show the new absolute path in src/ui/main_window.py
- [x] T030 [US2] On app startup in src/main.py, read settings.save_directory; if None or path invalid, call settings_manager.default_save_directory() and save that as the default; pass settings to MainWindow to display on startup in src/main.py

**Checkpoint**: User Stories 1 AND 2 work independently. Can record to a custom folder that survives restart.

---

## Phase 5: User Story 3 — Select Which Display to Record (Priority: P3)

**Goal**: When multiple monitors are connected, the user can choose which display to record.
The selection persists across restarts.

**Independent Test**: With 2 monitors connected — open app → display dropdown appears → select
secondary display → record 3s → stop → verify video shows secondary display content only.

### Tests for User Story 3 ⚠️ Write these first — they MUST FAIL before implementation

- [x] T031 [P] [US3] Write failing unit tests for DisplayEnumerator: mock QApplication.screens() with 1 screen → list_displays() returns 1 Display with is_primary=True; mock with 2 screens → returns 2 Displays with correct labels and geometries in tests/unit/recorder/test_display_enumerator.py
- [x] T032 [P] [US3] Write failing unit tests for display persistence: SettingsManager saves and restores selected_display_id; resets to None when saved ID is not in the current display list in tests/unit/settings/test_settings_manager.py

### Implementation for User Story 3

- [x] T033 [US3] Add display selector QComboBox to MainWindow; show only when DisplayEnumerator.list_displays() returns more than 1 display; hide (not just disable) when only 1 display is connected in src/ui/main_window.py
- [x] T034 [US3] Populate display selector on startup: call DisplayEnumerator.list_displays(), populate QComboBox with Display.label values, restore previously saved display selection from settings.selected_display_id (fall back to primary if ID not found) in src/ui/main_window.py
- [x] T035 [US3] Connect QApplication.screenAdded and QApplication.screenRemoved to a re-enumerate handler that repopulates the display selector and shows/hides it based on count in src/ui/main_window.py
- [x] T036 [US3] On display selection change, persist the selected display's id via settings_manager.save(updated_settings) in src/ui/main_window.py
- [x] T037 [US3] On recording Start, read the selected Display from the QComboBox (or use the single display when selector is hidden) and pass it to ScreenRecorder.start(display) in src/ui/main_window.py
- [x] T038 [US3] Handle monitor-unplugged mid-recording: in the screenRemoved handler, if currently RECORDING, call ScreenRecorder's internal _handle_display_lost() which emits error_occurred("Display disconnected during recording — recording stopped") and transitions to PARTIAL state in src/recorder/screen_recorder.py

**Checkpoint**: All 3 user stories work independently. Multi-monitor selection is persisted and restored.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Robustness, observability, distribution, and accessibility improvements
affecting all stories.

- [x] T045 [P] Implement SingleInstanceLock in src/main.py: Windows named mutex via ctypes (CreateMutexW / ERROR_ALREADY_EXISTS), POSIX exclusive flock via fcntl; integrate into main() to show QMessageBox.warning and exit(1) if a second instance is detected (FR-015). Unit tests in tests/unit/app/test_single_instance.py cover: first acquire succeeds, second acquire fails while first held, acquire succeeds after release, release is idempotent — for both platform paths. (Tests and implementation committed together — see plan.md Complexity Tracking.)
- [x] T039 [P] Add structured Python logging throughout ScreenRecorder lifecycle events: recording started (display, save_path), recording stopped (duration, status), DiskSpaceError, FFmpeg crash (exit code, stderr tail) — use logging.getLogger(__name__) with JSON-compatible field names in src/recorder/screen_recorder.py
- [x] T040 [P] Implement pre-recording disk space check: before spawning FFmpeg, call shutil.disk_usage(save_directory); if free < 500 MB, raise DiskSpaceError with available bytes in the message in src/recorder/screen_recorder.py
- [x] T041 [P] Implement save-folder existence check in MainWindow before each recording start: if settings.save_directory no longer exists, show QMessageBox prompting user to choose a new folder before proceeding in src/ui/main_window.py
- [x] T042 Review MainWindow for WCAG 2.1 AA compliance: set accessible names on all controls (setAccessibleName), verify tab order visits all interactive elements, confirm status label color is not the sole indicator (add text) in src/ui/main_window.py
- [x] T043 [P] Create PyInstaller spec file language_review_app.spec: onefile + windowed mode, bundle FFmpeg binary as a data file, include PyQt6 platform plugins for Windows (qwindows.dll) and macOS (libqcocoa.dylib) in language_review_app.spec
- [x] T044 Run quickstart.md golden path validation end-to-end (all 7 steps) on both Windows and macOS; document any discrepancies found in specs/001-screen-recorder/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — no dependency on US2 or US3
- **US2 (Phase 4)**: Depends on Phase 2 — no dependency on US1 or US3
- **US3 (Phase 5)**: Depends on Phase 2 — no dependency on US1 or US2
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no story cross-dependencies
- **US2 (P2)**: Can start after Foundational — no story cross-dependencies (SettingsManager built in Phase 2)
- **US3 (P3)**: Can start after Foundational — no story cross-dependencies (DisplayEnumerator is US3-specific)

### Within Each User Story

- Test tasks MUST be written and FAIL before implementation of their target
- DisplayEnumerator (T016) before ScreenRecorder.start() (T018) — start() needs a Display object
- ScreenRecorder (T017–T021) before MainWindow wiring (T022–T024) — signals must exist to wire
- MainWindow (T022–T024) before main.py (T025) — window class must exist to instantiate

### Parallel Opportunities

Setup tasks T002–T006 are all [P] — run together after T001.
Foundational: T009, T010–T011 are [P] with T007–T008 (different files). T012–T013 depend on T011.
US1: T014 and T015 are [P] (different test files). T016 is [P] with T017.
US2: T026 is [P] — write test while implementing US1.
US3: T031 and T032 are [P] — write both test files together.
Polish: T039, T040, T041, T043, T045 are all [P] — different files, no inter-dependencies.

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Run together (different files):
Task: "T007 — Write tests for models in tests/unit/recorder/test_models.py"
Task: "T009 — Implement exceptions in src/recorder/exceptions.py"
Task: "T010 — Write tests for Settings in tests/unit/settings/test_models.py"

# After T007 passes:
Task: "T008 — Implement models in src/recorder/models.py"

# After T010 passes + T011 complete:
Task: "T012 — Write SettingsManager tests"
# After T012 passes:
Task: "T013 — Implement SettingsManager"
```

## Parallel Example: User Story 1

```bash
# Write all US1 tests together (both [P]):
Task: "T014 — Unit tests for ScreenRecorder in tests/unit/recorder/test_screen_recorder.py"
Task: "T015 — Integration test in tests/integration/test_recording_flow.py"

# After T014 confirmed failing, run in parallel:
Task: "T016 — DisplayEnumerator in src/recorder/display_enumerator.py"
Task: "T017 — ScreenRecorder properties in src/recorder/screen_recorder.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T006)
2. Complete Phase 2: Foundational (T007–T013) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T014–T025)
4. **STOP and VALIDATE**: Launch app, record, stop, verify MP4 file
5. Optionally demo before continuing to US2

### Incremental Delivery

1. Setup + Foundational → tests green, models ready
2. User Story 1 → working recorder with Start/Stop UI → **demo/validate**
3. User Story 2 → add save location picker → **demo/validate**
4. User Story 3 → add display selector → **demo/validate**
5. Polish → production-ready packaging

### Parallel Team Strategy (if multiple developers)

After Foundational phase completes:
- Dev A: User Story 1 (recorder engine + basic UI)
- Dev B: User Story 2 (settings persistence + folder picker UI) — SettingsManager already exists from Phase 2
- Dev C: User Story 3 (display enumerator + dropdown UI)

All three stories are independently testable and non-conflicting at the file level.

---

## Notes

- [P] = different files, no dependencies on incomplete sibling tasks
- [US1/US2/US3] label maps each task to its user story for traceability
- Every test task MUST be confirmed failing before its paired implementation task begins
- File output naming convention: `recording_YYYYMMDD_HHMMSS.mp4` (from data-model.md)
- FFmpeg binary location at runtime: resolve relative to sys.executable for PyInstaller compatibility
- On macOS, ScreenRecorder must handle the `avfoundation` permission prompt gracefully (it's OS-managed — no app code required, but integration test must account for it)
