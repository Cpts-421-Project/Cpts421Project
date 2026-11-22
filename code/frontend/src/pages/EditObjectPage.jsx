import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const toNumberOrNull = (val) => {
    if (val === '' || val === null || val === undefined) return null;
    const parsed = parseFloat(val);
    return Number.isNaN(parsed) ? null : parsed;
};

const toNullIfBlank = (val) => {
    if (typeof val !== 'string') return val ?? null;
    const trimmed = val.trim();
    return trimmed === '' ? null : trimmed;
};

const EditObjectPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { isAdmin } = useAuth();
    
    const isEditMode = Boolean(id);
    const [loading, setLoading] = useState(isEditMode);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    
    // Form fields aligned with 2_excel
    const [formData, setFormData] = useState({
        object_type: '',
        material: '',
        findspot: '',
        present_location: '',
        production_location: '',
        object_group: '',
        date_display: '',
        date_start: 0,
        date_end: 0,
        date_basis: '',
        inventory_number: '',
        description: '',
        caption: '',
        height: '',
        width: '',
        depth: '',
        unit: 'cm',
        dimensions_display: '',
        weight: '',
        completeness: '',
        inscription_present: '',
        inscription_1: '',
        inscription_2: '',
        publications: '',
        latitude: '',
        longitude: ''
    });

    // Image Upload & Existing Image Provenance
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [existingImages, setExistingImages] = useState([]);

    useEffect(() => {
        if (!isAdmin) {
            navigate('/login');
            return;
        }

        if (isEditMode) {
            const fetchObject = async () => {
                try {
                    const response = await api.get(`/objects/${id}`);
                    const obj = response.data;
                    setFormData({
                        object_type: obj.object_type || '',
                        material: obj.material || '',
                        findspot: obj.findspot || '',
                        present_location: obj.present_location || '',
                        production_location: obj.production_location || '',
                        object_group: obj.object_group || '',
                        date_display: obj.date_display || '',
                        date_start: obj.date_start ?? 0,
                        date_end: obj.date_end ?? 0,
                        date_basis: obj.date_basis || '',
                        inventory_number: obj.inventory_number || '',
                        description: obj.description || '',
                        caption: obj.caption || '',
                        height: obj.height ?? '',
                        width: obj.width ?? '',
                        depth: obj.depth ?? '',
                        unit: obj.unit || 'cm',
                        dimensions_display: obj.dimensions_display || '',
                        weight: obj.weight || '',
                        completeness: obj.completeness || '',
                        inscription_present:
                            obj.inscription_present === true
                                ? 'true'
                                : obj.inscription_present === false
                                    ? 'false'
                                    : '',
                        inscription_1: obj.inscription_1 || '',
                        inscription_2: obj.inscription_2 || '',
                        publications: obj.publications || '',
                        latitude: obj.latitude ?? '',
                        longitude: obj.longitude ?? ''
                    });
                    setExistingImages(obj.images || []);
                } catch (err) {
                    setError('Failed to fetch object details');
                } finally {
                    setLoading(false);
                }
            };
            fetchObject();
        }
    }, [id, isAdmin, navigate, isEditMode]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleExistingImageChange = (index, field, value) => {
        setExistingImages((prev) =>
            prev.map((img, idx) => (idx === index ? { ...img, [field]: value } : img))
        );
    };

    const handleFileChange = (e) => {
        setSelectedFiles(Array.from(e.target.files));
    };

    const handleRemoveExistingImage = (indexToRemove) => {
        setExistingImages((prev) => prev.filter((_, idx) => idx !== indexToRemove));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');

        try {
            // First, upload new images
            let newImageUrls = [];
            if (selectedFiles.length > 0) {
                const formDataParams = new FormData();
                selectedFiles.forEach((file) => formDataParams.append('files', file));
                
                const uploadResponse = await api.post('/upload-images', formDataParams, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                const startSeq = existingImages.length + 1;
                newImageUrls = uploadResponse.data.urls.map((url, idx) => ({
                    file_url: url,
                    image_type: 'Photograph',
                    view_type: 'Front',
                    image_sequence: startSeq + idx,
                }));
            }

            // Combine with existing images
            const finalImages = [
                ...existingImages.map((img, idx) => ({
                    file_url: img.file_url || '',
                    image_type: img.image_type || 'Photograph',
                    view_type: img.view_type || 'Front',
                    image_sequence: img.image_sequence ?? idx + 1,
                    source_identifier: toNullIfBlank(img.source_identifier),
                    source_citation: toNullIfBlank(img.source_citation),
                })),
                ...newImageUrls
            ];

            const parsedStart = parseInt(formData.date_start, 10);
            const parsedEnd = parseInt(formData.date_end, 10);

            const payload = {
                object_type: formData.object_type.trim(),
                material: toNullIfBlank(formData.material),
                findspot: toNullIfBlank(formData.findspot),
                present_location: toNullIfBlank(formData.present_location),
                production_location: toNullIfBlank(formData.production_location),
                object_group: toNullIfBlank(formData.object_group),
                date_display: formData.date_display.trim(),
                date_start: Number.isNaN(parsedStart) ? 0 : parsedStart,
                date_end: Number.isNaN(parsedEnd) ? 0 : parsedEnd,
                date_basis: toNullIfBlank(formData.date_basis),
                inventory_number: toNullIfBlank(formData.inventory_number),
                description: toNullIfBlank(formData.description),
                caption: toNullIfBlank(formData.caption),
                height: toNumberOrNull(formData.height),
                width: toNumberOrNull(formData.width),
                depth: toNumberOrNull(formData.depth),
                unit: toNullIfBlank(formData.unit) || 'cm',
                dimensions_display: toNullIfBlank(formData.dimensions_display),
                weight: toNullIfBlank(formData.weight),
                completeness: toNullIfBlank(formData.completeness),
                inscription_present:
                    formData.inscription_present === ''
                        ? null
                        : formData.inscription_present === 'true',
                inscription_1: toNullIfBlank(formData.inscription_1),
                inscription_2: toNullIfBlank(formData.inscription_2),
                publications: toNullIfBlank(formData.publications),
                latitude: toNumberOrNull(formData.latitude),
                longitude: toNumberOrNull(formData.longitude),
                images: finalImages
            };

            if (isEditMode) {
                await api.put(`/objects/${id}`, payload);
            } else {
                const createRes = await api.post('/objects', payload);
                navigate(`/objects/${createRes.data.id}`);
                return;
            }

            navigate(`/objects/${id}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Operation failed');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-8">Loading...</div>;

    return (
        <div className="max-w-4xl mx-auto p-4 overflow-y-auto">
            <h1 className="text-3xl font-bold mb-6">{isEditMode ? 'Edit Artifact' : 'Add New Artifact'}</h1>
            {error && <div className="p-4 mb-6 bg-red-100 text-red-700 rounded">{error}</div>}
            
            <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 shadow rounded border border-gray-100">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Object Type *</label>
                        <input required type="text" name="object_type" value={formData.object_type} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Roundel with gold-glass" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Inventory Number</label>
                        <input type="text" name="inventory_number" value={formData.inventory_number} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Present Location (Museum / Collection)</label>
                        <input type="text" name="present_location" value={formData.present_location} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Museo Biblioteca Apostolica Vaticana, Vatican City" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Material / Materials</label>
                        <input type="text" name="material" value={formData.material} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Gold-glass, Clay" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Findspot (Geographic Location)</label>
                        <input type="text" name="findspot" value={formData.findspot} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Rome" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Production Location (if suggested)</label>
                        <input type="text" name="production_location" value={formData.production_location} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Group (e.g., Hoard / Treasure)</label>
                        <input type="text" name="object_group" value={formData.object_group} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Fragment / Complete Object</label>
                        <input type="text" name="completeness" value={formData.completeness} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Fragmentary, broken at the edges" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Date Assigned *</label>
                        <input required type="text" name="date_display" value={formData.date_display} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. c. 4th century CE" />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Start Year *</label>
                            <input required type="number" name="date_start" value={formData.date_start} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">End Year *</label>
                            <input required type="number" name="date_end" value={formData.date_end} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                    </div>

                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700">Basis / Discussion of Date</label>
                        <input type="text" name="date_basis" value={formData.date_basis} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Latitude</label>
                        <input type="number" step="any" name="latitude" value={formData.latitude} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Longitude</label>
                        <input type="number" step="any" name="longitude" value={formData.longitude} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                    </div>
                </div>

                {/* Dimensions & Weight */}
                <div className="border-t pt-4">
                    <h2 className="text-lg font-semibold mb-3">Dimensions &amp; Weight</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Height</label>
                            <input type="number" step="any" name="height" value={formData.height} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Width</label>
                            <input type="number" step="any" name="width" value={formData.width} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Depth</label>
                            <input type="number" step="any" name="depth" value={formData.depth} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Unit</label>
                            <input type="text" name="unit" value={formData.unit} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="cm" />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Dimensions Note</label>
                            <input type="text" name="dimensions_display" value={formData.dimensions_display} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. Diam. 10.2 cm" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Weight</label>
                            <input type="text" name="weight" value={formData.weight} onChange={handleChange} className="mt-1 w-full p-2 border rounded" placeholder="e.g. 45 g" />
                        </div>
                    </div>
                </div>

                {/* Inscriptions */}
                <div className="border-t pt-4">
                    <h2 className="text-lg font-semibold mb-3">Inscriptions</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Inscription Present?</label>
                            <select name="inscription_present" value={formData.inscription_present} onChange={handleChange} className="mt-1 w-full p-2 border rounded bg-white">
                                <option value="">Not recorded</option>
                                <option value="true">Yes</option>
                                <option value="false">No</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Inscription 1</label>
                            <input type="text" name="inscription_1" value={formData.inscription_1} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Inscription 2</label>
                            <input type="text" name="inscription_2" value={formData.inscription_2} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                        </div>
                    </div>
                </div>

                {/* Narrative, Caption & Publications */}
                <div className="border-t pt-4 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Description</label>
                        <textarea name="description" value={formData.description} onChange={handleChange} rows="3" className="mt-1 w-full p-2 border rounded"></textarea>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Custom Caption Override (leave blank to auto-assemble)</label>
                        <textarea name="caption" value={formData.caption} onChange={handleChange} rows="2" className="mt-1 w-full p-2 border rounded"></textarea>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Image Discussions / Publications</label>
                        <textarea name="publications" value={formData.publications} onChange={handleChange} rows="2" className="mt-1 w-full p-2 border rounded"></textarea>
                    </div>
                </div>

                <div className="border-t pt-6">
                    <h2 className="text-xl font-semibold mb-4">Images</h2>
                    {existingImages.length > 0 && (
                        <div className="mb-4 space-y-3">
                            <p className="text-sm font-medium text-gray-700">Existing Images:</p>
                            <div className="space-y-3">
                                {existingImages.map((img, idx) => (
                                    <div key={idx} className="flex flex-col sm:flex-row gap-4 p-3 border rounded bg-gray-50 relative">
                                        <img
                                            src={img.file_url || '/placeholder-artifact.svg'}
                                            alt={`artifact ${idx + 1}`}
                                            className="h-24 w-24 object-cover rounded shadow bg-white flex-shrink-0"
                                        />
                                        <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                            <div>
                                                <label className="block text-gray-600">Drawing / Photo Type</label>
                                                <input
                                                    type="text"
                                                    value={img.image_type || ''}
                                                    onChange={(e) => handleExistingImageChange(idx, 'image_type', e.target.value)}
                                                    className="mt-0.5 w-full p-1.5 border rounded bg-white"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-gray-600">View Type</label>
                                                <input
                                                    type="text"
                                                    value={img.view_type || ''}
                                                    onChange={(e) => handleExistingImageChange(idx, 'view_type', e.target.value)}
                                                    className="mt-0.5 w-full p-1.5 border rounded bg-white"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-gray-600">Source Identifier #</label>
                                                <input
                                                    type="text"
                                                    value={img.source_identifier || ''}
                                                    onChange={(e) => handleExistingImageChange(idx, 'source_identifier', e.target.value)}
                                                    className="mt-0.5 w-full p-1.5 border rounded bg-white"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-gray-600">Image Source (Chicago Citation)</label>
                                                <input
                                                    type="text"
                                                    value={img.source_citation || ''}
                                                    onChange={(e) => handleExistingImageChange(idx, 'source_citation', e.target.value)}
                                                    className="mt-0.5 w-full p-1.5 border rounded bg-white"
                                                />
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveExistingImage(idx)}
                                            className="self-start bg-red-500 text-white rounded-full p-1 w-6 h-6 flex items-center justify-center shadow opacity-85 hover:opacity-100"
                                            title="Remove image"
                                        >
                                            &times;
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Upload New Images</label>
                        <input
                            type="file"
                            multiple
                            accept="image/*"
                            onChange={handleFileChange}
                            className="mt-1 block w-full text-sm text-gray-500
                                file:mr-4 file:py-2 file:px-4
                                file:rounded file:border-0
                                file:text-sm file:font-semibold
                                file:bg-blue-50 file:text-blue-700
                                hover:file:bg-blue-100"
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-4 border-t pt-4">
                    <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded">
                        Cancel
                    </button>
                    <button type="submit" disabled={saving} className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded disabled:bg-blue-300 transition">
                        {saving ? 'Saving...' : 'Save Artifact'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default EditObjectPage;
