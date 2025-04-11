const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const routes = require('./api/routes');
const config = require('./config');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// API routes
app.use('/api', routes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Start the server
app.listen(config.PORT, () => {
  console.log(`Asset processing service running on port ${config.PORT}`);
});