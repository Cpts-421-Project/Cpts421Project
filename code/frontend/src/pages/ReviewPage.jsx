import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const ReviewPage = () => {
    const navigate = useNavigate();
    const { isAdmin } = useAuth();
    
    const [pendingArtifacts, setPendingArtifacts] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    
    // Form fields for currently viewed artifact
    const [formData, setFormData] = useState(null);
    
    // Undo stack for session
    const [undoStack, setUndoStack] = useState([]);

    const fetchPending = async () => {
        try {
            setLoading(true);
            const response = await api.get('/objects/pending');
            setPendingArtifacts(response.data);
            setCurrentIndex(0);
        } catch (err) {
            console.error('Failed to fetch pending artifacts', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!isAdmin) {
            navigate('/login');
            return;
        }
        fetchPending();
    }, [isAdmin, navigate]);

    useEffect(() => {
        if (pendingArtifacts.length > 0 && currentIndex < pendingArtifacts.length) {
            const obj = pendingArtifacts[currentIndex];
            setFormData({
                object_type: obj.object_type || '',
                material: obj.material || '',
                findspot: obj.findspot || '',
                date_display: obj.date_display || '',
                date_start: obj.date_start || 0,
                date_end: obj.date_end || 0,
                inventory_number: obj.inventory_number || '',
                description: obj.description || '',
                latitude: obj.latitude || '',
                longitude: obj.longitude || ''
            });
        } else {
            setFormData(null);
        }
    }, [pendingArtifacts, currentIndex]);

    const processAction = useCallback(async (action) => {
        if (processing || !formData || currentIndex >= pendingArtifacts.length) return;
        
        const currentObj = pendingArtifacts[currentIndex];
        setProcessing(true);

        try {
            if (action === 'skip') {
                setCurrentIndex(prev => prev + 1);
            } else {
                // First save any local edits to the backend
                const payload = {
                    ...formData,
                    date_start: parseInt(formData.date_start, 10) || 0,
                    date_end: parseInt(formData.date_end, 10) || 0,
                    latitude: formData.latitude ? parseFloat(formData.latitude) : null,
                    longitude: formData.longitude ? parseFloat(formData.longitude) : null,
                };
                
                await api.put(`/objects/${currentObj.id}`, payload);
                
                // Then apply the review status
                const status = action === 'accept' ? 'accepted' : 'rejected';
                await api.patch(`/objects/${currentObj.id}/review`, { status });
                
                if (action === 'deny') {
                    // Add to undo stack (max 3)
                    setUndoStack(prev => {
                        const newStack = [{ id: currentObj.id, title: payload.object_type || `Item #${currentObj.id}` }, ...prev];
                        return newStack.slice(0, 3);
                    });
                }
                
                // Move to next item
                setCurrentIndex(prev => prev + 1);
            }
        } catch (err) {
            console.error(`Failed to execute ${action}`, err);
            alert(`Failed to ${action} artifact. See console for details.`);
        } finally {
            setProcessing(false);
        }
    }, [processing, formData, currentIndex, pendingArtifacts]);

    useEffect(() => {
        const handleKeyDown = (e) => {
            // Don't trigger if user is typing in an input or textarea
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
                return;
            }

            if (e.code === 'Space') {
                e.preventDefault();
                processAction('accept');
            } else if (e.code === 'Delete' || e.code === 'Backspace') {
                e.preventDefault();
                processAction('deny');
            } else if (e.code === 'Enter') {
                e.preventDefault();
                processAction('skip');
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [processAction]);

    const handleUndo = async (item) => {
        if (processing) return;
        setProcessing(true);
        try {
            await api.patch(`/objects/${item.id}/review`, { status: 'pending' });
            // Remove from undo stack
            setUndoStack(prev => prev.filter(u => u.id !== item.id));
            // Reload the queue
            await fetchPending();
        } catch (error) {
            console.error('Failed to undo', error);
            alert('Failed to undo. The item might be permanently deleted.');
        } finally {
            setProcessing(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const isComplete = currentIndex >= pendingArtifacts.length;

    if (loading || (!isComplete && !formData)) return <div className="p-8">Loading pending artifacts...</div>;

    return (
        <div className="flex-1 bg-gray-50 flex flex-col items-center py-8 px-4 overflow-y-auto">
            <div className="w-full max-w-4xl flex justify-between items-end mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800">Review Queue</h1>
                    {!isComplete && (
                        <p className="text-gray-500 mt-2">
                            Item {currentIndex + 1} of {pendingArtifacts.length}
                        </p>
                    )}
                </div>
                
                {/* Undo Stack UI */}
                {undoStack.length > 0 && (
                    <div className="bg-white p-3 rounded shadow-sm border text-sm">
                        <strong className="text-gray-700 block mb-2">Recently Denied:</strong>
                        <ul className="space-y-1">
                            {undoStack.map((item) => (
                                <li key={item.id} className="flex items-center justify-between gap-4">
                                    <span className="truncate w-32">{item.title}</span>
                                    <button 
                                        onClick={() => handleUndo(item)}
                                        className="text-blue-600 hover:text-blue-800 font-semibold"
                                        disabled={processing}
                                    >
                                        Undo
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            {isComplete ? (
                <div className="bg-white p-12 text-center rounded shadow w-full max-w-4xl border">
                    <h2 className="text-2xl font-bold text-gray-700 mb-4">Queue Empty!</h2>
                    <p className="text-gray-500">You have reviewed all pending artifacts.</p>
                    <button onClick={fetchPending} className="mt-6 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                        Refresh Queue
                    </button>
                </div>
            ) : (
                <div className="bg-white shadow rounded-lg w-full max-w-4xl overflow-hidden border">
                    {/* Visualizer & Images */}
                    <div className="bg-gray-200 p-4 border-b">
                        {pendingArtifacts[currentIndex].images && pendingArtifacts[currentIndex].images.length > 0 ? (
                            <div className="flex gap-4 overflow-x-auto pb-2">
                                {pendingArtifacts[currentIndex].images.map((img, idx) => (
                                    <img key={idx} src={img.file_url} alt="artifact representation" className="h-48 rounded shadow-sm object-cover" />
                                ))}
                            </div>
                        ) : (
                            <div className="h-48 flex items-center justify-center text-gray-400">No Images Provided</div>
                        )}
                    </div>

                    {/* Editor Form */}
                    <div className="p-6">
                        <form className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Type</label>
                                    <input type="text" name="object_type" value={formData.object_type} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Inventory Number</label>
                                    <input type="text" name="inventory_number" value={formData.inventory_number} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Material</label>
                                    <input type="text" name="material" value={formData.material} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Findspot</label>
                                    <input type="text" name="findspot" value={formData.findspot} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Date Display</label>
                                    <input type="text" name="date_display" value={formData.date_display} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                </div>
                                
                                <div className="grid grid-cols-2 gap-2">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Start Year</label>
                                        <input type="number" name="date_start" value={formData.date_start} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">End Year</label>
                                        <input type="number" name="date_end" value={formData.date_end} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">Description</label>
                                <textarea name="description" value={formData.description} onChange={handleChange} rows="3" className="mt-1 w-full p-2 border rounded"></textarea>
                            </div>
                        </form>
                    </div>

                    {/* Action Bar */}
                    <div className="bg-gray-50 border-t p-4 flex justify-between items-center px-6">
                        <div className="text-gray-500 text-sm flex gap-6">
                            <span><strong className="text-gray-800 border px-1 rounded mx-1">Space</strong> Accept</span>
                            <span><strong className="text-gray-800 border px-1 rounded mx-1">Delete</strong> Deny</span>
                            <span><strong className="text-gray-800 border px-1 rounded mx-1">Enter</strong> Skip</span>
                        </div>
                        
                        <div className="flex gap-3">
                            <button 
                                onClick={() => processAction('deny')} 
                                disabled={processing}
                                className="px-5 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded font-medium disabled:opacity-50"
                            >
                                Deny
                            </button>
                            <button 
                                onClick={() => processAction('skip')} 
                                disabled={processing}
                                className="px-5 py-2 border hover:bg-gray-100 text-gray-700 rounded font-medium disabled:opacity-50"
                            >
                                Skip
                            </button>
                            <button 
                                onClick={() => processAction('accept')} 
                                disabled={processing}
                                className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium disabled:opacity-50"
                            >
                                Accept
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ReviewPage;
