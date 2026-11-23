/**
 * Frontend unit & integration tests for Admin Predefined Museum DiscoveryPage.
 * Covers Normal, Edge, and Extraordinary cases following AAA pattern.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DiscoveryPage from '../pages/DiscoveryPage';
import api from '../services/api';
import {
  createInitialProgressState,
  formatElapsedTime,
  reduceDiscoveryProgress,
} from '../utils/discoveryStream';

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

const originalFetch = globalThis.fetch;

function createNdjsonStreamResponse(chunks, status = 200) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    status,
    headers: { 'Content-Type': 'application/x-ndjson' },
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  // Default stub falls back gracefully to api.post in existing search tests
  globalThis.fetch = vi.fn().mockResolvedValue(new Response('', { status: 404 }));
});

afterEach(() => {
  globalThis.fetch = originalFetch;
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

  it('normal_streamsLiveNdjsonProgressAcrossSplitChunksAndTransitionsToResults', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    const encoder = new TextEncoder();
    let streamController;
    const controlledStream = new ReadableStream({
      start(controller) {
        streamController = controller;
      },
    });
    globalThis.fetch = vi.fn().mockResolvedValueOnce(
      new Response(controlledStream, {
        status: 200,
        headers: { 'Content-Type': 'application/x-ndjson' },
      })
    );

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });

    // Act 1: Submit search -> shows initial indeterminate connecting progress
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));

    await waitFor(() => {
      expect(screen.getByText('Live Discovery Progress')).toBeInTheDocument();
    });
    const spinner = screen.getByRole('progressbar', { name: 'Museum discovery in progress' });
    expect(spinner).not.toHaveAttribute('value');
    const overallBar = screen.getByLabelText(/Connecting to museum APIs.../i);
    expect(overallBar.tagName).toBe('PROGRESS');
    expect(overallBar).not.toHaveAttribute('value');

    // Act 2: Emit search_started + museum_started + keyword_searching + split JSON line
    const candidateLine = JSON.stringify({
      type: 'candidate_found',
      museum_id: 'met',
      museum_name: 'The Metropolitan Museum of Art',
      object_type: 'Gold-Glass Fragment',
      matched_keyword: 'glass',
      fetched_count: 1,
      new_count: 1,
      duplicates_skipped: 0,
      message: 'Found "Gold-Glass Fragment" at The Metropolitan Museum of Art',
    });
    const splitAt = Math.floor(candidateLine.length / 2);

    streamController.enqueue(
      encoder.encode(
        [
          JSON.stringify({
            type: 'search_started',
            museums: [
              { museum_id: 'met', museum_name: 'The Metropolitan Museum of Art' },
              { museum_id: 'cma', museum_name: 'Cleveland Museum of Art' },
            ],
            total_museums: 2,
            total_keywords: 2,
            message: 'Starting discovery across 2 museum(s)...',
          }),
          JSON.stringify({
            type: 'museum_started',
            museum_id: 'met',
            museum_name: 'The Metropolitan Museum of Art',
            museum_index: 1,
            total_museums: 2,
            total_keywords: 2,
            message: 'Connecting to The Metropolitan Museum of Art (1/2)...',
          }),
          JSON.stringify({
            type: 'keyword_searching',
            museum_id: 'met',
            museum_name: 'The Metropolitan Museum of Art',
            keyword: 'glass',
            keyword_index: 1,
            total_keywords: 2,
            fetched_count: 1,
            new_count: 0,
            duplicates_skipped: 1,
            message: 'The Metropolitan Museum of Art: searching "glass" (1/2)',
          }),
        ].join('\n') + '\n' + candidateLine.slice(0, splitAt)
      )
    );

    await waitFor(() => {
      expect(screen.getByText(/The Metropolitan Museum of Art: searching "glass" \(1\/2\)/i)).toBeInTheDocument();
    });
    expect(screen.getByText('Searching')).toBeInTheDocument();
    expect(screen.getByText('Queued')).toBeInTheDocument();

    // Finish split chunk + emit final complete event
    const finalPayload = {
      candidates: [
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
          assembled_caption: 'Gold-Glass Fragment, Rome',
          tags: ['Roman'],
          images: [{ file_url: 'https://images.metmuseum.org/CRDImages/md/original/DP123.jpg', image_sequence: 1 }],
          filled_fields_count: 10,
        },
      ],
      total_new: 1,
      total_duplicates_skipped: 1,
      museum_reports: [
        { museum_id: 'met', museum_name: 'The Metropolitan Museum of Art', fetched_count: 1, new_count: 1, duplicates_skipped: 1, error: null },
        { museum_id: 'cma', museum_name: 'Cleveland Museum of Art', fetched_count: 0, new_count: 0, duplicates_skipped: 0, error: null },
      ],
    };

    streamController.enqueue(
      encoder.encode(
        candidateLine.slice(splitAt) + '\n' + JSON.stringify({
          type: 'complete',
          total_new: 1,
          total_duplicates_skipped: 1,
          result: finalPayload,
          message: 'Discovery complete: 1 new artifact(s) found, 1 duplicate(s) skipped.',
        }) + '\n'
      )
    );

    await waitFor(() => {
      expect(screen.getByText(/Live Activity Feed/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Found "Gold-Glass Fragment" at The Metropolitan Museum of Art/i)).toBeInTheDocument();

    streamController.close();

    // Assert final transition to candidates section
    await waitFor(() => {
      expect(screen.getByText(/Discovered Candidates \(1 new\)/i)).toBeInTheDocument();
    });
    expect(screen.queryByText('Live Discovery Progress')).not.toBeInTheDocument();
  });

  it('edge_cancelActiveStreamAbortsRequestWithoutErrorAndReducesProgressCleanly', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    let capturedSignal = null;
    globalThis.fetch = vi.fn().mockImplementationOnce((_url, options) => {
      capturedSignal = options.signal;
      return new Promise((_resolve, reject) => {
        options.signal.addEventListener('abort', () => {
          reject(new DOMException('The operation was aborted.', 'AbortError'));
        });
      });
    });

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    const cancelBtn = await screen.findByRole('button', { name: 'Cancel Search' });

    // Act
    fireEvent.click(cancelBtn);

    // Assert
    expect(capturedSignal?.aborted).toBe(true);
    expect(await screen.findByRole('status')).toHaveTextContent('Discovery search cancelled.');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    // Pure utility coverage (elapsed timer formatting + reducer progression)
    expect(formatElapsedTime(0)).toBe('0:00');
    expect(formatElapsedTime(5)).toBe('0:05');
    expect(formatElapsedTime(65)).toBe('1:05');
    expect(formatElapsedTime(-3)).toBe('0:00');

    let state = createInitialProgressState(['met'], MOCK_MUSEUMS, 2);
    expect(state.percent).toBeNull();
    state = reduceDiscoveryProgress(state, {
      type: 'detail_fetching',
      museum_id: 'met',
      detail_index: 1,
      detail_total: 2,
      fetched_count: 2,
      new_count: 1,
      duplicates_skipped: 1,
      message: 'The Metropolitan Museum of Art: inspecting record 1 of 2...',
    });
    expect(state.percent).toBe(80);
    expect(state.museums[0].currentStage).toBe('Inspecting record 1/2');
    state = reduceDiscoveryProgress(state, {
      type: 'complete',
      message: 'Discovery complete',
    });
    expect(state.percent).toBe(100);
    expect(state.phase).toBe('complete');
  });

  it('extraordinary_streamErrorEventAndHttp500RenderVisibleAlerts', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    globalThis.fetch
      .mockResolvedValueOnce(
        createNdjsonStreamResponse([
          JSON.stringify({ type: 'error', message: 'Upstream museum API rate limited' }) + '\n',
        ])
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Gateway failure' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        })
      );

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });

    // Act 1: Terminal NDJSON error event
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Upstream museum API rate limited');

    // Act 2: HTTP 500 error JSON detail
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Gateway failure');
  });

  it('normal_rendersAndSearchesBritishMuseumOptionAndRestoresOnReset', async () => {
    // Arrange
    const museumsWithBm = [
      ...MOCK_MUSEUMS,
      {
        id: 'bm',
        name: 'The British Museum',
        present_location: 'The British Museum, London',
        description: 'British Museum collection via Wikidata Linked Open Data & Wikimedia Commons.',
        default_keywords: ['craftsman', 'glass'],
        default_date_start: 0,
        default_date_end: 899,
        default_limit: 10,
      },
    ];
    api.get.mockResolvedValueOnce({ data: museumsWithBm });
    api.post.mockImplementation((url) => {
      if (url === '/admin/discovery/search') {
        return Promise.resolve({
          data: {
            candidates: [
              {
                museum_id: 'bm',
                museum_name: 'The British Museum',
                source_record_id: 'Q2457011',
                object_type: 'Vindolanda Copper-Alloy Stylus',
                present_location: 'The British Museum, London',
                findspot: 'Vindolanda',
                material: 'bronze',
                date_display: '2nd century CE',
                date_start: 101,
                date_end: 200,
                inventory_number: '1986,1001.15',
                assembled_caption: 'Vindolanda Copper-Alloy Stylus, Vindolanda, 2nd century CE',
                tags: ['Ancient Rome', 'bronze'],
                images: [{
                  file_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Vindolanda_stylus_BM.jpg/1000px-Vindolanda_stylus_BM.jpg',
                  image_sequence: 1,
                }],
                filled_fields_count: 15,
              },
            ],
            total_new: 1,
            total_duplicates_skipped: 0,
            museum_reports: [
              { museum_id: 'bm', museum_name: 'The British Museum', fetched_count: 1, new_count: 1, duplicates_skipped: 0, error: null },
            ],
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    // Assert BM checkbox loads checked by default
    const bmCheckbox = await screen.findByLabelText(/The British Museum/i);
    expect(bmCheckbox).toBeChecked();

    // Toggle off and restore via Reset Defaults
    fireEvent.click(bmCheckbox);
    expect(bmCheckbox).not.toBeChecked();
    fireEvent.click(screen.getByRole('button', { name: /Reset Defaults/i }));
    expect(bmCheckbox).toBeChecked();

    // Act: Submit discovery search and verify 'bm' included and candidate rendered
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    await waitFor(() => {
      expect(screen.getByText('Vindolanda Copper-Alloy Stylus')).toBeInTheDocument();
    });
    expect(api.post).toHaveBeenCalledWith(
      '/admin/discovery/search',
      expect.objectContaining({
        museums: expect.arrayContaining(['met', 'cma', 'bm']),
      }),
      expect.any(Object)
    );
  });

  it('normal_rejectsCandidateDirectlyShowsRejectedCountsAndUndoesVia204', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    api.post.mockImplementation((url) => {
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
                date_display: '2nd century CE',
                date_start: 100,
                date_end: 199,
                inventory_number: '1985.12',
                external_url: 'https://clevelandart.org/art/1985.12',
                images: [{ file_url: 'https://openaccess-cdn.clevelandart.org/1985.12/web.jpg', image_sequence: 1 }],
                filled_fields_count: 8,
              },
            ],
            total_new: 1,
            total_duplicates_skipped: 4,
            total_rejected_skipped: 2,
            museum_reports: [
              { museum_id: 'cma', museum_name: 'Cleveland Museum of Art', fetched_count: 5, new_count: 1, duplicates_skipped: 4, rejected_skipped: 2, error: null },
            ],
          },
        });
      }
      if (url === '/admin/discovery/reject') {
        return Promise.resolve({
          data: {
            rejected_count: 1,
            already_rejected_count: 0,
            rejected_items: [
              {
                id: 42,
                museum_id: 'cma',
                source_record_id: '199001',
                inventory_number: '1985.12',
                external_url: 'https://clevelandart.org/art/1985.12',
                object_type: 'Blown Glass Unguentarium',
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: {} });
    });
    api.delete.mockResolvedValueOnce({ status: 204, data: '' });

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });

    // Act 1: Run discovery search and verify previously rejected breakdown renders
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    await waitFor(() => {
      expect(screen.getByText(/4 existing\/duplicate item\(s\) automatically skipped \(2 previously rejected\)\./i)).toBeInTheDocument();
    });
    expect(screen.getByText(/4 skipped \(2 rejected\)/i)).toBeInTheDocument();

    // Act 2: Reject candidate directly
    fireEvent.click(screen.getByRole('button', { name: 'Reject Blown Glass Unguentarium' }));

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(/Rejected .Blown Glass Unguentarium.\. It will be skipped in future searches\./i);
    });
    expect(api.post).toHaveBeenCalledWith('/admin/discovery/reject', {
      candidates: [
        expect.objectContaining({
          museum_id: 'cma',
          source_record_id: '199001',
          inventory_number: '1985.12',
        }),
      ],
    });
    expect(screen.getByText(/Discovered Candidates \(0 new\)/i)).toBeInTheDocument();

    // Act 3: Undo direct rejection via HTTP 204 DELETE
    fireEvent.click(screen.getByRole('button', { name: 'Undo' }));

    await waitFor(() => {
      expect(screen.getByText(/Discovered Candidates \(1 new\)/i)).toBeInTheDocument();
    });
    expect(api.delete).toHaveBeenCalledWith('/admin/discovery/rejected/42');
    expect(screen.getByRole('button', { name: 'Reject Blown Glass Unguentarium' })).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('edge_guardsDuplicateRejectClicksAndTracksStreamRejectedSkippedCounts', async () => {
    // Arrange: verify stream reducer tracks rejected_skipped and double-click is guarded
    let state = createInitialProgressState(['met'], MOCK_MUSEUMS, 1);
    state = reduceDiscoveryProgress(state, {
      type: 'detail_fetching',
      museum_id: 'met',
      detail_index: 1,
      detail_total: 2,
      fetched_count: 3,
      new_count: 1,
      duplicates_skipped: 2,
      rejected_skipped: 2,
      message: 'Inspecting...',
    });
    expect(state.totalSkipped).toBe(2);
    expect(state.totalRejectedSkipped).toBe(2);

    let resolveReject;
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    api.post.mockImplementation((url) => {
      if (url === '/admin/discovery/search') {
        return Promise.resolve({
          data: {
            candidates: [
              {
                museum_id: 'met',
                museum_name: 'The Metropolitan Museum of Art',
                source_record_id: '555001',
                object_type: 'Gold-Glass Fragment',
                date_display: '4th century CE',
                date_start: 300,
                date_end: 399,
                images: [{ file_url: 'https://images.metmuseum.org/CRDImages/md/original/DP123.jpg', image_sequence: 1 }],
                filled_fields_count: 6,
              },
            ],
            total_new: 1,
            total_duplicates_skipped: 0,
            total_rejected_skipped: 0,
            museum_reports: [
              { museum_id: 'met', museum_name: 'The Metropolitan Museum of Art', fetched_count: 1, new_count: 1, duplicates_skipped: 0, rejected_skipped: 0, error: null },
            ],
          },
        });
      }
      if (url === '/admin/discovery/reject') {
        return new Promise((resolve) => {
          resolveReject = resolve;
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

    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    const rejectBtn = await screen.findByRole('button', { name: 'Reject Gold-Glass Fragment' });

    // Act: click Reject twice while request is in-flight
    fireEvent.click(rejectBtn);
    expect(rejectBtn).toBeDisabled();
    expect(rejectBtn).toHaveTextContent('Rejecting...');
    fireEvent.click(rejectBtn);
    expect(api.post).toHaveBeenCalledTimes(2); // 1 search + 1 reject (second click ignored)

    resolveReject({
      data: {
        rejected_count: 1,
        already_rejected_count: 0,
        rejected_items: [{ id: 77, museum_id: 'met', source_record_id: '555001' }],
      },
    });

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(/Rejected .Gold-Glass Fragment./i);
    });
  });

  it('extraordinary_displaysAlertsOnRejectOrUndoFailuresWithoutDroppingCandidate', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    api.post.mockImplementation((url) => {
      if (url === '/admin/discovery/search') {
        return Promise.resolve({
          data: {
            candidates: [
              {
                museum_id: 'met',
                museum_name: 'The Metropolitan Museum of Art',
                source_record_id: '555002',
                object_type: 'Roman Bronze Lamp',
                date_display: '2nd century CE',
                date_start: 100,
                date_end: 199,
                images: [{ file_url: 'https://images.metmuseum.org/CRDImages/md/original/lamp.jpg', image_sequence: 1 }],
                filled_fields_count: 6,
              },
            ],
            total_new: 1,
            total_duplicates_skipped: 0,
            total_rejected_skipped: 0,
            museum_reports: [],
          },
        });
      }
      if (url === '/admin/discovery/reject') {
        return Promise.reject({ response: { data: { detail: 'Reject persistence error' } } });
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

    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    const rejectBtn = await screen.findByRole('button', { name: 'Reject Roman Bronze Lamp' });

    // Act 1: Reject fails -> shows alert and keeps candidate in list
    fireEvent.click(rejectBtn);
    expect(await screen.findByRole('alert')).toHaveTextContent('Reject persistence error');
    expect(screen.getByRole('button', { name: 'Reject Roman Bronze Lamp' })).toBeInTheDocument();

    // Act 2: Reject succeeds, then Undo fails -> shows alert
    api.post.mockResolvedValueOnce({
      data: {
        rejected_count: 1,
        already_rejected_count: 0,
        rejected_items: [{ id: 88, museum_id: 'met', source_record_id: '555002' }],
      },
    });
    api.delete.mockRejectedValueOnce({ response: { data: { detail: 'Undo failed on server' } } });

    fireEvent.click(screen.getByRole('button', { name: 'Reject Roman Bronze Lamp' }));
    const undoBtn = await screen.findByRole('button', { name: 'Undo' });
    fireEvent.click(undoBtn);

    expect(await screen.findByRole('alert')).toHaveTextContent('Undo failed on server');
  });

  it('normal_appliesWorkerPresetsBceEraAndRendersWorkerRelevanceDetails', async () => {
    // Arrange
    api.get.mockImplementation((url) => {
      if (url === '/admin/discovery/museums') {
        return Promise.resolve({ data: MOCK_MUSEUMS });
      }
      if (url === '/admin/discovery/presets') {
        return Promise.resolve({
          data: [
            {
              id: 'artisans_workshops',
              name: 'Artisans & Workshops',
              description: 'Potters and smiths',
              keywords: ['potter', 'shoemaker', 'ergasterion'],
              recommended_date_start: -2500,
              recommended_date_end: 899,
            },
          ],
        });
      }
      return Promise.resolve({ data: [] });
    });
    api.post.mockImplementation((url) => {
      if (url === '/admin/discovery/search') {
        return Promise.resolve({
          data: {
            candidates: [
              {
                museum_id: 'bm',
                museum_name: 'The British Museum',
                source_record_id: 'Q880009',
                matched_keyword: 'shoemaker',
                object_type: 'Grave Stele of Xanthippos',
                present_location: 'The British Museum, London',
                date_display: 'ca. 420 BCE',
                date_start: -420,
                date_end: -420,
                description: 'Athenian marble funerary stele depicting a seated shoemaker.',
                worker_relevance_score: 92,
                worker_confidence: 'high',
                worker_signals: ['Subject tag: shoemaker', 'Title depicts worker: shoemaker'],
                images: [{ file_url: 'https://upload.wikimedia.org/wikipedia/commons/x/xa/Xanthippos_stele.jpg', image_sequence: 1 }],
                filled_fields_count: 11,
              },
            ],
            total_new: 1,
            total_duplicates_skipped: 0,
            total_rejected_skipped: 0,
            total_filtered_non_worker: 3,
            search_mode: 'worker_depictions',
            museum_reports: [
              {
                museum_id: 'bm',
                museum_name: 'The British Museum',
                fetched_count: 4,
                new_count: 1,
                duplicates_skipped: 0,
                rejected_skipped: 0,
                filtered_non_worker: 3,
                error: null,
              },
            ],
          },
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
      expect(screen.getByRole('button', { name: 'Artisans & Workshops' })).toBeInTheDocument();
    });

    // Assert default focus mode radio
    expect(screen.getByLabelText(/Ancient Workers Depictions \(Recommended\)/i)).toBeChecked();

    // Act: Apply preset + BCE era focus + submit
    fireEvent.click(screen.getByRole('button', { name: 'Artisans & Workshops' }));
    expect(screen.getByText('ergasterion')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Ancient World (3000 BCE–500 CE)' }));
    expect(screen.getByLabelText(/Start Year/i)).toHaveValue(-3000);
    expect(screen.getByLabelText(/End Year/i)).toHaveValue(500);

    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));

    // Assert request payload + rendered relevance badge, signals, filtered summary, and native details
    expect(await screen.findByText('Grave Stele of Xanthippos')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith(
      '/admin/discovery/search',
      expect.objectContaining({
        keywords: ['potter', 'shoemaker', 'ergasterion'],
        date_start: -3000,
        date_end: 500,
        search_mode: 'worker_depictions',
        min_worker_score: 35,
        save_keywords: false,
      }),
      expect.any(Object)
    );
    expect(screen.getByText('★ High Worker Match (92%)')).toBeInTheDocument();
    expect(screen.getByText(/Matched:/)).toHaveTextContent('shoemaker');
    expect(screen.getByText('Subject tag: shoemaker')).toBeInTheDocument();
    expect(screen.getByText(/3 non-worker item\(s\) filtered\./i)).toBeInTheDocument();
    expect(screen.getByText('Catalog notes')).toBeInTheDocument();
  });

  it('edge_handlesStrictToggleBroadModeConfidenceFilteringAndStreamFilteredReducer', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({ data: MOCK_MUSEUMS });
    api.post.mockResolvedValue({
      data: {
        candidates: [
          {
            museum_id: 'met',
            museum_name: 'The Metropolitan Museum of Art',
            source_record_id: '9001',
            object_type: 'Meketre Bakery Model',
            date_display: '2000 BCE',
            date_start: -2000,
            date_end: -1990,
            worker_relevance_score: 95,
            worker_confidence: 'high',
            worker_signals: ['Subject tag: Bakers'],
            images: [],
            filled_fields_count: 9,
          },
          {
            museum_id: 'cma',
            museum_name: 'Cleveland Museum of Art',
            source_record_id: '9002',
            object_type: 'Shabti Servant Figure',
            date_display: '1300 BCE',
            date_start: -1300,
            date_end: -1290,
            worker_relevance_score: 45,
            worker_confidence: 'medium',
            worker_signals: ['Title mentions worker: shabti'],
            images: [],
            filled_fields_count: 7,
          },
        ],
        total_new: 2,
        total_duplicates_skipped: 0,
        total_rejected_skipped: 0,
        total_filtered_non_worker: 2,
        museum_reports: [],
      },
    });

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cleveland Museum of Art')).toBeInTheDocument();
    });

    // Act 1: Toggle Strict checkbox -> sends min_worker_score: 65
    fireEvent.click(screen.getByLabelText(/Strict: High-confidence worker depictions only/i));
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    expect(await screen.findByText('Meketre Bakery Model')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith(
      '/admin/discovery/search',
      expect.objectContaining({ min_worker_score: 65, search_mode: 'worker_depictions' }),
      expect.any(Object)
    );

    // Act 2: Filter UI to High Confidence Only
    fireEvent.click(screen.getByRole('button', { name: /High Confidence Only \(1\)/i }));
    expect(screen.getByText('Meketre Bakery Model')).toBeInTheDocument();
    expect(screen.queryByText('Shabti Servant Figure')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /All Results \(2\)/i }));
    expect(screen.getByText('Shabti Servant Figure')).toBeInTheDocument();

    // Act 3: Switch to Broad Keyword Search -> hides Strict checkbox and sends search_mode: 'broad'
    fireEvent.click(screen.getByLabelText(/Broad Keyword Search/i));
    expect(screen.queryByLabelText(/Strict: High-confidence/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/admin/discovery/search',
        expect.objectContaining({ search_mode: 'broad' }),
        expect.any(Object)
      );
    });

    // Act 4: Verify discoveryStream reducer tracks filtered_non_worker counts
    const init = createInitialProgressState(['met'], MOCK_MUSEUMS, 5);
    const updated = reduceDiscoveryProgress(init, {
      type: 'museum_completed',
      museum_id: 'met',
      fetched_count: 10,
      new_count: 2,
      duplicates_skipped: 1,
      filtered_non_worker: 4,
      message: 'Done',
    });
    expect(updated.totalFilteredNonWorker).toBe(4);
    expect(updated.museums[0].filtered_non_worker).toBe(4);
  });

  it('extraordinary_fallsBackSilentlyOnPresetsFailureAndShowsZeroFilteredGuidance', async () => {
    // Arrange
    api.get.mockImplementation((url) => {
      if (url === '/admin/discovery/museums') {
        return Promise.resolve({ data: MOCK_MUSEUMS });
      }
      if (url === '/admin/discovery/presets') {
        return Promise.reject(new Error('Presets unavailable'));
      }
      return Promise.resolve({ data: [] });
    });
    api.post.mockResolvedValueOnce({
      data: {
        candidates: [],
        total_new: 0,
        total_duplicates_skipped: 0,
        total_rejected_skipped: 0,
        total_filtered_non_worker: 12,
        museum_reports: [],
      },
    });

    render(
      <MemoryRouter>
        <DiscoveryPage />
      </MemoryRouter>
    );

    // Built-in presets still render with no alert banner
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'All Ancient Workers' })).toBeInTheDocument();
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    // Act: Run search with 0 surviving candidates after filtering
    fireEvent.click(screen.getByRole('button', { name: /Discover New Artifacts/i }));

    // Assert recovery guidance renders
    expect(
      await screen.findByText(/12 record\(s\) matched your keywords but scored below the worker depiction threshold/i)
    ).toBeInTheDocument();
  });
});
