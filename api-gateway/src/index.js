const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const { createProxyMiddleware } = require('http-proxy-middleware');
require('dotenv').config();

const app = express();
const PORT = process.env.API_GATEWAY_PORT || 8080;

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Route to Trade Engine
app.use('/api/engine', createProxyMiddleware({
  target: `http://localhost:${process.env.ENGINE_PORT || 8000}`,
  changeOrigin: true,
  pathRewrite: { '^/api/engine': '' }
}));

// Route to Trade Dashboard
app.use('/api/dashboard', createProxyMiddleware({
  target: `http://localhost:${process.env.DASHBOARD_PORT || 8001}`,
  changeOrigin: true,
  pathRewrite: { '^/api/dashboard': '' }
}));

// Route to Trade Batch
app.use('/api/batch', createProxyMiddleware({
  target: `http://localhost:${process.env.BATCH_PORT || 8002}`,
  changeOrigin: true,
  pathRewrite: { '^/api/batch': '' }
}));

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});