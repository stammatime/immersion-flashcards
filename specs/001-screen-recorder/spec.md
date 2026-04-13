# Feature Specification: Screen Recorder

**Feature Branch**: `001-screen-recorder`
**Created**: 2026-04-12
**Status**: Draft
**Input**: User description: "I want to create an application that will be able to record the screen
of the user. I would like this application to be able to work on many systems, with a focus on
Windows and MacOS. Later, this recording will be used to extract subtitle information from video
games and movies, parse out all the words, then create flash cards from all of the new words the
user has experienced. However, right now we will focus on just the screen recording. Provide a
simple user interface that also allows the user to turn the recording on and off and select where
to save it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start and Stop a Screen Recording (Priority: P1)

A user opens the application and wants to record their screen while watching a foreign-language
movie or playing a video game. They start the recording before the content begins and stop it
when they are done. The resulting video file is saved automatically to their chosen save folder.

**Why this priority**: This is the entire core value of the application. Without the ability to
reliably start and stop a recording and produce a saved video file, nothing else is possible.

**Independent Test**: Open the app, press Start, let it run for 10 seconds, press Stop. Verify
that a valid video file appears in the save folder and can be played back.

**Acceptance Scenarios**:

1. **Given** the application is open and not recording, **When** the user presses "Start
   Recording", **Then** recording begins, the status indicator changes to "Recording", and
   a visible timer begins counting elapsed time.
2. **Given** the application is actively recording, **When** the user presses "Stop Recording",
   **Then** recording stops, the video file is written to the save folder, the status indicator
   returns to "Idle", and the elapsed timer resets.
3. **Given** the application is recording, **When** the system experiences an unexpected
   interruption (sleep, crash), **Then** any captured footage up to that point is preserved
   as a recoverable partial file rather than discarded entirely.

---

### User Story 2 - Select Save Location (Priority: P2)

A user wants to control where their recordings are stored — for example, on an external drive or
in a specific project folder — so they can easily find and use the files later (e.g., for subtitle
extraction).

**Why this priority**: Without a configurable save location the application is still functional
(it can default to a known folder), but users need control over file placement to integrate this
tool into their workflow.

**Independent Test**: Open the app, change the save location to a new folder, start and stop a
recording. Verify the file appears in the newly selected folder, not the default location.

**Acceptance Scenarios**:

1. **Given** the application is open, **When** the user clicks "Choose Folder", **Then** the
   operating system's native folder-picker dialog opens.
2. **Given** the user selects a valid folder in the dialog, **When** they confirm the selection,
   **Then** the save location updates and the new path is displayed in the application.
3. **Given** the user has previously set a save location, **When** they close and reopen the
   application, **Then** the previously chosen save location is remembered and shown.
4. **Given** the user selects a folder they do not have write permission for, **When** they
   attempt to start recording, **Then** a clear error message is shown before recording begins.

---

### User Story 3 - Select Which Display to Record (Priority: P3)

A user with multiple monitors wants to choose which screen to record — for example, their
secondary monitor where the game or movie is playing — rather than always capturing the
primary display.

**Why this priority**: Single-monitor users are fully served by US1 and US2. Multi-monitor
support is a meaningful quality-of-life feature but does not block the core use case.

**Independent Test**: With two monitors connected, open the app, select the secondary display
from the display picker, record for 5 seconds, stop. Verify the video shows the secondary
display content only.

**Acceptance Scenarios**:

1. **Given** only one display is connected, **When** the application opens, **Then** no
   display selection control is shown (single display is used automatically).
2. **Given** two or more displays are connected, **When** the application opens, **Then** a
   display selector shows each available screen (labeled by position or system name).
3. **Given** multiple displays are available, **When** the user selects a display and starts
   recording, **Then** only that display's content is captured in the video.
4. **Given** the user has selected a non-primary display, **When** they close and reopen the
   application, **Then** their display selection is remembered.

---

### Edge Cases

- What happens when disk space runs out mid-recording? The application MUST stop recording
  gracefully and notify the user, preserving any footage already captured.
- What happens when the user attempts to start a second recording while one is already active?
  The Start button MUST be disabled (or replaced by Stop) while recording is in progress.
- What happens when the save folder is deleted while the app is running? The application MUST
  detect this before starting a new recording and prompt the user to choose a new location.
- What happens when the display configuration changes mid-recording (monitor unplugged)? The
  application MUST continue recording from the remaining display and notify the user of the
  change.
- What happens when the user launches the application while it is already running?
  The second launch MUST show a brief "already running" notice and exit immediately —
  it MUST NOT open a second window or silently fail.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST allow a user to start screen recording with a single
  on-screen interaction (one button press).
- **FR-002**: The application MUST allow a user to stop an active recording with a single
  on-screen interaction (one button press).
- **FR-003**: The application MUST display a clear recording status indicator showing whether
  it is currently recording or idle.
- **FR-004**: The application MUST display an elapsed-time counter while recording is active.
- **FR-005**: The application MUST save completed recordings as video files in a format playable
  by common media players without additional software.
- **FR-006**: The application MUST allow the user to choose the folder where recordings are
  saved using the operating system's native folder picker.
- **FR-007**: The application MUST display the currently configured save folder path at all
  times.
- **FR-008**: The application MUST persist the user's chosen save folder between sessions.
- **FR-009**: The application MUST run on Windows 10 or later without requiring manual
  installation of additional runtimes or codecs by the user.
- **FR-010**: The application MUST run on macOS 12 (Monterey) or later without requiring
  manual installation of additional runtimes or codecs by the user.
- **FR-011**: When multiple displays are connected, the application MUST allow the user to
  select which display to record.
- **FR-012**: The application MUST persist the user's chosen display selection between
  sessions.
- **FR-013**: The application MUST notify the user with a clear message if recording cannot
  start (e.g., invalid save folder, insufficient disk space, permission denied).
- **FR-014**: The application MUST preserve any footage already captured if a recording is
  interrupted unexpectedly (system sleep, crash, disk full).
- **FR-015**: The application MUST prevent more than one instance from running
  simultaneously. If a second instance is launched while one is already running,
  it MUST display a clear message to the user and exit without opening a second window.
  *(Edge-case-derived — no primary user story; see Edge Cases section.)*

### Key Entities

- **Recording**: A captured video session. Key attributes: start time, end time, duration,
  save path, target display, completion status (complete / partial).
- **Settings**: User-configurable application state persisted across sessions. Key attributes:
  save folder path, selected display identifier.
- **Display**: A connected monitor available for capture. Key attributes: system identifier,
  human-readable label (e.g., "Display 1 — Primary"), resolution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can go from launching the application to having a recording underway in
  under 3 interactions (open → start → recording active).
- **SC-002**: Completed recording files are available for playback in a standard media player
  within 5 seconds of pressing Stop.
- **SC-003**: The application runs on Windows 10+ and macOS 12+ without the user needing to
  install any additional software or codecs.
- **SC-004**: Users can change the save location in 2 interactions or fewer (click "Choose
  Folder" → select folder → confirmed).
- **SC-005**: 90% of first-time users can successfully start and stop a recording within 1
  minute of opening the application without referring to documentation.
- **SC-006**: No recording data is lost when the application is closed or interrupted, provided
  at least 1 second of footage was captured.

## Assumptions

- The application is a desktop application with a persistent window; it does not need to
  operate as a system-tray-only or headless process.
- Recordings capture the full visual content of the selected display (full-screen capture),
  not individual application windows. Window-level capture is out of scope for this feature.
- Audio capture is out of scope for this feature. Recordings are video-only. (Audio may be
  addressed in a future feature when the subtitle extraction workflow is specified.)
- The output video format will be a widely compatible container (e.g., MP4); the exact codec
  choice is an implementation decision to be made during planning.
- The default save location (before the user changes it) is the operating system's standard
  Videos or Movies folder for the current user.
- Linux support is explicitly out of scope for this feature, though the architecture should
  not preclude it in future.
- The application does not require an internet connection.
- No user account or authentication is required.
- There is no upper limit enforced on recording duration; users may record for as long as
  their disk space allows.
