const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'https://signaliq-api.onrender.com',
      changeOrigin: true,
      secure: false,
      logLevel: 'debug'
    })
  );
};
