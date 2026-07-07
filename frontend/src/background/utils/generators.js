// frontend/src/background/utils/generators.js
export const generateId = () => {
  return Date.now() + '_' + Math.random().toString(36).substr(2, 9);
};

export const randomBetween = (min, max) => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

export const randomItem = (array) => {
  return array[Math.floor(Math.random() * array.length)];
};

export const generateEndpoint = () => {
  const endpoints = ['/api/data', '/api/login', '/api/admin', '/api/user', '/api/transfer'];
  return randomItem(endpoints);
};

export const generateIP = () => {
  const ips = ['192.168.1.10', '172.16.0.5', '120.85.12.44', '203.0.113.25', '198.51.100.7'];
  return randomItem(ips);
};

export const generateMethod = () => {
  const methods = ['GET', 'POST', 'PUT', 'DELETE'];
  return randomItem(methods);
};

export const generateStatus = () => {
  const statuses = ['Allowed', 'Blocked', 'Challenge'];
  return randomItem(statuses);
};