const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const process = require('process');
const findProcess = require('find-process');
const kill = require('tree-kill');

let mainWindow;
let pythonProcess = null;
let serverPort = 5000;
let pythonPath = 'python3'; 
let serverScriptPath = path.join(__dirname, '..', 'Backend', 'app.py');


function startPythonServer() {
  console.log('Starting Python Flask server...');
  

  cleanupExistingProcesses()
    .then(() => {
 
      pythonProcess = spawn(pythonPath, [serverScriptPath]);
      

      pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
      });
      
      pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
      });
      
      pythonProcess.on('close', (code) => {
        console.log(`Python server process exited with code ${code}`);
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
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  

  mainWindow.loadURL('http://localhost:8080'); 
  

  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}


app.on('ready', startPythonServer);


app.on('will-quit', () => {
  cleanupPythonProcess();
});


app.on('window-all-closed', () => {

  if (process.platform !== 'darwin') {
    cleanupPythonProcess();
    app.quit();
  }
});

app.on('activate', () => {

  if (mainWindow === null) {
    createMainWindow();
  }
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


process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  cleanupPythonProcess();
  app.exit(1);
});