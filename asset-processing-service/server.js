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


// In server.js, add this route before your other routes

// Simple homepage route
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Asset Processing Service</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          line-height: 1.6;
        }
        .container {
          background-color: #f7f9fc;
          border-radius: 10px;
          padding: 30px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          margin-top: 40px;
        }
        h1 {
          color: #9810fa;
          margin-top: 0;
        }
        .status {
          background-color: #e6ffed;
          border-left: 4px solid #28a745;
          padding: 10px 15px;
          margin-bottom: 20px;
        }
        .button {
          display: inline-block;
          background-color: #9810fa;
          color: white;
          padding: 10px 20px;
          text-decoration: none;
          border-radius: 5px;
          font-weight: bold;
          margin-top: 20px;
        }
        .button:hover {
          background-color: #8300d9;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Asset Processing Service</h1>
        <div class="status">
          <p>✅ Service is running</p>
        </div>
        <p>This is the backend service for processing audio and video files for the AI Marketing Platform.</p>
        <p> It communicates with the main application through API endpoints.</p>
        <a href="https://www.aimarketingplatform.app" class="button">Return to Main Site</a>
      </div>
    </body>
    </html>
  `);
});


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