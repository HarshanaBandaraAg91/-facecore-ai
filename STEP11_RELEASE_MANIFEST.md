# FACECORE AI — STEP 11: PRODUCTION RELEASE MANIFEST
**Release Version:** `1.0.0-prod`  
**Release Date:** 2026-11-02  
**Package Root:** `release/facecore-ai/`  
**Total Files Packaged:** 91  
**Total Package Footprint:** 38.32 MB  

---

## 1. Release Specification & Environment

- **Operating Systems:** Windows 10/11 x64 (Native), Linux x86_64, macOS 12+
- **Python Version:** 3.10, 3.11, 3.12, 3.13
- **Node.js Version:** v18.0.0+
- **Neural Execution:** Local CPU via OpenCV DNN (INT8/FP32)
- **Network Dependency:** ZERO (100% Offline Local Operation)
- **Biometric Privacy:** ZERO image persistence, ZERO embedding persistence

## 2. Neural Network Model Weights Provenance

| Model File | Role | Expected SHA-256 | License |
| :--- | :--- | :--- | :---: |
| `face_detection_yunet_2023mar.onnx` | 5-point facial landmark detector | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | Apache-2.0 |
| `face_recognition_sface_2021dec.onnx` | 128-d hyperspherical feature extractor | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | Apache-2.0 |

## 3. Package File Inventory & SHA-256 Checksums

| File Relative Path | Size (Bytes) | SHA-256 Checksum |
| :--- | :---: | :--- |
| `.env.example` | 445 | `f937987c469ce8312874d4b64e7a6206b1ab07cedb0c8a09dcff72b7585b982d` |
| `README.md` | 7,205 | `4be46ace7970b3900ecd11991b8d073897ed3d51e9fcbff025ac534a8bd95538` |
| `backend/.env.example` | 445 | `f937987c469ce8312874d4b64e7a6206b1ab07cedb0c8a09dcff72b7585b982d` |
| `backend/app/__init__.py` | 70 | `57a64baf43695359e64c6676aecd694621c86aa7b5df3a28ad9fc909183cbadc` |
| `backend/app/benchmarks/__init__.py` | 470 | `22c9230adebca02f299bdcae73ba0fea594c6385fa077b8fc3d339938e749ea0` |
| `backend/app/benchmarks/dataset_installer.py` | 29,563 | `0a9fa8ea5cba1b823e5a67cbac92002cc5c6c4c3d7a883b2bad42dfb5e625e0d` |
| `backend/app/benchmarks/independent_audit.py` | 22,678 | `b4f550c1e1fbc9dea70dc52fa48e8d17841b0c92d9328faafab95f1ac0b272b3` |
| `backend/app/benchmarks/manifest.py` | 29,447 | `6f02362e623365705b40bccafdc66a34b60b8f453c59873aa55984a5e60736de` |
| `backend/app/benchmarks/metrics.py` | 24,973 | `0f0babec02ee4ca3ffc922c509bbe5472dc0adc7f8a8ac54ae13b782dc454687` |
| `backend/app/benchmarks/robustness.py` | 5,357 | `ceaa822d73b526f549738dd209496f49aaccbdff3780ee983b538ec11079adef` |
| `backend/app/benchmarks/router.py` | 5,665 | `0fccdbc27566676b01c64b9ad99f42de3a9e4834e711f91e01fbe7cd5d464af2` |
| `backend/app/benchmarks/runner.py` | 35,777 | `aa91f4e327e4971ff297f460630ab23152d9c80b679b44fa1c67519eb8103086` |
| `backend/app/benchmarks/schemas.py` | 12,496 | `2dfd070cadafbe2fdbecc488a493745e706a6bcbbfd4ab464fca251bc4f12673` |
| `backend/app/config.py` | 4,090 | `d2be77283ccb3ee2984b93f71275f91048086872b9767774249dfbe17113307c` |
| `backend/app/db/__init__.py` | 510 | `6710b9400b28c86d5354df40439b2811eeca39abf598de519b54f7949c0775a7` |
| `backend/app/db/database.py` | 19,606 | `30a8d4d31eba1d67f46e35da8939d92b66301d6e28f28ee6e3607476f6949fad` |
| `backend/app/engine/__init__.py` | 686 | `1fa0eeb666901259f8b864d5243f28d0517dca288a991aef4442e49c4be1dcd8` |
| `backend/app/engine/base.py` | 1,714 | `74155aab33ca6737148b6248868ebefacae3a98391aadf54a51e354c7f5fee24` |
| `backend/app/engine/real_engine.py` | 19,066 | `f15acd1c36b5a0f97310eb75c995c1ea33000ab04488cabdbb49a0e8d85f06aa` |
| `backend/app/engine/stub_engine.py` | 3,027 | `2580712f8b154d2351a5b6f18f2b1fee7fe0cb8f9dec056a3ae2170d3324519a` |
| `backend/app/main.py` | 18,694 | `b0498d5819f06318a833da46b22f8fc894ff28658b6e7eb9e52c68cb42170c50` |
| `backend/app/models/__init__.py` | 379 | `241f392b1b5d2ec4ae53a67bca08f7923ee514823e930c3336de3cd3fc4bf4fe` |
| `backend/app/models/schemas.py` | 11,884 | `2d73c99017120247e9cf5ce1e4b49571b5f5e8fd73601d0b0fabbfe16836411d` |
| `backend/app/services/__init__.py` | 140 | `e5e1dd7f050d89d2db8505ddbcb6e48e0f173e3ab517fa1ff0632bae80cfb7ba` |
| `backend/app/services/face_detector.py` | 18,655 | `8fff03d6a11cf9112fec5bf0678a82f4a54c0e4c0c3dcdea3559bbaacd1ae42a` |
| `backend/app/services/image_validator.py` | 10,441 | `db109849b1e67774d7389da77e0bb66e200eb1991cf8045f9b4516d7c707d099` |
| `backend/app/weights/download_weights.py` | 2,435 | `6aa17d2a21154d8d36a11a5af09640c2009d59c7ac45a345b02c3aa18cc6fc60` |
| `backend/app/weights/face_detection_yunet_2023mar.onnx` | 232,589 | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| `backend/app/weights/face_recognition_sface_2021dec.onnx` | 38,696,353 | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` |
| `backend/data/.gitkeep` | 28 | `41e95ea36045a5707025bf370fb1750fdf9a2fc632cf05f9d9f5874b9eafd6c7` |
| `backend/requirements.txt` | 181 | `129cc1b4dcd0549db395178b5798e821559a024c8924e67067eea46da240b030` |
| `backend/scripts/verify_weights.py` | 4,324 | `24852a84df85de4f7794016353906e255c7b02bc81cdebb75176cee39ee0b97b` |
| `docs/API_DOCUMENTATION.md` | 956 | `b36da1b808b6d48d253abb9c9c3e6f8880260383e2131a5d676356df810bcbdc` |
| `docs/INSTALLATION.md` | 1,057 | `ab553e8fb7c7299b32b1df29f7ebd0b1d5c4c7a773ff72384e6873c61beb23f0` |
| `docs/MODEL_PROVENANCE.md` | 1,164 | `a9a3196e6803636c63d31d7c06fd4b00faa44ab368204d29181fc34c87dfa590` |
| `frontend/.env.example` | 91 | `ea9b1f4c99446327a8f1acac63e634ad686245f70b590b52e6a954e065829508` |
| `frontend/dist/assets/index-0hWR37nX.js` | 417,760 | `e67d562d33675f0af21a1807948f2b64d172e3c0d1f185b4227ce286139d0d67` |
| `frontend/dist/assets/index-B5uWrYye.css` | 16,407 | `0929b3ab4153b521fde2f3fda1cde47da511ddd9ae1386ae18b9c99805e93621` |
| `frontend/dist/favicon.svg` | 9,522 | `61bc9a161de58248288e6905425d7180f0624c2865007b97d763fdac12043a66` |
| `frontend/dist/icons.svg` | 5,031 | `b45fa506195cfcdef406ba9f0c77b36ddc1a7c224040926ec70abc2fdea7b93a` |
| `frontend/dist/index.html` | 1,022 | `7f1c49f656e4bd715361024fbf662f99f0560c521a06aaf41a77d93f7fc29e27` |
| `frontend/index.html` | 924 | `98ce45b2e0f702ed0497afa3fed7e10e3846e8e2f5d53dfef67fc574fd62b0a2` |
| `frontend/package-lock.json` | 84,326 | `dff8845028ec99e9cb3b61280ae5e73494d0141cb0c0034f1f37591859328fb0` |
| `frontend/package.json` | 755 | `731f163abaa49487804841c08591edfd9afc43af94e74e1faeec218a8639faa2` |
| `frontend/src/App.css` | 2,891 | `6e25a776d3e8102da5bacb3cb99f4a5fc662a2e01e6143140671a556d28c3d5c` |
| `frontend/src/App.tsx` | 4,340 | `0df5e7897d38f70f02c980b4f785a6341a0d4e040f559919a865c4ffb755e3e6` |
| `frontend/src/assets/hero.png` | 13,057 | `881ffbcaafc212e49addad08846a5b82761355fa20624253af3477ba33262c5c` |
| `frontend/src/assets/react.svg` | 4,126 | `35ef61ed53b323ae94a16a8ec659b3d0af3880698791133f23b084085ab1c2e5` |
| `frontend/src/assets/vite.svg` | 8,709 | `5be21acd42eb7b896e517f4e0f0f11eb5c5d9e54fbbcebe9453f033008fcca6f` |
| `frontend/src/components/benchmarks/BenchmarksView.tsx` | 63,659 | `2611ad40cd254f081bf98356273ddcd0c512ff2a24f04b0615e837e8105c9b71` |
| `frontend/src/components/benchmarks/ScientificAuditView.tsx` | 32,583 | `ccf1e50b98c1f939ea25523924ed74218b072a0c63695d19b1835484c145cf8a` |
| `frontend/src/components/common/Badge.tsx` | 424 | `d7e3b9b3441f22c18006a44e6fd227fb14d5b91df0e795a3c188678bf65b5451` |
| `frontend/src/components/common/EmptyState.tsx` | 1,813 | `341b3b6ef44ac068d43635abfcdc4e6394b8966eb5ddc9754f3111ca896140e1` |
| `frontend/src/components/common/Toast.tsx` | 2,399 | `680d85a7dac2cbb6b620775993c7621d5466e455fa19f072693bb30605a97339` |
| `frontend/src/components/comparison/ComparisonProgress.tsx` | 12,573 | `fb53ccee42bc56094b4269ce770646027fb5530c9791588b909e8aa8aaaab4e6` |
| `frontend/src/components/comparison/ComparisonWorkspace.tsx` | 21,240 | `6ff11d71692795e373149b7913008232308ac4b6741f410f542214490938855e` |
| `frontend/src/components/comparison/FaceBoundingBoxOverlay.tsx` | 6,012 | `3e3c1a42ff6f48b58f853fd41f9da63eb1784b4e2f1c5b61a5f9602e03ba74ac` |
| `frontend/src/components/comparison/FaceSelectionBar.tsx` | 4,786 | `24e7469274b96f7f942481987b3b98451d848923a9a554600e13594c8e961be0` |
| `frontend/src/components/comparison/HistoryDrawer.tsx` | 8,014 | `8c68dd1b7a96a1c2ce14d2c792607faecd9ea78ff455ef16ff6730ca7be9ee15` |
| `frontend/src/components/comparison/ImagePreview.tsx` | 5,463 | `23aac7e4f90e559152e99036fd5d2653460dabf4d38956c855c95dd279ea72de` |
| `frontend/src/components/comparison/ImageUploadCard.tsx` | 13,398 | `b4b02956e088901319eee830b45542798e0350341dc378f392a04d522199c2e8` |
| `frontend/src/components/comparison/ManualCropModal.tsx` | 12,688 | `99155e86c3ad4671659a0099ef6da886697f2268919745439f79075a5643413d` |
| `frontend/src/components/comparison/QualityDiagnostics.tsx` | 9,976 | `28a5c7ece2b33b366aac7d75b86519d3893d44f110edc8fa3c669663352244e7` |
| `frontend/src/components/comparison/ResultPanel.tsx` | 21,331 | `561b21ce38a90b8f19447cc040ec5e20ccfda52fa88935eb17c4ecf57f6571b1` |
| `frontend/src/components/dashboard/DashboardView.tsx` | 23,520 | `6c7e0ccb619a1bbd3338960fa5d0a90a726f2f580f7a92459b76f717eb73f087` |
| `frontend/src/components/layout/AppShell.tsx` | 1,815 | `d57d0d6ed7b630f97b672e2916f06d0e68e84e33ef154db85ce40b1722271742` |
| `frontend/src/components/layout/Header.tsx` | 3,640 | `d046857afaab25b3408db46490375ad188e2c724ff4e31c4743928cf2d28a47d` |
| `frontend/src/components/layout/Sidebar.tsx` | 3,757 | `6e87a606eeeed6d4f025bb90b4c69020f0604ef23e3f9850f3c20f4a16a90d78` |
| `frontend/src/components/settings/SettingsView.tsx` | 19,265 | `89609e54b8fc50c79dea7d2bc173056cfff6d58e3c5801ef44e448a566a46152` |
| `frontend/src/components/testlab/TestLabView.tsx` | 7,616 | `c9ef1805e6f0b3a73edfc516c2ea5c8d4cc18bd702c889f155b4f8ffee6aa005` |
| `frontend/src/index.css` | 21,538 | `168da2a6b9709b208ee5ef36e8917a4ee6f9de2c9072edf1c51223c7f3fd703f` |
| `frontend/src/main.tsx` | 230 | `6e9e5807fcbd48b75a96db5cbef36c996262196be42e6d4760dc86babbe61ad2` |
| `frontend/src/services/api.ts` | 11,628 | `d8ce9aeda17e7f6c795e3a4534a18d800ba7d6e51f15c84708f4742071b33072` |
| `frontend/src/tests/App.test.tsx` | 4,292 | `6e59aa2634afbc019f9a31a78d7056b8cbfed228b34f595d64a54271904f92d7` |
| `frontend/src/tests/BenchmarksStep05.test.tsx` | 6,863 | `9af64b9e2c8278043ff35a75d622cba00dfdc3b3e60e1e88ded6b683cbd3c6a6` |
| `frontend/src/tests/BenchmarksStep07Real.test.tsx` | 6,283 | `e04769afa303af3e8728e984cd6a2f065d19a4a69957174475aedb0d9119b9e3` |
| `frontend/src/tests/BenchmarksStep08CrossDataset.test.tsx` | 7,070 | `f0263214432edf2b4655b7d61fc29501bb574cfa08197fcaac9161c0771fff73` |
| `frontend/src/tests/BenchmarksStep09Audit.test.tsx` | 6,332 | `a8a9572c56071236be569371e172461a6603bd0f501e5e37844787049a9d085b` |
| `frontend/src/tests/ComparisonProgress.test.tsx` | 4,534 | `ecfd04bb5e9e261ae7da00800b60ea8b9fe129979fac66e36aed79bb3490519d` |
| `frontend/src/tests/ComparisonWorkflow.test.tsx` | 13,716 | `e12fc90628c8ccff5caf7778f5c3ccd7544cbeeb7d9c66f89ada7dbf21c1be56` |
| `frontend/src/tests/DashboardView.test.tsx` | 4,255 | `9fe69065010dfc1961739d835a3d357a7304e7117177180d5ef9b7acbe1da2bb` |
| `frontend/src/tests/FaceDetectionStep04.test.tsx` | 7,306 | `4032f9221f44b3a7cbf21df0705f447269b1013917c29060395ccb3e5b7266ea` |
| `frontend/src/tests/ResultPanel.test.tsx` | 4,407 | `14a01754399825d0d49d8ec8b45a95983858491e2737f12aa4af593fbfc88a3b` |
| `frontend/src/tests/setup.ts` | 272 | `1cd07210c184af64fb66b714c2b33378420e88aebeba7797c7a7098233dc6fd2` |
| `frontend/src/types/index.ts` | 8,480 | `c0844c0bdb766defcd4b18ee03c0936cfab1b803f6d8f03d13de305862a44012` |
| `frontend/tsconfig.app.json` | 655 | `8e5d12ba330e7d86409edec74b95451e0db22ee09b9426c94b5bf817571eddb0` |
| `frontend/tsconfig.json` | 119 | `770b4140bbb581e2dfd9ea9946ffc9c75a1d86ba7d2db5f77c83e37cbdf9d808` |
| `frontend/tsconfig.node.json` | 558 | `d366cc0827139db39c61815f22491bbfda56c654354a42ad7795143d314e45e8` |
| `frontend/vite.config.ts` | 319 | `e91f22b34e92561219e79d4bc2c184edc263247cb817ca9c7a722940ba44ef42` |
| `start.bat` | 2,209 | `6e05eb3c7a10e8de6fb1e2057b37bd1ee9e53860452eec7dfb059c64c146bdfb` |
| `start.ps1` | 4,817 | `2f6a167a57938250132cf74e3b6cca4d542be77050a912ac462f156ddc3cc411` |

---

## 4. Verification & Installation

Operators can verify release package integrity by running:
```powershell
cd release\facecore-ai
python backend\scripts\verify_weights.py
.\start.ps1
```
