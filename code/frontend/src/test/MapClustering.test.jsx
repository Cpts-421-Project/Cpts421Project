/**
 * Unit & integration tests for dynamic map marker clustering (fusion) and
 * active map-cluster filtering in SearchPage & FilterSidebar.
 * Covers Normal, Edge, and Extraordinary cases following AAA pattern.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import {
  isValidCoordinate,
  summarizeClusterLabel,
  clusterMapPoints,
  buildClusterSearchUrl,
} from '../utils/mapClustering';
import MapVisualizer from '../components/MapVisualizer';
import SearchPage from '../pages/SearchPage';
import api from '../services/api';

const { zoomHandlers } = vi.hoisted(() => ({ zoomHandlers: {} }));

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }) => <div data-testid="mock-map">{children}</div>,
  TileLayer: () => null,
  Tooltip: ({ children }) => <div>{children}</div>,
  Popup: ({ children }) => <div>{children}</div>,
  useMapEvents: (handlers) => {
    Object.assign(zoomHandlers, handlers);
    return null;
  },
  Marker: ({ position, alt, eventHandlers, children }) => (
    <button
      type="button"
      data-testid="map-marker"
      data-lat={position[0]}
      data-lng={position[1]}
      aria-label={alt || 'Map marker'}
      onClick={() => eventHandlers?.click?.()}
    >
      {children}
    </button>
  ),
}));

beforeEach(() => {
  vi.clearAllMocks();
  delete zoomHandlers.zoomend;
});

describe('mapClustering utilities', () => {
  it('normal_fusesSameSiteAndClosePointsAtLowZoomAndSplitsWhenZoomedIn', () => {
    // Arrange: Two items in Rome, one in nearby Ostia (~25km away), one distant in Nineveh
    const points = [
      { id: 10, name: 'Gold-glass Roundel', findspot: 'Rome', latitude: 41.9028, longitude: 12.4964 },
      { id: 11, name: 'Marble Plaque', findspot: 'Rome', latitude: 41.9028, longitude: 12.4964 },
      { id: 12, name: 'Physician Sarcophagus', findspot: 'Ostia, Rome', latitude: 41.7558, longitude: 12.2906 },
      { id: 13, name: 'Nineveh Relief', findspot: 'Nineveh, Northern Iraq', latitude: 36.3594, longitude: 43.1528 },
    ];

    // Act
    const lowZoomClusters = clusterMapPoints(points, 5);
    const highZoomClusters = clusterMapPoints(points, 12);

    // Assert: At zoom 5, Rome (2) + Ostia (1) fuse into one cluster of 3; Nineveh remains 1
    expect(lowZoomClusters).toHaveLength(2);
    const romeOstia = lowZoomClusters.find((c) => c.ids.length === 3);
    expect(romeOstia.ids).toEqual([10, 11, 12]);
    expect(romeOstia.label).toBe('Rome & Ostia, Rome');
    expect(buildClusterSearchUrl(romeOstia)).toBe('/search?ids=10%2C11%2C12&map_label=Rome+%26+Ostia%2C+Rome');

    // Assert: At zoom 12, Ostia separates from Rome while the two co-located Rome pieces remain fused
    expect(highZoomClusters).toHaveLength(3);
    expect(highZoomClusters.find((c) => c.ids.length === 2).ids).toEqual([10, 11]);
  });

  it('edge_preservesZeroCoordinatesAndSummarizesManySites', () => {
    // Arrange (INV-UI-01: numeric 0 latitude/longitude must be kept)
    const points = [
      { id: 1, name: 'Equator Piece', findspot: 'Site A', latitude: 0, longitude: 0 },
      { id: 2, name: 'Prime Piece', findspot: 'Site B', latitude: 0.01, longitude: 0.01 },
      { id: 3, name: 'Third Piece', findspot: 'Site C', latitude: 0.02, longitude: 0.02 },
    ];

    // Act
    const clusters = clusterMapPoints(points, 5);

    // Assert
    expect(isValidCoordinate(0)).toBe(true);
    expect(clusters).toHaveLength(1);
    expect(clusters[0].ids).toEqual([1, 2, 3]);
    expect(summarizeClusterLabel(points)).toBe('Site A, Site B + 1 sites');
  });

  it('extraordinary_ignoresInvalidNullNaNCoordinatesWithoutCrashing', () => {
    // Arrange
    const dirtyPoints = [
      null,
      { id: 1, name: 'No Lat', latitude: null, longitude: 12.5 },
      { id: 2, name: 'NaN Coords', latitude: Number.NaN, longitude: 12.5 },
      { id: 3, name: 'String Coords', latitude: '41.9', longitude: '12.5' },
    ];

    // Act & Assert
    expect(clusterMapPoints(dirtyPoints, 5)).toEqual([]);
    expect(clusterMapPoints(null, 5)).toEqual([]);
  });
});

describe('MapVisualizer cluster interaction', () => {
  it('normal_clickingFusedClusterNavigatesToSearchWithActiveClusterFilter', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({
      data: [
        { id: 4, name: 'Roman Sarcophagus', findspot: 'Ostia, Rome', latitude: 41.7558, longitude: 12.2906 },
        { id: 61, name: 'Gold-glass Roundel', findspot: 'Rome', latitude: 41.9028, longitude: 12.4964 },
        { id: 55, name: 'Nineveh Bull', findspot: 'Nineveh', latitude: 36.3594, longitude: 43.1528 },
      ],
    });

    render(
      <MemoryRouter initialEntries={['/map']}>
        <Routes>
          <Route path="/map" element={<MapVisualizer />} />
          <Route path="/search" element={<SearchPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for markers to render: Rome + Ostia fuse into 1 cluster marker of 2, Nineveh is 1 single marker
    await waitFor(() => {
      expect(screen.getAllByTestId('map-marker')).toHaveLength(2);
    });

    // Mock Search API response for navigation target
    api.get.mockImplementation((url) => {
      if (url === '/tags') return Promise.resolve({ data: ['Roman'] });
      if (url === '/objects/search') {
        return Promise.resolve({
          data: [
            { id: 61, object_type: 'Gold-glass Roundel', date_display: '4th c. CE', images: [], tags: ['Roman'] },
            { id: 4, object_type: 'Roman Sarcophagus', date_display: '300 CE', images: [], tags: ['Roman'] },
          ],
        });
      }
      return Promise.resolve({ data: [] });
    });

    // Act: Click the fused cluster marker (contains IDs 4 and 61)
    const clusterButton = screen.getByRole('button', { name: /2 artifacts in Ostia, Rome & Rome/i });
    fireEvent.click(clusterButton);

    // Assert: SearchPage renders with ids=4,61 active filter pill and sidebar Map Selection card
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        '/objects/search',
        expect.objectContaining({
          params: expect.objectContaining({ ids: '4,61' }),
        })
      );
    });
    expect(screen.getByText(/Map Cluster: Ostia, Rome & Rome \(2 artifacts\)/i)).toBeInTheDocument();
    expect(screen.getByText('Map Selection')).toBeInTheDocument();

    // Act 2: Clear the map cluster filter from active pill and verify Search re-queries without ids
    fireEvent.click(screen.getByRole('button', { name: 'Remove map cluster filter' }));
    await waitFor(() => {
      const searchCalls = api.get.mock.calls.filter(([url]) => url === '/objects/search');
      const lastCallParams = searchCalls[searchCalls.length - 1][1].params;
      expect(lastCallParams.ids).toBeUndefined();
    });
  });

  it('edge_zoomingInSeparatesClusteredMarkers', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({
      data: [
        { id: 4, name: 'Ostia Sarcophagus', findspot: 'Ostia, Rome', latitude: 41.7558, longitude: 12.2906 },
        { id: 61, name: 'Rome Roundel', findspot: 'Rome', latitude: 41.9028, longitude: 12.4964 },
      ],
    });

    render(
      <MemoryRouter initialEntries={['/map']}>
        <MapVisualizer />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByTestId('map-marker')).toHaveLength(1);
    });

    // Act: Simulate Leaflet zoomend event to zoom level 12
    act(() => {
      zoomHandlers.zoomend({ target: { getZoom: () => 12 } });
    });

    // Assert: Cluster splits into two individual markers
    await waitFor(() => {
      expect(screen.getAllByTestId('map-marker')).toHaveLength(2);
    });
  });
});
