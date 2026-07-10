// config.chunk.js
// Medium twist: the API key is not written as one obvious string, but it is still public JS.
(function () {
  const p1 = 'campus';
  const p2 = 'medium';
  const p3 = 'public';
  const p4 = 'api';
  const p5 = 'key';
  const p6 = '2026';

  window.__CAMPUS_CONFIG__ = {
    apiBase: '',
    headers: {
      apiKeyHeader: 'x-api-key',
      sessionHeader: 'x-session-id'
    },
    getApiKey: function () {
      return [p1, p2, p3, p4, p5, p6].join('-');
    }
  };
})();
