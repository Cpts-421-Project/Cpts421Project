/**
 * Frontend unit & integration tests for Admin ReviewPage image display,
 * lightbox inspection, automatic museum image recovery, and error handling.
 * Covers Normal, Edge, and Extraordinary cases following AAA pattern.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ReviewPage from '../pages/ReviewPage';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
  },
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ isAdmin: true }),
}));

beforeEach(() => {
  vi.clearAllMocks();

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

describe('ReviewPage', () => {
  it('normal_rendersImagesWithNoReferrerOpensLightboxAndBlocksShortcutsWhileInspecting', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 101,
          object_type: 'Roman Glass Beaker',
          inventory_number: '1981.11',
          material: 'Mold-blown glass',
          findspot: 'Rome',
          present_location: 'The Art Institute of Chicago, Chicago',
          date_display: '1st century CE',
          date_start: 1,
          date_end: 100,
          description: 'Beaker with geometric pattern.',
          external_url: 'https://www.artic.edu/artworks/61600',
          images: [
            {
              id: 501,
              db_identifier: '101.1',
              image_type: 'Colour photo',
              view_type: 'Front',
              source_identifier: 'AIC 1981.11',
              source_citation: 'The Art Institute of Chicago.',
              file_url: '/api/images/aic_1981_11.jpg',
            },
          ],
        },
      ],
    });

    render(
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    );

    // Act & Assert: image renders with no-referrer policy
    const img = await screen.findByAltText('Roman Glass Beaker - Front');
    expect(img).toHaveAttribute('src', '/api/images/aic_1981_11.jpg');
    expect(img).toHaveAttribute('referrerpolicy', 'no-referrer');
    expect(screen.getByText('101.1')).toBeInTheDocument();

    // Open ImageLightbox by clicking image preview
    fireEvent.click(screen.getByRole('button', { name: /Inspect Roman Glass Beaker image 1/i }));
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalledTimes(1);

    // Spacebar inside lightbox must NOT trigger accept API mutations
    fireEvent.keyDown(window, { code: 'Space' });
    expect(api.put).not.toHaveBeenCalled();
    expect(api.patch).not.toHaveBeenCalled();
  });

  it('edge_autoRecoversEmptyMuseumImageOnceAndRendersPlaceholderWithoutMuseumProvenance', async () => {
    // Arrange: Item 1 has empty file_url + V&A provenance; Item 2 has empty file_url without provenance
    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 201,
          object_type: 'Facet-cut Glass Cup',
          inventory_number: 'C.58-1963',
          date_display: '6th century CE',
          date_start: 500,
          date_end: 599,
          external_url: 'https://collections.vam.ac.uk/item/O5328',
          images: [
            {
              id: 601,
              image_type: 'Colour photo',
              view_type: 'Front',
              source_identifier: 'V&A O5328 / 2006AF6997',
              file_url: '',
            },
          ],
        },
        {
          id: 202,
          object_type: 'Manual Unphotographed Vessel',
          inventory_number: 'MAN-202',
          date_display: '4th century CE',
          date_start: 300,
          date_end: 399,
          external_url: null,
          images: [
            {
              id: 602,
              image_type: 'Line drawing',
              view_type: 'Full',
              file_url: '',
            },
          ],
        },
      ],
    });

    api.post.mockResolvedValueOnce({
      data: {
        id: 201,
        object_type: 'Facet-cut Glass Cup',
        inventory_number: 'C.58-1963',
        date_display: '6th century CE',
        date_start: 500,
        date_end: 599,
        external_url: 'https://collections.vam.ac.uk/item/O5328',
        images: [
          {
            id: 601,
            image_type: 'Colour photo',
            view_type: 'Front',
            source_identifier: 'V&A O5328 / 2006AF6997',
            file_url: 'https://framemark.vam.ac.uk/collections/2006AF6997/full/!800,800/0/default.jpg',
          },
        ],
      },
    });

    render(
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    );

    // Assert Item 1 triggers automatic recovery once and renders the recovered image
    const recoveredImg = await screen.findByAltText('Facet-cut Glass Cup - Front');
    expect(recoveredImg).toHaveAttribute(
      'src',
      'https://framemark.vam.ac.uk/collections/2006AF6997/full/!800,800/0/default.jpg'
    );
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(api.post).toHaveBeenCalledWith('/objects/201/recover-images');

    // Act: Skip to Item 2 (no museum provenance)
    fireEvent.click(screen.getByRole('button', { name: 'Skip' }));

    // Assert Item 2 shows clean placeholder instead of <img src=""> and does not call recover-images
    const placeholder = await screen.findByAltText('Image pending upload');
    expect(placeholder).toHaveAttribute('src', '/placeholder-artifact.svg');
    expect(placeholder.parentElement).toHaveTextContent('Image Pending Upload');
    expect(api.post).toHaveBeenCalledTimes(1);
  });

  it('extraordinary_handlesBrokenImageFallbackWithoutLeakingAcrossItemsAndDisplaysFetchErrors', async () => {
    // Arrange: Item 1 has a broken URL; Item 2 has a valid URL
    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 301,
          object_type: 'Broken Image Artifact',
          inventory_number: 'BRK-1',
          date_display: '200 CE',
          date_start: 200,
          date_end: 200,
          images: [
            {
              id: 701,
              image_type: 'Colour photo',
              view_type: 'Front',
              file_url: '/api/images/missing_file.jpg',
            },
          ],
        },
        {
          id: 302,
          object_type: 'Healthy Second Artifact',
          inventory_number: 'OK-2',
          date_display: '300 CE',
          date_start: 300,
          date_end: 300,
          images: [
            {
              id: 702,
              image_type: 'Colour photo',
              view_type: 'Front',
              file_url: '/api/images/valid_second.jpg',
            },
          ],
        },
      ],
    });

    const { unmount } = render(
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    );

    // Act 1: Trigger onError on Item 1 image -> swaps cleanly to placeholder + "Image Unavailable"
    const firstImg = await screen.findByAltText('Broken Image Artifact - Front');
    fireEvent.error(firstImg);

    await waitFor(() => {
      expect(screen.getByText('Image Unavailable')).toBeInTheDocument();
    });
    expect(screen.getByAltText('Image unavailable')).toHaveAttribute('src', '/placeholder-artifact.svg');

    // Act 2: Skip to Item 2 -> error state must not suppress Item 2's valid image
    fireEvent.click(screen.getByRole('button', { name: 'Skip' }));
    const secondImg = await screen.findByAltText('Healthy Second Artifact - Front');
    expect(secondImg).toHaveAttribute('src', '/api/images/valid_second.jpg');
    expect(screen.queryByText('Image Unavailable')).not.toBeInTheDocument();

    // Act 3: Pending fetch error renders visible role="alert"
    unmount();
    api.get.mockRejectedValueOnce({ response: { data: { detail: 'Review queue unavailable' } } });
    render(
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('Review queue unavailable');
  });

  it('normal_quickKeyboardShortcutsAcceptDenyUndoSkipPrevZoomAndToggleKeyDialog', async () => {
    // Arrange
    const items = [
      {
        id: 1,
        object_type: 'Item One',
        inventory_number: 'INV-1',
        date_display: '100 CE',
        date_start: 100,
        date_end: 100,
        images: [{ id: 11, image_type: 'Colour photo', view_type: 'Front', file_url: '/api/images/1.jpg' }],
      },
      {
        id: 2,
        object_type: 'Item Two',
        inventory_number: 'INV-2',
        date_display: '200 CE',
        date_start: 200,
        date_end: 200,
        images: [{ id: 21, image_type: 'Colour photo', view_type: 'Front', file_url: '/api/images/2.jpg' }],
      },
      {
        id: 3,
        object_type: 'Item Three',
        inventory_number: 'INV-3',
        date_display: '300 CE',
        date_start: 300,
        date_end: 300,
        images: [{ id: 31, image_type: 'Colour photo', view_type: 'Front', file_url: '/api/images/3.jpg' }],
      },
    ];
    api.get.mockResolvedValue({ data: items });
    api.put.mockResolvedValue({ data: {} });
    api.patch.mockResolvedValue({ data: {} });

    render(
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    );

    await screen.findByDisplayValue('Item One');

    // Compact shortcut key bar with semantic <kbd> tags is visible immediately
    const shortcutAside = screen.getByRole('complementary', { name: 'Keyboard shortcuts' });
    expect(shortcutAside.querySelectorAll('kbd').length).toBeGreaterThanOrEqual(6);

    // Act 1: 's' skips to Item Two, 'ArrowLeft' returns to Item One
    fireEvent.keyDown(window, { key: 's', code: 'KeyS' });
    expect(await screen.findByDisplayValue('Item Two')).toBeInTheDocument();
    fireEvent.keyDown(window, { key: 'ArrowLeft', code: 'ArrowLeft' });
    expect(await screen.findByDisplayValue('Item One')).toBeInTheDocument();

    // Act 2: 'z' opens ImageLightbox
    fireEvent.keyDown(window, { key: 'z', code: 'KeyZ' });
    const lightboxDialog = document.querySelector('dialog.image-lightbox');
    expect(lightboxDialog).toHaveAttribute('open');
    fireEvent.click(screen.getByLabelText('Close image viewer'));
    expect(lightboxDialog).not.toHaveAttribute('open');

    // Act 3: 'a' accepts Item One and advances to Item Two
    fireEvent.keyDown(window, { key: 'a', code: 'KeyA' });
    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/objects/1', expect.objectContaining({ object_type: 'Item One' }));
      expect(api.patch).toHaveBeenCalledWith('/objects/1/review', { status: 'accepted' });
    });
    expect(await screen.findByDisplayValue('Item Two')).toBeInTheDocument();

    // Act 4: 'd' denies Item Two, advances to Item Three, and populates Undo stack
    fireEvent.keyDown(window, { key: 'd', code: 'KeyD' });
    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/objects/2', expect.objectContaining({ object_type: 'Item Two' }));
      expect(api.patch).toHaveBeenCalledWith('/objects/2/review', { status: 'rejected' });
    });
    expect(await screen.findByDisplayValue('Item Three')).toBeInTheDocument();

    // Act 5: 'u' restores last denied item (Item Two) and reloads queue
    fireEvent.keyDown(window, { key: 'u', code: 'KeyU' });
    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/objects/2/review', { status: 'pending' });
      expect(api.get).toHaveBeenCalledTimes(2);
    });

    // Act 6: '?' opens and closes the full Shortcut Key <dialog>
    const shortcutHeading = screen.getByText('Review Queue Keyboard Shortcuts');
    const shortcutDialog = shortcutHeading.closest('dialog');
    expect(shortcutDialog).not.toHaveAttribute('open');
    fireEvent.keyDown(window, { key: '?', shiftKey: true });
    expect(shortcutDialog).toHaveAttribute('open');
    fireEvent.keyDown(window, { key: '?', shiftKey: true });
    expect(shortcutDialog).not.toHaveAttribute('open');
  });

  it('edge_pausesShortcutsInInputsBlursOnEscIgnoresButtonSpaceEnterAndGuardsOpenShortcutDialog', async () => {
    // Arrange
    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 10,
          object_type: 'Lamp',
          inventory_number: 'L-10',
          date_display: '150 CE',
          date_start: 150,
          date_end: 150,
          images: [{ id: 100, file_url: '/api/images/lamp.jpg' }],
        },
      ],
    });

    render(
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    );

    const typeInput = await screen.findByDisplayValue('Lamp');

    // Act 1: Typing a/d/s inside an input does NOT trigger review shortcuts
    typeInput.focus();
    expect(document.activeElement).toBe(typeInput);
    fireEvent.keyDown(typeInput, { key: 'a', code: 'KeyA' });
    fireEvent.keyDown(typeInput, { key: 'd', code: 'KeyD' });
    fireEvent.keyDown(typeInput, { key: 's', code: 'KeyS' });
    expect(api.put).not.toHaveBeenCalled();
    expect(api.patch).not.toHaveBeenCalled();

    // Act 2: Escape inside input blurs the field
    fireEvent.keyDown(typeInput, { key: 'Escape', code: 'Escape' });
    expect(document.activeElement).not.toBe(typeInput);

    // Act 3: Space / Enter on focused button does NOT fire window shortcuts
    const skipBtn = screen.getByRole('button', { name: 'Skip' });
    skipBtn.focus();
    fireEvent.keyDown(skipBtn, { key: ' ', code: 'Space' });
    fireEvent.keyDown(skipBtn, { key: 'Enter', code: 'Enter' });
    expect(api.put).not.toHaveBeenCalled();
    expect(api.patch).not.toHaveBeenCalled();
    expect(screen.getByDisplayValue('Lamp')).toBeInTheDocument();

    // Act 4: When Shortcut Key <dialog> is open, a/d/s do NOT trigger actions
    fireEvent.click(screen.getByRole('button', { name: /All Shortcuts/i }));
    const shortcutDialog = screen.getByText('Review Queue Keyboard Shortcuts').closest('dialog');
    expect(shortcutDialog).toHaveAttribute('open');
    fireEvent.keyDown(window, { key: 'a', code: 'KeyA' });
    fireEvent.keyDown(window, { key: 'd', code: 'KeyD' });
    fireEvent.keyDown(window, { key: 's', code: 'KeyS' });
    expect(api.put).not.toHaveBeenCalled();
    expect(api.patch).not.toHaveBeenCalled();
    expect(screen.getByDisplayValue('Lamp')).toBeInTheDocument();
  });

  it('extraordinary_ignoresModifierChordsAutoRepeatsAndBoundaryNoOps', async () => {
    // Arrange: Single item at index 0 with empty undo stack and zero images
    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 20,
          object_type: 'Plain Shard',
          inventory_number: 'PS-20',
          date_display: '250 CE',
          date_start: 250,
          date_end: 250,
          images: [],
        },
      ],
    });

    render(
      <MemoryRouter>
        <ReviewPage />
      </MemoryRouter>
    );

    await screen.findByDisplayValue('Plain Shard');

    // Act: Modifier chords and key auto-repeat are ignored
    fireEvent.keyDown(window, { key: 'a', code: 'KeyA', ctrlKey: true });
    fireEvent.keyDown(window, { key: 'd', code: 'KeyD', metaKey: true });
    fireEvent.keyDown(window, { key: 's', code: 'KeyS', altKey: true });
    fireEvent.keyDown(window, { key: ' ', code: 'Space', repeat: true });

    // Act: Boundary no-ops (u with empty stack, ArrowLeft at index 0, z with zero images)
    fireEvent.keyDown(window, { key: 'u', code: 'KeyU' });
    fireEvent.keyDown(window, { key: 'ArrowLeft', code: 'ArrowLeft' });
    fireEvent.keyDown(window, { key: 'z', code: 'KeyZ' });

    // Assert
    expect(api.put).not.toHaveBeenCalled();
    expect(api.patch).not.toHaveBeenCalled();
    expect(HTMLDialogElement.prototype.showModal).not.toHaveBeenCalled();
    expect(screen.getByDisplayValue('Plain Shard')).toBeInTheDocument();
  });
});
