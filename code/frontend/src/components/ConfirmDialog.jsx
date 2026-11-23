import { useEffect, useId, useRef } from 'react';

const ConfirmDialog = ({
    isOpen,
    title,
    message,
    confirmLabel = 'Delete',
    cancelLabel = 'Cancel',
    submittingLabel = 'Deleting...',
    isSubmitting = false,
    onConfirm,
    onCancel,
}) => {
    const dialogRef = useRef(null);
    const cancelButtonRef = useRef(null);
    const headingId = useId();
    const descId = useId();

    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) return;

        if (isOpen) {
            if (!dialog.open && typeof dialog.showModal === 'function') {
                dialog.showModal();
            }
            cancelButtonRef.current?.focus();
        } else if (dialog.open && typeof dialog.close === 'function') {
            dialog.close();
        }
    }, [isOpen]);

    const handleNativeCancel = (event) => {
        if (isSubmitting) {
            event.preventDefault();
        }
    };

    const handleNativeClose = () => {
        const dialog = dialogRef.current;
        if (dialog) {
            dialog.returnValue = '';
        }
        if (!isSubmitting) {
            onCancel?.();
        }
    };

    const handleRequestCancel = () => {
        if (isSubmitting) return;
        const dialog = dialogRef.current;
        if (dialog && dialog.open && typeof dialog.close === 'function') {
            dialog.close();
        } else {
            onCancel?.();
        }
    };

    return (
        <dialog
            ref={dialogRef}
            aria-labelledby={headingId}
            aria-describedby={descId}
            onCancel={handleNativeCancel}
            onClose={handleNativeClose}
            className="m-auto w-[92vw] max-w-md rounded-xl bg-white text-gray-900 shadow-2xl border border-gray-200 p-0 overflow-hidden backdrop:bg-slate-950/60"
        >
            <div className="p-6 space-y-4">
                <div className="space-y-2">
                    <h2 id={headingId} className="text-lg font-semibold text-gray-900">
                        {title}
                    </h2>
                    <p id={descId} className="text-sm text-gray-600 leading-relaxed">
                        {message}
                    </p>
                </div>

                <div className="flex flex-wrap justify-end gap-3 pt-2 border-t border-gray-100">
                    <button
                        ref={cancelButtonRef}
                        type="button"
                        autoFocus
                        disabled={isSubmitting}
                        onClick={handleRequestCancel}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50"
                    >
                        {cancelLabel}
                    </button>
                    <button
                        type="button"
                        disabled={isSubmitting}
                        onClick={() => onConfirm?.()}
                        className="px-4 py-2 text-sm font-semibold text-white bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-60"
                    >
                        {isSubmitting ? submittingLabel : confirmLabel}
                    </button>
                </div>
            </div>
        </dialog>
    );
};

export default ConfirmDialog;
