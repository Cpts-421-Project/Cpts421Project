/**
 * Frontend unit & component tests for 2_excel alignment, alphabetical tags,
 * configurable search sorting, 0-899 CE focus filtering, and ImageLightbox.
 * Covers Normal, Edge, and Extraordinary cases following AAA pattern.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ImageLightbox from '../components/ImageLightbox';
import FilterSidebar from '../components/FilterSidebar';
import SearchPage from '../pages/SearchPage';
import ObjectPage from '../pages/ObjectPage';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ isAdmin: false }),
}));

beforeEach(() => {
  vi.clearAllMocks();

  // Polyfill native <dialog> methods for happy-dom / jsdom test environments
  if (typeof HTMLDialogElement !== 'undefined') {
    HTMLDialogElement.prototype.showModal = vi.fn(function showModalMock() {
      this.setAttribute('open', '');
    });
    HTMLDialogElement.prototype.close = vi.fn(function closeMock() {
      this.removeAttribute('open');
      this.dispatchEvent(new Event('close'));
    });
  }
});

describe('ImageLightbox', () => {
  const sampleImages = [
    {
      id: 1,
      db_identifier: '61.1',
      image_type: 'Line drawing',
      view_type: 'Full',
      source_identifier: 'Kisa 1908, fig. 357',
      source_citation: 'Kisa, Anton. Das Glas im Altertume. 1908.',
      file_url: '/api/images/test1.jpg',
    },
    {
      id: 2,
      db_identifier: '61.2',
      image_type: 'b+w photo',
      view_type: 'Full',
      source_identifier: 'Morey 1959, no. 96',
      source_citation: 'Morey, Charles Rufus. Gold-Glass Collection. 1959.',
      file_url: '/api/images/test2.jpg',
    },
  ];

  it('normal_rendersNativeDialogZoomsInOutResetsAndSwitchesImages', () => {
    const onClose = vi.fn();
    const onSelectIndex = vi.fn();

    render(
      <ImageLightbox
        isOpen={true}
        images={sampleImages}
        activeIndex={0}
        objectTitle="Roundel with gold-glass"
        onClose={onClose}
        onSelectIndex={onSelectIndex}
      />
    );

    const dialog = document.querySelector('dialog');
    expect(dialog).not.toBeNull();
    expect(dialog).not.toHaveAttribute('role');
    expect(dialog).not.toHaveAttribute('aria-modal');
    expect(screen.getByTestId('lightbox-zoom-level')).toHaveTextContent('100%');

    fireEvent.click(screen.getByLabelText('Zoom in'));
    expect(screen.getByTestId('lightbox-zoom-level')).toHaveTextContent('150%');

    fireEvent.click(screen.getByLabelText('Zoom out'));
    expect(screen.getByTestId('lightbox-zoom-level')).toHaveTextContent('100%');

    fireEvent.click(screen.getByLabelText('Zoom in'));
    fireEvent.click(screen.getByLabelText('Reset zoom'));
    expect(screen.getByTestId('lightbox-zoom-level')).toHaveTextContent('100%');

    fireEvent.click(screen.getByLabelText('Next image'));
    expect(onSelectIndex).toHaveBeenCalledWith(1);

    fireEvent.click(screen.getByLabelText('Close image viewer'));
    expect(onClose).toHaveBeenCalled();
  });

  it('edge_pendingUploadImage_rendersPlaceholderAndDisablesZoom', () => {
    render(
      <ImageLightbox
        isOpen={true}
        images={[{ id: 3, db_identifier: '61.3', image_type: 'Colour photo', file_url: '' }]}
        activeIndex={0}
        objectTitle="Roundel with gold-glass"
        onClose={vi.fn()}
        onSelectIndex={vi.fn()}
      />
    );

    expect(screen.getByText('Image Pending Upload')).toBeInTheDocument();
    expect(screen.getByLabelText('Zoom in')).toBeDisabled();
  });
});

describe('FilterSidebar', () => {
  it('normal_sortsTagsAlphabeticallyAndApplies0To899Preset', async () => {
    api.get.mockResolvedValueOnce({ data: ['Workshop', 'arch', 'Roman', 'bronze'] });
    const onFilterChange = vi.fn();

    render(
      <FilterSidebar
        filters={{ search: '', selectedTags: [], startDate: null, endDate: null }}
        onFilterChange={onFilterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('arch')).toBeInTheDocument();
    });

    const tagCheckboxes = screen.getAllByRole('checkbox');
    const renderedLabels = tagCheckboxes.map((cb) => cb.parentElement.textContent.trim());
    expect(renderedLabels).toEqual(['arch', 'bronze', 'Roman', 'Workshop']);

    fireEvent.click(screen.getByRole('button', { name: /Filter to 0–899 CE Focus/i }));
    expect(onFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ startDate: 0, endDate: 899 })
    );
  });

  it('edge_preservesNumericZeroInStartDateInput', async () => {
    api.get.mockResolvedValueOnce({ data: [] });
    const onFilterChange = vi.fn();

    render(
      <FilterSidebar
        filters={{ search: '', selectedTags: [], startDate: 0, endDate: 899 }}
        onFilterChange={onFilterChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Start Year')).toHaveValue(0);
      expect(screen.getByLabelText('End Year')).toHaveValue(899);
    });
  });

  it('extraordinary_handlesTagFetchFailureGracefully', async () => {
    api.get.mockRejectedValueOnce(new Error('Network down'));

    render(
      <FilterSidebar
        filters={{ search: '', selectedTags: [], startDate: null, endDate: null }}
        onFilterChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Error loading tags.')).toBeInTheDocument();
    });
  });
});

describe('SearchPage Sorting & 0 CE Filter', () => {
  it('normal_requestsDefaultTitleAscSortAndSwitchesSortOptions', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/tags') return Promise.resolve({ data: ['Roman'] });
      if (url === '/objects/search') {
        return Promise.resolve({
          data: [
            {
              id: 1,
              object_type: 'Amphora',
              date_display: 'c. 100 CE',
              findspot: 'Rome',
              present_location: 'Met Museum',
              images: [],
              tags: ['Roman'],
            },
          ],
        });
      }
      return Promise.resolve({ data: [] });
    });

    render(
      <MemoryRouter initialEntries={['/search']}>
        <SearchPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        '/objects/search',
        expect.objectContaining({
          params: expect.objectContaining({ sort_by: 'title', sort_order: 'asc' }),
        })
      );
    });

    const sortSelect = screen.getByLabelText('Sort by');
    expect(sortSelect).toHaveValue('title:asc');

    fireEvent.change(sortSelect, { target: { value: 'date:asc' } });
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        '/objects/search',
        expect.objectContaining({
          params: expect.objectContaining({ sort_by: 'date', sort_order: 'asc' }),
        })
      );
    });
  });

  it('edge_displaysZeroInActiveYearsPillFor0To899CE', async () => {
    api.get.mockResolvedValue({ data: [] });

    render(
      <MemoryRouter initialEntries={['/search?date_start=0&date_end=899']}>
        <SearchPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Years: 0 – 899/i)).toBeInTheDocument();
    });
  });
});

describe('ObjectPage 2_excel Details', () => {
  it('normal_displaysCaptionCollectionMultiImageIdsPublicationsAndImageSources', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        id: 61,
        object_type: 'Roundel with gold-glass, fragment from a vessel',
        present_location: 'Museo Biblioteca Apostolica Vaticana, Vatican City',
        findspot: 'Rome',
        date_display: 'c. 4th century CE',
        date_start: 300,
        date_end: 399,
        date_basis: 'Not yet ascertained (= ?), see Kisa 1908',
        inventory_number: '60788',
        description: 'Six Craftworkers (and a patron?)',
        completeness: 'Fragmentary, broken at the edges',
        publications: 'Kisa 1908; Morey and Ferrari 1959, no. 96.',
        assembled_caption:
          'Six Craftworkers (and a patron?), Roundel with gold-glass, fragment from a vessel, Rome, c. 4th century CE, Museo Biblioteca Apostolica Vaticana, Vatican City, inv. 60788',
        bibliography: ['Kisa, Anton. Das Glas im Altertume. 1908.'],
        tags: ['Craftworkers', 'Roman'],
        images: [
          {
            id: 101,
            db_identifier: '61.1',
            image_type: 'Line drawing',
            view_type: 'Full',
            source_identifier: 'Kisa 1908, vol. III, fig. 357',
            source_citation: 'Kisa, Anton. Das Glas im Altertume. 1908.',
            file_url: '/api/images/sample_drawing.jpg',
          },
          {
            id: 102,
            db_identifier: '61.2',
            image_type: 'b+w photo',
            view_type: 'Full',
            source_identifier: 'Morey and Ferrari 1959, no. 96',
            source_citation: 'Morey and Ferrari. 1959.',
            file_url: '',
          },
        ],
      },
    });

    render(
      <MemoryRouter initialEntries={['/objects/61']}>
        <Routes>
          <Route path="/objects/:id" element={<ObjectPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Caption')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Six Craftworkers \(and a patron\?\), Roundel with gold-glass/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText('Museo Biblioteca Apostolica Vaticana, Vatican City').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Image Discussions & Publications')).toBeInTheDocument();
    expect(screen.getByText('Image Sources (Chicago Style)')).toBeInTheDocument();
    expect(screen.queryByText('Bibliography')).not.toBeInTheDocument();
    expect(screen.getAllByText('61.1').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('61.2').length).toBeGreaterThanOrEqual(1);

    fireEvent.click(screen.getByRole('button', { name: /Zoom \/ Inspect/i }));
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalled();
  });
});
