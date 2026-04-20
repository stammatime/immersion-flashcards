# Tasks: Video Text Extraction for Anki Flashcards

**Input**: Design documents from `/specs/002-video-text-extraction/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests follow the project's Test-First (Constitution Principle III) approach. Tests are written first and confirmed to fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and create module structure for extractor and anki packages

- [ ] T001 Add new dependencies (manga-ocr, paddleocr, paddlepaddle, genanki, imagehash, Pillow) to requirements.txt
- [ ] T002 Create extractor module structure: src/extractor/__init__.py, src/extractor/models.py, src/extractor/exceptions.py, src/extractor/frame_sampler.py, src/extractor/ocr_engine.py, src/extractor/language_detector.py, src/extractor/text_deduplicator.py, src/extractor/transcript_writer.py
- [ ] T003 [P] Create anki module structure: src/anki/__init__.py, src/anki/models.py, src/anki/deck_builder.py, src/anki/exporter.py
- [ ] T004 [P] Create test directory structure: tests/unit/extractor/, tests/unit/anki/, tests/fixtures/sample_frames/, tests/fixtures/expected_outputs/
- [ ] T005 [P] Add sample test fixture images to tests/fixtures/sample_frames/ (japanese_dialogue.png, chinese_menu.png, english_ui.png, mixed_language.png, no_text.png)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and enums shared across all user stories

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Write failing tests for LearningLanguage enum and ExtractionConfig dataclass in tests/unit/extractor/test_models.py
- [ ] T007 Implement LearningLanguage enum and ExtractionConfig dataclass in src/extractor/models.py
- [ ] T008 [P] Write failing tests for TextEntry dataclass validation in tests/unit/extractor/test_models.py
- [ ] T009 [P] Implement TextEntry dataclass in src/extractor/models.py
- [ ] T010 Write failing tests for ExtractionStatus enum and ExtractionSession dataclass in tests/unit/extractor/test_models.py
- [ ] T011 Implement ExtractionStatus enum and ExtractionSession dataclass in src/extractor/models.py
- [ ] T012 [P] Write failing tests for FlashcardEntry and DeckMetadata dataclasses in tests/unit/anki/test_models.py
- [ ] T013 [P] Implement FlashcardEntry and DeckMetadata dataclasses in src/anki/models.py
- [ ] T014 Implement exception classes (OCREngineError, NoTextDetectedError, ExtractionError) in src/extractor/exceptions.py

**Checkpoint**: Foundation ready - all data models and enums in place. User story implementation can now begin.

---

## Phase 3: User Story 1 - Extract Text from Video Game Footage (Priority: P1) MVP

**Goal**: Process a recorded video, extract text via OCR, deduplicate, and export an Anki-importable .apkg deck with screenshots.

**Independent Test**: Provide a short video with visible Japanese text. Verify text is extracted, transcript is produced, .apkg imports into Anki with one card per unique word, and screenshots are attached.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Write failing tests for FrameSampler.sample_frames() and FrameSampler.is_duplicate_frame() in tests/unit/extractor/test_frame_sampler.py
- [ ] T016 [P] [US1] Write failing tests for OCREngine.__init__() and OCREngine.extract_text() with mocked backends in tests/unit/extractor/test_ocr_engine.py
- [ ] T017 [P] [US1] Write failing tests for TextDeduplicator.process() and TextDeduplicator.reset() in tests/unit/extractor/test_text_deduplicator.py
- [ ] T018 [P] [US1] Write failing tests for TranscriptWriter.write() in tests/unit/extractor/test_transcript_writer.py
- [ ] T019 [P] [US1] Write failing tests for DeckBuilder.add_card() and DeckBuilder.get_metadata() in tests/unit/anki/test_deck_builder.py
- [ ] T020 [P] [US1] Write failing tests for AnkiExporter.export() in tests/unit/anki/test_exporter.py

### Implementation for User Story 1

- [ ] T021 [US1] Implement FrameSampler.sample_frames() using FFmpeg scene-change detection in src/extractor/frame_sampler.py
- [ ] T022 [US1] Implement FrameSampler.is_duplicate_frame() using perceptual hashing in src/extractor/frame_sampler.py
- [ ] T023 [US1] Implement OCREngine wrapping manga-ocr (Japanese) and PaddleOCR (Chinese/English) in src/extractor/ocr_engine.py
- [ ] T024 [US1] Implement TextDeduplicator with exact-match deduplication in src/extractor/text_deduplicator.py
- [ ] T025 [US1] Implement TranscriptWriter producing chronological [HH:MM:SS] [LANG] format in src/extractor/transcript_writer.py
- [ ] T026 [US1] Implement DeckBuilder with genanki note model (Front, Back, Language, Timestamp fields) in src/anki/deck_builder.py
- [ ] T027 [US1] Implement AnkiExporter.export() producing .apkg with embedded screenshot media in src/anki/exporter.py
- [ ] T028 [US1] Write failing integration test for end-to-end extraction flow (sample frames -> OCR -> dedup -> transcript + .apkg) in tests/integration/test_extraction_flow.py
- [ ] T029 [US1] Implement extraction pipeline orchestrator that chains FrameSampler -> OCREngine -> TextDeduplicator -> TranscriptWriter -> DeckBuilder -> AnkiExporter in src/extractor/__init__.py or a new src/extractor/pipeline.py

**Checkpoint**: At this point, the core extraction pipeline works end-to-end. A video can be processed and an Anki deck generated via code (no UI yet for extraction, but the pipeline is callable).

---

## Phase 4: User Story 2 - Specify Target Learning Language (Priority: P1)

**Goal**: Allow the user to select their target learning language before extraction. Flashcards are generated only for text in the learning language. Additional languages may be enabled for transcript-only capture.

**Independent Test**: Run extraction on a video with multiple languages. Verify flashcards contain only the selected learning language, while the transcript captures all enabled languages.

### Tests for User Story 2

- [ ] T030 [P] [US2] Write failing tests for language-filtered extraction: OCREngine initialized per learning language, flashcards generated only for learning language entries in tests/unit/extractor/test_ocr_engine.py
- [ ] T031 [P] [US2] Write failing tests for multi-language transcript: transcript includes all enabled languages even when flashcards are filtered in tests/unit/extractor/test_transcript_writer.py

### Implementation for User Story 2

- [ ] T032 [US2] Implement language-based OCR engine selection in extraction pipeline (manga-ocr for JA, PaddleOCR for ZH/EN) in src/extractor/ocr_engine.py
- [ ] T033 [US2] Implement learning language filtering in pipeline: only first-occurrence entries in the learning language become flashcards in src/extractor/pipeline.py
- [ ] T034 [US2] Implement additional_languages support in pipeline: run secondary OCR engines for transcript capture without generating flashcards in src/extractor/pipeline.py
- [ ] T035 [US2] Add learning_language validation to ExtractionConfig (must be set, no default) in src/extractor/models.py

**Checkpoint**: Extraction pipeline respects language selection. Flashcards are learning-language-only, transcript captures all enabled languages.

---

## Phase 5: User Story 3 - Full Transcript Review (Priority: P2)

**Goal**: Produce a complete chronological transcript of all detected text with timestamps and language tags, viewable as a standalone file.

**Independent Test**: Run extraction on a video and verify the transcript file contains all detected text in chronological order with timestamps and language labels.

### Tests for User Story 3

- [ ] T036 [P] [US3] Write failing tests for transcript formatting: verify [HH:MM:SS] [LANG] format, chronological ordering, all entries included in tests/unit/extractor/test_transcript_writer.py

### Implementation for User Story 3

- [ ] T037 [US3] Enhance TranscriptWriter to format timestamps as HH:MM:SS, include language tag per entry, and sort by timestamp in src/extractor/transcript_writer.py
- [ ] T038 [US3] Ensure pipeline writes transcript to output_directory with descriptive filename (e.g., video_name_transcript.txt) in src/extractor/pipeline.py

**Checkpoint**: Transcript file is produced alongside the .apkg and contains a complete chronological record of all detected text.

---

## Phase 6: User Story 4 - Screenshot Context for Flashcards (Priority: P3)

**Goal**: Each flashcard in Anki includes a screenshot of the video frame where the text was first detected, providing visual context for recall.

**Independent Test**: Import generated .apkg into Anki. Verify each card shows the extracted text on the front and a legible screenshot on the back.

### Tests for User Story 4

- [ ] T039 [P] [US4] Write failing tests for screenshot capture: verify screenshot is saved for each first-occurrence entry, path is associated with FlashcardEntry in tests/unit/extractor/test_frame_sampler.py
- [ ] T040 [P] [US4] Write failing tests for screenshot embedding in .apkg: verify media files are included and card back HTML references correct image filename in tests/unit/anki/test_exporter.py

### Implementation for User Story 4

- [ ] T041 [US4] Implement screenshot saving in pipeline: copy the source frame image for each first-occurrence entry to output_directory/media/ with unique filename in src/extractor/pipeline.py
- [ ] T042 [US4] Wire screenshot_path into FlashcardEntry and generate back_html with `<img src="filename.png">` tag in src/anki/deck_builder.py
- [ ] T043 [US4] Update AnkiExporter to include all screenshot media files in the .apkg package via genanki.Package(media_files=[...]) in src/anki/exporter.py

**Checkpoint**: Flashcards in Anki display screenshots. The full extraction-to-Anki pipeline is complete.

---

## Phase 7: UI Integration (Priority: P2)

**Goal**: Add an extraction panel to the existing PyQt6 application so users can select a video, choose their learning language, run extraction, and access results — all from the GUI.

**Independent Test**: Launch the app, navigate to the extraction panel, select a video and language, click Extract, verify progress updates and results are displayed.

### Tests for User Story UI

- [ ] T044 [P] [US-UI] Write failing tests for ExtractionPanel state machine (IDLE -> CONFIGURED -> PROCESSING -> COMPLETE/ERROR) in tests/unit/ui/test_extraction_panel.py
- [ ] T045 [P] [US-UI] Write failing tests for ExtractionPanel accessibility: labels, keyboard navigation, screen reader support in tests/unit/ui/test_extraction_panel.py

### Implementation for UI

- [ ] T046 [US-UI] Create ExtractionPanel widget with video file picker, learning language dropdown, additional language checkboxes, and Extract button in src/ui/extraction_panel.py
- [ ] T047 [US-UI] Implement progress panel in ExtractionPanel: progress bar, status label, cancel button; update during PROCESSING state in src/ui/extraction_panel.py
- [ ] T048 [US-UI] Implement results panel in ExtractionPanel: card count, transcript path link, .apkg path link, low-confidence count, Open in Anki button in src/ui/extraction_panel.py
- [ ] T049 [US-UI] Implement state machine transitions (IDLE/CONFIGURED/PROCESSING/COMPLETE/ERROR) per contracts/ui-extraction.md in src/ui/extraction_panel.py
- [ ] T050 [US-UI] Integrate ExtractionPanel into existing MainWindow (add as tab or panel) in src/ui/main_window.py
- [ ] T051 [US-UI] Wire ExtractionPanel to extraction pipeline: run pipeline in background thread (QThread), emit progress signals, handle completion/error in src/ui/extraction_panel.py
- [ ] T052 [US-UI] Implement accessibility requirements: visible labels, keyboard tab order, status announcements per WCAG 2.1 AA in src/ui/extraction_panel.py

**Checkpoint**: Users can run the full extraction workflow from the GUI.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, logging, edge cases, and validation across all stories

- [ ] T053 [P] Add structured logging throughout extraction pipeline (progress, OCR confidence, errors) in src/extractor/pipeline.py
- [ ] T054 [P] Implement low-confidence flagging: mark entries below confidence_threshold with is_low_confidence=True, add "low-confidence" Anki tag in src/extractor/pipeline.py and src/anki/deck_builder.py
- [ ] T055 Handle edge case: no text detected in video — produce empty result set with informative message in src/extractor/pipeline.py
- [ ] T056 Handle edge case: video file not found or unreadable — raise clear error before processing begins in src/extractor/pipeline.py
- [ ] T057 [P] Add extraction progress reporting: emit frame count, percentage, current phase to UI or console in src/extractor/pipeline.py
- [ ] T058 Extend Settings dataclass with extraction defaults (default learning language, output directory) in src/settings/models.py
- [ ] T059 Run quickstart.md golden path validation end-to-end
- [ ] T060 Run linting (ruff check .) and fix any issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 - Extract Text (Phase 3)**: Depends on Foundational — core pipeline
- **US2 - Learning Language (Phase 4)**: Depends on US1 (extends the pipeline with language filtering)
- **US3 - Transcript (Phase 5)**: Depends on US1 (enhances transcript output)
- **US4 - Screenshots (Phase 6)**: Depends on US1 (adds media to flashcards)
- **UI Integration (Phase 7)**: Depends on US1, US2 (wires pipeline to GUI)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Depends on US1 pipeline existing — extends it with language filtering
- **US3 (P2)**: Can start after US1 — enhances transcript format (light dependency)
- **US4 (P3)**: Can start after US1 — adds screenshot media to cards (light dependency)
- **UI**: Can start after US1+US2 — needs pipeline and language selection working

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution Principle III)
- Models before services
- Services before pipeline integration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004, T005 can run in parallel (Setup phase)
- T008/T009 and T010/T011 and T012/T013 can run in parallel (Foundational)
- T015-T020 (all US1 tests) can run in parallel
- T030, T031 (US2 tests) can run in parallel
- T039, T040 (US4 tests) can run in parallel
- T044, T045 (UI tests) can run in parallel
- T053, T054, T057 (Polish) can run in parallel
- US3 and US4 can be worked on in parallel once US1 is complete

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (write failing tests first):
Task: "T015 - FrameSampler tests in tests/unit/extractor/test_frame_sampler.py"
Task: "T016 - OCREngine tests in tests/unit/extractor/test_ocr_engine.py"
Task: "T017 - TextDeduplicator tests in tests/unit/extractor/test_text_deduplicator.py"
Task: "T018 - TranscriptWriter tests in tests/unit/extractor/test_transcript_writer.py"
Task: "T019 - DeckBuilder tests in tests/unit/anki/test_deck_builder.py"
Task: "T020 - AnkiExporter tests in tests/unit/anki/test_exporter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (core extraction pipeline)
4. **STOP and VALIDATE**: Test pipeline end-to-end with a sample video
5. The system can process videos and produce .apkg files at this point

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. US1 (Extract Text) -> Core pipeline works -> MVP!
3. US2 (Learning Language) -> Language filtering works
4. US3 (Transcript) -> Full transcript output
5. US4 (Screenshots) -> Visual context in cards
6. UI Integration -> GUI workflow complete
7. Polish -> Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Constitution Principle III)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- manga-ocr is used for Japanese; PaddleOCR for Chinese/English (per research.md)
- genanki is used for .apkg generation (per research.md)
- FFmpeg scene-change detection + perceptual hashing for frame sampling (per research.md)
