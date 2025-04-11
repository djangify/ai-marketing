const express = require('express');
const controllers = require('./controllers');

const router = express.Router();

// Authentication middleware
const authenticate = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid Authorization header' });
  }

  const token = authHeader.split(' ')[1];
  if (token !== process.env.API_KEY) {
    return res.status(403).json({ error: 'Invalid API key' });
  }

  next();
};

// Apply authentication to all routes
router.use(authenticate);

// Asset processing job routes
router.get('/asset-processing-job', controllers.getJobs);
router.patch('/asset-processing-job', controllers.updateJob);

// Asset routes
router.get('/asset', controllers.getAsset);
router.patch('/asset', controllers.updateAsset);

module.exports = router;