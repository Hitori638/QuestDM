<template>
  <div id="app">
    <h1>Welcome to Your Adventure Game</h1>
    
    <div v-if="!conversationStarted" id="selection-area">
      <p>Please choose a mode:</p>
      <div id="mode-buttons">
        <button @click="startGame('novel mode')">Novel Mode</button>
        <button @click="startGame('dnd mode')">D&D Mode (Experimental)</button>
      </div>
      <p v-if="errorMessage" style="color: red;">{{ errorMessage }}</p>
    </div>
    <div v-else>
      <div id="conversation">
        <div v-for="(message, index) in conversation" :key="index">
          <p>
            <strong>{{ message.role }}:</strong>
            <span v-html="formatMessage(message.content)"></span>
          </p>
        </div>
      </div>
      <div id="input-area">
        <input
          v-model="userInput"
          @keyup.enter="sendMessage"
          placeholder="Your action..."
        />
        <button @click="sendMessage">Send</button>
        <button @click="resetGame">Restart</button>
        
        <!-- NEW: Save Story button -->
        <button @click="saveStory">Save Story</button>
      </div>
    </div>
    
    <!-- NEW: Popup Overlay when saving -->
    <div v-if="saving" class="popup-overlay">
      <div class="popup-content">
        <div class="spinner"></div>
        <p>Saving Story...</p>
      </div>
    </div>
    
  </div>
</template>

<script>
export default {
  name: 'StoryView',
  data() {
    return {
      conversationStarted: false,
      userInput: '',
      conversation: [],
      errorMessage: '',
      // NEW: track saving state
      saving: false
    };
  },
  methods: {
    formatMessage(content) {
      const formatted = content.replace(/(\d\.\s)/g, '<br>$1');
      return formatted;
    },
    async startGame(mode) {
      try {
        const response = await fetch('http://localhost:5000/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: mode })
        });

        if (!response.ok) {
          throw new Error('Failed to start the game');
        }

        this.conversationStarted = true;
        this.conversation.push({
          role: 'DM',
          content: 'The game has started. Please enter your action.'
        });
      } catch (error) {
        this.errorMessage = error.message || 'An error occurred.';
      }
    },
    async sendMessage() {
      if (!this.userInput.trim()) {
        return;
      }

      const message = this.userInput.trim();
      this.conversation.push({ role: 'You', content: message });
      this.userInput = '';

      const dmMessage = { role: 'DM', content: '' };
      this.conversation.push(dmMessage);

      try {
        const response = await fetch('http://localhost:5000/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: message })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let done = false;

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;

          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            const match = chunk.match(/data: (.+)\n\n/);
            if (match) {
              const data = JSON.parse(match[1]);
              dmMessage.content += data.content;

              this.conversation[this.conversation.length - 1] = {
                role: 'DM',
                content: this.formatMessage(dmMessage.content)
              };
            }
          }
        }
      } catch (error) {
        dmMessage.content = 'Failed to receive a response. Please try again.';
        this.conversation[this.conversation.length - 1] = dmMessage;
      }
    },
    resetGame() {
      this.conversationStarted = false;
      this.userInput = '';
      this.conversation = [];
    },

    // NEW: Save Story method
    async saveStory() {
      this.saving = true; // show popup
      try {
        const response = await fetch('http://localhost:5000/save_story', {
          method: 'GET'
        });

        if (!response.ok) {
          throw new Error('Failed to save the story');
        }

        // We expect JSON: { summary: "...some story summary..." }
        const data = await response.json();
        // If you want to do something with `data.summary`, do it here
        // For example: this.savedSummary = data.summary; 
        console.log(data.summary);
      } catch (error) {
        console.error(error);
      } finally {
        this.saving = false; // hide popup
      }
    }
  }
};
</script>

<style>
body {
  font-family: 'Lora', serif;
  background: linear-gradient(to bottom, #d3d3d3, #b0b0b0);
  color: #3c3c3c;
  margin: 0;
  padding: 0;
}

h1 {
  text-align: center;
  font-family: 'Arial', sans-serif;
  color: #4f4f4f;
  margin-top: 20px;
  text-shadow: 0 0 3px #a0a0a0;
}

#selection-area {
  text-align: center;
  margin-top: 40px;
}

#mode-buttons {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
}

#conversation {
  max-width: 800px;
  margin: 20px auto;
  padding: 15px;
  border: 2px solid #a8a8a8;
  background: rgba(210, 210, 210, 0.95);
  border-radius: 10px;
  box-shadow: 0 0 5px rgba(150, 150, 150, 0.6);
  overflow-y: auto;
  height: 400px;
}

#conversation p {
  margin: 10px 0;
  padding: 10px;
  border-radius: 10px;
  line-height: 1.5;
}

#conversation p strong {
  color: #4f4f4f;
}

#conversation p:nth-child(odd) {
  background-color: rgba(190, 190, 190, 0.9);
}

#conversation p:nth-child(even) {
  background-color: rgba(220, 220, 220, 0.9);
}

#input-area {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

#input-area input {
  width: 400px;
  padding: 10px;
  border: 2px solid #a8a8a8;
  border-radius: 5px;
  background: #eaeaea;
  color: #3c3c3c;
  font-size: 16px;
}

#input-area button {
  padding: 10px 20px;
  margin-left: 10px;
  border: none;
  border-radius: 5px;
  background: #7f7f7f;
  color: #ffffff;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.3s, transform 0.2s;
}

#input-area button:hover {
  background: #5f5f5f;
  transform: scale(1.05);
}

#input-area button:active {
  transform: scale(0.95);
}

::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-thumb {
  background: #a8a8a8;
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: #888888;
}

/* NEW: Popup overlay styles */
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0,0,0,0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999; /* Ensure it appears over everything */
}

.popup-content {
  background: #fff;
  padding: 20px 40px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.spinner {
  margin: 0 auto 10px;
  border: 5px solid #f3f3f3; /* light grey */
  border-top: 5px solid #555; /* dark color for the spinning part */
  border-radius: 50%;
  width: 36px;
  height: 36px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
