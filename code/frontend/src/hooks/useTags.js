import { useState, useEffect } from 'react';
import api from '../services/api';

const useTags = () => {
    const [tags, setTags] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchTags = async () => {
            try {
                const response = await api.get('/tags');
                const sortedTags = Array.isArray(response.data)
                    ? [...response.data].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }))
                    : [];
                setTags(sortedTags);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch tags:", err);
                setError(err);
                setLoading(false);
            }
        };

        fetchTags();
    }, []);

    return { tags, loading, error };
};

export default useTags;
