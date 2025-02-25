<template>
  <div id="chatbox">
    <h1>{{ storySummary.name }}</h1>
    <div id="conversation">
      <div v-for="(message, index) in conversation" :key="index">
        <p>
          <strong>{{ message.role }}:</strong> {{ message.content }}
        </p>
      </div>
    </div>
    <div id="input-area">
      <input
        v-model="userInput"
        @keyup.enter="sendMessage"
        placeholder="Your action..."
      />

      <button @click="sendMessage">{{ streaming ? 'Abort' : 'Send' }}</button>
      <button @click="saveStory">Save Story</button>
    </div>
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
  props: {
    storySummary: {
      type: Object,
      required: true,
    },
    conversation: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      userInput: '',
      saving: false,
      streaming: false,       
      abortController: null,  
    };
  },
  methods: {
    async sendMessage() {
      if (this.streaming) {
        if (this.abortController) {
          this.abortController.abort();
          this.streaming = false;
          console.log('Streaming aborted by user.');
        }
        return;
      }
      
      if (!this.userInput.trim()) return;
      const message = this.userInput.trim();
      this.conversation.push({ role: 'You', content: message });
      this.userInput = '';
      const dmMessage = { role: 'DM', content: '' };
      this.conversation.push(dmMessage);
      
      this.abortController = new AbortController();
      this.streaming = true;
      
      try {
        const response = await fetch('http://localhost:5000/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            story_name: this.storySummary.name,
            story_details: this.storySummary,
            message: message,
          }),
          signal: this.abortController.signal,
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
                content: dmMessage.content,
              };
            }
          }
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Fetch aborted.');
        } else {
          dmMessage.content = 'Failed to receive a response. Please try again.';
          this.conversation[this.conversation.length - 1] = dmMessage;
        }
      } finally {
        this.streaming = false;
        this.abortController = null;
      }
    },
    async saveStory() {
      this.saving = true;
      try {
        const response = await fetch('http://localhost:5000/save_story', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: this.storySummary.name,
            conversation: this.conversation,
          }),
        });
        if (!response.ok) {
          throw new Error('Failed to save the story');
        }
        const data = await response.json();
        alert(data.message || 'Story saved successfully!');
      } catch (error) {
        console.error(error);
        alert('Error saving the story.');
      } finally {
        this.saving = false;
      }
    },
  },
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

.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.popup-content {
  background: #fff;
  padding: 20px 40px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.spinner {
  margin: 0 auto 10px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #555;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
