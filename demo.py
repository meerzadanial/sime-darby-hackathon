"""Run the face-recognition dummy from the terminal with two local images."""

from __future__ import annotations

import argparse
import json
import sys

from face_id import FaceVerificationError, verify_face


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare a reference face to a probe face.")
    parser.add_argument("reference_image", help="Path to the enrolled/reference face image")
    parser.add_argument("probe_image", help="Path to the current/probe face image")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Optional cosine-similarity threshold; default is FACE_MATCH_THRESHOLD or 0.363.",
    )
    args = parser.parse_args()

    try:
        result = verify_face(
            args.reference_image,
            args.probe_image,
            threshold=args.threshold,
        )
    except FaceVerificationError as error:
        print(json.dumps({"error": str(error), "mode": "dummy"}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
