"""Face recognition attendance system using OpenCV and embeddings.

This module offers a small reference implementation of an attendance system
that relies on a face detector (OpenCV Haar cascades by default) and a
pre-trained embedding model such as FaceNet. It supports live webcam
processing, enrollment of new identities, labeling of detected faces, and
attendance logging to a CSV file.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence, Tuple

import cv2
import numpy as np


EmbeddingModel = Callable[[np.ndarray], np.ndarray]
Detection = Tuple[int, int, int, int]


@dataclass
class AttendanceLogger:
    """CSV-backed attendance logger that avoids duplicate session entries."""

    log_path: Path
    recorded_names: set[str] = field(default_factory=set)

    def log(self, name: str) -> None:
        """Append a timestamped entry for ``name`` to the CSV log.

        Args:
            name: Identity to log. ``"Unknown"`` entries are ignored.
        """

        if name == "Unknown" or name in self.recorded_names:
            return

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not self.log_path.exists()
        with self.log_path.open("a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if new_file:
                writer.writerow(["name", "timestamp"])
            writer.writerow([name, datetime.now(UTC).isoformat()])
        self.recorded_names.add(name)


class FaceAttendanceSystem:
    """Recognize faces from a webcam stream and log attendance.

    The system relies on a detector to produce face bounding boxes and an
    embedding model (e.g., FaceNet) to generate face embeddings. It compares
    embeddings against stored encodings and logs matches to a CSV file.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        detector: Optional[Callable[[np.ndarray], Sequence[Detection]]] = None,
        known_encodings_path: Path | str = Path("face_encodings.json"),
        attendance_log_path: Path | str = Path("attendance_log.csv"),
        match_threshold: float = 0.6,
    ) -> None:
        """Create a new attendance system instance.

        Args:
            embedding_model: Callable that returns an embedding vector for a
                face image (RGB ``np.ndarray``).
            detector: Optional callable returning face detections. When absent,
                OpenCV's Haar cascade frontal face detector is used.
            known_encodings_path: File storing known embeddings as JSON.
            attendance_log_path: CSV file to write attendance events to.
            match_threshold: Euclidean distance threshold for a match.
        """

        self.embedding_model = embedding_model
        self.detector = detector
        self.match_threshold = match_threshold
        self.known_encodings_path = Path(known_encodings_path)
        self.attendance_logger = AttendanceLogger(Path(attendance_log_path))
        self.known_encodings: Dict[str, np.ndarray] = {}
        self._cascade: Optional[cv2.CascadeClassifier] = None
        self._load_known_encodings()

    def _get_cascade(self) -> cv2.CascadeClassifier:
        if self._cascade is None:
            cascade_path = str(
                Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            )
            self._cascade = cv2.CascadeClassifier(cascade_path)
        return self._cascade

    def _load_known_encodings(self) -> None:
        if not self.known_encodings_path.exists():
            return
        with self.known_encodings_path.open("r") as handle:
            raw_data = json.load(handle)
        for name, encoding in raw_data.items():
            self.known_encodings[name] = np.asarray(encoding, dtype=np.float32)

    def _save_known_encodings(self) -> None:
        serializable = {k: v.tolist() for k, v in self.known_encodings.items()}
        self.known_encodings_path.parent.mkdir(parents=True, exist_ok=True)
        with self.known_encodings_path.open("w") as handle:
            json.dump(serializable, handle, indent=2)

    def detect_faces(self, frame: np.ndarray) -> Sequence[Detection]:
        """Detect faces in a frame.

        Args:
            frame: BGR image from OpenCV.

        Returns:
            A sequence of bounding boxes ``(x, y, w, h)``.
        """

        if self.detector is not None:
            return self.detector(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade = self._get_cascade()
        detections = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return detections

    def _extract_face_roi(self, frame: np.ndarray, box: Detection) -> np.ndarray:
        x, y, w, h = box
        face = frame[y : y + h, x : x + w]
        return cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

    def get_embedding(self, frame: np.ndarray, box: Detection) -> np.ndarray:
        """Compute an embedding for the region defined by ``box``."""

        rgb_face = self._extract_face_roi(frame, box)
        return self.embedding_model(rgb_face)

    def match_embedding(self, embedding: np.ndarray) -> str:
        """Return the closest known identity for the embedding."""

        best_match = "Unknown"
        best_distance = self.match_threshold
        for name, known_embedding in self.known_encodings.items():
            distance = float(np.linalg.norm(known_embedding - embedding))
            if distance < best_distance:
                best_match = name
                best_distance = distance
        return best_match

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Detect, recognize, annotate, and log attendance for a frame."""

        output = frame.copy()
        detections = self.detect_faces(frame)
        for box in detections:
            embedding = self.get_embedding(frame, box)
            name = self.match_embedding(embedding)
            self._annotate_frame(output, box, name)
            self.attendance_logger.log(name)
        return output

    def _annotate_frame(self, frame: np.ndarray, box: Detection, name: str) -> None:
        x, y, w, h = box
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            frame,
            name,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
            cv2.LINE_AA,
        )

    def enroll(self, name: str, frame: np.ndarray) -> bool:
        """Enroll a new identity from the first detected face in ``frame``.

        Returns ``True`` on success and ``False`` if no face is detected.
        """

        detections = self.detect_faces(frame)
        if not detections:
            return False
        embedding = self.get_embedding(frame, detections[0])
        self.known_encodings[name] = embedding.astype(np.float32)
        self._save_known_encodings()
        return True

    def run(self, camera_index: int = 0) -> None:
        """Start webcam capture until the user presses ``q``.

        Press ``e`` to enroll the current frame under a prompted name.
        """

        cap = cv2.VideoCapture(camera_index)
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                annotated = self.process_frame(frame)
                cv2.imshow("Face Attendance", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("e"):
                    name = input("Enter name to enroll: ")
                    self.enroll(name, frame)
        finally:
            cap.release()
            cv2.destroyAllWindows()
