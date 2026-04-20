# Feature Specification: Video Text Extraction for Anki Flashcards

**Feature Branch**: `002-video-text-extraction`  
**Created**: 2026-04-19  
**Status**: Draft  
**Input**: User description: "Scan video for on-screen text in user's target learning language (Japanese, Chinese, and/or English), extract text, and generate Anki-compatible flashcards with screenshots for language immersion learning."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Text from Video Game Footage (Priority: P1)

A language learner plays a Japanese RPG and records their gameplay using the screen recorder feature. Before running extraction, they specify their target learning language (e.g., Japanese). After the session, they run the text extraction tool on the recorded video. The system scans each frame, prioritizing detection of the user's specified learning language — capturing dialogue boxes, menu items, status screens, and any other on-screen text in that language. Each unique word or phrase is captured the first time it appears, along with a screenshot of the frame where it was found. The full transcript is saved, and a set of Anki flashcards is generated containing only first-occurrence entries, ready for import and study.

**Why this priority**: This is the core value proposition — converting passive gameplay into active study material. Without this, no other feature matters.

**Independent Test**: Can be fully tested by providing a short video containing visible Japanese text, specifying Japanese as the learning language, and verifying that (a) text is extracted, (b) a complete transcript is produced, (c) an Anki-importable file is generated with one card per unique word, and (d) screenshots are attached.

**Acceptance Scenarios**:

1. **Given** a recorded video containing Japanese dialogue text and the user has set Japanese as their learning language, **When** the user runs text extraction, **Then** the system identifies and extracts all visible Japanese text from dialogue boxes and menus.
2. **Given** a video with repeated words across multiple scenes, **When** extraction completes, **Then** only the first occurrence of each word generates a flashcard, while all occurrences appear in the full transcript.
3. **Given** extracted text and screenshots, **When** the user imports the output into Anki, **Then** each card displays the extracted text on the front and the corresponding screenshot on the back.

---

### User Story 2 - Specify Target Learning Language (Priority: P1)

Before starting extraction, the learner selects their target learning language from the supported set (Japanese, Chinese, English). This tells the system which language to prioritize and build flashcards for. The user may also optionally enable detection of additional languages for transcript completeness, but the flashcard deck focuses on the learning language.

**Why this priority**: The learning language selection is essential to the core workflow — it determines what flashcards are generated and ensures the user studies the right content.

**Independent Test**: Can be tested by running extraction on a video containing multiple languages with different learning language selections and verifying flashcards are generated only for the selected learning language.

**Acceptance Scenarios**:

1. **Given** the user selects Japanese as their learning language, **When** extraction runs on a video with Japanese, Chinese, and English text, **Then** flashcards are generated only for Japanese text entries.
2. **Given** the user selects Chinese as their learning language and also enables English for transcript capture, **When** extraction runs, **Then** flashcards contain only Chinese text, while the transcript includes both Chinese and English entries.
3. **Given** the user does not specify a learning language, **When** they attempt to run extraction, **Then** the system prompts them to select a learning language before proceeding.

---

### User Story 3 - Full Transcript Review (Priority: P2)

After extraction, the learner wants to review everything that was said or displayed during their play session. They open the transcript file and see a chronological log of all text that appeared on screen in any detected language, including timestamps and scene context. This lets them revisit dialogue they may have missed or review the full narrative flow.

**Why this priority**: The transcript provides complete coverage and context that individual flashcards cannot. It supports review and comprehension beyond vocabulary drilling.

**Independent Test**: Can be tested by running extraction on a video and verifying the transcript contains all detected text entries in chronological order with timestamps.

**Acceptance Scenarios**:

1. **Given** a video with text appearing at various points, **When** extraction completes, **Then** a transcript file is produced listing every detected text entry in chronological order with approximate timestamps.
2. **Given** a transcript file, **When** the user opens it, **Then** each entry shows the detected text, the timestamp in the video, and which language was detected.

---

### User Story 4 - Screenshot Context for Flashcards (Priority: P3)

When reviewing flashcards in Anki, the learner sees not just the extracted text but also a screenshot of the exact moment in the video where that text appeared. This visual context helps with recall — they can see the game scene, the character speaking, and the surrounding UI, which strengthens memory association.

**Why this priority**: Visual context significantly improves retention for language learning, but the core extraction and card generation must work first.

**Independent Test**: Can be tested by importing generated cards into Anki and verifying each card includes a legible screenshot showing the text in its original on-screen context.

**Acceptance Scenarios**:

1. **Given** a generated flashcard for a word first seen at a specific frame, **When** the user views the card in Anki, **Then** the card includes a screenshot of that frame showing the text in context.
2. **Given** a video with small or partially obscured text, **When** extraction captures the text, **Then** the screenshot is still taken from the frame where the text was most clearly visible.

---

### Edge Cases

- What happens when text appears partially off-screen or is obscured by other UI elements? The system should attempt extraction on whatever is visible and flag low-confidence results.
- What happens when the video has no detectable text at all? The system should complete gracefully and produce an empty transcript with a message indicating no text was found.
- What happens when the same word appears in multiple languages in the same frame (e.g., Japanese kanji and Chinese hanzi share characters)? The system should use language context (surrounding characters, sentence structure) to determine the language, and treat ambiguous cases based on the user's selected learning language.
- What happens when text appears for only a single frame (very briefly)? The system should still attempt to capture it, though it may flag it as low-confidence.
- What happens when the video quality is very low or the text is stylized (e.g., fantasy fonts)? The system should attempt extraction and flag low-confidence results rather than silently skipping them.
- What happens when the user's learning language is not present in the video? The system should complete successfully with an empty flashcard deck and inform the user that no text in their learning language was detected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow the user to specify a target learning language from the supported set (Japanese, Chinese, English) before starting extraction.
- **FR-002**: System MUST prioritize detection of the user's specified learning language and generate flashcards exclusively for text in that language.
- **FR-003**: System MUST scan video frames and detect text rendered in Japanese (hiragana, katakana, kanji), Chinese (simplified and traditional), and/or English.
- **FR-004**: System MUST extract detected text from each frame where text is present, including dialogue boxes, menus, status screens, and any other on-screen text regions.
- **FR-005**: System MUST produce a complete chronological transcript of all detected text across all enabled languages, including approximate timestamps for each entry.
- **FR-006**: System MUST identify unique words/phrases and generate a flashcard only for the first occurrence of each unique entry in the learning language.
- **FR-007**: System MUST capture a screenshot of the video frame where each first-occurrence text was detected and associate it with the corresponding flashcard.
- **FR-008**: System MUST export flashcards in a format compatible with Anki's import functionality (Anki deck package or tab/comma-separated file with media references).
- **FR-009**: System MUST tag each extracted text entry with its detected language.
- **FR-010**: System MUST handle videos of varying lengths and resolutions without crashing or producing corrupt output.
- **FR-011**: System MUST report extraction progress to the user during processing.
- **FR-012**: System MUST handle cases where no text is detected by producing an empty result set with an informative message.
- **FR-013**: System MUST flag low-confidence text extractions so the user can review them.
- **FR-014**: System MUST allow the user to optionally enable additional languages for transcript capture beyond their learning language.

### Key Entities

- **Learning Language Configuration**: The user's selected target language for flashcard generation, plus any additional languages enabled for transcript capture.
- **Video Source**: The recorded gameplay video file to be processed; key attributes include file path, duration, and resolution.
- **Text Entry**: A detected piece of text from a video frame; includes the text content, language, confidence level, timestamp, and reference to the source frame.
- **Transcript**: An ordered collection of all Text Entries from a video, arranged chronologically across all detected languages.
- **Flashcard**: A study card generated from a first-occurrence Text Entry in the learning language; contains the extracted text (front), screenshot image (back), language tag, and source timestamp.
- **Flashcard Deck**: The complete set of Flashcards from a single extraction session, exported in Anki-compatible format with associated media files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can process a 30-minute gameplay video and receive a complete set of flashcards ready for Anki import within a single workflow.
- **SC-002**: At least 85% of clearly legible on-screen text in the user's learning language is successfully detected and extracted.
- **SC-003**: Generated flashcard files import into Anki without errors, with all cards displaying correctly including text and screenshot images.
- **SC-004**: Users report that flashcard screenshots provide sufficient visual context to recall where and when the text appeared in the game.
- **SC-005**: Duplicate words are eliminated — each unique word/phrase appears exactly once in the flashcard deck, regardless of how many times it appeared in the video.
- **SC-006**: Users can complete the full workflow (select video, set learning language, run extraction, import to Anki) in under 5 steps.
- **SC-007**: Flashcard decks contain only text in the user's selected learning language — no cards are generated for non-target languages.

## Assumptions

- Users have the screen recorder feature (001-screen-recorder) available to produce video files, or can provide pre-recorded video files.
- Target videos are primarily from video games (RPGs, visual novels, etc.) where text is rendered clearly on screen rather than embedded in complex animations.
- Anki is already installed on the user's machine and the user is familiar with importing decks/files.
- The initial supported languages are Japanese, Chinese (simplified and traditional), and English; additional languages may be added in the future but are out of scope for this version.
- The system processes videos after recording (not in real-time during gameplay).
- Video files are in common formats compatible with the existing screen recorder output.
- "First occurrence" deduplication is based on exact text match — minor variations (e.g., different conjugations of the same verb) are treated as separate entries.
- The user must select a learning language before extraction; there is no default learning language.
