# FACECORE AI &mdash; STEP 05: DATASET RESEARCH & EVALUATION PROTOCOLS

**Document:** Facial Verification Dataset Research & Feasibility Evaluation  
**Author:** Senior Machine-Learning Evaluation Engineer & Computer-Vision Researcher  
**Status:** Approved & Formally Documented  
**Phase:** STEP 05 &mdash; Dataset Discovery and Facial Model Benchmarking Framework  

---

## 1. Executive Summary & Legal Framework

Evaluating facial recognition and similarity systems requires strict adherence to scientific reproducibility, statistical validity, legal licensing, and data privacy governance. 

Public accessibility on the internet does **not** imply that a dataset is legally unrestricted, ethically consented to, or suitable for model deployment. Many early computer vision datasets were assembled via web-scraping search engines without explicit individual consent. Recent European regulations (GDPR, EU AI Act), US state biometric privacy statutes (e.g., Illinois BIPA), and ethical research consensus mandate that evaluation datasets must be audited for:
1. **Express Licensing Terms:** Permissible scope (academic research vs. commercial evaluation).
2. **Subject Consent & Privacy:** Whether biometric subjects provided informed consent.
3. **Data Protection & Storage:** Strict ephemeral local storage with zero cloud redistribution.
4. **Task Suitability:** Ensuring the benchmark matches 1:1 facial verification ($\text{genuine vs. impostor}$) rather than open-universe identification or mass surveillance.

This document reviews five key academic and industry benchmark datasets (LFW, CFP-FP, AgeDB, FHIBE, and DFW), plus derivative standards (CALFW, CPLFW), and provides a formal recommendation for FACECORE AI's initial benchmarking framework.

---

## 2. In-Depth Dataset Analysis

### 2.1. Labeled Faces in the Wild (LFW)

- **Official Source & Download Location:**
  - University of Massachusetts Amherst, Computer Vision Laboratory (Erik Learned-Miller et al.).
  - Official Repository: [http://vis-www.cs.umass.edu/lfw/](http://vis-www.cs.umass.edu/lfw/)
- **Dataset Size & Identity Count:**
  - Total Images: 13,233 images.
  - Total Identities: 5,749 unique individuals.
  - Distribution: 1,680 people have two or more distinct photos; 4,069 people have only one image.
- **Image Formats & Annotations:**
  - Format: Standard 24-bit RGB JPEG, resolution $250 \times 250$ pixels.
  - Annotations: Subject names as directory identifiers, official `pairs.txt` defining 10 disjoint evaluation folds. Aligned subsets (`lfw-funneled`, `lfw-deepfunneled`, and MTCNN-aligned) provide facial landmark anchors.
- **Genuine & Impostor Pair Availability:**
  - Standard Verification Protocol: Exactly 10 folds, each containing 300 genuine (same-person) pairs and 300 impostor (different-person) pairs.
  - Total Standard Benchmark Pairs: **6,000 pairs** (3,000 genuine, 3,000 impostor).
- **Variation Coverage:**
  - Lighting: Natural unconstrained variations (indoor, outdoor, flash, shadow).
  - Pose: Primarily near-frontal ($\pm 30^\circ$ yaw/pitch), with limited extreme profile shots.
  - Age: Natural adult age distribution (celebrities, politicians, athletes in news media).
  - Occlusion: Common accessories (eyeglasses, sunglasses, microphones, hats).
  - Disguise: Minimal; no intentional biometric obfuscation or adversarial makeup.
- **License & Usage Restrictions:**
  - Non-commercial academic research use only. Images were originally gathered from Yahoo News during 2002–2003 under fair-use provisions for scientific research.
- **Consent, Privacy & Redistribution:**
  - **No explicit subject consent** was obtained prior to collection; subjects were public figures in international news media.
  - Commercial redistribution is prohibited. Redistribution of raw images must respect original copyright holders. Local research evaluation is legally accepted under fair-use doctrines in major academic jurisdictions.
- **Download Size & Access Requirements:**
  - Archive Size: ~173 MB (original), ~200 MB (aligned).
  - Access: Direct public HTTP/FTP download from UMass servers without paywall or mandatory credentialing.
- **Suitability & Assessment:**
  - Suitable for: **1:1 Face Verification Model Evaluation only.**
  - Not suitable for: General model training (modern deep backbones easily achieve $>99.5\%$ on LFW, leading to saturation; LFW is a test set, not a training corpus).
  - Local Research Use: **Permitted**.

---

### 2.2. Celebrities in Frontal-Profile in the Wild (CFP-FP)

- **Official Source & Download Location:**
  - University of Maryland (Soumyadip Sengupta, Jun-Cheng Chen, Carlos D. Castillo, Vishal M. Patel, Rama Chellappa et al., 2016).
  - Official Repository: [http://www.cfpdb.org/](http://www.cfpdb.org/)
- **Dataset Size & Identity Count:**
  - Total Images: 7,000 images.
  - Total Identities: 500 distinct celebrities.
  - Distribution: Exactly 10 frontal images and 4 profile images per identity.
- **Image Formats & Annotations:**
  - Format: Standard JPEG, varying native resolutions cropped to facial bounding boxes.
  - Annotations: Subject identities, frontal vs. profile labels, 4 landmark points, and official 10-fold split definitions.
- **Genuine & Impostor Pair Availability:**
  - Two Evaluation Protocols:
    1. **Frontal-to-Frontal (FF):** 10 folds $\times$ (350 genuine + 350 impostor) = 7,000 pairs.
    2. **Frontal-to-Profile (FP):** 10 folds $\times$ (350 genuine + 350 impostor) = 7,000 pairs.
  - Frontal-to-Profile is the standard benchmark for testing extreme yaw degradation ($\sim 90^\circ$).
- **Variation Coverage:**
  - Lighting: Unconstrained real-world illumination.
  - Pose: **Extreme cross-pose coverage** ($0^\circ$ frontal vs. $90^\circ$ profile).
  - Age & Expression: Natural variation across web images.
  - Occlusion & Disguise: Casual occlusions (hair covering ears/cheeks, sunglasses).
- **License & Usage Restrictions:**
  - Restricted strictly to academic, non-commercial research purposes.
- **Consent, Privacy & Redistribution:**
  - Web-scraped celebrity imagery without prior biometric release agreements. Commercial use and secondary redistribution are prohibited.
- **Download Size & Access Requirements:**
  - Archive Size: ~120 MB.
  - Access: Freely accessible via university research portals.
- **Suitability & Assessment:**
  - Suitable for: **Controlled Cross-Pose Robustness Benchmarking.**
  - Local Research Use: **Permitted**.

---

### 2.3. AgeDB (AgeDB-30)

- **Official Source & Download Location:**
  - Imperial College London (Stylianos Moschoglou, Athanasios Papaioannou, Christos Sagonas, Jiankang Deng, Stefanos Zafeiriou, 2017).
  - Official Repository: [https://ibug.doc.ic.ac.uk/resources/agedb/](https://ibug.doc.ic.ac.uk/resources/agedb/)
- **Dataset Size & Identity Count:**
  - Total Images: 16,488 images.
  - Total Identities: 568 distinct subjects (actors, authors, scientists, politicians).
  - Age Range: 1 to 101 years old (average age 50.3 years).
- **Image Formats & Annotations:**
  - Format: High-quality JPEG.
  - Annotations: Subject name, biological gender, year of birth, and exact chronological age at the time the photo was taken (manually verified via public records).
- **Genuine & Impostor Pair Availability:**
  - Four Standard Protocols: AgeDB-5, AgeDB-10, AgeDB-20, and **AgeDB-30**.
  - AgeDB-30 Protocol: 10 folds $\times$ (300 genuine + 300 impostor pairs) = **6,000 pairs** where genuine pairs have an age gap of approximately 30 years.
- **Variation Coverage:**
  - Lighting: Vintage and modern photography across multiple decades (1900s through 2010s).
  - Pose: Mild to moderate pose variations.
  - Age: **Extreme chronological aging gaps** ($>30$ years).
  - Occlusion: Wrinkles, eyeglasses, natural facial hair alterations.
- **License & Usage Restrictions:**
  - Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) or custom iBUG academic research agreement.
- **Consent, Privacy & Redistribution:**
  - Historical and contemporary public figures. Non-commercial scientific study only.
- **Download Size & Access Requirements:**
  - Archive Size: ~500 MB.
  - Access: Available upon submitting an academic research verification form to the iBUG group.
- **Suitability & Assessment:**
  - Suitable for: **Cross-Age Verification & Temporal Invariance Benchmarking.**
  - Local Research Use: **Permitted under academic research terms**.

---

### 2.4. Fair Human-Centric Image Benchmark (FHIBE)

- **Official Source & Download Location:**
  - Sony AI & Mozilla Data Collective (2023–2024).
  - Official Repository: [https://ai.sony/research/FHIBE/](https://ai.sony/research/FHIBE/) and Mozilla Data Collective.
- **Dataset Size & Identity Count:**
  - Total Images: Over 100,000 multi-demographic images globally collected across multiple continents.
  - Subsets include **FHIBE-Face Unaligned** (bounding-box crops with $2\times$ padding) and **FHIBE-Face Aligned**.
- **Image Formats & Annotations:**
  - Format: Uncompressed high-resolution PNG / JPEG.
  - Annotations: Demographic attributes (age group, skin tone on the Monk Skin Tone scale, gender presentation), geographic region, illumination category, camera sensor type, bounding boxes, and landmark keypoints.
- **Genuine & Impostor Pair Availability:**
  - Evaluation splits designed specifically for fairness auditing (comparing verification accuracy, false match rates, and false non-match rates across demographic strata).
- **Variation Coverage:**
  - Lighting: Controlled studio, indoor domestic, and harsh outdoor solar illumination.
  - Pose: Frontal, three-quarters, and casual conversational poses.
  - Skin Tone & Demographics: Explicitly balanced across global skin tone spectra.
- **License & Usage Restrictions:**
  - Distributed under custom Sony AI / Mozilla Data Collective Data License Agreement. Strictly non-commercial evaluation use.
- **Consent, Privacy & Redistribution:**
  - **Highest Ethical Gold Standard:** All participants provided **explicit, compensated, informed consent** for computer vision fairness benchmarking. Biometric data is strictly protected, with identity tokens pseudonymized.
- **Download Size & Access Requirements:**
  - Archive Size: Multi-gigabyte (15 GB to 40 GB depending on resolution tier).
  - Access: Requires signed institutional data agreement with Sony AI / Mozilla Data Collective. Automated downloading without license verification is prohibited.
- **Suitability & Assessment:**
  - Suitable for: **Demographic Fairness, Skin Tone Bias Auditing, and Sensor Invariance.**
  - Local Research Use: **Permitted with signed institutional credentials**.

---

### 2.5. Disguised Faces in the Wild (DFW)

- **Official Source & Download Location:**
  - Image Analysis and Biometrics (IAB) Lab, Indraprastha Institute of Information Technology Delhi (IIIT-Delhi) (Maneet Singh, Shruti Nagpal, Richa Singh, Mayank Vatsa et al., CVPR 2018).
  - Official Repository: [http://iab-rubric.org/resources/dfw.html](http://iab-rubric.org/resources/dfw.html)
- **Dataset Size & Identity Count:**
  - Total Images: 11,157 images.
  - Total Identities: 1,000 distinct subjects.
  - Composition: Neutral/normal images, disguised images (obfuscation), and impersonator images (look-alikes attempting spoofing).
- **Image Formats & Annotations:**
  - Format: JPEG images in wild unconstrained resolutions.
  - Annotations: Subject IDs, image type tags (`neutral`, `disguised`, `impersonator`), difficulty protocol splits (Easy, Medium, Hard).
- **Genuine & Impostor Pair Availability:**
  - Protocols evaluate two challenging biometrics frontiers:
    1. **Disguise Verification:** Matching a disguised face against the subject's neutral enrollment image.
    2. **Impersonator Discrimination:** Distinguishing a true subject from an active look-alike/impersonator.
- **Variation Coverage:**
  - Disguises: Wigs, fake beards, theatrical makeup, hats, veils, facial bandages, plastic surgery look-alikes.
  - Lighting, Pose & Expression: High in-the-wild variance.
- **License & Usage Restrictions:**
  - IIIT-Delhi Academic Research License. Strictly non-commercial research.
- **Consent, Privacy & Redistribution:**
  - Hybrid collection of lab-controlled participant images (with release forms) and publicly available web imagery of celebrities and impersonators.
- **Download Size & Access Requirements:**
  - Archive Size: ~1.8 GB.
  - Access: Academic request form required to receive password-protected archive credentials.
- **Suitability & Assessment:**
  - Suitable for: **Anti-Spoofing, Disguise Invariance, and Adversarial Impersonator Robustness.**
  - Local Research Use: **Permitted under signed academic license**.

---

### 2.6. Additional Noteworthy Benchmarks (CALFW & CPLFW)

| Dataset | Origin & Authors | Size & Protocol | Primary Focus | Licensing & Access |
| :--- | :--- | :--- | :--- | :--- |
| **CALFW** *(Cross-Age LFW)* | Zheng et al., 2017 (Tsinghua University) | 3,000 genuine + 3,000 impostor pairs ($N=6,000$) drawn from LFW identities | Age gap between pairs maximized | Academic non-commercial research; public download (~150 MB). |
| **CPLFW** *(Cross-Pose LFW)* | Zheng et al., 2018 (Tsinghua University) | 3,000 genuine + 3,000 impostor pairs ($N=6,000$) drawn from LFW identities | Pose difference between pairs maximized | Academic non-commercial research; public download (~150 MB). |

---

## 3. Comprehensive Dataset Comparison Matrix

| Evaluation Dimension | LFW (UMass) | CFP-FP (UMD) | AgeDB-30 (Imperial) | FHIBE (Sony AI) | DFW (IIIT-Delhi) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Primary Evaluation Focus** | Unconstrained Baseline | Cross-Pose ($90^\circ$ Yaw) | Cross-Age ($>30$ yrs) | Fairness & Bias | Disguise & Impersonation |
| **Image Count** | 13,233 | 7,000 | 16,488 | $>100,000$ | 11,157 |
| **Subject Count** | 5,749 | 500 | 568 | $>1,000$ | 1,000 |
| **Standard Evaluation Pairs** | 6,000 (10 folds) | 7,000 (10 folds) | 6,000 (10 folds) | Stratified demographic | Multi-tier difficulty |
| **Pairwise Ground Truth** | Yes (`pairs.txt`) | Yes (Protocol lists) | Yes (10-fold pairs) | Custom split manifests | Yes (Match/Impersonator) |
| **Explicit Subject Consent** | No (Web scraped) | No (Web scraped) | No (Public figures) | **Yes (Full Consent)** | Partial (Lab subjects) |
| **License Framework** | Non-Commercial | Academic Non-Comm | CC BY-NC 4.0 | Custom Sony Data Lic | Academic Agreement |
| **Archive Download Size** | ~173 MB | ~120 MB | ~500 MB | $>15\text{ GB}$ | ~1.8 GB |
| **Access Friction** | Zero (Public direct) | Minimal (Public direct)| Form Request | Heavy (Institutional) | Form Request |
| **Suited for Local SFace Benchmark**| **High (Primary Standard)**| **High (Pose Robustness)**| **Moderate (Age Gap)** | **High (Fairness Phase)**| **Moderate (Disguises)** |

---

## 4. Formal Recommendation for FACECORE AI Initial Evaluation

### Recommended Primary Evaluation Dataset: **Labeled Faces in the Wild (LFW)**

#### Scientific & Engineering Justification:
1. **Industry & Academic Gold Standard:** LFW remains the most universally cited baseline in facial verification literature. Publishing SFace (SphereFace2) performance on LFW establishes an unambiguous scientific comparison against published OpenCV Model Zoo baselines ($\sim 99.4\% \text{ reported by OpenCV authors}$).
2. **Canonical 10-Fold Protocol:** The standard `pairs.txt` protocol (10 identity-disjoint folds, each with 300 genuine and 300 impostor pairs) enables clean validation-threshold calibration and unbiased test-fold evaluation without identity leakage.
3. **Reproducibility & Access:** The dataset is publicly downloadable without credentials, allowing automated verification pipelines and benchmark test fixtures to validate manifest parsing, duplicate detection, and metric math instantly.
4. **Lightweight & Ephemeral:** At under 200 MB, LFW can be processed in memory on developer machines without exhausting disk or RAM resources.

### Recommended Secondary & Extension Datasets:
- **Secondary (Step 05 Robustness Extension):** **CFP-FP** (Frontal-to-Profile) to benchmark SFace's known limitation under extreme angular yaw.
- **Future Demographic Audit (Step 06):** **FHIBE-Face** once institutional access agreements are formally executed, providing fully consented, Monk Skin Tone-stratified fairness auditing.

---

## 5. Ethical Compliance, Storage & Data Handling Policy

1. **Ephemeral Local Storage:** Under FACECORE AI's privacy principles, benchmark images must be stored exclusively in a secure, git-ignored local directory (`backend/data/benchmarks/`).
2. **Zero Cloud Sync:** No biometric images or unmasked embeddings may be uploaded to external third-party APIs or cloud endpoints.
3. **No General Identity Database:** Benchmark data is restricted solely to pair-matching evaluation. The system will **never** construct a searchable global identity surveillance index.
4. **Reproducible Test Fixtures:** For continuous integration and automated testing, a lightweight, legally unencumbered synthetic test fixture (`test_lfw_fixture`) containing synthetic genuine/impostor pairs will be bundled to verify all metrics without downloading raw biometric archives during automated CI runs.
