/**
 * Frontend unit & integration tests for Admin Predefined Museum DiscoveryPage.
 * Covers Normal, Edge, and Extraordinary cases following AAA pattern.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DiscoveryPage from '../pages/DiscoveryPage';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ isAdmin: true }),
}));

const MOCK_MUSEUMS = [
  {
    id: 'met',
    name: 'The Metropolitan Museum of Art',
    present_location: 'The Metropolitan Museum of Art, New York',
    description: 'Met Open Access API',
    default_keywords: ['craftsman', 'glass'],
    default_date_start: 0,
    default_date_end: 899,
    default_limit: 10,
  },
  {
    id: 'cma',
    name: 'Cleveland Museum of Art',
    present_location: 'The Cleveland Museum of Art, Cleveland',
    description: 'CMA Open Access API',
    default_keywords: ['craftsman', 'glass'],
    default_date_start: 0,
    default_date_end: 899,
    default_limit: 10,
  },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe('DiscoveryPage', () => {
  it('normal_loadsMuseumsEditsAndPersistsKeywordsDiscoversAndImportsSelected', async () => {
    // Arrange
    let persistedKeywords = ['craftsman', 'glass'];
    api.get.mockImplementation((url) => {
      if (url === '/admin/discovery/museums') {
        return Promise.resolve({
          data: MOCK_MUSEUMS.map((m) => ({ ...m, default_keywords: [...persistedKeywords] })),
        });
      }
      return Promise.resolve({ data: [] });
    });
    api.delete.mockImplementation((url, { params }) => {
      if (url === '/admin/discovery/keywords') {
        persistedKeywords = persistedKeywords.filter((k) => k !== params.keyword);
        return Promise.resolve({ status: 204, data: '' });
      }
      return Promise.resolve({ status: 204, data: '' });
    });
    api.post.mockImplementation((url, body) => {
      if (url === '/admin/discovery/keywords') {
        if (!persistedKeywords.some((k) => k.toLowerCase() === body.keyword.toLowerCase())) {
          persistedKeywords = [...persistedKeywords, body.keyword];
        }
        return Promise.resolve({
          data: { keyword: body.keyword, keywords: [...persistedKeywords], created: true },
        });
      }
      if (url === '/admin/discovery/search') {
        return Promise.resolve({
          data: {
            candidates: [
              {
                museum_id: 'cma',
                museum_name: 'Cleveland Museum of Art',
                source_record_id: '199001',
                object_type: 'Blown Glass Unguentarium',
                present_location: 'The Cleveland Museum of Art, Cleveland',
                findspot: 'Syria',
                material: 'Free-blown glass',
                date_display: '2nd–3rd century CE',
                date_start: 100,
                date_end: 299,
                inventory_number: '1985.12',
                dimensions_display: 'H. 12 cm',
                assembled_caption: 'Blown Glass Unguentarium, Syria, 2nd–3rd century CE',
                tags: ['Roman', 'Glass'],
                images: [{ file_url: 'https://openaccess-cdn.clevelandart.org/1985.12/web.jpg', image_sequence: 1 }],
                filled_fields_count: 14,
              },
              {
                museum_id: 'met',
                museum_name: 'The Metropolitan Museum of Art',
                source_record_id: '555001',
                object_type: 'Gold-Glass Fragment',
                present_location: 'The Metropolitan Museum of Art, New York',
                findspot: 'Rome',
                material: 'Glass',
                date_display: '4th century CE',
                date_start: 300,
                date_end: 399,
                inventory_number: '17.194.100',
                assembled_caption: 'Gold-Glass Fragment, Rome, 4th century CE',
                tags: ['Roman'],
                images: [{ file_url: 'https://images.metmuseum.org/CRDImages/md/original/DP123.jpg', image_sequence: 1 }],
                filled_fields_count: 12,
              },
            ],
            total_new: 2,
            total_duplicates_skipped: 3,
            museum_reports: [
              { museum_id: 'met', museum_name: 'The Metropolitan Museum of Art', fetched_count: 3, new_count: 1, duplicates_skipped: 2, error: null },
              { museum_id: 'cma', museum_name: 'Cleveland Museum of Art', fetched_count: 2, new_count: 1, duplicates_skipped: 1, error: null },
            ],
          },
        });
      }
      if (url === '/admin/discovery/import') {
        return Promise.resolve({
          data: {
            imported_count: 1,
            duplicates_skipped: 0,
            failed_count: 0,
            imported_objects: [
              {
                id: 99,
                object_type: 'Blown Glass Unguentarium',
                inventory_number: '1985.12',
                present_location: 'The Cleveland Museum of Art, Cleveland',
                review_status: 'pending',
              },
            ],
            skipped_inventory_numbers: [],
            errors: [],
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    const { unmount } = render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    // Assert museums loaded and 0 CE preserved
    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Start Year/i)).toHaveValue(0);
    expect(screen.getByLabelText(/End Year/i)).toHaveValue(899);

    // Add a keyword (persisted via POST) and remove one (persisted via DELETE 204)
    const kwInput = screen.getByLabelText(/Add keyword/i);
    fireEvent.change(kwInput, { target: { value: 'gold-glass' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Keyword' }));

    await waitFor(() => {
      expect(screen.getByText('gold-glass')).toBeInTheDocument();
    });
    expect(api.post).toHaveBeenCalledWith('/admin/discovery/keywords', { keyword: 'gold-glass' });

    fireEvent.click(screen.getByLabelText('Remove keyword craftsman'));
    await waitFor(() => {
      expect(screen.queryByText('craftsman')).not.toBeInTheDocument();
    });
    expect(api.delete).toHaveBeenCalledWith('/admin/discovery/keywords', { params: { keyword: 'craftsman' } });

    // Act: Submit discovery search
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));

    await waitFor(() => {
      expect(screen.getByText(/Discovered Candidates \(2 new\)/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/3 existing\/duplicate item\(s\) automatically skipped/i)).toBeInTheDocument();

    // Deselect one candidate and import remaining 1
    fireEvent.click(screen.getByLabelText('Select Gold-Glass Fragment'));
    fireEvent.click(screen.getByRole('button', { name: /Import Selected to Review Queue \(1\)/i }));

    await waitFor(() => {
      expect(screen.getByText(/Imported 1 new artifact\(s\) to Review Queue/i)).toBeInTheDocument();
    });
    expect(api.post).toHaveBeenCalledWith(
      '/admin/discovery/import',
      expect.objectContaining({
        candidates: [expect.objectContaining({ inventory_number: '1985.12' })],
      })
    );

    // Remount page to confirm added keyword is kept for future sessions
    unmount();
    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('gold-glass')).toBeInTheDocument();
    });
    expect(screen.queryByText('craftsman')).not.toBeInTheDocument();
  });

  it('edge_validatesInvertedDatesAndGuardsImeCompositionOnEnter', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    api.post.mockImplementation((url, body) => {
      if (url === '/admin/discovery/keywords') {
        return Promise.resolve({
          data: { keyword: body.keyword, keywords: ['craftsman', 'glass', body.keyword], created: true },
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });

    // Act 1: Enter during IME composition must not add keyword
    const kwInput = screen.getByLabelText(/Add keyword/i);
    fireEvent.change(kwInput, { target: { value: 'amphora' } });
    fireEvent.keyDown(kwInput, { key: 'Enter', isComposing: true, keyCode: 229 });
    expect(screen.queryByText('amphora')).not.toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();

    // Act 2: Non-composing Enter adds and persists keyword
    fireEvent.keyDown(kwInput, { key: 'Enter' });
    await waitFor(() => {
      expect(screen.getByText('amphora')).toBeInTheDocument();
    });
    expect(api.post).toHaveBeenCalledWith('/admin/discovery/keywords', { keyword: 'amphora' });

    // Act 3: Set inverted dates and submit -> shows aria-invalid validation error without search API call
    const startInput = screen.getByLabelText(/Start Year/i);
    fireEvent.change(startInput, { target: { value: '950' } });
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));

    expect(await screen.findByText(/Start Year must be less than or equal to End Year/i)).toBeInTheDocument();
    expect(startInput).toHaveAttribute('aria-invalid', 'true');
    expect(api.post).not.toHaveBeenCalledWith('/admin/discovery/search', expect.anything());
  });

  it('extraordinary_displaysVisibleErrorAlertWhenSearchOrKeywordSaveFails', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    api.post.mockImplementation((url) => {
      if (url === '/admin/discovery/keywords') {
        return Promise.reject({ response: { data: { detail: 'Keyword storage failed' } } });
      }
      return Promise.reject({ response: { data: { detail: 'Museum gateway unreachable' } } });
    });

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });

    // Act 1: Keyword save fails -> shows alert and keeps input value
    const kwInput = screen.getByLabelText(/Add keyword/i);
    fireEvent.change(kwInput, { target: { value: 'enamel' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Keyword' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Keyword storage failed');
    expect(screen.queryByText('enamel')).not.toBeInTheDocument();

    // Clear typed input and test search failure alert
    fireEvent.change(kwInput, { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));

    // Assert
    expect(await screen.findByRole('alert')).toHaveTextContent('Museum gateway unreachable');
  });
});
