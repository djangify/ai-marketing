require('dotenv').config();

const config = {
  PORT: process.env.PORT || 3000,
  DJANGO_API_BASE_URL: process.env.DJANGO_API_BASE_URL || 'https://www.aimarketingplatform.app/api',
  API_KEY: process.env.API_KEY,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  OPENAI_MODEL: process.env.OPENAI_MODEL || 'whisper-1',
  MAX_CHUNK_SIZE_BYTES: parseInt(process.env.MAX_CHUNK_SIZE_BYTES || (24 * 1024 * 1024)),
  HEARTBEAT_INTERVAL_SECONDS: parseInt(process.env.HEARTBEAT_INTERVAL_SECONDS || 10),
  MAX_JOB_ATTEMPTS: parseInt(process.env.MAX_JOB_ATTEMPTS || 3),
  STUCK_JOB_THRESHOLD_SECONDS: parseInt(process.env.STUCK_JOB_THRESHOLD_SECONDS || 30),
};

module.exports = config;
