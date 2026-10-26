import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Mock window.URL methods for object URL generation
if (typeof window !== 'undefined') {
  window.URL.createObjectURL = vi.fn(() => 'blob:mock-image-url');
  window.URL.revokeObjectURL = vi.fn();
}
