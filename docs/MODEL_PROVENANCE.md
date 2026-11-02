# Neural Model Provenance & Verification

FACECORE AI utilizes two lightweight, high-performance neural network backbones from the official OpenCV Model Zoo under the Apache-2.0 license:

---

## 1. YuNet (Facial Landmark Detector)
- **Model File:** `backend/app/weights/face_detection_yunet_2023mar.onnx`
- **File Size:** 232,589 bytes (~232 KB)
- **Official SHA-256 Digest:** `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`
- **Architecture:** Lightweight depthwise separable convolutional neural network optimized for CPU execution.
- **Inputs:** Dynamic resolution image tensor $(B, 3, H, W)$.
- **Outputs:** Bounding box $[x, y, w, h]$, detection confidence score $[0.0, 1.0]$, and 5 facial landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner).
- **Upstream Source:** [OpenCV Zoo YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
- **License:** Apache-2.0

---

## 2. SFace / SphereFace2 (Hyperspherical Feature Extractor)
- **Model File:** `backend/app/weights/face_recognition_sface_2021dec.onnx`
- **File Size:** 38,696,353 bytes (~38.7 MB)
- **Official SHA-256 Digest:** `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`
- **Architecture:** Deep convolutional neural network trained using hyperspherical margin loss (SphereFace2) for robust identity discrimination.
- **Inputs:** Normalized $112 \times 112$ 5-point affine-aligned facial crop.
- **Outputs:** 128-dimensional unit normalized feature embedding on a hypersphere ($\|u\|_2 = 1.0$).
- **Comparison Metric:** Exact inner dot-product cosine similarity $\cos(\theta) = u \cdot v \in [-1.0, 1.0]$.
- **Upstream Source:** [OpenCV Zoo SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)
- **License:** Apache-2.0

---

## 3. Cryptographic Verification Command

To verify that the local ONNX weights match the official OpenCV Zoo checksums bit-for-bit:
```bash
python backend/scripts/verify_weights.py
```
If weights are corrupted or missing, the verification script exits with code `1` and prints direct download links.

