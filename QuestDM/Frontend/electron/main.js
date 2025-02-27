// Electron main process file
const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('node:path')
const { spawn } = require('child_process')
const isDev = process.env.NODE_ENV === 'development'

let mainWindow
let flaskProcess

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'build/icon.png')
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')  // Development: Vite dev server
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist_electron/index.html'))  // Production: Local file
  }
  

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// Start Flask backend
function startFlaskBackend() {
  console.log('Starting Flask backend...')

  // Adjust paths based on your project structure
  // For development - Backend is next to Frontend
  let flaskPath = isDev
    ? path.join(__dirname, '..', '..', 'Backend')
    // For production - Backend is in extraResources
    : path.join(process.resourcesPath, 'backend')

  console.log(`Looking for Flask backend at: ${flaskPath}`)

  // Try to use python or python3 based on platform
  const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3'

  console.log(`Using Python executable: ${pythonExecutable}`)

  try {
    // Spawn Flask process with shell option for better compatibility
    flaskProcess = spawn(pythonExecutable, [path.join(flaskPath, 'app.py')], {
      cwd: flaskPath,
      shell: true,
      env: process.env
    })
   
    flaskProcess.stdout.on('data', (data) => {
      console.log(`Flask stdout: ${data}`)
    })
   
    flaskProcess.stderr.on('data', (data) => {
      console.error(`Flask stderr: ${data}`)
     
      // If stderr contains ENOENT, it means Python wasn't found
      if (data.toString().includes('ENOENT') || data.toString().includes('not found')) {
        dialog.showErrorBox(
          'Python Not Found',
          `QuestDM requires Python to run. Please install Python and make sure it's in your PATH.`
        )
      }
    })
   
    flaskProcess.on('error', (error) => {
      console.error(`Failed to start Flask process: ${error}`)
     
      if (error.code === 'ENOENT') {
        dialog.showErrorBox(
          'Python Not Found',
          `QuestDM requires Python to run. Please install Python and make sure it's in your PATH.`
        )
      }
    })
   
    flaskProcess.on('close', (code) => {
      console.log(`Flask process exited with code ${code}`)
     
      if (code !== 0 && code !== null) {
        dialog.showErrorBox(
          'Backend Error',
          `The Flask backend crashed with code ${code}. Please check the logs for details.`
        )
      }
    })
  } catch (error) {
    console.error('Error starting Flask backend:', error)
    dialog.showErrorBox(
      'Backend Error',
      `Failed to start the Flask backend: ${error.message}`
    )
  }
}

app.whenReady().then(() => {
  startFlaskBackend()
  createWindow()
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (flaskProcess) {
      flaskProcess.kill()
    }
    app.quit()
  }
})

app.on('before-quit', () => {
  if (flaskProcess) {
    flaskProcess.kill()
  }
})

// Handle IPC messages from renderer process if needed
ipcMain.handle('some-action', async () => {
  // Do something
  return 'result'
})