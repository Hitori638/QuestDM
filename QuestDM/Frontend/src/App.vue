<template>
  <div id="app">
    <h1>Welcome to Your Adventure Game</h1>
    <div v-if="!conversationStarted">
      <p>Please choose a mode:</p>
      <button @click="startGame('novel mode')">Novel Mode</button>
      <button @click="startGame('dnd mode')">D&D Mode (Experimental)</button>
      <p v-if="errorMessage" style="color: red;">{{ errorMessage }}</p>
    </div>
    <div v-else>
      <div id="conversation">
        <div v-for="(message, index) in conversation" :key="index">
          <p><strong>{{ message.role }}:</strong> <span v-html="formatMessage(message.content)"></span></p>
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
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'App',
  data() {
    return {
      conversationStarted: false,
      userInput: '',
      conversation: [],
      errorMessage: ''
    };
  },
  methods: {
  
    formatMessage(content) {

      const formatted = content.replace(/(\d\.\s)/g, '<br>$1');
      return formatted;
    },
    async startGame(mode) {
      try {
        await axios.post('http://localhost:5000/start', { mode: mode });
        this.conversationStarted = true;
        this.conversation.push({
          role: 'DM',
          content: 'The game has started. Please enter your action.'
        });
      } catch (error) {
        this.errorMessage = error.response?.data?.error || 'An error occurred.';
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
    }
  }
};
</script>

<style>
#conversation {
  max-width: 800px;
  margin: 20px auto;
  padding: 10px;
  border: 1px solid #ccc;
  overflow-y: auto;
  height: 400px;
}
#input-area {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
#input-area input {
  width: 400px;
  padding: 10px;
  margin-right: 10px;
}
#input-area button {
  padding: 10px 20px;
}
</style>
