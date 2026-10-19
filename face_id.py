"""Small, importable face-recognition dummy for app integration.

This module compares one enrolled/reference face to one current/probe face and
returns a JSON-friendly demo result. It does not call Fiuu or authorize payments.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypeAlias

import cv2
import numpy as np
from dotenv import load_dotenv

# Load only this demo's local configuration; never use the repository-root .env.
_PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(_PROJECT_DIR / ".env", override=False)

ImageInput: TypeAlias = str | Path | bytes | bytearray
DEFAULT_THRESHOLD = 0.363


class FaceVerificationError(ValueError):
    """Raised when an image cannot be used for one-to-one face verification."""


@dataclass(frozen=True)
class FaceVerificationResult:
    """Simple result returned to the application that embeds this demo."""

    matched: bool
    similarity_score: float
    threshold: float
    payment_eligible: bool
    payment_status: str
    mode: str = "dummy"

    def to_dict(self) -> dict[str, bool | float | str]:
        """Return a JSON-friendly handoff payload."""
        return asdict(self)


class FaceVerifier:
    """OpenCV YuNet + SFace verifier for one reference face and one probe face."""

    def __init__(
        self,
        detector_model_path: str | Path | None = None,
        recognizer_model_path: str | Path | None = None,
        threshold: float | None = None,
    ) -> None:
        self._threshold = _resolve_threshold(threshold)
        detector_path = _resolve_model_path(
            detector_model_path,
            "FACE_DETECTOR_MODEL",
            "face_detection_yunet_2023mar.onnx",
        )
        recognizer_path = _resolve_model_path(
            recognizer_model_path,
            "FACE_RECOGNIZER_MODEL",
            "face_recognition_sface_2021dec.onnx",
        )
        self._detector = cv2.FaceDetectorYN.create(
            str(detector_path),
            "",
            (320, 320),
            score_threshold=0.9,
            nms_threshold=0.3,
            top_k=5000,
        )
        self._recognizer = cv2.FaceRecognizerSF.create(str(recognizer_path), "")

    def verify(
        self,
        reference_image: ImageInput,
        probe_image: ImageInput,
    ) -> FaceVerificationResult:
        """Compare exactly one face in each image and return a dummy eligibility result."""
        reference_embedding = self._embedding(reference_image)
        probe_embedding = self._embedding(probe_image)
        score = float(
            self._recognizer.match(
                reference_embedding,
                probe_embedding,
                cv2.FaceRecognizerSF_FR_COSINE,
            )
        )
        matched = score >= self._threshold
        return FaceVerificationResult(
            matched=matched,
            similarity_score=round(score, 4),
            threshold=self._threshold,
            payment_eligible=matched,
            payment_status="approved_for_demo" if matched else "declined_for_demo",
        )

    def _embedding(self, image_input: ImageInput) -> np.ndarray:
        image = _decode_image(image_input)
        height, width = image.shape[:2]
        self._detector.setInputSize((width, height))
        _, faces = self._detector.detect(image)
        if faces is None or len(faces) != 1:
            raise FaceVerificationError(
                "Each image must contain exactly one detectable face."
            )

        aligned_face = self._recognizer.alignCrop(image, faces[0])
        return self._recognizer.feature(aligned_face)


def verify_face(
    reference_image: ImageInput,
    probe_image: ImageInput,
    *,
    detector_model_path: str | Path | None = None,
    recognizer_model_path: str | Path | None = None,
    threshold: float | None = None,
) -> dict[str, bool | float | str]:
    """Return a simple dummy face-match result for another application's use.

    Arguments may be local image paths or image bytes received from an app upload.
    A successful match only returns a demo eligibility flag; it is not a payment
    authorization and it does not contact Fiuu.
    """
    verifier = FaceVerifier(
        detector_model_path=detector_model_path,
        recognizer_model_path=recognizer_model_path,
        threshold=threshold,
    )
    return verifier.verify(reference_image, probe_image).to_dict()


def _decode_image(image_input: ImageInput) -> np.ndarray:
    if isinstance(image_input, (str, Path)):
        image = cv2.imread(str(image_input), cv2.IMREAD_COLOR)
    elif isinstance(image_input, (bytes, bytearray)):
        encoded = np.frombuffer(image_input, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    else:
        raise FaceVerificationError("Image input must be a path or image bytes.")

    if image is None:
        raise FaceVerificationError("Image could not be decoded.")
    return image


def _resolve_model_path(
    supplied_path: str | Path | None,
    environment_name: str,
    default_filename: str,
) -> Path:
    candidate = supplied_path or os.getenv(environment_name)
    path = Path(candidate).expanduser() if candidate else _PROJECT_DIR / "models" / default_filename
    if not path.is_file():
        raise FaceVerificationError(
            f"{environment_name} does not point to a model file. Expected {path}."
        )
    return path


def _resolve_threshold(threshold: float | None) -> float:
    value = threshold if threshold is not None else float(
        os.getenv("FACE_MATCH_THRESHOLD", str(DEFAULT_THRESHOLD))
    )
    if not 0 < value <= 1:
        raise FaceVerificationError("Face-match threshold must be greater than 0 and at most 1.")
    return value
