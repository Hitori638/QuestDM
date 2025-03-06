// api.js - API helper for Electron environment

// Determine if running in Electron production, Electron dev, or web browser
const isElectron = window.navigator.userAgent.toLowerCase().indexOf('electron') > -1;
const isDev = process.env.NODE_ENV === 'development';

// Base URL for API calls
const getBaseUrl = () => {
  if (isElectron) {
    // In Electron production build
    return 'http://localhost:5000';
  } else if (isDev) {
    // In development (browser or Electron dev mode)
    return 'http://localhost:5000';
  } else {
    // In production web app
    return '/api'; // or your production API URL
  }
};

// API helper functions
export const api = {
  async get(endpoint) {
    const response = await fetch(`${getBaseUrl()}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return response.json();
  },
  
  async post(endpoint, data) {
    const response = await fetch(`${getBaseUrl()}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return response.json();
  },
  
  async put(endpoint, data) {
    const response = await fetch(`${getBaseUrl()}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return response.json();
  },
  
  async delete(endpoint, data = null) {
    const options = {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    };
    
    if (data) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${getBaseUrl()}${endpoint}`, options);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return response.json();
  },
  
  // For streaming responses like chat
  getEventSource(endpoint, data) {
    const url = new URL(`${getBaseUrl()}${endpoint}`);
    return fetch(`${getBaseUrl()}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }
};