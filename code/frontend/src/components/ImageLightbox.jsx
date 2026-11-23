import { useEffect, useId, useRef, useState } from 'react';

const MIN_SCALE = 1;
const MAX_SCALE = 4;
const ZOOM_STEP = 0.5;

const ImageLightbox = ({
    isOpen,
    images = [],
    activeIndex = 0,
    objectTitle = 'Artifact Image',
    onClose,
    onSelectIndex,
}) => {
    const dialogRef = useRef(null);
    const dragStartRef = useRef(null);
    const headingId = useId();

    const [scale, setScale] = useState(MIN_SCALE);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);

    const safeIndex = images.length > 0 ? Math.min(Math.max(activeIndex, 0), images.length - 1) : 0;
    const currentImage = images[safeIndex] || null;
    const hasImageUrl = Boolean(currentImage?.file_url);

    // Reset zoom and pan when lightbox opens or active image changes
    useEffect(() => {
        setScale(MIN_SCALE);
        setPan({ x: 0, y: 0 });
        setIsDragging(false);
    }, [isOpen, safeIndex, currentImage?.file_url]);

    // Sync React isOpen prop with native <dialog> top-layer modal state
    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) return;

        if (isOpen) {
            if (!dialog.open && typeof dialog.showModal === 'function') {
                dialog.showModal();
            }
        } else if (dialog.open && typeof dialog.close === 'function') {
            dialog.close();
        }
    }, [isOpen]);

    // Safari fallback for light-dismiss when closedby="any" is unsupported
    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog || typeof HTMLDialogElement === 'undefined') return;
        if ('closedBy' in HTMLDialogElement.prototype) return;

        const isOutside = (event) => {
            const rect = dialog.getBoundingClientRect();
            return (
                event.clientX < rect.left ||
                event.clientX > rect.right ||
                event.clientY < rect.top ||
                event.clientY > rect.bottom
            );
        };

        let pressedOutside = false;
        const handlePointerDown = (event) => {
            pressedOutside = isOutside(event);
        };
        const handlePointerUp = (event) => {
            if (pressedOutside && isOutside(event) && dialog.open) {
                dialog.close();
            }
            pressedOutside = false;
        };

        dialog.addEventListener('pointerdown', handlePointerDown);
        dialog.addEventListener('pointerup', handlePointerUp);
        return () => {
            dialog.removeEventListener('pointerdown', handlePointerDown);
            dialog.removeEventListener('pointerup', handlePointerUp);
        };
    }, []);

    const handleNativeClose = () => {
        const dialog = dialogRef.current;
        if (dialog) {
            dialog.returnValue = '';
        }
        onClose?.();
    };

    const handleRequestClose = () => {
        const dialog = dialogRef.current;
        if (dialog && dialog.open && typeof dialog.close === 'function') {
            dialog.close();
        } else {
            onClose?.();
        }
    };

    const applyScale = (nextScale) => {
        const clamped = Math.min(MAX_SCALE, Math.max(MIN_SCALE, Number(nextScale.toFixed(2))));
        setScale(clamped);
        if (clamped <= MIN_SCALE) {
            setPan({ x: 0, y: 0 });
        }
    };

    const handleZoomIn = () => applyScale(scale + ZOOM_STEP);
    const handleZoomOut = () => applyScale(scale - ZOOM_STEP);
    const handleResetZoom = () => {
        setScale(MIN_SCALE);
        setPan({ x: 0, y: 0 });
    };

    const handleDoubleClick = () => {
        if (!hasImageUrl) return;
        if (scale > MIN_SCALE) {
            handleResetZoom();
        } else {
            applyScale(2.5);
        }
    };

    const handleWheel = (event) => {
        if (!hasImageUrl) return;
        event.preventDefault();
        const delta = event.deltaY < 0 ? 0.25 : -0.25;
        applyScale(scale + delta);
    };

    const handlePointerDown = (event) => {
        if (!hasImageUrl || scale <= MIN_SCALE || event.button !== 0) return;
        event.currentTarget.setPointerCapture?.(event.pointerId);
        dragStartRef.current = {
            x: event.clientX,
            y: event.clientY,
            panX: pan.x,
            panY: pan.y,
        };
        setIsDragging(true);
    };

    const handlePointerMove = (event) => {
        if (!isDragging || !dragStartRef.current) return;
        const dx = event.clientX - dragStartRef.current.x;
        const dy = event.clientY - dragStartRef.current.y;
        setPan({
            x: dragStartRef.current.panX + dx,
            y: dragStartRef.current.panY + dy,
        });
    };

    const handlePointerUp = () => {
        setIsDragging(false);
        dragStartRef.current = null;
    };

    const handlePrev = () => {
        if (images.length <= 1) return;
        const nextIdx = (safeIndex - 1 + images.length) % images.length;
        onSelectIndex?.(nextIdx);
    };

    const handleNext = () => {
        if (images.length <= 1) return;
        const nextIdx = (safeIndex + 1) % images.length;
        onSelectIndex?.(nextIdx);
    };

    const imageLabel = currentImage?.db_identifier
        ? `${objectTitle} (${currentImage.db_identifier})`
        : objectTitle;

    return (
        <dialog
            ref={dialogRef}
            closedby="any"
            aria-labelledby={headingId}
            onClose={handleNativeClose}
            className="image-lightbox m-auto w-[95vw] max-w-6xl h-[90vh] flex-col rounded-xl bg-slate-950 text-white shadow-2xl border border-slate-700 p-0 overflow-hidden"
        >
            {/* Header & Zoom Toolbar */}
            <header className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-slate-900 border-b border-slate-800">
                <div className="min-w-0">
                    <h2 id={headingId} className="text-sm sm:text-base font-semibold text-white truncate">
                        {imageLabel}
                    </h2>
                    {images.length > 1 && (
                        <p className="text-xs text-slate-400">
                            Image {safeIndex + 1} of {images.length}
                        </p>
                    )}
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                    <div className="inline-flex items-center rounded-lg bg-slate-800 border border-slate-700 p-0.5">
                        <button
                            type="button"
                            onClick={handleZoomOut}
                            disabled={!hasImageUrl || scale <= MIN_SCALE}
                            aria-label="Zoom out"
                            className="px-2.5 py-1 text-sm font-semibold rounded hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            −
                        </button>
                        <span
                            data-testid="lightbox-zoom-level"
                            className="px-2 text-xs font-mono text-slate-200 min-w-[3.25rem] text-center"
                        >
                            {Math.round(scale * 100)}%
                        </span>
                        <button
                            type="button"
                            onClick={handleZoomIn}
                            disabled={!hasImageUrl || scale >= MAX_SCALE}
                            aria-label="Zoom in"
                            className="px-2.5 py-1 text-sm font-semibold rounded hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            +
                        </button>
                        <button
                            type="button"
                            onClick={handleResetZoom}
                            disabled={!hasImageUrl || (scale === MIN_SCALE && pan.x === 0 && pan.y === 0)}
                            aria-label="Reset zoom"
                            className="px-2.5 py-1 text-xs font-medium border-l border-slate-700 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            Reset
                        </button>
                    </div>

                    {images.length > 1 && (
                        <div className="inline-flex items-center gap-1">
                            <button
                                type="button"
                                onClick={handlePrev}
                                aria-label="Previous image"
                                className="px-2.5 py-1 text-xs font-medium rounded bg-slate-800 border border-slate-700 hover:bg-slate-700"
                            >
                                Prev
                            </button>
                            <button
                                type="button"
                                onClick={handleNext}
                                aria-label="Next image"
                                className="px-2.5 py-1 text-xs font-medium rounded bg-slate-800 border border-slate-700 hover:bg-slate-700"
                            >
                                Next
                            </button>
                        </div>
                    )}

                    <button
                        type="button"
                        autoFocus
                        onClick={handleRequestClose}
                        aria-label="Close image viewer"
                        className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white"
                    >
                        Close
                    </button>
                </div>
            </header>

            {/* Zoomable / Pannable Viewport */}
            <div
                onWheel={handleWheel}
                onDoubleClick={handleDoubleClick}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onPointerCancel={handlePointerUp}
                className={`relative flex-1 overflow-hidden flex items-center justify-center bg-slate-950 select-none touch-none ${
                    hasImageUrl && scale > MIN_SCALE
                        ? isDragging
                            ? 'cursor-grabbing'
                            : 'cursor-grab'
                        : 'cursor-zoom-in'
                }`}
            >
                {hasImageUrl ? (
                    <img
                        src={currentImage.file_url}
                        alt={imageLabel}
                        draggable={false}
                        referrerPolicy="no-referrer"
                        style={{
                            transform: `translate3d(${pan.x}px, ${pan.y}px, 0) scale(${scale})`,
                            transition: isDragging ? 'none' : 'transform 150ms ease-out',
                        }}
                        className="max-h-full max-w-full object-contain will-change-transform"
                        onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = '/placeholder-artifact.svg';
                        }}
                    />
                ) : (
                    <div className="text-center p-8 max-w-md space-y-2">
                        <p className="text-base font-semibold text-slate-200">Image Pending Upload</p>
                        <p className="text-xs text-slate-400">
                            No digital scan has been uploaded for this image record yet.
                        </p>
                    </div>
                )}
            </div>

            {/* Image Source & Identifier Footer */}
            <footer className="px-4 py-3 bg-slate-900 border-t border-slate-800 text-xs text-slate-300 flex flex-wrap items-center justify-between gap-2">
                <div className="space-y-0.5">
                    <p>
                        <span className="font-semibold text-slate-100">
                            {[currentImage?.image_type, currentImage?.view_type].filter(Boolean).join(' · ') || 'Artifact Image'}
                        </span>
                        {currentImage?.source_identifier && (
                            <span className="text-slate-400"> — {currentImage.source_identifier}</span>
                        )}
                    </p>
                    {currentImage?.source_citation && (
                        <p className="text-slate-400">{currentImage.source_citation}</p>
                    )}
                </div>
                <span className="text-[11px] text-slate-400">
                    Scroll or double-click to zoom · Drag to pan when zoomed · Esc or click outside to close
                </span>
            </footer>
        </dialog>
    );
};

export default ImageLightbox;
