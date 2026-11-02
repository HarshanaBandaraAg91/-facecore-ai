import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FaceBoundingBoxOverlay } from '../components/comparison/FaceBoundingBoxOverlay';
import { FaceSelectionBar } from '../components/comparison/FaceSelectionBar';
import { ManualCropModal } from '../components/comparison/ManualCropModal';
import { QualityDiagnostics } from '../components/comparison/QualityDiagnostics';
import type { DetectedFaceSummary, ImageQualityDiagnostics } from '../types';

const mockFaces: DetectedFaceSummary[] = [
  {
    index: 0,
    box: [50, 60, 100, 120],
    confidence: 0.942,
    landmarks: [
      [75, 95],
      [125, 95],
      [100, 120],
      [80, 145],
      [120, 145],
    ],
    quality_advisories: [],
  },
  {
    index: 1,
    box: [200, 70, 90, 110],
    confidence: 0.887,
    landmarks: [
      [225, 100],
      [265, 100],
      [245, 125],
      [230, 150],
      [260, 150],
    ],
    quality_advisories: ['Low lighting or underexposed face region'],
  },
];

describe('STEP 04: Robust Face Detection UI Components', () => {
  describe('FaceBoundingBoxOverlay', () => {
    it('renders bounding boxes for all detected faces with correct labels', () => {
      const handleSelect = vi.fn();
      render(
        <div style={{ position: 'relative', width: 400, height: 300 }}>
          <FaceBoundingBoxOverlay
            faces={mockFaces}
            imageWidth={400}
            imageHeight={300}
            selectedFaceIndex={0}
            onSelectFace={handleSelect}
          />
        </div>
      );

      expect(screen.getByText(/FACE #\s*1/i)).toBeDefined();
      expect(screen.getByText(/FACE #\s*2/i)).toBeDefined();
      expect(screen.getByText(/ACTIVE/i)).toBeDefined();
    });

    it('triggers onSelectFace when a bounding box is clicked', () => {
      const handleSelect = vi.fn();
      render(
        <div style={{ position: 'relative', width: 400, height: 300 }}>
          <FaceBoundingBoxOverlay
            faces={mockFaces}
            imageWidth={400}
            imageHeight={300}
            selectedFaceIndex={0}
            onSelectFace={handleSelect}
          />
        </div>
      );

      const face2Button = screen.getByRole('button', { name: /Face #2/i });
      fireEvent.click(face2Button);
      expect(handleSelect).toHaveBeenCalledWith(1);
    });
  });

  describe('FaceSelectionBar', () => {
    it('displays multiple detected faces and allows switching active target', () => {
      const handleSelect = vi.fn();

      render(
        <FaceSelectionBar
          faces={mockFaces}
          selectedFaceIndex={0}
          onSelectFace={handleSelect}
        />
      );

      expect(screen.getByText(/MULTIPLE FACES DETECTED/i)).toBeDefined();
      expect(screen.getByText(/2 LOCATED/i)).toBeDefined();
      const faceButtons = screen.getAllByRole('button');
      expect(faceButtons.length).toBe(2);

      fireEvent.click(faceButtons[1]);
      expect(handleSelect).toHaveBeenCalledWith(1);
    });
  });

  describe('ManualCropModal', () => {
    it('renders crop guidance, coordinate readouts, and action buttons', () => {
      const handleApply = vi.fn();
      const handleClose = vi.fn();

      render(
        <ManualCropModal
          isOpen={true}
          imageUrl="data:image/jpeg;base64,mock"
          imageWidth={400}
          imageHeight={400}
          initialCropBox={null}
          onApplyCrop={handleApply}
          onClose={handleClose}
        />
      );

      expect(screen.getByText(/MANUAL FACE CROP & REGION RECOVERY/i)).toBeDefined();
      expect(screen.getByText(/Click and drag across the image to enclose the subject/i)).toBeDefined();
      expect(screen.getByRole('button', { name: /Apply & Validate Crop/i })).toBeDefined();
      expect(screen.getByRole('button', { name: /Center Box/i })).toBeDefined();
    });

    it('calls onApplyCrop with validated coordinates when confirmed', () => {
      const handleApply = vi.fn();
      const handleClose = vi.fn();

      render(
        <ManualCropModal
          isOpen={true}
          imageUrl="data:image/jpeg;base64,mock"
          imageWidth={400}
          imageHeight={400}
          initialCropBox={[40, 40, 200, 200]}
          onApplyCrop={handleApply}
          onClose={handleClose}
        />
      );

      const applyButton = screen.getByRole('button', { name: /Apply & Validate Crop/i });
      fireEvent.click(applyButton);

      expect(handleApply).toHaveBeenCalled();
      const appliedCrop = handleApply.mock.calls[0][0];
      expect(appliedCrop).toHaveLength(4);
      expect(appliedCrop[0]).toBeGreaterThanOrEqual(0);
      expect(appliedCrop[1]).toBeGreaterThanOrEqual(0);
      expect(appliedCrop[2]).toBeGreaterThanOrEqual(32);
      expect(appliedCrop[3]).toBeGreaterThanOrEqual(32);
    });
  });

  describe('QualityDiagnostics with Step 04 shared detection', () => {
    it('accurately displays face count, selected index, and bounding box coordinates', () => {
      const diagnostics: ImageQualityDiagnostics = {
        filename: 'probe.jpg',
        format: 'JPEG',
        color_mode: 'RGB',
        width: 400,
        height: 300,
        aspect_ratio: '4:3',
        file_size_bytes: 45000,
        sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        estimated_sharpness: 120.5,
        contrast_std: 45.2,
        brightness_mean: 110.0,
        resolution_category: 'Standard',
        face_detected: true,
        face_count: 2,
        face_confidence: 0.942,
        face_bounding_box: [50, 60, 100, 120],
        crop_bounding_box: null,
        selected_face_index: 0,
        detected_faces: mockFaces,
        passes_quality_check: true,
        warnings: [],
      };

      render(<QualityDiagnostics diagnostics={diagnostics} />);

      expect(screen.getByText(/2 Faces Detected \(Face #1 Active\)/i)).toBeDefined();
      expect(screen.getByText(/\[50, 60, 100, 120\]/i)).toBeDefined();
      expect(screen.getByText(/Pass/i)).toBeDefined();
    });

    it('displays No Face Localized badge and 0 Faces Detected when 0 faces found', () => {
      const zeroFaceDiagnostics: ImageQualityDiagnostics = {
        filename: 'blank.jpg',
        format: 'JPEG',
        color_mode: 'RGB',
        width: 300,
        height: 300,
        aspect_ratio: '1:1',
        file_size_bytes: 25000,
        sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        estimated_sharpness: 10.0,
        contrast_std: 5.0,
        brightness_mean: 128.0,
        resolution_category: 'Low',
        face_detected: false,
        face_count: 0,
        face_confidence: null,
        face_bounding_box: null,
        crop_bounding_box: null,
        selected_face_index: null,
        detected_faces: [],
        passes_quality_check: false,
        warnings: ['No human face detected. Use the Manual Face Crop tool or upload a clearer, well-lit image.'],
      };

      render(<QualityDiagnostics diagnostics={zeroFaceDiagnostics} />);

      expect(screen.getByText(/0 Faces Detected/i)).toBeDefined();
      expect(screen.getByText(/No Face Localized/i)).toBeDefined();
      expect(screen.getByText(/No human face detected/i)).toBeDefined();
    });
  });
});
