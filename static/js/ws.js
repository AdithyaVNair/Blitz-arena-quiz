// ws.js - WebSocket connect with automatic reconnection
class BlitzSocket {
  constructor(path) {
    this.path = path;
    this.socket = null;
    this.handlers = {};
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 5000;
    this.isConnected = false;
    this.connect();
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}${this.path}`;
    
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.emit('open');
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const type = data.type;
        if (type && this.handlers[type]) {
          this.handlers[type].forEach(callback => callback(data));
        }
        this.emit('message', data);
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    this.socket.onclose = () => {
      this.isConnected = false;
      this.emit('close');
      // Auto-reconnect with exponential backoff
      const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), delay);
    };

    this.socket.onerror = (err) => {
      this.emit('error', err);
    };
  }

  on(type, callback) {
    if (!this.handlers[type]) {
      this.handlers[type] = [];
    }
    this.handlers[type].push(callback);
  }

  emit(event, data) {
    if (this.handlers[event]) {
      this.handlers[event].forEach(cb => cb(data));
    }
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('Socket not open, message queued or dropped:', data);
    }
  }

  close() {
    if (this.socket) {
      this.socket.close();
    }
  }
}
