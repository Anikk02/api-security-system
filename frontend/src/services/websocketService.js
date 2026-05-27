import { WS_URL } from '../utils/constants';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
  }

  connect() {
    try {
      this.ws = new WebSocket(WS_URL);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected', { connected: true });
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.payload);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        this.connect();
      }, this.reconnectDelay);
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index !== -1) callbacks.splice(index, 1);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  send(type, payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
// Add this method to periodically generate random violator locations
export const startMockViolatorStream = (callback, interval = 10000) => {
  const locations = ['New York', 'London', 'Tokyo', 'Shanghai', 'Mumbai', 'Sydney', 'Sao Paulo', 'Moscow', 'Berlin', 'Paris', 'Dubai', 'Singapore', 'Toronto', 'Mexico City', 'Johannesburg'];
  const names = ['Scanner-X', 'Bot-Attack', 'Crawler-Pro', 'API-Abuser', 'DDoS-Source', 'Brute-Force', 'Spam-Bot', 'Data-Scraper'];
  
  return setInterval(() => {
    const newViolator = {
      id: `${names[Math.floor(Math.random() * names.length)]}-${Math.floor(Math.random() * 10000)}`,
      location: locations[Math.floor(Math.random() * locations.length)],
      threatScore: 0.5 + Math.random() * 0.5,
      violations: Math.floor(Math.random() * 50) + 5,
      status: Math.random() > 0.7 ? 'critical' : 'active',
      ip: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
      lastSeen: new Date()
    };
    
    callback(newViolator);
  }, interval);
};

export default new WebSocketService();