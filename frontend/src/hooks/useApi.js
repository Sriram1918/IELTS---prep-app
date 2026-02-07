import { useState, useCallback } from 'react';
import { client } from '../api/client';

export const useApi = (endpoint, method = 'GET', initialData = null) => {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (body = null) => {
    setLoading(true);
    setError(null);
    try {
      let result;
      if (method === 'GET') {
        result = await client.get(endpoint);
      } else if (method === 'POST') {
        result = await client.post(endpoint, body);
      } else if (method === 'PUT') {
        result = await client.put(endpoint, body);
      }
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint, method]);

  return { data, loading, error, execute, reset: () => setData(initialData) };
};
