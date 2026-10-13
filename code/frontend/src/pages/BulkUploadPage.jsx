import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const BulkUploadPage = () => {
    const navigate = useNavigate();
    const { isAdmin } = useAuth();

    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState(null); // result of the last request
    const [error, setError] = useState('');

    useEffect(() => {
        if (!isAdmin) navigate('/login');
    }, [isAdmin, navigate]);

    const handleFileChange = (e) => {
        setFile(e.target.files[0] || null);
        setReport(null);
        setError('');
    };

    const send = async (dryRun) => {
        if (!file) return;
        setLoading(true);
        setError('');
        try {
            const body = new FormData();
            body.append('file', file);
            body.append('dry_run', dryRun ? 'true' : 'false');
            const res = await api.post('/objects/bulk-import', body, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setReport(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed');
        } finally {
            setLoading(false);
        }
    };

    const hasErrors = report && report.errors.length > 0;
    const imported = report && !report.dry_run && !hasErrors;
    const failed = report?.failed || [];
    const canConfirm = report && report.dry_run && !hasErrors && report.objects_count > 0;

    return (
        <div className="max-w-4xl mx-auto p-4">
            <h1 className="text-3xl font-bold mb-2">Bulk Upload Artifacts</h1>
            <p className="text-gray-600 mb-6">
                Upload an Excel (.xlsx) file based on the template: one row per object. Columns marked * are required;
                put dates as whole years (negative for BC). Image URL may hold several links separated by semicolons.{' '}
                <a href="bulk_upload_template.xlsx" download className="text-blue-600 underline">Download the template</a>
                {' '}.
            </p>

            {error && <div className="p-4 mb-6 bg-red-100 text-red-700 rounded">{error}</div>}

            <div className="bg-white p-6 shadow rounded border border-gray-100 space-y-4">
                <input type="file" accept=".xlsx" onChange={handleFileChange}
                    className="block w-full text-sm text-gray-500
                        file:mr-4 file:py-2 file:px-4 file:rounded file:border-0
                        file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700
                        hover:file:bg-blue-100" />
                <div className="flex gap-4">
                    <button type="button" onClick={() => send(true)} disabled={!file || loading}
                        className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded disabled:bg-blue-300 transition">
                        {loading ? 'Working...' : 'Validate & Preview'}
                    </button>
                    {canConfirm && (
                        <button type="button" onClick={() => send(false)} disabled={loading}
                            className="px-4 py-2 text-white bg-green-600 hover:bg-green-700 rounded disabled:bg-green-300 transition">
                            Import {report.objects_count} objects
                        </button>
                    )}
                </div>
            </div>

            {report && (
                <div className="mt-6 space-y-6">
                    <div className={`p-4 rounded ${imported ? 'bg-green-100 text-green-800' : hasErrors ? 'bg-red-100 text-red-700' : 'bg-blue-50 text-blue-800'}`}>
                        {imported
                            ? `Created ${report.created_count} of ${report.objects_count} objects.`
                            : hasErrors
                                ? `${report.errors.length} error(s) found. Fix the spreadsheet and re-upload; nothing has been saved.`
                                : `Ready to import: ${report.objects_count} objects, ${report.images_count} images, ${report.new_sources_count} new sources.`}
                    </div>

                    {failed.length > 0 && (
                        <div>
                            <h2 className="text-lg font-semibold mb-2">Failed to create</h2>
                            <ul className="bg-white border rounded divide-y text-sm">
                                {failed.map((f, i) => (
                                    <li key={i} className="p-2"><span className="font-mono text-red-600">Row {f.row}</span>: {f.message}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {hasErrors && (
                        <div>
                            <h2 className="text-lg font-semibold mb-2">Errors</h2>
                            <ul className="bg-white border rounded divide-y text-sm">
                                {report.errors.map((e, i) => (
                                    <li key={i} className="p-2"><span className="font-mono text-red-600">{e.sheet} row {e.row}</span>: {e.message}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {report.warnings.length > 0 && (
                        <div>
                            <h2 className="text-lg font-semibold mb-2">Warnings</h2>
                            <ul className="bg-white border rounded divide-y text-sm">
                                {report.warnings.map((w, i) => (
                                    <li key={i} className="p-2"><span className="font-mono text-yellow-700">{w.sheet} row {w.row}</span>: {w.message}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {!imported && report.preview.length > 0 && (
                        <div>
                            <h2 className="text-lg font-semibold mb-2">Preview{report.objects_count > report.preview.length ? ` (first ${report.preview.length})` : ''}</h2>
                            <div className="overflow-x-auto">
                                <table className="min-w-full bg-white border text-sm">
                                    <thead className="bg-gray-50 text-left">
                                        <tr>
                                            {['Row', 'Type', 'Material', 'Date', 'Years', 'Inv. #', 'Images'].map(h => (
                                                <th key={h} className="p-2 border-b">{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {report.preview.map(o => (
                                            <tr key={o.key} className="border-b">
                                                <td className="p-2">{o.key}</td>
                                                <td className="p-2">{o.object_type}</td>
                                                <td className="p-2">{o.material || '—'}</td>
                                                <td className="p-2">{o.date_display}</td>
                                                <td className="p-2">{o.date_start} to {o.date_end}</td>
                                                <td className="p-2">{o.inventory_number || '—'}</td>
                                                <td className="p-2">{o.image_count}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {imported && (
                        <button type="button" onClick={() => navigate('/')}
                            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded">
                            Done
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

export default BulkUploadPage;
