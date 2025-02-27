<template>
  <div id="chatbox">
    
    <div id="conversation">
      <h1>{{ storySummary.name }}</h1>
      <div v-for="(message, index) in conversation" :key="index">
        <p :class="{ 'dm-message': message.role === 'DM', 'player-message': message.role === 'You' }">
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

      <button @click="sendMessage" :class="{ streaming: streaming }">
        {{ streaming ? 'Abort' : 'Send' }}
      </button>
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

<style scoped>





#chatbox {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 15px;
  transition: padding 0.5s cubic-bezier(0.19, 1, 0.22, 1);
  position: relative;
}


body.dice-panel-open #chatbox {
  padding-right: 320px;
}

h1 {
  text-align: center;
  font-family: 'Cinzel', serif; 
  color: #d4af37; 
  margin-top: 20px;
  margin-bottom: 30px;
  font-size: 32px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.6);
  letter-spacing: 1px;
}


#conversation {
  max-width: 100%;
  margin: 0 auto 30px;
  padding: 20px;
  border: 2px solid #8D6E63;
  background: rgba(33, 33, 33, 0.75);
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  overflow-y: auto;
  height: 500px;
  transition: all 0.3s;
  position: relative;
}


#conversation p {
  margin: 15px 0;
  padding: 15px;
  border-radius: 10px;
  line-height: 1.6;
  font-size: 16px;
  position: relative;
  transition: all 0.3s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

#conversation p:hover {
  transform: translateX(5px);
}


#conversation p strong {
  font-weight: 700;
  font-size: 18px;
  margin-right: 10px;
}


.dm-message {
  background-color: rgba(62, 39, 35, 0.85) !important; 
  border-left: 3px solid #4CAF50 !important;
}

.dm-message strong {
  color: #4CAF50 !important;
}


.player-message {
  background-color: rgba(62, 39, 35, 0.85) !important;
  border-left: 3px solid #d4af37 !important;
}

.player-message strong {
  color: #d4af37 !important;
}

/* Input area */
#input-area {
  display: flex;
  justify-content: center;
  margin: 0 auto;
  max-width: 100%;
  position: relative;
  transition: padding 0.5s cubic-bezier(0.19, 1, 0.22, 1);
}

#input-area input {
  flex-grow: 1;
  padding: 15px;
  border: 2px solid #8D6E63;
  border-radius: 8px 0 0 8px;
  background-color: rgba(78, 52, 46, 0.9);
  color: #fff;
  font-size: 16px;
  transition: all 0.3s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

#input-area input:focus {
  outline: none;
  border-color: #d4af37;
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.3);
}

#input-area input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

#input-area button {
  padding: 15px 25px;
  border: none;
  border-radius: 0 8px 8px 0;
  background-color: #8b4513;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

#input-area button:hover {
  background-color: #a0522d;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

#input-area button:active {
  transform: translateY(0);
}

/* Streaming button state */
#input-area button.streaming {
  background-color: #C62828;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

/* Saving overlay popup */
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.popup-content {
  background: linear-gradient(to bottom, #3d2824, #4E342E);
  padding: 30px 50px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}

.popup-content p {
  margin-top: 15px;
  font-size: 18px;
  color: #d4af37;
  font-weight: 600;
}

/* Spinner animation */
.spinner {
  margin: 0 auto;
  border: 5px solid rgba(78, 52, 46, 0.3);
  border-top: 5px solid #d4af37;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive design for story component */
@media (max-width: 768px) {
  #conversation {
    height: 400px;
    padding: 15px;
  }
  
  #input-area input,
  #input-area button {
    padding: 12px;
  }
  
  h1 {
    font-size: 24px;
    margin-top: 15px;
    margin-bottom: 20px;
  }
  
  body.dice-panel-open #chatbox {
    padding-right: 15px;
  }
}
</style>
