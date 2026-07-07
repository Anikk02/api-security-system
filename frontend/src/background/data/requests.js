// frontend/src/background/data/requests.js
export const requestTypes = {
  GET: { color: '#3498db', icon: '📥' },
  POST: { color: '#2ecc71', icon: '📤' },
  PUT: { color: '#f1c40f', icon: '🔄' },
  DELETE: { color: '#e74c3c', icon: '🗑️' }
};

export const statusTypes = {
  Allowed: { color: '#2ecc71', icon: '✅' },
  Blocked: { color: '#e74c3c', icon: '❌' },
  Throttled: { color: '#f1c40f', icon: '⚠️' }
};