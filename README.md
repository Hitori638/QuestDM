# QuestDM

## Interactive Storytelling and Role-Playing Application

This project is part of my bachelor's thesis and serves as an academic exploration of interactive storytelling and role-playing using AI models. The application enables users to engage in immersive narrative experiences in two modes:
- **Novel Mode**: A rich, immersive storytelling mode for creative adventures.
- **D&D Mode**: A structured role-playing experience based on Dungeons & Dragons mechanics.

## Purpose

The primary purpose of this application is academic. It demonstrates how advanced AI models can be integrated into narrative-driven applications for educational and personal exploration. This project is **not intended for commercial use**.

## Features

- **Dynamic Conversation Modes**:
  - **Novel Mode**: Crafting compelling, immersive adventures.
  - **D&D Mode**: Following D&D 5th Edition rules for role-playing.
- **Streaming Chat**: Real-time responses for a seamless user experience.
- **Model Flexibility**: The application is designed to work with any AI model installed via [Ollama](https://ollama.ai). Users can switch between models based on their preferences.
- **Interactive Design**: User choices dynamically influence story progression.

## Technical Details

This application uses a **Flask backend** for handling API requests and a **Vue.js frontend** for the user interface. The backend leverages the [Ollama](https://ollama.ai) framework to interact with AI models. Although the project initially used the **Mistral Small** model, it is built to work with any model that a user installs via Ollama, and users can seamlessly switch between models as desired.

### Key Dependencies

#### **Backend**
- **Flask**: Web framework for the application.
- **Ollama**: Local AI runtime and chat interface, supporting multiple models.

#### **Frontend**
- **Vue.js**: Framework for building the interactive user interface.

