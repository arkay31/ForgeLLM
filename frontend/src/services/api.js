import axios from 'axios';

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000/api/v1';

const API_KEY = 'forge-secret-key-2026-prod';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});



// ============================================================
// SYSTEM
// ============================================================

export const fetchSystemMetrics = async () => {
  const response =
    await apiClient.get(
      '/system/metrics'
    );

  return response.data;
};


export const fetchSystemHistory = async () => {
  const response =
    await apiClient.get(
      '/system/history'
    );

  return response.data.history;
};


export const fetchLatencyHistory = async () => {
  const response =
    await apiClient.get(
      '/system/latency-history'
    );

  return response.data.history;
};



// ============================================================
// MODELS
// ============================================================

export const fetchModels = async () => {
  const response =
    await apiClient.get('/models');

  return response.data;
};


export const fetchActiveModel = async () => {
  const response =
    await apiClient.get(
      '/models/active'
    );

  return response.data;
};


export const hotSwapModel = async (
  checkpoint_id
) => {

  const response =
    await apiClient.post(
      '/models/active/swap',
      {
        checkpoint_id,
      }
    );

  return response.data;
};


export const deleteCheckpoint = async (
  checkpoint_id
) => {

  const response =
    await apiClient.delete(
      `/models/${checkpoint_id}`
    );

  return response.data;
};


export const rollbackModel = async () => {
  const response = await apiClient.post('/models/rollback');
  return response.data;
};


export const fetchDeploymentHistory = async () => {
  const response = await apiClient.get('/models/deployments/history');
  return response.data;
};



// ============================================================
// FINE-TUNING
// ============================================================

export const triggerFineTuneJob = async (
  jobData
) => {

  const response =
    await apiClient.post(
      '/finetune/jobs',
      jobData
    );

  return response.data;
};


export const fetchTrainingJobs = async () => {

  const response =
    await apiClient.get(
      '/finetune/jobs'
    );

  return response.data;
};


// ============================================================
// INFERENCE
// ============================================================

export const generateSQL = async (
  payload
) => {

  const response =
    await apiClient.post(
      '/serve/generate',
      payload
    );

  return response.data;
};


// ============================================================
// DATASETS
// ============================================================

export const fetchDatasets = async () => {

  const response =
    await apiClient.get(
      '/datasets'
    );

  return response.data;
};


export const fetchDatasetSamples = async (
  datasetName
) => {

  const response =
    await apiClient.get(
      `/datasets/${datasetName}/samples`
    );

  return response.data;
};


export const validateSQL = async (
  sql
) => {

  const response =
    await apiClient.post(
      '/datasets/validate-sql',
      {
        sql,
      }
    );

  return response.data;
};


export const prepareDataset = async (
  dataset = 'spider',
  format_type = 'gemma'
) => {

  const response =
    await apiClient.post(
      `/datasets/prepare?dataset=${dataset}&format_type=${format_type}`
    );

  return response.data;
};


// ============================================================
// EVALUATION
// ============================================================

export const runBenchmark = async (
  datasetName = 'spider_sample.json',
  checkpointId = 'forgellm-qlora-v1-spider',
  limit = 5
) => {

  const response =
    await apiClient.post(
      `/eval/benchmark?dataset_name=${datasetName}&checkpoint_id=${checkpointId}&limit=${limit}`
    );

  return response.data;
};


export const runPerformanceBenchmark = async (payload) => {
  const response = await apiClient.post('/eval/performance-benchmark', payload);
  return response.data;
};

// ============================================================
// EXPERIMENTS & MLOPS
// ============================================================

export const fetchExperiments = async () => {
  const response = await apiClient.get('/experiments');
  return response.data;
};

export const fetchExperiment = async (experimentId) => {
  const response = await apiClient.get(`/experiments/${experimentId}`);
  return response.data;
};

export const compareExperiments = async (exp1Id, exp2Id) => {
  const response = await apiClient.get(`/experiments/compare?exp1_id=${exp1Id}&exp2_id=${exp2Id}`);
  return response.data;
};