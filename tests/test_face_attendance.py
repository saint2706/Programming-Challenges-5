from __future__ import annotations

from pathlib import Path

import numpy as np

from ArtificialIntelligence.face_attendance import FaceAttendanceSystem


def test_match_and_log(tmp_path: Path) -> None:
    known_path = tmp_path / "encodings.json"
    log_path = tmp_path / "attendance.csv"
    embeddings = {"Alice": np.array([0.1, 0.2, 0.3], dtype=np.float32)}
    known_path.write_text('{"Alice": [0.1, 0.2, 0.3]}')

    def detector(_frame):
        return [(0, 0, 2, 2)]

    def embedder(_face):
        return embeddings["Alice"]

    system = FaceAttendanceSystem(
        embedding_model=embedder,
        detector=detector,
        known_encodings_path=known_path,
        attendance_log_path=log_path,
        match_threshold=0.5,
    )

    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    system.process_frame(frame)

    log_content = log_path.read_text().splitlines()
    assert log_content[0] == "name,timestamp"
    assert log_content[1].startswith("Alice,")


def test_unknown_not_logged(tmp_path: Path) -> None:
    known_path = tmp_path / "encodings.json"
    log_path = tmp_path / "attendance.csv"

    def detector(_frame):
        return [(1, 1, 2, 2)]

    def embedder(_face):
        return np.array([5.0, 5.0, 5.0], dtype=np.float32)

    system = FaceAttendanceSystem(
        embedding_model=embedder,
        detector=detector,
        known_encodings_path=known_path,
        attendance_log_path=log_path,
        match_threshold=0.4,
    )

    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    system.process_frame(frame)

    assert not log_path.exists()


def test_enrollment_saves_encoding(tmp_path: Path) -> None:
    known_path = tmp_path / "encodings.json"
    log_path = tmp_path / "attendance.csv"
    expected_embedding = np.array([0.5, 0.5, 0.5], dtype=np.float32)

    def detector(_frame):
        return [(0, 0, 2, 2)]

    def embedder(_face):
        return expected_embedding

    system = FaceAttendanceSystem(
        embedding_model=embedder,
        detector=detector,
        known_encodings_path=known_path,
        attendance_log_path=log_path,
    )

    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    enrolled = system.enroll("Bob", frame)

    assert enrolled is True
    saved = FaceAttendanceSystem(
        embedding_model=embedder,
        detector=detector,
        known_encodings_path=known_path,
        attendance_log_path=log_path,
    )
    np.testing.assert_allclose(saved.known_encodings["Bob"], expected_embedding)
