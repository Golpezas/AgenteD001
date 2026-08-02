/* ──────────────────────────────────────────────
   AnalysisPage — Página principal de análisis
   ────────────────────────────────────────────── */

import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, Card, Button, Input, Form, Modal, message, Spin, Space } from 'antd';
import { PlusOutlined, UploadOutlined, FileImageOutlined, LinkOutlined, ReloadOutlined } from '@ant-design/icons';
import { useAnalysis } from '@/hooks/useAnalysis';
import { AnalysisJobTable } from '@/components/analysis/AnalysisJobTable';
import { AnalysisResultCard } from '@/components/analysis/AnalysisResultCard';
import { ScrapedSourceManager } from '@/components/analysis/ScrapedSourceManager';
import type { AnalysisJob, AnalysisJobCreate, AnalysisResult, ScrapedSource } from '@/types';

const { TabPane } = Tabs;

export const AnalysisPage: React.FC = () => {
  const {
    loading,
    error,
    createJob,
    listJobs,
    getJobStatus,
    listResults,
    approveResult,
    rejectResult,
    createSource,
    listSources,
    deleteSource,
  } = useAnalysis();

  // State
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [sources, setSources] = useState<ScrapedSource[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [resultsLoading, setResultsLoading] = useState(false);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [jobPage, setJobPage] = useState(1);
  const [resultPage, setResultPage] = useState(1);
  const [sourcePage] = useState(1);
  const [jobStatusFilter, setJobStatusFilter] = useState<string>('');
  const [resultStatusFilter, setResultStatusFilter] = useState<string>('');

  // Modals
  const [createJobModalOpen, setCreateJobModalOpen] = useState(false);
  const [createJobType, setCreateJobType] = useState<'image' | 'url'>('url');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [urlInput, setUrlInput] = useState('');

  // Polling for job status
  const [pollingJobs, setPollingJobs] = useState<Set<string>>(new Set());

  // Load data
  const loadJobs = useCallback(async () => {
    setJobsLoading(true);
    const data = await listJobs(jobPage, 10, jobStatusFilter || undefined);
    if (data) setJobs(data.items);
    setJobsLoading(false);
  }, [listJobs, jobPage, jobStatusFilter]);

  const loadResults = useCallback(async () => {
    setResultsLoading(true);
    const data = await listResults(resultPage, 10, resultStatusFilter || undefined);
    if (data) setResults(data.items);
    setResultsLoading(false);
  }, [listResults, resultPage, resultStatusFilter]);

  const loadSources = useCallback(async () => {
    setSourcesLoading(true);
    const data = await listSources(sourcePage, 10);
    if (data) setSources(data.items);
    setSourcesLoading(false);
  }, [listSources, sourcePage]);

  // Initial load
  useEffect(() => {
    loadJobs();
    loadResults();
    loadSources();
  }, [loadJobs, loadResults, loadSources]);

  // Polling for active jobs
  useEffect(() => {
    const activeJobs = jobs.filter((j) => j.status === 'pending' || j.status === 'processing');
    if (activeJobs.length === 0) return;

    const interval = setInterval(async () => {
      for (const job of activeJobs) {
        if (pollingJobs.has(job.id)) continue;
        setPollingJobs((prev) => new Set(prev).add(job.id));
        const updated = await getJobStatus(job.id);
        if (updated) {
          setJobs((prev) => prev.map((j) => (j.id === job.id ? updated : j)));
          if (updated.status === 'completed' || updated.status === 'failed') {
            setPollingJobs((prev) => {
              const next = new Set(prev);
              next.delete(job.id);
              return next;
            });
            loadResults(); // Refresh results when job completes
            message.success(`Job ${updated.status === 'completed' ? 'completado' : 'fallido'}`);
          }
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [jobs, getJobStatus, loadResults, pollingJobs]);

  // Handlers
  const handleCreateJob = async (jobData: AnalysisJobCreate) => {
    const job = await createJob(jobData);
    if (job) {
      message.success('Job creado exitosamente');
      setCreateJobModalOpen(false);
      setImagePreview(null);
      setImageFile(null);
      setUrlInput('');
      loadJobs();
    }
  };

  const handleApproveResult = async (resultId: string) => {
    await approveResult(resultId);
    loadResults();
  };

  const handleRejectResult = async (resultId: string, reason?: string) => {
    await rejectResult(resultId, reason);
    loadResults();
  };

  const handleCreateSource = async (payload: { url: string; name?: string; schedule_interval_minutes?: number }) => {
    const success = await createSource(payload);
    if (success) {
      message.success('Fuente creada');
      loadSources();
      return true;
    }
    return false;
  };

  const handleDeleteSource = async (sourceId: string) => {
    const success = await deleteSource(sourceId);
    if (success) message.success('Fuente eliminada');
    return success;
  };

  const handleImageUpload = (file: File) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
      setImageFile(file);
    };
    reader.readAsDataURL(file);
  };

  const handleCreateJobSubmit = (values: { url?: string }) => {
    if (createJobType === 'image') {
      if (!imageFile) {
        message.error('Selecciona una imagen');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = (reader.result as string).split(',')[1];
        handleCreateJob({
          job_type: 'image',
          input_data: { image_bytes: base64 },
        });
      };
      reader.readAsDataURL(imageFile);
    } else {
      if (!values.url) {
        message.error('Ingresa una URL');
        return;
      }
      handleCreateJob({
        job_type: 'url',
        input_data: { url: values.url },
      });
    }
  };

  const handleJobStatusFilterChange = (value: string) => {
    setJobStatusFilter(value);
    setJobPage(1);
  };

  const handleResultStatusFilterChange = (value: string) => {
    setResultStatusFilter(value);
    setResultPage(1);
  };

  if (error) {
    message.error(error);
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Análisis de Imágenes y URLs</h1>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateJobModalOpen(true)}
          >
            Nuevo análisis
          </Button>
        </Space>
      </div>

      <Tabs defaultActiveKey="1" style={{ marginBottom: 24 }}>
        {/* Tab 1: Jobs */}
        <TabPane tab="Jobs" key="1">
          <Card>
            <div style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} align="start">
                <Space>
                  <Input
                    placeholder="Filtrar por estado…"
                    allowClear
                    value={jobStatusFilter}
                    onChange={(e) => handleJobStatusFilterChange(e.target.value)}
                    style={{ width: 200 }}
                  />
                  <Button icon={<ReloadOutlined />} onClick={loadJobs} loading={jobsLoading}>
                    Actualizar
                  </Button>
                </Space>
              </Space>
            </div>
            <AnalysisJobTable
              jobs={jobs}
              loading={jobsLoading}
              onRefresh={loadJobs}
            />
          </Card>
        </TabPane>

        {/* Tab 2: Results */}
        <TabPane tab="Resultados" key="2">
          <Card>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Input
                  placeholder="Filtrar por estado…"
                  allowClear
                  value={resultStatusFilter}
                  onChange={(e) => handleResultStatusFilterChange(e.target.value)}
                  style={{ width: 200 }}
                />
                <Button icon={<ReloadOutlined />} onClick={loadResults} loading={resultsLoading}>
                  Actualizar
                </Button>
              </Space>
            </div>
            {resultsLoading ? (
              <Spin tip="Cargando resultados…" />
            ) : results.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>
                No hay resultados aún. Los jobs completados generarán propuestas aquí.
              </div>
            ) : (
              <div>
                {results.map((result) => (
                  <AnalysisResultCard
                    key={result.id}
                    result={result}
                    onApprove={handleApproveResult}
                    onReject={handleRejectResult}
                    loading={resultsLoading}
                  />
                ))}
              </div>
            )}
          </Card>
        </TabPane>

        {/* Tab 3: Sources */}
        <TabPane tab="Fuentes" key="3">
          <ScrapedSourceManager
            sources={sources}
            loading={sourcesLoading}
            onRefresh={loadSources}
            onCreate={handleCreateSource}
            onDelete={handleDeleteSource}
          />
        </TabPane>
      </Tabs>

      {/* Create Job Modal */}
      <Modal
        open={createJobModalOpen}
        onCancel={() => {
          setCreateJobModalOpen(false);
          setImagePreview(null);
          setImageFile(null);
          setUrlInput('');
        }}
        title="Crear nuevo análisis"
        width={600}
        destroyOnClose
      >
        <Form layout="vertical" onFinish={handleCreateJobSubmit}>
          <Form.Item label="Tipo de análisis">
            <Space direction="vertical" style={{ width: '100%' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="radio"
                  checked={createJobType === 'url'}
                  onChange={() => setCreateJobType('url')}
                />
                <LinkOutlined style={{ marginRight: 8 }} />
                <span>Analizar URL (scraping + Gemini Vision)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="radio"
                  checked={createJobType === 'image'}
                  onChange={() => setCreateJobType('image')}
                />
                <FileImageOutlined style={{ marginRight: 8 }} />
                <span>Analizar imagen (subir archivo)</span>
              </label>
            </Space>
          </Form.Item>

          {createJobType === 'url' ? (
            <Form.Item
              name="url"
              label="URL a analizar"
              rules={[{ required: true, message: 'La URL es obligatoria' }]}
            >
              <Input
                placeholder="https://ejemplo.com/producto/123"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
              />
            </Form.Item>
          ) : (
            <Form.Item label="Imagen" rules={[{ required: true, message: 'Selecciona una imagen' }]}>
              <div style={{ border: '2px dashed #d9d9d9', borderRadius: 8, padding: 24, textAlign: 'center' }}>
                {imagePreview ? (
                  <div>
                    <img src={imagePreview} alt="preview" style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 4 }} />
                    <div style={{ marginTop: 8 }}>
                      <Button type="link" onClick={() => { setImagePreview(null); setImageFile(null); }}>
                        Cambiar imagen
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button icon={<UploadOutlined />} type="dashed" onClick={() => document.getElementById('image-upload')?.click()}>
                    <input
                      id="image-upload"
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={(e) => e.target.files?.[0] && handleImageUpload(e.target.files[0])}
                    />
                    Haz clic para subir una imagen
                  </Button>
                )}
              </div>
            </Form.Item>
          )}

          <Space style={{ marginTop: 24, justifyContent: 'flex-end' }}>
            <Button onClick={() => setCreateJobModalOpen(false)}>Cancelar</Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {createJobType === 'image' ? 'Analizar imagen' : 'Analizar URL'}
            </Button>
          </Space>
        </Form>
      </Modal>
    </div>
  );
};

export default AnalysisPage;