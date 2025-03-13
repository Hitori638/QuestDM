// api.js - Enhanced API helper for Electron environment
// Determine if running in Electron production, Electron dev, or web browser
const isElectron = window.navigator.userAgent.toLowerCase().indexOf('electron') > -1;
const isDev = process.env.NODE_ENV === 'development';


const getBaseUrl = () => {
  if (isElectron) {

    return 'http://localhost:5000';
  } else if (isDev) {
 
    return 'http://localhost:5000';
  } else {

    return '/api'; 
  }
};


const getCommonOptions = () => ({
  mode: 'cors', 
  credentials: 'same-origin', 
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});


const fetchWithRetry = async (url, options, retries = 3, delay = 500) => {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (retries > 0) {
      console.warn(`Request failed, retrying... (${retries} attempts left)`);
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 1.5);
    }
    throw error;
  }
};


export const api = {
  async get(endpoint) {
    const options = {
      ...getCommonOptions(),
      method: 'GET',
    };
    
    const response = await fetchWithRetry(
      `${getBaseUrl()}${endpoint}`, 
      options
    );
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  },
 
  async post(endpoint, data) {
    const options = {
      ...getCommonOptions(),
      method: 'POST',
      body: JSON.stringify(data),
    };
    
    const response = await fetchWithRetry(
      `${getBaseUrl()}${endpoint}`, 
      options
    );
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  },
 
  async put(endpoint, data) {
    const options = {
      ...getCommonOptions(),
      method: 'PUT',
      body: JSON.stringify(data),
    };
    
    const response = await fetchWithRetry(
      `${getBaseUrl()}${endpoint}`, 
      options
    );
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  },
 
  async delete(endpoint, data = null) {
    const options = {
      ...getCommonOptions(),
      method: 'DELETE',
    };
   
    if (data) {
      options.body = JSON.stringify(data);
    }
   
    const response = await fetchWithRetry(
      `${getBaseUrl()}${endpoint}`, 
      options
    );
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  },
 

  getEventSource(endpoint, data) {
    const options = {
      ...getCommonOptions(),
      method: 'POST',
      body: JSON.stringify(data),
    };
    
    return fetchWithRetry(`${getBaseUrl()}${endpoint}`, options);
  },
  

  async testCors() {
    try {
      const response = await fetch(`${getBaseUrl()}/cors-test`, {
        mode: 'cors',
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        return {
          success: false,
          status: response.status,
          statusText: response.statusText
        };
      }
      
      const data = await response.json();
      return {
        success: true,
        data,
        cors: "CORS is working correctly!"
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        cors: "CORS test failed"
      };
    }
  }
};