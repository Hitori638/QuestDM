// Preload script for Electron
const { contextBridge, ipcRenderer } = require('electron')

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Examples of exposed APIs
  someAction: () => ipcRenderer.invoke('some-action'),
  
  // Add more API methods as needed for your application
  // For example, you might want to handle operations that need Node.js
  // or provide methods to interact with the OS
})