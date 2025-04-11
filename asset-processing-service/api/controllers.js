const axios = require('axios');
const config = require('../config');
const jobProcessor = require('../services/job_processor');

// Headers for requests to Django API
const HEADERS = {
  'Authorization': `Bearer ${config.API_KEY}`,
  'Content-Type': 'application/json'
};

// Get available jobs from Django
const getJobs = async (req, res) => {
  try {
    const response = await axios.get(`${config.DJANGO_API_BASE_URL}/asset-processing-jobs/`, {
      headers: HEADERS
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching jobs:', error);
    res.status(500).json({ error: 'Failed to fetch jobs' });
  }
};

// Update job status
const updateJob = async (req, res) => {
  const { jobId } = req.query;
  if (!jobId) {
    return res.status(400).json({ error: 'Missing jobId parameter' });
  }

  try {
    const response = await axios.patch(
      `${config.DJANGO_API_BASE_URL}/asset-processing-jobs/${jobId}/`,
      req.body,
      { headers: HEADERS }
    );
    res.json(response.data);
  } catch (error) {
    console.error(`Error updating job ${jobId}:`, error);
    res.status(500).json({ error: 'Failed to update job' });
  }
};

// Get asset details
const getAsset = async (req, res) => {
  const { assetId } = req.query;
  if (!assetId) {
    return res.status(400).json({ error: 'Missing assetId parameter' });
  }

  try {
    const response = await axios.get(
      `${config.DJANGO_API_BASE_URL}/assets/${assetId}/`,
      { headers: HEADERS }
    );
    res.json(response.data);
  } catch (error) {
    console.error(`Error fetching asset ${assetId}:`, error);
    res.status(500).json({ error: 'Failed to fetch asset' });
  }
};

// Update asset content
const updateAsset = async (req, res) => {
  const { assetId } = req.query;
  if (!assetId) {
    return res.status(400).json({ error: 'Missing assetId parameter' });
  }

  try {
    const response = await axios.patch(
      `${config.DJANGO_API_BASE_URL}/assets/${assetId}/`,
      req.body,
      { headers: HEADERS }
    );
    res.json(response.data);
  } catch (error) {
    console.error(`Error updating asset ${assetId}:`, error);
    res.status(500).json({ error: 'Failed to update asset' });
  }
};

// Process job worker
const processJob = async (req, res) => {
  const { jobId } = req.body;
  if (!jobId) {
    return res.status(400).json({ error: 'Missing jobId parameter' });
  }

  try {
    // Start job processing in the background
    jobProcessor.processJob(jobId)
      .catch(error => console.error(`Error processing job ${jobId}:`, error));

    res.json({ message: 'Job processing started' });
  } catch (error) {
    console.error(`Error starting job processing for ${jobId}:`, error);
    res.status(500).json({ error: 'Failed to start job processing' });
  }
};

module.exports = {
  getJobs,
  updateJob,
  getAsset,
  updateAsset,
  processJob
};
