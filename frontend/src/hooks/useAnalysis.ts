/* ──────────────────────────────────────────────
   Hook useAnalysis — API de análisis de imágenes/URLs
   ────────────────────────────────────────────── */

import { useCallback, useState } from 'react';
import { api, ApiError } from '../services/api';
import type {
  AnalysisJob,
  AnalysisJobCreate,
  AnalysisJobList,
  AnalysisResult,
  AnalysisResultList,
  AnalysisResultAction,
  ScrapedSource,
  ScrapedSourceCreate,
  ScrapedSourceList,
} from '../types';

interface UseAnalysisState {
  loading: boolean;
  error: string | null;
}

export function useAnalysis() {
  const [state, setState] = useState<UseAnalysisState>({
    loading: false,
    error: null,
  });

  const setLoading = useCallback((loading: boolean) => {
    setState((s) => ({ ...s, loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState((s) => ({ ...s, error }));
  }, []);

  const handleError = useCallback((err: unknown): string => {
    if (err instanceof ApiError) {
      return err.detail || `Error ${err.status}`;
    }
    if (err instanceof Error) {
      return err.message;
    }
    return 'Error desconocido';
  }, []);

  // ── Jobs ─────────────────────────────────────────────

  const createJob = useCallback(
    async (payload: AnalysisJobCreate): Promise<AnalysisJob | null> => {
      setLoading(true);
      setError(null);
      try {
        const job = await api.post<AnalysisJob>('/api/v1/analysis/jobs', payload);
        return job;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  const listJobs = useCallback(
    async (page = 1, perPage = 10, statusFilter?: string): Promise<AnalysisJobList | null> => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
        if (statusFilter) params.append('status', statusFilter);
        const list = await api.get<AnalysisJobList>(`/api/v1/analysis/jobs?${params}`);
        return list;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  const getJobStatus = useCallback(
    async (jobId: string): Promise<AnalysisJob | null> => {
      setLoading(true);
      setError(null);
      try {
        const job = await api.get<AnalysisJob>(`/api/v1/analysis/jobs/${jobId}`);
        return job;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  // ── Results ──────────────────────────────────────────

  const listResults = useCallback(
    async (page = 1, perPage = 10, statusFilter?: string): Promise<AnalysisResultList | null> => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
        if (statusFilter) params.append('status', statusFilter);
        const list = await api.get<AnalysisResultList>(`/api/v1/analysis/results?${params}`);
        return list;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  const approveResult = useCallback(
    async (resultId: string): Promise<AnalysisResult | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.post<AnalysisResult>(`/api/v1/analysis/results/${resultId}/approve`, {});
        return result;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  const rejectResult = useCallback(
    async (resultId: string, reason?: string): Promise<AnalysisResult | null> => {
      setLoading(true);
      setError(null);
      try {
        const payload: AnalysisResultAction = { reason };
        const result = await api.post<AnalysisResult>(`/api/v1/analysis/results/${resultId}/reject`, payload);
        return result;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  // ── Scraped Sources ──────────────────────────────────

  const createSource = useCallback(
    async (payload: ScrapedSourceCreate): Promise<ScrapedSource | null> => {
      setLoading(true);
      setError(null);
      try {
        const source = await api.post<ScrapedSource>('/api/v1/analysis/sources', payload);
        return source;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  const listSources = useCallback(
    async (page = 1, perPage = 10): Promise<ScrapedSourceList | null> => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
        const list = await api.get<ScrapedSourceList>(`/api/v1/analysis/sources?${params}`);
        return list;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  const deleteSource = useCallback(
    async (sourceId: string): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        await api.del(`/api/v1/analysis/sources/${sourceId}`);
        return true;
      } catch (err) {
        const msg = handleError(err);
        setError(msg);
        return false;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, handleError]
  );

  return {
    // state
    loading: state.loading,
    error: state.error,
    // jobs
    createJob,
    listJobs,
    getJobStatus,
    // results
    listResults,
    approveResult,
    rejectResult,
    // sources
    createSource,
    listSources,
    deleteSource,
  };
}