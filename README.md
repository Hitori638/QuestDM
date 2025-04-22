# QuestDM
## Interactive Storytelling and Role-Playing Application with Local Language Models

**QuestDM** is a desktop application developed as part of my bachelor's thesis, serving as an academic exploration of interactive storytelling and role-playing using local language models. The application enables users to create and experience immersive narrative adventures with AI-powered storytelling in two distinct modes:

- **Novel Mode**: Rich, literary storytelling focused on narrative quality and style.  
- **D&D Mode**: Structured role-playing experience implementing Dungeons & Dragons 5th Edition rules and mechanics.

## Key Features

- **Dynamic Story Generation**: AI-powered narrative creation that responds to user choices and actions.  
- **Character Management System**: Create, edit, and manage characters with D&D-style attributes and backstories.  
- **Virtual Dice Roller**: Integrated dice system for RPG mechanics with preset and custom dice configurations.  
- **Local LLM Integration**: Powered by local language models through Ollama, with no need for external API calls.  
- **Model Selection**: Freedom to choose from any compatible model installed via Ollama based on performance needs and available computing resources.  
- **Real-time Response Streaming**: See the AI's responses as they're generated for improved user experience.  
- **Story Summarization**: Automatic context compression for maintaining narrative consistency in long adventures.

## Technical Architecture

QuestDM employs a multi-layered architecture:

- **Frontend**: Vue.js application bundled with Electron for cross-platform desktop compatibility  
- **Backend**: Flask-based API server handling communication with language models  
- **Database**: TinyDB document-based storage for story and character persistence  
- **LLM Integration**: Ollama API for interfacing with local language models  
- **Packaging**: Electron for creating native desktop applications

## Installation Guide

To get started with **QuestDM**, follow these steps:

1. **Install Python**  
   - Make sure you have **Python 3.11 or higher** installed.  
   - Download it from the official site: [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. **Install Ollama**  
   - Download and install Ollama from: [https://ollama.com/](https://ollama.com/)  
   - Follow the installation instructions for your OS.

3. **Download at Least One LLM**  
   - After installing Ollama, run a command like the following to install a model:  
     ```
     ollama run llama3
     ```
   - The recommended model for QuestDM is:  
     ```
     ollama run llama3.2-vision:latest
     ```

4. **Download the Latest Release**  
   - Download the latest version of the application zip file for your operating system.  
   - Extract the zip file to a desired location on your system.

5. **Run the Application**  
   - On **Windows**: Inside the extracted folder, locate and run the `QuestDM.exe` file.
   - On **macOS/Linux**: You will need to build the application from source (see next step).

6. **Building for macOS/Linux from Source**  
   - If you're not using the Windows release, you'll need to build the application from source:
     - Clone the repository
     - Navigate into the project directory
     - Run `npm install`
     - Then run `npm run electron:build` to build a native version for your OS
   - Make sure you have **Node.js**, **npm**, and **Electron** installed before building.


## Requirements

- **Ollama**: Required for running local language models  
- **Recommended Model**: `llama3.2-vision:latest` (optimized for this application)  
- **Python Version**: 3.11 or higher  
- **Hardware**: 16GB+ RAM recommended for optimal performance  
- **OS Support**: Windows, macOS, and Linux (through Electron)

## Academic Purpose

This project demonstrates the potential of local language models for interactive narrative experiences and role-playing games. It explores technical solutions for optimizing context management, handling JSON outputs from LLMs, and creating responsive user interfaces for AI-driven applications.

## Future Development

- Visual content generation integration  
- Multiplayer support  
- Export/import functionality for stories and characters  
- Support for additional rule systems beyond D&D 5E  
- Performance optimizations for lower-end hardware

## License

This project is academic in nature and **not intended for commercial use**.
