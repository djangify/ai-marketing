const axios = require('axios');
const config = require('../config');
const mediaProcessor = require('./media_processor');
const { encode } = require('tiktoken');

// Headers for requests to Django API
const HEADERS = {
  'Authorization': `Bearer ${config.API_KEY}`,
  'Content-Type': 'application/json'
};

// Process a job
const processJob = async (jobId) => {
  console.log(`Processing job ${jobId}...`);

  try {
    // Update job status to "in_progress"
    await updateJobStatus(jobId, 'in_progress');

    // Set up heartbeat interval
    const heartbeatInterval = setInterval(() => {
      updateJobHeartbeat(jobId).catch(err =>
        console.error(`Error updating heartbeat for job ${jobId}:`, err)
      );
    }, config.HEARTBEAT_INTERVAL_SECONDS * 1000);

    try {
      // Fetch job details to get the asset ID
      const jobResponse = await axios.get(
        `${config.DJANGO_API_BASE_URL}/asset-processing-jobs/${jobId}/`,
        { headers: HEADERS }
      );
      const assetId = jobResponse.data.asset_id;

      // Fetch asset details
      const asset = await fetchAsset(assetId);
      if (!asset) {
        throw new Error(`Asset with ID ${assetId} not found`);
      }

      // Fetch the file content
      const fileBuffer = await fetchAssetFile(asset.file_url);

      // Process the file based on its type
      let content = '';

      if (asset.file_type === 'text' || asset.file_type === 'markdown') {
        console.log(`Text file detected. Reading content of ${asset.file_name}`);
        content = fileBuffer.toString('utf-8');
      }
      else if (asset.file_type === 'audio') {
        console.log('Processing audio file...');
        const chunks = await mediaProcessor.splitAudioFile(
          fileBuffer,
          config.MAX_CHUNK_SIZE_BYTES,
          asset.file_name
        );
        const transcribedChunks = await mediaProcessor.transcribeChunks(chunks);
        content = transcribedChunks.join('\n\n');
      }
      else if (asset.file_type === 'video') {
        console.log('Processing video file...');
        const chunks = await mediaProcessor.extractAudioAndSplit(
          fileBuffer,
          config.MAX_CHUNK_SIZE_BYTES,
          asset.file_name
        );
        const transcribedChunks = await mediaProcessor.transcribeChunks(chunks);
        content = transcribedChunks.join('\n\n');
      }
      else {
        throw new Error(`Unsupported content type: ${asset.file_type}`);
      }

      console.log('FINAL CONTENT:', content);

      // Update asset content
      await updateAssetContent(assetId, content);

      // Update job status to completed
      await updateJobStatus(jobId, 'completed');

      console.log(`Job ${jobId} completed successfully`);
    }
    catch (error) {
      console.error(`Error processing job ${jobId}:`, error);

      // Get current job to update attempts count
      const jobResponse = await axios.get(
        `${config.DJANGO_API_BASE_URL}/asset-processing-jobs/${jobId}/`,
        { headers: HEADERS }
      );

      // Update job status to failed
      await updateJobDetails(jobId, {
        status: 'failed',
        error_message: error.message,
        attempts: jobResponse.data.attempts + 1
      });
    }
    finally {
      // Clear the heartbeat interval
      clearInterval(heartbeatInterval);
    }
  }
  catch (error) {
    console.error(`Error in job processing flow for ${jobId}:`, error);
  }
};

// Fetch asset details
const fetchAsset = async (assetId) => {
  try {
    const response = await axios.get(
      `${config.DJANGO_API_BASE_URL}/assets/${assetId}/`,
      { headers: HEADERS }
    );
    return response.data;
  }
  catch (error) {
    console.error(`Error fetching asset ${assetId}:`, error);
    return null;
  }
};

// Fetch asset file content
const fetchAssetFile = async (fileUrl) => {
  try {
    const response = await axios.get(fileUrl, {
      responseType: 'arraybuffer',
      headers: HEADERS
    });
    return Buffer.from(response.data);
  }
  catch (error) {
    console.error('Error fetching asset file:', error);
    throw new Error('Failed to fetch asset file');
  }
};

// Update asset content
const updateAssetContent = async (assetId, content) => {
  try {
    // Calculate token count
    const encoding = encode();
    const tokens = encoding.encode(content);
    const tokenCount = tokens.length;

    const updateData = {
      content: content,
      token_count: tokenCount
    };

    await axios.patch(
      `${config.DJANGO_API_BASE_URL}/assets/${assetId}/`,
      updateData,
      { headers: HEADERS }
    );
  }
  catch (error) {
    console.error(`Failed to update asset content for asset ${assetId}:`, error);
    throw new Error('Failed to update asset content');
  }
};

// Update job status
const updateJobStatus = async (jobId, status) => {
  await updateJobDetails(jobId, { status });
};

// Update job heartbeat
const updateJobHeartbeat = async (jobId) => {
  try {
    await updateJobDetails(jobId, {
      last_heartbeat: new Date().toISOString()
    });
  }
  catch (error) {
    console.error(`Failed to update job heartbeat for job ${jobId}:`, error);
  }
};

// Update job details
const updateJobDetails = async (jobId, updateData) => {
  try {
    await axios.patch(
      `${config.DJANGO_API_BASE_URL}/asset-processing-jobs/${jobId}/`,
      updateData,
      { headers: HEADERS }
    );
  }
  catch (error) {
    console.error(`Failed to update job details for job ${jobId}:`, error);
    throw error;
  }
};

module.exports = {
  processJob
};