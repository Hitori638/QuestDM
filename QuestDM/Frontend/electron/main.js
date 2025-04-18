const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const process = require('process');
const findProcess = require('find-process');
const kill = require('tree-kill');

const isDev = process.env.NODE_ENV === 'development';

let mainWindow;
let pythonProcess = null;
let serverPort = 5000;
let pythonPath = process.platform === 'win32' ? 'python' : 'python3';
let serverScriptPath;


if (isDev) {

  serverScriptPath = path.join(__dirname, '..', '..', 'Backend', 'app.py');
} else {

  serverScriptPath = path.join(process.resourcesPath, 'backend', 'app.py');
}


function startPythonServer() {
  console.log('Starting Python Flask server...');
  console.log(`Looking for Flask backend at: ${serverScriptPath}`);
  console.log(`Using Python executable: ${pythonPath}`);
  

  cleanupExistingProcesses()
    .then(() => {

      pythonProcess = spawn(pythonPath, [serverScriptPath], {
        shell: true,
        env: process.env
      });
      

      pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
      });
      
      pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
        

        if (data.toString().includes('ENOENT') || data.toString().includes('not found')) {
          dialog.showErrorBox(
            'Python Not Found',
            `QuestDM requires Python to run. Please install Python and make sure it's in your PATH.`
          );
        }
      });
      
      pythonProcess.on('error', (error) => {
        console.error(`Failed to start Flask process: ${error}`);
        
        if (error.code === 'ENOENT') {
          dialog.showErrorBox(
            'Python Not Found',
            `QuestDM requires Python to run. Please install Python and make sure it's in your PATH.`
          );
        }
      });
      
      pythonProcess.on('close', (code) => {
        console.log(`Python server process exited with code ${code}`);
        
        if (code !== 0 && code !== null) {
          dialog.showErrorBox(
            'Backend Error',
            `The Flask backend crashed with code ${code}. Please check the logs for details.`
          );
        }
        
        pythonProcess = null;
      });
      

      console.log('Waiting for Flask server to start...');
      setTimeout(() => {
        createMainWindow();
      }, 1000);
    })
    .catch((err) => {
      console.error('Failed to clean up existing processes:', err);
      createMainWindow();
    });
}


async function cleanupExistingProcesses() {
  try {
    const processList = await findProcess('port', serverPort);
    
    if (processList.length > 0) {
      console.log(`Found ${processList.length} existing processes on port ${serverPort}`);
      
      for (const proc of processList) {
        console.log(`Killing process ${proc.pid} (${proc.name})`);
        kill(proc.pid, 'SIGTERM', (err) => {
          if (err) {
            console.error(`Failed to kill process ${proc.pid}:`, err);
          }
        });
      }
      

      return new Promise(resolve => setTimeout(resolve, 500));
    }
  } catch (e) {
    console.error('Error finding processes:', e);
  }
  
  return Promise.resolve();
}


function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'build/icon.png')
  });
  

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');  
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist_electron/index.html'));  
  }
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}


app.whenReady().then(() => {
  startPythonServer();
  
  app.on('activate', () => {

    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});


app.on('will-quit', () => {
  cleanupPythonProcess();
});


app.on('window-all-closed', () => {

  if (process.platform !== 'darwin') {
    cleanupPythonProcess();
    app.quit();
  }
});

app.on('before-quit', () => {
  cleanupPythonProcess();
});


function cleanupPythonProcess() {
  if (pythonProcess) {
    console.log('Terminating Python Flask server...');
    

    kill(pythonProcess.pid, 'SIGTERM', (err) => {
      if (err) {
        console.error('Failed to kill Python process:', err);
        
   
        pythonProcess.kill();
      }
      
      pythonProcess = null;
    });
  }
  

  cleanupExistingProcesses().catch(err => {
    console.error('Error during final cleanup:', err);
  });
}


ipcMain.handle('some-action', async () => {

  return 'result';
});


process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  cleanupPythonProcess();
  app.exit(1);
});