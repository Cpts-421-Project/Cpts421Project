import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import useObject from '../hooks/useObject';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import ImageLightbox from '../components/ImageLightbox';
import ConfirmDialog from '../components/ConfirmDialog';

const formatMeasurement = (val, unit) => {
    if (val === null || val === undefined || val === '') return 'N/A';
    return `${val} ${unit || 'cm'}`;
};

const formatInscriptionPresence = (flag) => {
    if (flag === true) return 'Yes';
    if (flag === false) return 'No';
    return 'Not recorded';
};

const ObjectPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { object, loading, error } = useObject(id);
    const { isAdmin } = useAuth();

    const [activeImageIdx, setActiveImageIdx] = useState(0);
    const [lightboxOpen, setLightboxOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState('');
    const [deleteSessionExpired, setDeleteSessionExpired] = useState(false);

    useEffect(() => {
        setActiveImageIdx(0);
        setLightboxOpen(false);
        setDeleteDialogOpen(false);
        setDeleting(false);
        setDeleteError('');
        setDeleteSessionExpired(false);
    }, [id]);

    const handleOpenDeleteDialog = () => {
        setDeleteError('');
        setDeleteSessionExpired(false);
        setDeleteDialogOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (deleting) return;
        const targetId = object?.id ?? id;
        if (targetId === undefined || targetId === null || targetId === '') {
            setDeleteDialogOpen(false);
            setDeleteError('Unable to delete artifact: missing artifact identifier.');
            return;
        }

        setDeleting(true);
        setDeleteError('');
        setDeleteSessionExpired(false);

        try {
            const response = await api.delete(`/objects/${targetId}`);
            if (
                response &&
                response.status !== undefined &&
                response.status !== 204 &&
                (response.status < 200 || response.status >= 300)
            ) {
                throw new Error(`Unexpected response status: ${response.status}`);
            }
            setDeleteDialogOpen(false);
            navigate('/search', {
                replace: true,
                state: { deletedArtifactTitle: object?.object_type || 'Artifact' },
            });
        } catch (err) {
            const statusCode = err?.response?.status;
            const detail = err?.response?.data?.detail || err?.message || 'Unable to delete artifact.';
            setDeleteDialogOpen(false);
            if (statusCode === 401) {
                setDeleteSessionExpired(true);
                setDeleteError('Your admin session has expired. Please log in again and retry deleting this artifact.');
            } else if (statusCode === 403) {
                setDeleteError('You do not have administrator privileges to delete this artifact.');
            } else {
                setDeleteError(`Failed to delete artifact: ${detail}`);
            }
        } finally {
            setDeleting(false);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading object details...</div>;
    if (error) return <div className="p-8 text-center text-red-500">Error loading object.</div>;
    if (!object) return <div className="p-8 text-center text-gray-500">Object not found.</div>;

    const images = object.images || [];
    const safeIdx = images.length > 0 ? Math.min(activeImageIdx, images.length - 1) : 0;
    const activeImage = images[safeIdx] || null;
    const hasActiveImageUrl = Boolean(activeImage?.file_url && activeImage.file_url.trim() !== '');
    const hasInscriptionSection =
        object.inscription_present !== null && object.inscription_present !== undefined ||
        Boolean(object.inscription_1) ||
        Boolean(object.inscription_2);

    return (
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
            <div className="max-w-5xl mx-auto bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-6 border-b border-gray-200 flex flex-wrap justify-between items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">{object.object_type}</h1>
                        {object.present_location && (
                            <p className="text-sm text-gray-600 mt-1">{object.present_location}</p>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        {isAdmin && (
                            <>
                                <button
                                    type="button"
                                    onClick={() => navigate(`/objects/${id}/edit`)}
                                    className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                                >
                                    Edit
                                </button>
                                <button
                                    type="button"
                                    onClick={handleOpenDeleteDialog}
                                    disabled={deleting}
                                    aria-haspopup="dialog"
                                    className="px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 disabled:opacity-50"
                                >
                                    {deleting ? 'Deleting...' : 'Delete'}
                                </button>
                            </>
                        )}
                        <button
                            type="button"
                            onClick={() => navigate(-1)}
                            className="text-sm font-medium text-gray-600 hover:text-gray-900"
                        >
                            Back
                        </button>
                    </div>
                </div>

                {deleteError && (
                    <div
                        role="alert"
                        className="mx-6 mt-4 p-4 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800 flex flex-wrap items-center justify-between gap-3"
                    >
                        <div className="flex flex-wrap items-center gap-2">
                            <span>{deleteError}</span>
                            {deleteSessionExpired && (
                                <Link to="/login" className="font-semibold underline text-red-900 hover:text-red-950">
                                    Log in
                                </Link>
                            )}
                        </div>
                        <button
                            type="button"
                            onClick={() => {
                                setDeleteError('');
                                setDeleteSessionExpired(false);
                            }}
                            aria-label="Dismiss error"
                            className="text-xs font-semibold text-red-800 hover:text-red-950 underline"
                        >
                            Dismiss
                        </button>
                    </div>
                )}

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Images & Image Provenance Section */}
                    <div className="space-y-4">
                        {images.length > 0 ? (
                            <>
                                <div className="rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
                                    {hasActiveImageUrl ? (
                                        <div className="relative group">
                                            <button
                                                type="button"
                                                onClick={() => setLightboxOpen(true)}
                                                aria-label="Inspect and zoom image"
                                                className="block w-full text-left cursor-zoom-in focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            >
                                                <img
                                                    src={activeImage.file_url}
                                                    alt={`${object.object_type} - ${activeImage.view_type || 'View'}`}
                                                    className="w-full h-auto object-contain min-h-[300px] max-h-[460px] mx-auto"
                                                    referrerPolicy="no-referrer"
                                                    onError={(e) => {
                                                        e.target.onerror = null;
                                                        e.target.src = '/placeholder-artifact.svg';
                                                    }}
                                                />
                                            </button>
                                            <div className="flex items-center justify-between px-3 py-2 bg-white border-t border-gray-200 text-xs text-gray-600">
                                                <span>
                                                    {activeImage.db_identifier && (
                                                        <strong className="text-gray-900 mr-2">ID {activeImage.db_identifier}</strong>
                                                    )}
                                                    {[activeImage.image_type, activeImage.view_type].filter(Boolean).join(' · ')}
                                                </span>
                                                <button
                                                    type="button"
                                                    onClick={() => setLightboxOpen(true)}
                                                    className="px-2.5 py-1 font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded"
                                                >
                                                    Zoom / Inspect
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="p-6 text-center bg-gray-50 min-h-[260px] flex flex-col items-center justify-center space-y-2">
                                            <img
                                                src="/placeholder-artifact.svg"
                                                alt="Image pending upload"
                                                className="w-40 h-28 object-contain opacity-90"
                                            />
                                            <p className="text-sm font-semibold text-gray-700">Image Pending Upload</p>
                                            <p className="text-xs text-gray-500">
                                                {activeImage.db_identifier && `ID ${activeImage.db_identifier} · `}
                                                {[activeImage.image_type, activeImage.view_type].filter(Boolean).join(' · ')}
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {/* Multi-image Thumbnail Strip */}
                                {images.length > 1 && (
                                    <div className="flex gap-2 overflow-x-auto pb-1">
                                        {images.map((img, idx) => {
                                            const isSelected = idx === safeIdx;
                                            return (
                                                <button
                                                    key={img.id || idx}
                                                    type="button"
                                                    onClick={() => setActiveImageIdx(idx)}
                                                    className={`flex-shrink-0 w-24 rounded-md border overflow-hidden text-left transition ${
                                                        isSelected
                                                            ? 'border-blue-600 ring-2 ring-blue-200'
                                                            : 'border-gray-200 hover:border-gray-400'
                                                    }`}
                                                >
                                                    <img
                                                        src={img.file_url || '/placeholder-artifact.svg'}
                                                        alt={`${object.object_type} ${img.db_identifier || idx + 1}`}
                                                        className="w-full h-16 object-cover bg-gray-100"
                                                        onError={(e) => {
                                                            e.target.onerror = null;
                                                            e.target.src = '/placeholder-artifact.svg';
                                                        }}
                                                    />
                                                    <div className="px-1.5 py-1 bg-white text-[11px] leading-tight">
                                                        <p className="font-semibold text-gray-900 truncate">
                                                            {img.db_identifier || `${object.id}.${idx + 1}`}
                                                        </p>
                                                        <p className="text-gray-500 truncate">{img.image_type || 'Image'}</p>
                                                    </div>
                                                </button>
                                            );
                                        })}
                                    </div>
                                )}

                                {/* Active Image Source Metadata */}
                                {activeImage && (
                                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3.5 text-xs space-y-1.5">
                                        <h2 className="font-semibold text-gray-700 uppercase tracking-wider">
                                            Active Image Provenance
                                        </h2>
                                        <p className="text-gray-800">
                                            <span className="text-gray-500">Database ID:</span>{' '}
                                            <span className="font-medium">{activeImage.db_identifier || `${object.id}.${safeIdx + 1}`}</span>
                                        </p>
                                        <p className="text-gray-800">
                                            <span className="text-gray-500">Drawing / Photo Type:</span>{' '}
                                            <span className="font-medium">
                                                {[activeImage.image_type, activeImage.view_type].filter(Boolean).join(' · ') || 'N/A'}
                                            </span>
                                        </p>
                                        {activeImage.source_identifier && (
                                            <p className="text-gray-800">
                                                <span className="text-gray-500">Source Identifier #:</span>{' '}
                                                <span className="font-medium">{activeImage.source_identifier}</span>
                                            </p>
                                        )}
                                        {activeImage.source_citation && (
                                            <p className="text-gray-800">
                                                <span className="text-gray-500">Image Source:</span>{' '}
                                                <span>{activeImage.source_citation}</span>
                                            </p>
                                        )}
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="flex items-center justify-center h-64 bg-gray-100 rounded text-gray-400">
                                No Images Available
                            </div>
                        )}
                    </div>

                    {/* Metadata Section */}
                    <div className="space-y-6">
                        {object.assembled_caption && (
                            <div className="rounded-lg bg-slate-50 border border-slate-200 p-4">
                                <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                                    Caption
                                </h2>
                                <p className="text-sm text-slate-900 leading-relaxed">{object.assembled_caption}</p>
                            </div>
                        )}

                        {object.description && (
                            <div>
                                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Description</h2>
                                <p className="text-gray-900 text-sm leading-relaxed">{object.description}</p>
                            </div>
                        )}

                        <div>
                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                Collection &amp; Geographic Provenance
                            </h2>
                            <dl className="grid grid-cols-1 gap-y-2 text-sm">
                                <div className="grid grid-cols-3 gap-2">
                                    <dt className="text-gray-500">Present Location</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.present_location || 'Not recorded'}</dd>
                                </div>
                                {object.inventory_number && (
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Inventory #</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">{object.inventory_number}</dd>
                                    </div>
                                )}
                                <div className="grid grid-cols-3 gap-2">
                                    <dt className="text-gray-500">Findspot</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.findspot || 'Unknown'}</dd>
                                </div>
                                {object.production_location && (
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Production Site</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">{object.production_location}</dd>
                                    </div>
                                )}
                                {object.object_group && (
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Group / Hoard</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">{object.object_group}</dd>
                                    </div>
                                )}
                            </dl>
                        </div>

                        <div>
                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Dating</h2>
                            <dl className="grid grid-cols-1 gap-y-2 text-sm">
                                <div className="grid grid-cols-3 gap-2">
                                    <dt className="text-gray-500">Date Assigned</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.date_display}</dd>
                                </div>
                                {object.date_basis && (
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Date Basis</dt>
                                        <dd className="col-span-2 text-gray-800">{object.date_basis}</dd>
                                    </div>
                                )}
                            </dl>
                        </div>

                        <div>
                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                Physical Description
                            </h2>
                            <dl className="grid grid-cols-1 gap-y-2 text-sm">
                                <div className="grid grid-cols-3 gap-2">
                                    <dt className="text-gray-500">Material(s)</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{object.material || 'N/A'}</dd>
                                </div>
                                {object.dimensions_display && (
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Dimensions</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">{object.dimensions_display}</dd>
                                    </div>
                                )}
                                <div className="grid grid-cols-3 gap-2">
                                    <dt className="text-gray-500">Height</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{formatMeasurement(object.height, object.unit)}</dd>
                                </div>
                                <div className="grid grid-cols-3 gap-2">
                                    <dt className="text-gray-500">Width</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{formatMeasurement(object.width, object.unit)}</dd>
                                </div>
                                <div className="grid grid-cols-3 gap-2">
                                    <dt className="text-gray-500">Depth</dt>
                                    <dd className="col-span-2 font-medium text-gray-900">{formatMeasurement(object.depth, object.unit)}</dd>
                                </div>
                                {object.weight && (
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Weight</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">{object.weight}</dd>
                                    </div>
                                )}
                                {object.completeness && (
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Completeness</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">{object.completeness}</dd>
                                    </div>
                                )}
                            </dl>
                        </div>

                        {hasInscriptionSection && (
                            <div>
                                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Inscriptions</h2>
                                <dl className="grid grid-cols-1 gap-y-2 text-sm">
                                    <div className="grid grid-cols-3 gap-2">
                                        <dt className="text-gray-500">Present?</dt>
                                        <dd className="col-span-2 font-medium text-gray-900">
                                            {formatInscriptionPresence(object.inscription_present)}
                                        </dd>
                                    </div>
                                    {object.inscription_1 && (
                                        <div className="grid grid-cols-3 gap-2">
                                            <dt className="text-gray-500">Inscription 1</dt>
                                            <dd className="col-span-2 text-gray-900">{object.inscription_1}</dd>
                                        </div>
                                    )}
                                    {object.inscription_2 && (
                                        <div className="grid grid-cols-3 gap-2">
                                            <dt className="text-gray-500">Inscription 2</dt>
                                            <dd className="col-span-2 text-gray-900">{object.inscription_2}</dd>
                                        </div>
                                    )}
                                </dl>
                            </div>
                        )}

                        {/* Tags */}
                        {object.tags && object.tags.length > 0 && (
                            <div>
                                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Tags</h2>
                                <div className="flex flex-wrap gap-2">
                                    {object.tags.map((tag) => (
                                        <span
                                            key={tag}
                                            className="inline-block px-3 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded-full border border-blue-200"
                                        >
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Image Discussions & Publications */}
                        {object.publications && (
                            <div>
                                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                    Image Discussions &amp; Publications
                                </h2>
                                <p className="text-sm text-gray-700 leading-relaxed">{object.publications}</p>
                            </div>
                        )}

                        {/* Image Sources (Chicago Style) */}
                        {object.bibliography && object.bibliography.length > 0 && (
                            <div>
                                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                    Image Sources (Chicago Style)
                                </h2>
                                <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                                    {object.bibliography.map((ref, idx) => (
                                        <li key={idx}>{ref}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <ImageLightbox
                isOpen={lightboxOpen}
                images={images}
                activeIndex={safeIdx}
                objectTitle={object.object_type}
                onClose={() => setLightboxOpen(false)}
                onSelectIndex={setActiveImageIdx}
            />

            {isAdmin && (
                <ConfirmDialog
                    isOpen={deleteDialogOpen}
                    title="Delete Artifact"
                    message={`Are you sure you want to permanently delete "${object.object_type}"? This action cannot be undone.`}
                    confirmLabel="Delete Artifact"
                    cancelLabel="Cancel"
                    submittingLabel="Deleting..."
                    isSubmitting={deleting}
                    onConfirm={handleConfirmDelete}
                    onCancel={() => {
                        if (!deleting) {
                            setDeleteDialogOpen(false);
                        }
                    }}
                />
            )}
        </main>
    );
};

export default ObjectPage;
