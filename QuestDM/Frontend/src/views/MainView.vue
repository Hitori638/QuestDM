<template>
  <div id="main-view">
    <header>
      <h1>Welcome, Adventurer!</h1>
      <!-- Settings Button -->
      <button class="settings-btn" @click="openSettingsModal">⚙️</button>
    </header>
    <div id="content">
      <aside id="sidebar">
        <div id="tabs">
          <button @click="currentTab = 'stories'">Your Stories</button>
          <button @click="currentTab = 'characters'">Your Characters</button>
        </div>
        <div v-if="currentTab === 'stories'">
          <div id="stories">
            <h2>Stories</h2>
            <ul>
              <li v-for="(story, index) in stories" :key="index">
                <span
                  @click="openStory(story)"
                  class="story-title"
                  :class="{ selected: selectedStory && selectedStory.name === story.name }"
                >
                  {{ story.name }}
                </span>
                <button class="edit-btn" @click="openEditStoryModal(story)">✏️</button>
                <button class="delete-btn" @click="openDeleteConfirmation(story, index, 'story')">🗑️</button>
              </li>
            </ul>
            <button @click="showCreateStoryModal = true">Create a Story</button>
          </div>
        </div>
        <div v-else-if="currentTab === 'characters'">
          <div id="characters">
            <h2>Characters</h2>
            <ul>
              <li v-for="(character, index) in characters" :key="index">
                <span>{{ character.name }}</span>
                <button class="edit-btn" @click="openEditCharacterModal(character)">✏️</button>
                <button class="delete-btn" @click="openDeleteConfirmation(character, index, 'character')">🗑️</button>
              </li>
            </ul>
            <button @click="showCreateCharacterModal = true">Create a Character</button>
          </div>
        </div>
      </aside>
      <main id="main-content">
        <div v-if="!selectedStory">
          <p>Select a story to begin your adventure!</p>
        </div>
        <div v-else>
          <h2>{{ selectedStory.name }}</h2>
          <StoryComponent :storySummary="selectedStory" :conversation="conversation" />
        </div>
      </main>
    </div>

    <!-- MODALS SECTION -->
    <!-- Create Story Modal -->
    <div v-if="showCreateStoryModal" id="create-story-modal">
      <div class="modal-overlay" @click="closeModal"></div>
      <div class="modal-content">
        <h2>Create a New Story</h2>
        <label>
          Name:
          <input v-model="newStory.name" type="text" placeholder="Story Name" />
        </label>
        <label>
          Description:
          <textarea v-model="newStory.description" placeholder="Story Description"></textarea>
        </label>
        <label>
          Genre:
          <input v-model="newStory.genre" type="text" placeholder="Story Genre" />
        </label>
        <label>
          Mode:
          <select v-model="newStory.mode">
            <option value="dnd">DND</option>
            <option value="novel">Novel</option>
          </select>
        </label>

        <!-- Character + Dropdown for Create Story -->
        <div class="character-section">
          <label>Characters:</label>
          <div class="chips-container">
 
            <span class="chip" v-for="(charName, idx) in newStory.characters" :key="idx">
              {{ charName }}
              <button class="remove-chip" @click="removeCharacterFromNewStory(charName)">✕</button>
            </span>
          </div>
          <div class="add-character-row">
            <select v-model="selectedCharacterToAddNew">
              <option disabled value="">-- Select a character --</option>
              <option 
                v-for="char in availableCharactersForNew" 
                :key="char.name" 
                :value="char.name"
              >
                {{ char.name }}
              </option>
            </select>
            <button @click="addCharacterToNewStory">Add</button>
          </div>
        </div>

        <button @click="saveStoryData">Save Story</button>
        <button @click="closeModal">Cancel</button>
      </div>
    </div>

    <!-- Edit Story Modal -->
    <div v-if="showEditStoryModal" id="edit-story-modal">
      <div class="modal-overlay" @click="closeModal"></div>
      <div class="modal-content">
        <h2>Edit Story</h2>
        <label>
          Name:
          <input v-model="editedStory.name" type="text" placeholder="Story Name" />
        </label>
        <label>
          Description:
          <textarea v-model="editedStory.description" placeholder="Story Description"></textarea>
        </label>
        <label>
          Genre:
          <input v-model="editedStory.genre" type="text" placeholder="Story Genre" />
        </label>
        <label>
          Mode:
          <select v-model="editedStory.mode">
            <option value="dnd">DND</option>
            <option value="novel">Novel</option>
          </select>
        </label>

        <!-- Character + Dropdown for Edit Story -->
        <div class="character-section">
          <label>Characters:</label>
          <div class="chips-container">

            <span class="chip" v-for="(charName, idx) in editedStory.characters" :key="idx">
              {{ charName }}
              <button class="remove-chip" @click="removeCharacterFromEditedStory(charName)">✕</button>
            </span>
          </div>
          <div class="add-character-row">
            <select v-model="selectedCharacterToAddEdit">
              <option disabled value="">-- Select a character --</option>
              <option 
                v-for="char in availableCharactersForEdit" 
                :key="char.name" 
                :value="char.name"
              >
                {{ char.name }}
              </option>
            </select>
            <button @click="addCharacterToEditedStory">Add</button>
          </div>
        </div>

        <button @click="saveEditedStoryData">Save Changes</button>
        <button @click="closeModal">Cancel</button>
      </div>
    </div>

    <!-- Create Character Modal -->
    <div v-if="showCreateCharacterModal" id="create-character-modal">
      <div class="modal-overlay" @click="closeModal"></div>
      <div class="modal-content">
        <h2>Create a New Character</h2>
        <label>
          Name:
          <input v-model="newCharacter.name" type="text" placeholder="Character Name" />
        </label>
        <label>
          Race:
          <input v-model="newCharacter.race" type="text" placeholder="Character Race" />
        </label>
        <label>
          Class:
          <input v-model="newCharacter.class" type="text" placeholder="Character Class" />
        </label>
        <textarea v-model="newCharacter.backstory" placeholder="Backstory"></textarea>
        <button @click="saveCharacterData">Save Character</button>
        <button @click="closeModal">Cancel</button>
      </div>
    </div>

    <!-- Edit Character Modal -->
    <div v-if="showEditCharacterModal" id="edit-character-modal">
      <div class="modal-overlay" @click="closeModal"></div>
      <div class="modal-content">
        <h2>Edit Character</h2>
        <label>
          Name:
          <input v-model="editedCharacter.name" type="text" placeholder="Character Name" />
        </label>
        <label>
          Race:
          <input v-model="editedCharacter.race" type="text" placeholder="Character Race" />
        </label>
        <label>
          Class:
          <input v-model="editedCharacter.class" type="text" placeholder="Character Class" />
        </label>
        <label>
          Backstory:
          <textarea v-model="editedCharacter.backstory" placeholder="Backstory"></textarea>
        </label>
        <button @click="saveEditedCharacterData">Save Changes</button>
        <button @click="closeModal">Cancel</button>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirmModal" class="confirmation-modal">
      <div class="modal-overlay" @click="cancelDelete"></div>
      <div class="modal-content">
        <h2>Confirm Delete</h2>
        <p>
          Are you sure you want to delete this
          <strong>{{ deleteTarget.type }}</strong>
          "<strong>{{ deleteTarget.item.name }}</strong>"?
        </p>
        <button @click="confirmDelete">Yes, Delete</button>
        <button @click="cancelDelete">Cancel</button>
      </div>
    </div>

    <!-- Settings Modal -->
    <div v-if="showSettingsModal" id="settings-modal">
      <div class="modal-overlay" @click="closeSettingsModal"></div>
      <div class="modal-content">
        <h2>Settings</h2>
        <p>Select the LLM you wish to use:</p>
        <ul>
          <li v-for="(model, index) in installedLLMs" :key="index" :class="{ active: model.model_name === currentLLM }">
            <div class="model-info">
              <strong>{{ model.model_name }}</strong>
              <p>Parameter Size: {{ model.parameter_size }}</p>
            </div>
            <button class="use-btn" @click="useLLM(model.model_name)">USE LLM</button>
          </li>
        </ul>
        <button @click="closeSettingsModal">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
import StoryComponent from '@/components/StoryComponent.vue';

export default {
  components: { StoryComponent },
  data() {
    return {
      currentTab: 'stories',
      stories: [],
      characters: [],
      selectedStory: null,
      conversation: [],


      showCreateStoryModal: false,
      showCreateCharacterModal: false,
      showEditStoryModal: false,
      showEditCharacterModal: false,
      showSettingsModal: false,
      showDeleteConfirmModal: false,


      deleteTarget: { type: '', item: null, index: null },


      newStory: { name: '', description: '', genre: '', mode: '', characters: [] },

      selectedCharacterToAddNew: '',


      newCharacter: { name: '', race: '', class: '', backstory: '' },


      editedStory: { name: '', description: '', genre: '', mode: '', characters: [], originalName: '' },

      selectedCharacterToAddEdit: '',


      editedCharacter: { name: '', race: '', class: '', backstory: '', originalName: '' },

      installedLLMs: [],
      currentLLM: '',
    };
  },
  computed: {

    availableCharactersForNew() {
      return this.characters.filter(
        (c) => !this.newStory.characters.includes(c.name)
      );
    },

    availableCharactersForEdit() {
      return this.characters.filter(
        (c) => !this.editedStory.characters.includes(c.name)
      );
    },
  },
  methods: {
    // ----- Character Logic (NEW STORY) -----
    addCharacterToNewStory() {
      if (!this.selectedCharacterToAddNew) return;

      this.newStory.characters.push(this.selectedCharacterToAddNew);

      this.selectedCharacterToAddNew = '';
    },
    removeCharacterFromNewStory(charName) {
      const index = this.newStory.characters.indexOf(charName);
      if (index !== -1) {
        this.newStory.characters.splice(index, 1);
      }
    },

    // ----- Character Logic (EDIT STORY) -----
    addCharacterToEditedStory() {
      if (!this.selectedCharacterToAddEdit) return;
      this.editedStory.characters.push(this.selectedCharacterToAddEdit);
      this.selectedCharacterToAddEdit = '';
    },
    removeCharacterFromEditedStory(charName) {
      const index = this.editedStory.characters.indexOf(charName);
      if (index !== -1) {
        this.editedStory.characters.splice(index, 1);
      }
    },

    // ----- Data Fetching -----
    async fetchStories() {
      try {
        const response = await fetch('http://localhost:5000/get_stories');
        const data = await response.json();
        this.stories = data.stories || [];
      } catch (error) {
        console.error('Error fetching stories:', error);
      }
    },
    async fetchCharacters() {
      try {
        const response = await fetch('http://localhost:5000/get_characters');
        const data = await response.json();
        this.characters = data.characters || [];
      } catch (error) {
        console.error('Error fetching characters:', error);
      }
    },

    // ----- Story Modals -----
    openEditStoryModal(story) {
      this.editedStory = {
        ...story,
        originalName: story.name,
      };

      if (Array.isArray(this.editedStory.characters)) {
        this.editedStory.characters = this.editedStory.characters.map((char) =>
          typeof char === 'object' ? char.name : char
        );
      }
      this.showEditStoryModal = true;
    },

    // ----- Character Modals -----
    openEditCharacterModal(character) {
      this.editedCharacter = { ...character, originalName: character.name };
      this.showEditCharacterModal = true;
    },

    // ----- Story CRUD -----
    async saveEditedStoryData() {
      try {
        const response = await fetch('http://localhost:5000/edit_story', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.editedStory),
        });
        if (response.ok) {
          const updatedStory = await response.json();
          const index = this.stories.findIndex(
            (story) => story.name === this.editedStory.originalName
          );
          if (index !== -1) {
            this.stories.splice(index, 1, updatedStory);
          }
          if (
            this.selectedStory &&
            this.selectedStory.name === this.editedStory.originalName
          ) {
            this.selectedStory = updatedStory;
          }
          this.closeModal();
        } else {
          throw new Error(`Failed to edit story: ${response.statusText}`);
        }
      } catch (error) {
        console.error('Error editing story:', error);
      }
    },
    async saveStoryData() {
      try {
        const response = await fetch('http://localhost:5000/create_story', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.newStory),
        });
        if (!response.ok) {
          throw new Error(`Failed to create story: ${response.statusText}`);
        }
        const data = await response.json();
        if (!data.story) {
          throw new Error('The created story object is missing in the response.');
        }
        this.stories.push(data.story);
        this.closeModal();
      } catch (error) {
        console.error('Error creating story:', error);
        alert(`An error occurred while creating the story: ${error.message}`);
      }
    },

    // ----- Character CRUD -----
    async saveCharacterData() {
      try {
        const response = await fetch('http://localhost:5000/create_character', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.newCharacter),
        });
        const data = await response.json();
        if (data.character) {
          this.characters.push(data.character);
        }
        this.closeModal();
      } catch (error) {
        console.error('Error creating character:', error);
      }
    },
    async saveEditedCharacterData() {
      try {
        const response = await fetch('http://localhost:5000/edit_character', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.editedCharacter),
        });
        if (response.ok) {
          const updatedCharacter = await response.json();
          const index = this.characters.findIndex(
            (c) => c.name === this.editedCharacter.originalName
          );
          if (index !== -1) {
            this.characters.splice(index, 1, updatedCharacter);
          }
          this.closeModal();
        } else {
          throw new Error(`Failed to edit character: ${response.statusText}`);
        }
      } catch (error) {
        console.error('Error editing character:', error);
      }
    },

    // ----- Story Loading -----
    async openStory(story) {
      if (!story || !story.name) {
        console.error('Invalid story passed to openStory:', story);
        return;
      }
      this.selectedStory = story;
      try {
        await this.loadStory();
      } catch (error) {
        console.error('Error opening story:', error);
        this.selectedStory = null;
      }
    },
    async loadStory() {
      if (!this.selectedStory || !this.selectedStory.name) {
        console.error('No story selected or story has no name.');
        return;
      }
      try {
        const response = await fetch('http://localhost:5000/load_story', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: this.selectedStory.name }),
        });
        if (!response.ok) {
          throw new Error(`Failed to load story: ${response.statusText}`);
        }
        const data = await response.json();
        this.conversation = data.conversation || [];
      } catch (error) {
        console.error('Error loading story:', error);
      }
    },

    // ----- Deletion -----
    openDeleteConfirmation(item, index, type) {
      this.deleteTarget = { type, item, index };
      this.showDeleteConfirmModal = true;
    },
    async confirmDelete() {
      try {
        if (this.deleteTarget.type === 'story') {
          const response = await fetch('http://localhost:5000/delete_story', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: this.deleteTarget.item.name }),
          });
          if (response.ok) {
            this.stories.splice(this.deleteTarget.index, 1);
            if (
              this.selectedStory &&
              this.selectedStory.name === this.deleteTarget.item.name
            ) {
              this.selectedStory = null;
            }
          }
        } else if (this.deleteTarget.type === 'character') {
          const response = await fetch('http://localhost:5000/delete_character', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: this.deleteTarget.item.name }),
          });
          if (response.ok) {
            this.characters.splice(this.deleteTarget.index, 1);
          }
        }
      } catch (error) {
        console.error('Error deleting item:', error);
      } finally {
        this.cancelDelete();
      }
    },
    cancelDelete() {
      this.showDeleteConfirmModal = false;
      this.deleteTarget = { type: '', item: null, index: null };
    },

    // ----- Modal Controls -----
    closeModal() {
      this.showCreateStoryModal = false;
      this.showCreateCharacterModal = false;
      this.showEditStoryModal = false;
      this.showEditCharacterModal = false;
      this.showDeleteConfirmModal = false;


      this.newStory = { name: '', description: '', genre: '', mode: '', characters: [] };
      this.newCharacter = { name: '', race: '', class: '', backstory: '' };
      this.editedStory = { name: '', description: '', genre: '', mode: '', characters: [], originalName: '' };
      this.editedCharacter = { name: '', race: '', class: '', backstory: '', originalName: '' };

      this.selectedCharacterToAddNew = '';
      this.selectedCharacterToAddEdit = '';
    },
    openSettingsModal() {
      this.fetchInstalledLLMs();
      this.showSettingsModal = true;
    },
    closeSettingsModal() {
      this.showSettingsModal = false;
    },

    // ----- LLMs -----
    async fetchInstalledLLMs() {
      try {
        const response = await fetch('http://localhost:5000/list_models');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        this.installedLLMs = data;
        const modelResponse = await fetch('http://localhost:5000/get_model');
        if (modelResponse.ok) {
          const modelData = await modelResponse.json();
          this.currentLLM = modelData.model;
        }
      } catch (error) {
        console.error('Error fetching installed LLMs:', error);
      }
    },
    async useLLM(modelName) {
      try {
        const response = await fetch('http://localhost:5000/set_model', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model_name: modelName }),
        });
        if (!response.ok) {
          throw new Error(`Failed to set model: ${response.statusText}`);
        }
        const data = await response.json();
        this.currentLLM = data.model;
        alert(`Model changed to ${data.model}`);
      } catch (error) {
        console.error('Error setting LLM:', error);
      }
    },
  },
  mounted() {
    this.fetchStories();
    this.fetchCharacters();

    fetch('http://localhost:5000/get_model')
      .then((res) => res.json())
      .then((data) => {
        this.currentLLM = data.model;
      })
      .catch((err) => console.error(err));
  },
};
</script>

<style>

body {
  font-family: 'Lora', serif;
  background: linear-gradient(to bottom, #1c1c1c, #333);
  color: #fff;
  margin: 0;
  padding: 0;
}
header {
  text-align: center;
  padding: 20px;
  background-color: #6d6d6d;
  border-bottom: 2px solid #bdbdbd;
  position: relative;
}
.settings-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  transition: transform 0.3s, color 0.3s;
}
.settings-btn:hover {
  color: #ccc;
  transform: rotate(20deg);
}
#content {
  display: flex;
  height: calc(100vh - 80px);
}
#sidebar {
  width: 300px;
  background-color: #222;
  padding: 15px;
  border-right: 2px solid #444;
}
#tabs {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
}
#tabs button {
  padding: 10px;
  background-color: #555;
  color: white;
  border: none;
  cursor: pointer;
  transition: background-color 0.3s;
}
#tabs button:hover {
  background-color: #777;
}
#stories ul,
#characters ul {
  list-style: none;
  padding: 0;
}
#stories li,
#characters li {
  margin: 10px 0;
  padding: 10px;
  background-color: #333;
  border-radius: 5px;
}
#stories button,
#characters button {
  margin-top: 15px;
  padding: 10px;
  background-color: #555;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  transition: background-color 0.3s;
}
#stories button:hover,
#characters button:hover {
  background-color: #777;
}
#main-content {
  flex-grow: 1;
  padding: 20px;
}

/* Conversation Area */
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

/* Scrollbar styling */
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

/* Modals */
#create-story-modal,
#edit-story-modal,
#character-selection-modal,
#create-character-modal,
#edit-character-modal,
#settings-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
}
.modal-content {
  position: relative;
  background: #1c1c1c;
  color: #fff;
  padding: 20px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  z-index: 1001;
  animation: fadeIn 0.3s ease-in-out;
  text-align: center;
}
.modal-content h2 {
  font-size: 24px;
  margin-bottom: 15px;
  text-align: center;
}
.modal-content label {
  display: block;
  margin-bottom: 10px;
  font-size: 16px;
}
.modal-content input[type="text"],
.modal-content textarea,
.modal-content select {
  width: 100%;
  padding: 10px;
  margin-top: 5px;
  margin-bottom: 15px;
  border: 1px solid #555;
  border-radius: 5px;
  background-color: #333;
  color: #fff;
  font-size: 14px;
  box-sizing: border-box;
}
.modal-content textarea {
  resize: none;
  height: 80px;
}
.modal-content button {
  display: inline-block;
  padding: 10px 15px;
  margin: 10px 5px 0 0;
  border: none;
  border-radius: 5px;
  background-color: #555;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}
.modal-content button:hover {
  background-color: #777;
}
.modal-content button:last-child {
  background-color: #333;
}
.modal-content button:last-child:hover {
  background-color: #555;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Confirmation Modal */
.confirmation-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.confirmation-modal .modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  z-index: 999;
}
.confirmation-modal .modal-content {
  position: relative;
  background: #222;
  color: white;
  padding: 20px;
  border-radius: 10px;
  width: 300px;
  text-align: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  z-index: 1000;
}
.confirmation-modal button {
  display: inline-block;
  padding: 10px 20px;
  margin: 10px;
  border: none;
  border-radius: 5px;
  background-color: #555;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}
.confirmation-modal button:hover {
  background-color: #777;
}

/* Settings Modal */
#settings-modal .modal-content {
  background: #1c1c1c;
  border-radius: 12px;
  padding: 20px;
  max-width: 500px;
  width: 90%;
  text-align: left;
}
#settings-modal .modal-content ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
#settings-modal .modal-content li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #333;
  margin: 10px 0;
  padding: 10px 15px;
  border-radius: 8px;
  transition: background 0.3s;
}
#settings-modal .modal-content li.active {
  background: #555;
  border: 2px solid #0a8;
}
#settings-modal .modal-content li:hover {
  background: #444;
}
#settings-modal .modal-content .model-info {
  flex-grow: 1;
}
#settings-modal .modal-content .use-btn {
  background: #0a8;
  border: none;
  border-radius: 5px;
  color: #fff;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.3s;
}
#settings-modal .modal-content .use-btn:hover {
  background: #06c;
}

/* Delete button styling */
.delete-btn {
  background: none;
  border: none;
  color: #f55;
  font-size: 18px;
  cursor: pointer;
  margin-left: 10px;
  transition: color 0.3s ease;
}
.delete-btn:hover {
  color: #d33;
}

/* Character Chips */
.character-section {
  text-align: left;
  margin-bottom: 20px;
}
.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.chip {
  display: inline-flex;
  align-items: center;
  background-color: #444;
  color: #fff;
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 14px;
}
.remove-chip {
  background: none;
  border: none;
  color: #bbb;
  margin-left: 8px;
  cursor: pointer;
  font-size: 16px;
}
.remove-chip:hover {
  color: #fff;
}
.add-character-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.add-character-row select {
  flex: 1;
}
</style>
