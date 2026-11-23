import { useEffect, useId, useRef } from 'react';

export const REVIEW_SHORTCUTS = [
    { id: 'accept', label: 'Accept', keys: ['A', 'Space'], summary: 'Save edits & accept' },
    { id: 'deny', label: 'Deny', keys: ['D', 'Del'], summary: 'Save edits & deny' },
    { id: 'skip', label: 'Skip', keys: ['S', 'Enter', '→'], summary: 'Skip to next item' },
    { id: 'prev', label: 'Previous', keys: ['←', 'P'], summary: 'Go to previous item' },
    { id: 'zoom', label: 'Zoom Image', keys: ['Z'], summary: 'Open image zoom lightbox' },
    { id: 'undo', label: 'Undo Denied', keys: ['U'], summary: 'Restore last denied item' },
    { id: 'exit', label: 'Exit Field', keys: ['Esc'], summary: 'Leave input to use shortcuts' },
    { id: 'help', label: 'Shortcut Key', keys: ['?'], summary: 'Toggle full shortcut key' },
];

const COMPACT_SHORTCUTS = [
    { id: 'accept', label: 'Accept', keys: ['A', 'Space'] },
    { id: 'deny', label: 'Deny', keys: ['D', 'Del'] },
    { id: 'skip', label: 'Skip', keys: ['S', 'Enter'] },
    { id: 'prev', label: 'Prev', keys: ['←'] },
    { id: 'zoom', label: 'Zoom', keys: ['Z'] },
    { id: 'undo', label: 'Undo', keys: ['U'] },
];

const KeyCap = ({ children, muted = false, ariaHidden = false }) => (
    <kbd
        aria-hidden={ariaHidden || undefined}
        className={`inline-flex items-center justify-center px-1.5 py-0.5 text-[11px] font-mono font-semibold rounded border shadow-2xs ${
            muted
                ? 'bg-gray-100 text-gray-400 border-gray-200'
                : 'bg-white text-gray-800 border-gray-300'
        }`}
    >
        {children}
    </kbd>
);

const ReviewShortcutKey = ({
    isOpen,
    onOpen,
    onClose,
    canUndo = false,
    canGoPrev = false,
    canZoom = false,
}) => {
    const dialogRef = useRef(null);
    const headingId = useId();

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

    const availability = {
        prev: canGoPrev,
        zoom: canZoom,
        undo: canUndo,
    };

    return (
        <>
            <aside
                aria-label="Keyboard shortcuts"
                className="w-full max-w-4xl mb-4 bg-white border border-gray-200 rounded-lg px-4 py-2.5 shadow-2xs flex flex-wrap items-center justify-between gap-3"
            >
                <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-gray-600">
                    {COMPACT_SHORTCUTS.map((item) => {
                        const isAvailable = availability[item.id] ?? true;
                        return (
                            <li
                                key={item.id}
                                className={`inline-flex items-center gap-1 ${
                                    isAvailable ? 'text-gray-700' : 'text-gray-400'
                                }`}
                            >
                                <span className="inline-flex items-center gap-1">
                                    {item.keys.map((keyLabel, idx) => (
                                        <span key={keyLabel} className="inline-flex items-center gap-1">
                                            {idx > 0 && <span className="text-gray-400">/</span>}
                                            <KeyCap muted={!isAvailable}>{keyLabel}</KeyCap>
                                        </span>
                                    ))}
                                </span>
                                <span className="font-medium">{item.label}</span>
                            </li>
                        );
                    })}
                </ul>

                <button
                    type="button"
                    onClick={onOpen}
                    aria-keyshortcuts="?"
                    aria-haspopup="dialog"
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md transition"
                >
                    <span>All Shortcuts</span>
                    <KeyCap ariaHidden>?</KeyCap>
                </button>
            </aside>

            <dialog
                ref={dialogRef}
                closedby="any"
                aria-labelledby={headingId}
                onClose={handleNativeClose}
                className="m-auto w-[92vw] max-w-lg rounded-xl bg-white text-gray-900 shadow-2xl border border-gray-200 p-0 overflow-hidden backdrop:bg-slate-950/60"
            >
                <header className="flex items-center justify-between gap-3 px-5 py-3.5 bg-gray-50 border-b border-gray-200">
                    <h2 id={headingId} className="text-base font-semibold text-gray-900">
                        Review Queue Keyboard Shortcuts
                    </h2>
                    <button
                        type="button"
                        autoFocus
                        onClick={handleRequestClose}
                        aria-label="Close keyboard shortcuts"
                        className="px-3 py-1 text-xs font-semibold rounded-md bg-blue-600 hover:bg-blue-700 text-white"
                    >
                        Close
                    </button>
                </header>

                <div className="p-5 space-y-4">
                    <dl className="divide-y divide-gray-100 text-sm">
                        {REVIEW_SHORTCUTS.map((shortcut) => (
                            <div
                                key={shortcut.id}
                                className="py-2.5 first:pt-0 last:pb-0 flex items-center justify-between gap-4"
                            >
                                <dt className="flex items-center gap-1.5 flex-wrap">
                                    {shortcut.keys.map((keyLabel, idx) => (
                                        <span key={keyLabel} className="inline-flex items-center gap-1">
                                            {idx > 0 && <span className="text-xs text-gray-400">or</span>}
                                            <KeyCap>{keyLabel}</KeyCap>
                                        </span>
                                    ))}
                                </dt>
                                <dd className="text-right">
                                    <span className="font-medium text-gray-900">{shortcut.label}</span>
                                    <span className="block text-xs text-gray-500">{shortcut.summary}</span>
                                </dd>
                            </div>
                        ))}
                    </dl>

                    <p className="text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded-md px-3 py-2">
                        Shortcuts pause automatically while typing in a form field. Press <KeyCap>Esc</KeyCap> to
                        leave the field and resume keyboard review.
                    </p>
                </div>
            </dialog>
        </>
    );
};

export default ReviewShortcutKey;
