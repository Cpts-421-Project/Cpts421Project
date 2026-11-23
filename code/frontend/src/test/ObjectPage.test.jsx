/**
 * Frontend unit & component tests for admin artifact deletion flow on ObjectPage,
 * accessible ConfirmDialog, HTTP 204 handling, and SearchPage status confirmation.
 * Covers Normal, Edge, and Extraordinary cases following AAA pattern.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ObjectPage from '../pages/ObjectPage';
import SearchPage from '../pages/SearchPage';
import api from '../services/api';

let mockIsAdmin = true;

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ isAdmin: mockIsAdmin }),
}));

const sampleObject = {
  id: 61,
  object_type: 'Roundel with gold-glass',
  present_location: 'Museo Biblioteca Apostolica Vaticana, Vatican City',
  findspot: 'Rome',
  date_display: 'c. 4th century CE',
  date_start: 300,
  date_end: 399,
  material: 'Gold-glass',
  images: [],
  tags: ['Roman'],
  bibliography: [],
};

const renderObjectRoute = () =>
  render(
    <MemoryRouter initialEntries={['/objects/61']}>
      <Routes>
        <Route path="/objects/:id" element={<ObjectPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  vi.clearAllMocks();
  mockIsAdmin = true;

  if (typeof HTMLDialogElement !== 'undefined') {
    HTMLDialogElement.prototype.showModal = vi.fn(function showModalMock() {
      this.setAttribute('open', '');
    });
    HTMLDialogElement.prototype.close = vi.fn(function closeMock() {
      this.removeAttribute('open');
      this.dispatchEvent(new Event('close'));
    });
  }

  api.get.mockImplementation((url) => {
    if (url === '/objects/61') {
      return Promise.resolve({ data: sampleObject });
    }
    if (url === '/tags' || url === '/objects/search') {
      return Promise.resolve({ data: [] });
    }
    return Promise.resolve({ data: [] });
  });
});

describe('ObjectPage Admin Delete Flow', () => {
  it('normal_opensNativeDialogConfirmDeletesWith204AndShowsSearchStatus', async () => {
    // Arrange
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => false);
    api.delete.mockResolvedValueOnce({ status: 204, data: '' });

    renderObjectRoute();
    const deleteBtn = await screen.findByRole('button', { name: 'Delete' });

    // Act 1: Click Delete button -> opens accessible native <dialog> without window.confirm
    fireEvent.click(deleteBtn);

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalledTimes(1);

    const confirmDialogHeading = screen.getByRole('heading', { name: 'Delete Artifact' });
    const dialogEl = confirmDialogHeading.closest('dialog');
    expect(dialogEl).not.toBeNull();
    expect(dialogEl).not.toHaveAttribute('role');
    expect(dialogEl).not.toHaveAttribute('aria-modal');

    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    expect(document.activeElement).toBe(cancelBtn);

    // Act 2: Confirm permanent deletion
    fireEvent.click(screen.getByRole('button', { name: 'Delete Artifact' }));

    // Assert: API DELETE 204 handled and navigates to /search with confirmation notice
    await waitFor(() => {
      expect(api.delete).toHaveBeenCalledWith('/objects/61');
    });

    const statusBanner = await screen.findByRole('status');
    expect(statusBanner).toHaveTextContent('Deleted artifact "Roundel with gold-glass".');
    confirmSpy.mockRestore();
  });

  it('edge_cancelClosesWithoutDeleteAndNonAdminHidesDeleteAndInFlightDisablesRepeat', async () => {
    // Arrange & Act 1: Admin clicks Delete then Cancel
    renderObjectRoute();
    fireEvent.click(await screen.findByRole('button', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    // Assert 1: No delete request fired
    expect(api.delete).not.toHaveBeenCalled();

    // Act 2: Pending delete disables buttons and prevents Esc cancel dismissal
    let resolveDelete;
    api.delete.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveDelete = resolve;
        })
    );

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete Artifact' }));

    const deletingBtns = screen.getAllByRole('button', { name: 'Deleting...' });
    expect(deletingBtns).toHaveLength(2);
    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    deletingBtns.forEach((btn) => expect(btn).toBeDisabled());
    expect(cancelBtn).toBeDisabled();

    fireEvent.click(deletingBtns[1]);
    expect(api.delete).toHaveBeenCalledTimes(1);

    const dialogEl = screen.getByRole('heading', { name: 'Delete Artifact' }).closest('dialog');
    const cancelEvent = new Event('cancel', { cancelable: true });
    fireEvent(dialogEl, cancelEvent);
    expect(cancelEvent.defaultPrevented).toBe(true);

    resolveDelete({ status: 204, data: '' });
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Deleted artifact "Roundel with gold-glass".'
    );

    // Act 3: Non-admin view hides Delete button
    cleanup();
    mockIsAdmin = false;
    renderObjectRoute();
    await screen.findByRole('heading', { name: 'Roundel with gold-glass', level: 1 });
    expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
  });

  it('extraordinary_401And500And404ShowInlineAlertWithoutWindowAlert', async () => {
    // Arrange
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});

    // Act 1: 401 session expired
    api.delete.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Not authenticated' } },
      message: 'Request failed with status code 401',
    });

    renderObjectRoute();
    fireEvent.click(await screen.findByRole('button', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete Artifact' }));

    const expiredAlert = await screen.findByRole('alert');
    expect(expiredAlert).toHaveTextContent(/admin session has expired/i);
    expect(screen.getByRole('link', { name: 'Log in' })).toHaveAttribute('href', '/login');
    expect(alertSpy).not.toHaveBeenCalled();

    // Act 2: 500 backend error stays on object page and surfaces backend detail
    api.delete.mockRejectedValueOnce({
      response: { status: 500, data: { detail: 'Internal database error during deletion' } },
      message: 'Request failed with status code 500',
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete Artifact' }));

    const serverAlert = await screen.findByRole('alert');
    expect(serverAlert).toHaveTextContent('Internal database error during deletion');
    expect(screen.getByRole('heading', { name: 'Roundel with gold-glass' })).toBeInTheDocument();

    // Act 3: 404 object not found
    api.delete.mockRejectedValueOnce({
      response: { status: 404, data: { detail: 'Object not found (ID: 61)' } },
      message: 'Request failed with status code 404',
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete Artifact' }));

    const notFoundAlert = await screen.findByRole('alert');
    expect(notFoundAlert).toHaveTextContent('Object not found');
    expect(alertSpy).not.toHaveBeenCalled();

    alertSpy.mockRestore();
  });
});
