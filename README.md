# Face-recognition dummy

A small Python component for another application to call. It compares one reference face with one current face and returns a simple match/no-match result plus a **dummy** payment-eligibility flag.

It does **not** call Fiuu, submit a payment, store images, run a web server, or require Strands, Bedrock, AWS, FastAPI, or Swagger.

## Files to hand to the app team

- `face_id.py` — importable face-matching function.
- `demo.py` — optional terminal demonstration.
- `requirements.txt` — only the three packages needed by this component.
- `.env.example` — optional local model configuration template.

The `models/` directory is intentionally ignored by Git. Your teammate must download or receive the two ONNX model files separately.

## Setup

```zsh
cd SimeDarbyHackathon
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Place these local OpenCV model files in `SimeDarbyHackathon/models/`:

- `face_detection_yunet_2023mar.onnx`
- `face_recognition_sface_2021dec.onnx`

If they are in another location, copy `.env.example` to `.env` and set their absolute paths. The module loads only this folder's `.env`, never the repository-root `.env`.

## Quick terminal demo

Use two images containing exactly one consenting face each:

```zsh
python3 demo.py reference.jpg probe.jpg
```

Example output:

```json
{
  "matched": true,
  "similarity_score": 0.82,
  "threshold": 0.363,
  "payment_eligible": true,
  "payment_status": "approved_for_demo",
  "mode": "dummy"
}
```

`payment_eligible` and `payment_status` are dummy fields for the app team to consume. They are not a payment authorization and do not contact Fiuu.

## App integration

```python
from face_id import FaceVerificationError, verify_face

try:
    result = verify_face(reference_image_bytes, probe_image_bytes)
except FaceVerificationError as error:
    # Ask the user for a clearer image with one face.
    print(error)
else:
    if result["matched"]:
        # The app team's own payment workflow begins here.
        print("Face match")
    else:
        print("Face does not match")
```

`reference_image_bytes` and `probe_image_bytes` may also be file paths. The module processes images in memory and does not write captures or embeddings to disk.

## Demo limitations

Use only consented images. This is a one-to-one demo matcher, not a one-to-many identification system. It has no real liveness detection, authentication, encrypted persistence, anti-spoofing, or production-payment authorization.
