<template>
  <div id="main-view">

    <header>
      <h1>Welcome, Adventurer!</h1>
      <button class="dice-btn" @click="toggleDicePanel">🎲</button>
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
        </div>
        <div v-else>
          <StoryComponent :storySummary="selectedStory" :conversation="conversation" />
        </div>
      </main>
    </div>

    <transition name="slide">
      <div v-if="showDicePanel" id="dice-panel">
        <button class="close-dice-btn" @click="toggleDicePanel">✖️</button>
        <h2>Dice Roller</h2>
        <div class="preset-roll">
          <h3>Preset Rolls</h3>
          <label>
            Modifier:
            <input type="number" v-model.number="presetModifier" placeholder="0" />
          </label>
          <div class="dice-buttons">
            <button @click="rollDice(4, presetModifier)">1d4</button>
            <button @click="rollDice(6, presetModifier)">1d6</button>
            <button @click="rollDice(8, presetModifier)">1d8</button>
            <button @click="rollDice(10, presetModifier)">1d10</button>
            <button @click="rollDice(12, presetModifier)">1d12</button>
            <button @click="rollDice(20, presetModifier)">1d20</button>
            <button @click="rollDice(100, presetModifier)">1d100</button>
          </div>
        </div>

        <div class="custom-roll">
          <h3>Custom Roll</h3>
          <input type="text" v-model="customDiceNotation" placeholder="e.g. 1d20+2" />
          <button @click="rollCustomDice">Roll</button>
          <p class="error-message" v-if="customDiceError">{{ customDiceError }}</p>
        </div>

        <div class="dice-result" v-if="diceResult !== null">
          <h3>Result:</h3>
          <p>{{ diceResult }}</p>
        </div>
      </div>
    </transition>


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
        <button @click="openManageCharactersModal('create')">Manage Characters</button>
        <button @click="saveStoryData">Save Story</button>
        <button @click="closeModal">Cancel</button>
      </div>
    </div>

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
        <button @click="openManageCharactersModal('edit')">Manage Characters</button>
        <button @click="saveEditedStoryData">Save Changes</button>
        <button @click="closeModal">Cancel</button>
      </div>
    </div>


    <div v-if="showManageCharactersModal" id="manage-characters-modal">
      <div class="modal-overlay" @click="closeManageCharactersModal"></div>
      <div class="modal-content manage-characters-modal-content">
        <h2>
          Manage Characters for
          {{ manageCharactersMode === 'edit' ? editedStory.name : newStory.name }}
        </h2>
        <section class="assigned-characters">
          <h3>Assigned Characters</h3>
          <div v-if="tempAssignedCharacters.length === 0">
            <p>No characters assigned yet.</p>
          </div>
          <ul v-else>
            <li
              v-for="char in buildAssignedCharacters()"
              :key="char.name"
              class="character-card"
            >
              <div>
                <strong>{{ char.name }}</strong>
                <span v-if="char.isLLM"> (LLM-Generated)</span>
              </div>
              <button @click="removeCharacter(char.name)">Remove from Story</button>
              <button v-if="char.isLLM" @click="importCharacterToUser(char)">
                Add to My Characters
              </button>
            </li>
          </ul>
        </section>

        <section class="available-characters">
          <h3>Available Characters</h3>
          <div class="tabs">
            <button :class="{ active: activeTab === 'user' }" @click="activeTab = 'user'">User</button>
          </div>
          <div v-if="activeTab === 'user'" class="tab-content">
            <ul v-if="availableUserCharacters.length > 0">
              <li
                v-for="char in availableUserCharacters"
                :key="char.name"
                class="character-card"
              >
                <div>
                  <strong>{{ char.name }}</strong>
                </div>
                <button @click="assignCharacter(char.name)">Add to Story</button>
              </li>
            </ul>
            <p v-else>No user-created characters available.</p>
          </div>
          <div v-else-if="activeTab === 'llm'" class="tab-content">
            <ul v-if="availableLLMCharacters.length > 0">
              <li v-for="char in availableLLMCharacters" :key="char.name" class="character-card">
                <div>
                  <strong>{{ char.name }}</strong>
                </div>
                <button @click="assignCharacter(char.name)">Add to Story</button>
                <button @click="importCharacterToUser(char)">Add to My Characters</button>
              </li>
            </ul>
            <p v-else>No LLM-generated characters available.</p>
          </div>
        </section>
        <button class="close-btn" @click="closeManageCharactersModal">Close</button>
      </div>
    </div>


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
        <button @click="toggleAdvancedOptions('create')">
          {{ showAdvancedOptionsCreateCharacter ? 'Hide Advanced Options' : 'Show Advanced Options' }}
        </button>
        <div v-if="showAdvancedOptionsCreateCharacter" class="advanced-options">
          <div class="tooltip">
            <p>
              Advanced options help the Dungeon Master understand more about your character.
              It is recommended to fill out and play with a D&D 5e character sheet.
              You can get one <a href="https://media.wizards.com/2022/dnd/downloads/DnD_5E_CharacterSheet_FormFillable.pdf" target="_blank">here</a>
              and for a guide on how to fill a sheet, click <a href="https://www.thegamer.com/dungeons-dragons-character-sheet-examples/" target="_blank">here</a>.
            </p>
          </div>
          <label>
            Ability Scores (comma separated, e.g. 10,12,14,10,13,8):
            <input type="text" v-model="newCharacter.ability_scores" placeholder="STR, DEX, CON, INT, WIS, CHA" />
          </label>
          <label>
            Skills (comma separated):
            <input type="text" v-model="newCharacter.skills" placeholder="Perception, Stealth" />
          </label>
          <label>
            Proficiencies (comma separated):
            <input type="text" v-model="newCharacter.proficiencies" placeholder="Longsword, Shield" />
          </label>
          <label>
            Equipment (comma separated):
            <input type="text" v-model="newCharacter.equipment" placeholder="Sword, Armor" />
          </label>
          <label>
            Spells (comma separated):
            <input type="text" v-model="newCharacter.spells" placeholder="Magic Missile, Shield" />
          </label>
          <label>
            Class Features:
            <textarea v-model="newCharacter.class_features" placeholder="List class features"></textarea>
          </label>
          <label>
            Background:
            <input type="text" v-model="newCharacter.background" placeholder="Background" />
          </label>
          <label>
            Alignment:
            <input type="text" v-model="newCharacter.alignment" placeholder="Alignment" />
          </label>
          <label>
            Level:
            <input type="number" v-model.number="newCharacter.level" placeholder="Level" />
          </label>
          <label>
            Experience:
            <input type="number" v-model.number="newCharacter.experience" placeholder="Experience" />
          </label>
        </div>
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
        <button @click="toggleAdvancedOptions('edit')">
          {{ showAdvancedOptionsEditCharacter ? 'Hide Advanced Options' : 'Show Advanced Options' }}
        </button>
        <div v-if="showAdvancedOptionsEditCharacter" class="advanced-options">
          <div class="tooltip">
            <p>
              Advanced options help the Dungeon Master understand more about your character.
              It is recommended to fill out and play with a D&D 5e character sheet.
              You can get one <a href="https://media.wizards.com/2022/dnd/downloads/DnD_5E_CharacterSheet_FormFillable.pdf" target="_blank">here</a>
              and for a guide on how to fill a sheet, click <a href="https://www.thegamer.com/dungeons-dragons-character-sheet-examples/" target="_blank">here</a>.
            </p>
          </div>
          <label>
            Ability Scores (comma separated, e.g. 10,12,14,10,13,8):
            <input type="text" v-model="editedCharacter.ability_scores" placeholder="STR, DEX, CON, INT, WIS, CHA" />
          </label>
          <label>
            Skills (comma separated):
            <input type="text" v-model="editedCharacter.skills" placeholder="Perception, Stealth" />
          </label>
          <label>
            Proficiencies (comma separated):
            <input type="text" v-model="editedCharacter.proficiencies" placeholder="Longsword, Shield" />
          </label>
          <label>
            Equipment (comma separated):
            <input type="text" v-model="editedCharacter.equipment" placeholder="Sword, Armor" />
          </label>
          <label>
            Spells (comma separated):
            <input type="text" v-model="editedCharacter.spells" placeholder="Magic Missile, Shield" />
          </label>
          <label>
            Class Features:
            <textarea v-model="editedCharacter.class_features" placeholder="List class features"></textarea>
          </label>
          <label>
            Background:
            <input type="text" v-model="editedCharacter.background" placeholder="Background" />
          </label>
          <label>
            Alignment:
            <input type="text" v-model="editedCharacter.alignment" placeholder="Alignment" />
          </label>
          <label>
            Level:
            <input type="number" v-model.number="editedCharacter.level" placeholder="Level" />
          </label>
          <label>
            Experience:
            <input type="number" v-model.number="editedCharacter.experience" placeholder="Experience" />
          </label>
        </div>
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

    <!-- New Tabbed Settings Modal -->
    <div v-if="showSettingsModal" id="settings-modal">
      <div class="modal-overlay" @click="closeSettingsModal"></div>
      <div class="modal-content">
        <!-- Tab header -->
        <div class="tabs">
          <button :class="{ active: settingsActiveTab === 'llms' }" @click="settingsActiveTab = 'llms'">LLMs</button>
          <button :class="{ active: settingsActiveTab === 'settings' }" @click="settingsActiveTab = 'settings'">Settings</button>
        </div>
        <!-- LLMs Tab -->
        <div v-if="settingsActiveTab === 'llms'">
          <h2>LLMs</h2>
          <div class="llm-recommendation">
            <p>
              <strong>Recommended LLM:</strong> llama3.2-vision:latest
              <br>
              This version of the project was developed and tested with <a href="https://ollama.com/library/llama3.2-vision" target="_blank">llama3.2-vision:latest</a>.
            </p>
            <div class="tooltip">
              <p>
                General Guidelines:
                <ul>
                  <li>It is recommended to use llama3.2-vision:latest for the best experience.</li>
                  <li>Feel free to experiment with other LLMs, but some features might not work due to limited JSON parsing capabilities.</li>
                  <li>As a rule of thumb, more advanced LLMs tend to provide better results.</li>
                  <li>LLMs with a strong "thinking" nature are not recommended in this version.</li>
                </ul>
              </p>
            </div>
          </div>
          <ul>
            <li v-for="(model, index) in installedLLMs" :key="index" :class="{ active: model.model_name === currentLLM, recommended: model.model_name === 'llama3.2-vision:latest' }">
              <div class="model-info">
                <strong>{{ model.model_name }}</strong>
                <p>Parameter Size: {{ model.parameter_size }}</p>
                <span v-if="model.model_name === 'llama3.2-vision:latest'" class="recommended-badge">Recommended</span>
              </div>
              <button class="use-btn" @click="useLLM(model.model_name)">USE LLM</button>
            </li>
          </ul>
        </div>
        <!-- Settings Tab -->
        <div v-else-if="settingsActiveTab === 'settings'">
          <h2>Settings</h2>
          <div class="setting-item">
            <label>
              Model Accuracy:
              <input type="range" min="3" max="20" step="1" v-model.number="modelAccuracy" />
              <span>{{ modelAccuracy }}</span>
            </label>
            <div class="tooltip">
              Adjust the summarization threshold. Lower values (e.g. 3) trigger more frequent summarization (helpful on lower‐end PCs), while higher values (e.g. 10 or more) reduce summarization frequency for higher‐end systems.
            </div>
          </div>
          <div class="setting-item">
            <label>
              Context Size:
              <input type="number" min="0" v-model.number="contextSize" placeholder="4096" />
            </label>
            <div class="tooltip">
              Set the context size for the model. Default is 4096. Increase this if your model supports larger context windows. Recommended: 4096 for standard usage; higher values for more context.
            </div>
          </div>
          <button @click="saveSettings">Save Settings</button>
        </div>
        <button @click="closeSettingsModal">Close</button>
      </div>
    </div>

  </div>
</template>

<script>
import StoryComponent from '@/components/StoryComponent.vue';
import { api } from '@/utils/api.js';

export default {
  components: { StoryComponent },
  data() {
    return {
      currentTab: 'stories',
      stories: [],
      characters: [],
      selectedStory: null,
      conversation: [],
      customDiceError: '',

      showCreateStoryModal: false,
      showEditStoryModal: false,

      showCreateCharacterModal: false,
      showEditCharacterModal: false,

      showManageCharactersModal: false,
      manageCharactersMode: '',
      tempAssignedCharacters: [],
      activeTab: 'user',

      llmCharacters: [],

      showDeleteConfirmModal: false,
      deleteTarget: { type: '', item: null, index: null },

      showSettingsModal: false,
      installedLLMs: [],
      currentLLM: '',

      newStory: {
        name: '',
        description: '',
        genre: '',
        mode: '',
        characters: [],
      },
      editedStory: {
        name: '',
        description: '',
        genre: '',
        mode: '',
        characters: [],
        originalName: '',
      },

      newCharacter: {
        name: '',
        race: '',
        class: '',
        backstory: '',
        ability_scores: '',
        skills: '',
        proficiencies: '',
        equipment: '',
        spells: '',
        class_features: '',
        background: '',
        alignment: '',
        level: 1,
        experience: 0,
      },
      editedCharacter: {
        name: '',
        race: '',
        class: '',
        backstory: '',
        ability_scores: '',
        skills: '',
        proficiencies: '',
        equipment: '',
        spells: '',
        class_features: '',
        background: '',
        alignment: '',
        level: 1,
        experience: 0,
        originalName: '',
      },

      showAdvancedOptionsCreateCharacter: false,
      showAdvancedOptionsEditCharacter: false,

      // DICE ROLLER PROPERTIES
      showDicePanel: false,
      presetModifier: 0,
      customDiceNotation: '',
      diceResult: null,

      settingsActiveTab: 'llms',
      modelAccuracy: 3,
      contextSize: 4096,
    };
  },
  computed: {
    availableUserCharacters() {
      return this.characters.filter(
        (c) => !this.tempAssignedCharacters.includes(c.name) && !c.isLLM
      );
    },
    availableLLMCharacters() {
      return this.llmCharacters.filter(
        (c) => !this.tempAssignedCharacters.includes(c.name)
      );
    },
  },
  methods: {
    async fetchStories() {
      try {
        const data = await api.get('/get_stories');
        this.stories = data.stories || [];
      } catch (error) {
        console.error('Error fetching stories:', error);
      }
    },
    async fetchCharacters() {
      try {
        const data = await api.get('/get_characters');
        this.characters = data.characters || [];
      } catch (error) {
        console.error('Error fetching characters:', error);
      }
    },
    openEditStoryModal(story) {
      api.post('/load_story', { name: story.name })
        .then((data) => {
          const updatedStory = data.story;
          let charactersArray = [];
          if (updatedStory.characters && !Array.isArray(updatedStory.characters)) {
            charactersArray = Object.values(updatedStory.characters);
          } else {
            charactersArray = updatedStory.characters || [];
          }
          this.editedStory = {
            ...updatedStory,
            originalName: updatedStory.name,
            characters: charactersArray,
          };
          this.showEditStoryModal = true;
        })
        .catch((err) => {
          console.error('Error fetching updated story:', err);
          alert(`Error fetching updated story: ${err.message}`);
        });
    },
    openEditCharacterModal(character) {
      this.editedCharacter = { ...character, originalName: character.name };
      this.showEditCharacterModal = true;
    },
    closeModal() {
      this.showCreateStoryModal = false;
      this.showEditStoryModal = false;
      this.showCreateCharacterModal = false;
      this.showEditCharacterModal = false;
      this.showDeleteConfirmModal = false;
      this.showManageCharactersModal = false;

      this.newStory = {
        name: '',
        description: '',
        genre: '',
        mode: '',
        characters: [],
      };
      this.editedStory = {
        name: '',
        description: '',
        genre: '',
        mode: '',
        characters: [],
        originalName: '',
      };

      this.newCharacter = {
        name: '',
        race: '',
        class: '',
        backstory: '',
        ability_scores: '',
        skills: '',
        proficiencies: '',
        equipment: '',
        spells: '',
        class_features: '',
        background: '',
        alignment: '',
        level: 1,
        experience: 0,
      };
      this.editedCharacter = {
        name: '',
        race: '',
        class: '',
        backstory: '',
        ability_scores: '',
        skills: '',
        proficiencies: '',
        equipment: '',
        spells: '',
        class_features: '',
        background: '',
        alignment: '',
        level: 1,
        experience: 0,
        originalName: '',
      };

      this.tempAssignedCharacters = [];
      this.manageCharactersMode = '';
      this.activeTab = 'user';

      this.showAdvancedOptionsCreateCharacter = false;
      this.showAdvancedOptionsEditCharacter = false;
    },
    openManageCharactersModal(mode) {
      this.manageCharactersMode = mode;
      this.showManageCharactersModal = true;
      if (mode === 'create') {
        this.tempAssignedCharacters = this.newStory.characters.map((char) =>
          typeof char === 'string' ? char : char.name
        );
      } else if (mode === 'edit') {
        this.tempAssignedCharacters = this.editedStory.characters.map((char) =>
          typeof char === 'string' ? char : char.name
        );
      }
    },
    closeManageCharactersModal() {
      if (this.manageCharactersMode === 'create') {
        this.newStory.characters = [...this.tempAssignedCharacters];
      } else if (this.manageCharactersMode === 'edit') {
        this.editedStory.characters = [...this.tempAssignedCharacters];
      }
      this.showManageCharactersModal = false;
      this.manageCharactersMode = '';
      this.tempAssignedCharacters = [];
      this.activeTab = 'user';
    },
    assignCharacter(charName) {
      if (!this.tempAssignedCharacters.includes(charName)) {
        this.tempAssignedCharacters.push(charName);
      }
    },
    removeCharacter(charName) {
      const idx = this.tempAssignedCharacters.indexOf(charName);
      if (idx !== -1) {
        this.tempAssignedCharacters.splice(idx, 1);
      }
    },
    importCharacterToUser(charObj) {
  api.post('/load_story', { name: this.selectedStory.name })
    .then((data) => {
      const story = data.story;
      const characters = story.characters || {};
      
      const fullCharacter = characters[charObj.name] || {};
      

      const characterData = {
        name: fullCharacter.name || charObj.name,
        race: fullCharacter.race || '',
        class: fullCharacter.class || '',
        backstory: fullCharacter.backstory || '',
      };

      const filteredData = Object.fromEntries(
        Object.entries(characterData).filter(([_, v]) => v !== '')
      );


      return api.post('/create_character', filteredData);
    })
    .then((data) => {
      if (data.character) {
        data.character.isLLM = false;
        this.characters.push(data.character);
        alert(`${data.character.name} has been added to your characters!`);
      }
    })
    .catch((error) => {
      console.error('Error importing character:', error);
      alert(`Failed to import character: ${error.message}`);
    });
},
    buildAssignedCharacters() {
      return this.tempAssignedCharacters.map((char) => {
        const found = this.characters.find((c) => c.name === char);
        return found
          ? found
          : { name: char, isLLM: true, race: 'Unknown', class: 'Unknown', backstory: '' };
      });
    },
    async saveStoryData() {
      try {
        const dict = {};
        this.newStory.characters.forEach((charObj) => {
          if (typeof charObj === 'string') {
            dict[charObj] = { name: charObj };
          } else {
            dict[charObj.name] = charObj;
          }
        });
        const payload = {
          ...this.newStory,
          characters: dict
        };
        
        const data = await api.post('/create_story', payload);
        
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
    async saveEditedStoryData() {
      try {
        const dict = {};
        this.editedStory.characters.forEach((charObj) => {
          if (typeof charObj === 'string') {
            dict[charObj] = { name: charObj };
          } else {
            dict[charObj.name] = charObj;
          }
        });
        const payload = {
          ...this.editedStory,
          characters: dict
        };
        
        const updatedStory = await api.put('/edit_story', payload);
        
        const index = this.stories.findIndex(
          (s) => s.name === this.editedStory.originalName
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
      } catch (error) {
        console.error('Error editing story:', error);
      }
    },
    async saveCharacterData() {
      try {
        const data = await api.post('/create_character', this.newCharacter);
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
        const updatedCharacter = await api.put('/edit_character', this.editedCharacter);
        const index = this.characters.findIndex(
          (c) => c.name === this.editedCharacter.originalName
        );
        if (index !== -1) {
          this.characters.splice(index, 1, updatedCharacter);
        }
        this.closeModal();
      } catch (error) {
        console.error('Error editing character:', error);
      }
    },
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
        const data = await api.post('/load_story', { name: this.selectedStory.name });
        this.conversation = data.conversation || [];
      } catch (error) {
        console.error('Error loading story:', error);
      }
    },
    openDeleteConfirmation(item, index, type) {
      this.deleteTarget = { type, item, index };
      this.showDeleteConfirmModal = true;
    },
    async confirmDelete() {
      try {
        if (this.deleteTarget.type === 'story') {
          await api.delete('/delete_story', { name: this.deleteTarget.item.name });
          this.stories.splice(this.deleteTarget.index, 1);
          if (
            this.selectedStory &&
            this.selectedStory.name === this.deleteTarget.item.name
          ) {
            this.selectedStory = null;
          }
        } else if (this.deleteTarget.type === 'character') {
          await api.delete('/delete_character', { name: this.deleteTarget.item.name });
          this.characters.splice(this.deleteTarget.index, 1);
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
    openSettingsModal() {
      this.fetchInstalledLLMs();
      this.showSettingsModal = true;
    },
    closeSettingsModal() {
      this.showSettingsModal = false;
    },
    async fetchInstalledLLMs() {
      try {
        const data = await api.get('/list_models');
        this.installedLLMs = data;
        
        const modelData = await api.get('/get_model');
        this.currentLLM = modelData.model;
      } catch (error) {
        console.error('Error fetching installed LLMs:', error);
      }
    },
    async useLLM(modelName) {
      try {
        const data = await api.post('/set_model', { model_name: modelName });
        this.currentLLM = data.model;
        alert(`Model changed to ${data.model}`);
      } catch (error) {
        console.error('Error setting LLM:', error);
      }
    },
    toggleDicePanel() {
      this.showDicePanel = !this.showDicePanel;
      if (this.showDicePanel) {
        document.body.classList.add('dice-panel-open');
      } else {
        document.body.classList.remove('dice-panel-open');
        this.diceResult = null;
        this.customDiceNotation = '';
        this.customDiceError = '';
      }
    },
    rollDice(sides, modifier) {
      const roll = Math.floor(Math.random() * sides) + 1;
      const total = roll + modifier;
      const modStr = modifier >= 0 ? `+${modifier}` : `${modifier}`;
      this.diceResult = `${roll}${modStr}=${total}`;
    },
    rollCustomDice() {
      const regex = /^(\d+)[dD](\d+)([+-]\d+)?$/;
      const match = this.customDiceNotation.trim().match(regex);
      if (match) {
        this.customDiceError = '';
        const count = parseInt(match[1], 10);
        const sides = parseInt(match[2], 10);
        const modifier = match[3] ? parseInt(match[3], 10) : 0;
        const rolls = [];
        for (let i = 0; i < count; i++) {
          rolls.push(Math.floor(Math.random() * sides) + 1);
        }
        const rollString = rolls.join('+');
        const total = rolls.reduce((a, b) => a + b, 0) + modifier;
        const modStr = modifier !== 0 ? (modifier > 0 ? `+${modifier}` : `${modifier}`) : '';
        this.diceResult = `${rollString}${modStr}=${total}`;
      } else {
        this.customDiceError = 'Invalid dice notation';
      }
    },
    toggleAdvancedOptions(mode) {
      if (mode === 'create') {
        this.showAdvancedOptionsCreateCharacter = !this.showAdvancedOptionsCreateCharacter;
      } else if (mode === 'edit') {
        this.showAdvancedOptionsEditCharacter = !this.showAdvancedOptionsEditCharacter;
      }
    },
    async saveSettings() {
      localStorage.setItem('modelAccuracy', this.modelAccuracy);
      localStorage.setItem('contextSize', this.contextSize);

      try {
        const data = await api.post('/update_settings', {
          model_accuracy: this.modelAccuracy,
          context_size: this.contextSize,
        });
        alert(data.message || 'Settings updated!');
      } catch (err) {
        console.error('Error updating settings:', err);
        alert('Error saving settings.');
      }
    },
  },
  mounted() {
    this.fetchStories();
    this.fetchCharacters();
    
    api.get('/get_model')
      .then((data) => {
        this.currentLLM = data.model;
      })
      .catch((err) => console.error(err));

    const savedModelAccuracy = localStorage.getItem('modelAccuracy');
    const savedContextSize = localStorage.getItem('contextSize');
    if (savedModelAccuracy !== null) {
      this.modelAccuracy = parseInt(savedModelAccuracy, 10);
    }
    if (savedContextSize !== null) {
      this.contextSize = parseInt(savedContextSize, 10);
    }
  },
};
</script>
<style>

body {
  font-family: 'Lora', serif;
  margin: 0;
  padding: 0;
  color: #fff;
  position: relative; 
  overflow-x: hidden;
  line-height: 1.6;
}

body::before {
  content: "";
  position: fixed;
  top: 0; 
  left: 0;
  width: 100%; 
  height: 100%;
  background: url('https://img.stablecog.com/insecure/1920w/aHR0cHM6Ly9iLnN0YWJsZWNvZy5jb20vOGQyYWM4ZDAtMzEyZC00ZDI1LWE5NWQtZDUzZDg5N2YxY2E2LmpwZWc.webp') center center / cover no-repeat;
  z-index: -1;
  filter: brightness(0.9);
}


::-webkit-scrollbar { 
  width: 8px; 
}
::-webkit-scrollbar-thumb { 
  background: #8D6E63; 
  border-radius: 10px; 
}
::-webkit-scrollbar-thumb:hover { 
  background: #7B5E57; 
}


header {
  text-align: center;
  padding: 20px;
  background-color: rgba(62, 39, 35, 0.95);
  position: relative;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
  z-index: 10;
  height: 40px;
}

header h1 {
  color: #d4af37;
  margin: 0;
  font-size: 32px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
  letter-spacing: 1px;
  font-weight: 700;
}

.settings-btn, .dice-btn {
  position: absolute;
  background: none;
  border: none;
  color: #fff;
  font-size: 26px;
  cursor: pointer;
  transition: all 0.3s;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-btn:hover, .dice-btn:hover { 
  background-color: rgba(255, 255, 255, 0.1);
  transform: scale(1.1);
  color: #d4af37;
}

.settings-btn { top: 20px; right: 20px; }
.dice-btn { top: 20px; right: 70px; }


#content { 
  display: flex; 
  height: calc(100vh - 80px);
  position: relative;
  overflow: hidden; 
}


#sidebar { 
  width: 280px;
  background-color: rgba(62, 39, 35, 0.95);
  padding: 15px;
  border-right: 2px solid #5D4037;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.3);
  overflow-y: auto;
  position: fixed;
  left: 0;
  top: 80px; 
  bottom: 0;
  z-index: 5;
}


#main-content { 
  margin-left: 280px; 
  flex-grow: 1; 
  padding: 20px; 
  overflow-y: auto;
  position: relative;
  z-index: 1;
  height: calc(100vh - 80px);
  transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
}


body.dice-panel-open #main-content {
  padding-right: 320px;
}


#tabs { 
  display: flex; 
  justify-content: space-around; 
  margin-bottom: 20px;
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: rgba(62, 39, 35, 0.98);
  padding-top: 10px;
}

#tabs button { 
  flex: 1;
  padding: 12px;
  background-color: #5D4037; 
  color: white; 
  border: none;
  border-radius: 5px;
  cursor: pointer; 
  transition: all 0.3s;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0 5px;
}

#tabs button:hover, 
#tabs button:focus { 
  background-color: #6D4C41;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

#tabs button:active {
  transform: translateY(0);
}

#stories ul, 
#characters ul { 
  list-style: none; 
  padding: 0;
  margin: 0;
}

#stories li, 
#characters li { 
  margin: 12px 0; 
  padding: 10px; 
  background-color: #4E342E; 
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

#stories li:hover,
#characters li:hover {
  transform: translateX(5px);
  background-color: #5D4037;
}

.story-title {
  cursor: pointer;
  flex-grow: 1;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s;
}

.story-title.selected {
  background-color: rgba(212, 175, 55, 0.2);
  font-weight: bold;
}

.story-title:hover {
  color: #d4af37;
}


.edit-btn, .delete-btn {
  background: none;
  border: none;
  margin-left: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-btn {
  color: #9e9e9e;
}

.delete-btn {
  color: #ff6f61;
}

.edit-btn:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.1);
}

.delete-btn:hover {
  color: white;
  background-color: rgba(255, 111, 97, 0.2);
}

#stories button, 
#characters button { 
  width: 100%;
  margin-top: 15px; 
  padding: 12px; 
  background-color: #5D4037; 
  color: white; 
  border: none; 
  cursor: pointer; 
  border-radius: 8px; 
  transition: all 0.3s; 
  font-weight: 600;
  letter-spacing: 0.5px;
}

#stories button:hover, 
#characters button:hover { 
  background-color: #6D4C41; 
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

#stories button:active,
#characters button:active {
  transform: translateY(0);
}


#chatbox {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
}


body.dice-panel-open #chatbox {
  padding-right: 280px;
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
  width: 100%;
  margin: 0 auto 20px;
  padding: 20px;
  background: rgba(51, 25, 15, 0.9);
  border: 2px solid #8D6E63;
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  overflow-y: auto;
  max-height: calc(100vh - 250px);
  transition: all 0.5s;
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
  color: #d4af37;
  font-weight: 700;
  font-size: 18px;
  margin-right: 10px;
}


#conversation p:nth-of-type(odd) {
  background-color: rgba(78, 52, 46, 0.85);
  border-left: 3px solid #d4af37;
}

#conversation p:nth-of-type(even) {
  background-color: rgba(62, 39, 35, 0.85);
  border-left: 3px solid #a1887f;
}


#input-area {
  display: flex;
  justify-content: center;
  margin: 0 auto 20px;
  width: 100%;
  transition: all 0.5s;
}

#input-area input {
  flex-grow: 1;
  padding: 15px;
  border: 2px solid #8D6E63;
  border-radius: 8px 0 0 8px;
  background-color: rgba(51, 25, 15, 0.9);
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


#input-area button.streaming {
  background-color: #C62828;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}


#dice-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 300px;
  height: 100vh;
  background: rgba(41, 55, 41, 0.95);
  border-left: 2px solid #5D4037;
  padding: 20px;
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.5);
  overflow-y: auto;
  z-index: 50;
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.slide-enter-from {
  transform: translateX(100%);
}

.slide-enter-to {
  transform: translateX(0%);
}

.slide-leave-from {
  transform: translateX(0%);
}

.slide-leave-to {
  transform: translateX(100%);
}

.slide-enter-active, 
.slide-leave-active {
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

#dice-panel h2 { 
  margin-top: 10px;
  margin-bottom: 20px;
  text-align: center; 
  color: #d4af37;
  font-size: 24px;
}

.close-dice-btn { 
  position: absolute; 
  top: 15px; 
  right: 15px; 
  background: none; 
  border: none; 
  font-size: 20px; 
  color: #fff; 
  cursor: pointer; 
  transition: all 0.3s;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-dice-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ff6f61;
}

.preset-roll, .custom-roll {
  background: rgba(78, 52, 46, 0.7);
  border-radius: 10px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.preset-roll h3, .custom-roll h3, .dice-result h3 {
  color: #d4af37;
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 18px;
}

.dice-buttons { 
  display: grid; 
  grid-template-columns: repeat(3, 1fr);
  gap: 10px; 
  margin-top: 15px; 
}

#dice-panel button {
  background-color: #5D4037;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
}

#dice-panel button:hover { 
  background-color: #6D4C41; 
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

#dice-panel button:active {
  transform: translateY(0);
}

#dice-panel label {
  display: block;
  margin-bottom: 10px;
  font-weight: 500;
}

#dice-panel input[type="text"],
#dice-panel input[type="number"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #5D4037;
  border-radius: 8px;
  background: rgba(62, 39, 35, 0.8);
  color: #fff;
  margin-top: 5px;
  margin-bottom: 15px;
  box-sizing: border-box;
  transition: all 0.3s;
}

#dice-panel input:focus {
  outline: none;
  border-color: #d4af37;
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.3);
}

.dice-result {
  background: rgba(78, 52, 46, 0.7);
  border-radius: 10px;
  padding: 15px;
  margin-top: 20px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
  text-align: center;
}

.dice-result p {
  font-size: 24px;
  font-weight: 700;
  color: #d4af37;
  margin: 10px 0;
}

.error-message { 
  color: #ff6f61; 
  font-size: 14px; 
  margin-top: 5px; 
  font-weight: 500;
}


#create-story-modal,
#edit-story-modal,
#create-character-modal,
#edit-character-modal,
#manage-characters-modal,
#settings-modal,
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

.modal-overlay { 
  position: fixed; 
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%; 
  background: rgba(0, 0, 0, 0.7); 
  backdrop-filter: blur(3px);
  z-index: 1000;
}

.modal-content {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: linear-gradient(to bottom, #3d2824, #4E342E);
  color: #fff;
  padding: 25px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  z-index: 1001;
  animation: fadeInScale 0.3s ease-in-out;
  max-height: 80vh;
  overflow-y: auto;
}

@keyframes fadeInScale { 
  from { opacity: 0; transform: translate(-50%, -50%) scale(0.95); } 
  to { opacity: 1; transform: translate(-50%, -50%) scale(1); } 
}

.modal-content h2 { 
  font-size: 24px; 
  margin-bottom: 20px; 
  text-align: center; 
  color: #d4af37;
}

.modal-content label { 
  display: block; 
  margin-bottom: 5px; 
  font-size: 16px;
  font-weight: 500;
}

.modal-content input[type="text"],
.modal-content input[type="number"],
.modal-content textarea,
.modal-content select {
  width: 100%;
  padding: 12px;
  margin-top: 5px;
  margin-bottom: 15px;
  border: 1px solid #5D4037;
  border-radius: 8px;
  background-color: rgba(78, 52, 46, 0.7);
  color: #fff;
  font-size: 14px;
  box-sizing: border-box;
  transition: all 0.3s;
}

.modal-content input:focus,
.modal-content textarea:focus,
.modal-content select:focus {
  outline: none;
  border-color: #d4af37;
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.3);
}

.modal-content textarea { 
  resize: vertical; 
  min-height: 80px;
  max-height: 200px;
}

.modal-content button {
  display: inline-block;
  padding: 12px 18px;
  margin: 15px 5px 0;
  border: none;
  border-radius: 8px;
  background-color: #5D4037;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.modal-content button:hover { 
  background-color: #6D4C41; 
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.modal-content button:active {
  transform: translateY(0);
}

.modal-content button:last-child { 
  background-color: #3E2723; 
}

.modal-content button:last-child:hover { 
  background-color: #4E342E; 
}


.manage-characters-modal-content { 
  max-width: 700px; 
  text-align: left; 
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
}

.assigned-characters, 
.available-characters { 
  margin: 1rem 0; 
  background-color: rgba(78, 52, 46, 0.5);
  padding: 15px;
  border-radius: 8px;
}

.assigned-characters h3, 
.available-characters h3 {
  color: #d4af37;
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 18px;
}

.character-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(93, 64, 55, 0.7);
  margin: 0.8rem 0;
  padding: 12px 15px;
  border-radius: 8px;
  transition: all 0.3s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.character-card:hover {
  transform: translateY(-2px);
  background: rgba(109, 76, 65, 0.7);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.character-card div {
  flex-grow: 1;
}

.character-card button { 
  margin: 0 0 0 10px;
  padding: 8px 10px;
  font-size: 12px;
}

.tabs { 
  display: flex; 
  gap: 1rem; 
  margin-bottom: 1rem; 
  position: sticky;
  top: 0;
  background: linear-gradient(to bottom, #3d2824, #4E342E);
  padding-top: 10px;
  z-index: 5;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.tabs button { 
  background: #5D4037; 
  color: #fff; 
  border: none; 
  padding: 10px 15px; 
  cursor: pointer; 
  border-radius: 8px 8px 0 0;
  font-weight: 600;
  transition: all 0.3s;
}

.tabs button.active { 
  background: #6D4C41; 
  color: #d4af37;
}

.tab-content { 
  border-top: 1px solid #5D4037; 
  padding-top: 1rem; 
}


#settings-modal .modal-content {
  background: linear-gradient(to bottom, #3d2824, #4E342E);
  border-radius: 12px;
  max-width: 600px;
}

#settings-modal .modal-content ul { 
  list-style: none; 
  padding: 0; 
  margin: 15px 0; 
}

#settings-modal .modal-content li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(62, 39, 35, 0.7);
  margin: 15px 0;
  padding: 15px;
  border-radius: 8px;
  transition: all 0.3s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

#settings-modal .modal-content li.active { 
  background: rgba(93, 64, 55, 0.9);
  border-left: 3px solid #d4af37;
}

#settings-modal .modal-content li:hover { 
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

#settings-modal .modal-content .model-info { 
  flex-grow: 1; 
}

#settings-modal .modal-content .model-info p {
  margin: 5px 0 0;
  font-size: 14px;
  color: #ccc;
}

#settings-modal .modal-content .use-btn {
  background: #2E7D32;
  border: none;
  border-radius: 8px;
  color: #fff;
  padding: 10px 15px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
}

#settings-modal .modal-content .use-btn:hover { 
  background: #388E3C; 
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.setting-item {
  background: rgba(62, 39, 35, 0.7);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  transition: all 0.3s;
}

.setting-item:hover {
  background: rgba(78, 52, 46, 0.7);
}

.setting-item label {
  display: block;
  margin-bottom: 10px;
}

.setting-item input[type="range"] {
  width: 100%;
  margin: 10px 0;
  -webkit-appearance: none;
  appearance: none;
  height: 5px;
  background: #5D4037;
  border-radius: 5px;
  outline: none;
}

.setting-item input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  background: #d4af37;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
}

.setting-item input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.setting-item span {
  display: inline-block;
  margin-left: 10px;
  font-weight: 600;
  color: #d4af37;
}

.tooltip {
  background-color: rgba(93, 64, 55, 0.9);
  color: #fff;
  padding: 12px;
  border-radius: 8px;
  margin: 10px 0;
  font-size: 13px;
  line-height: 1.5;
  border-left: 3px solid #d4af37;
}

.tooltip a {
  color: #A5D6A7;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.tooltip a:hover {
  color: #81C784;
  text-decoration: underline;
}


.advanced-options {
  margin-top: 15px;
  padding: 15px;
  border: 1px solid #5D4037;
  border-radius: 8px;
  background-color: rgba(62, 39, 35, 0.5);
}


.confirmation-modal .modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.confirmation-modal .modal-content {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 350px;
}

.confirmation-modal button {
  display: inline-block;
  padding: 12px 20px;
  margin: 15px 10px 0;
  border: none;
  border-radius: 8px;
  background-color: #5D4037;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
}

.confirmation-modal button:hover { 
  background-color: #6D4C41; 
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.confirmation-modal button:first-of-type {
  background-color: #C62828;
}

.confirmation-modal button:first-of-type:hover {
  background-color: #D32F2F;
}


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


.spinner {
  margin: 0 auto;
  border: 5px solid rgba(78, 52, 46, 0.3);
  border-top: 5px solid #d4af37;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}


@media (max-width: 992px) {
  #sidebar {
    width: 220px;
  }
  
  #main-content {
    margin-left: 220px;
  }
  
  body.dice-panel-open #main-content {
    padding-right: 250px;
  }
  
  #dice-panel {
    width: 250px;
  }
  
  body.dice-panel-open #chatbox {
    padding-right: 250px;
  }
}

@media (max-width: 768px) {
  #content {
    flex-direction: column;
  }
  
  #sidebar {
    position: relative;
    width: 100%;
    top: 0;
    height: auto;
    max-height: 30vh;
  }
  
  #main-content {
    margin-left: 0;
    height: auto;
  }
  
  body.dice-panel-open #main-content {
    padding-right: 0;
  }
  
  body.dice-panel-open #chatbox {
    padding-right: 0;
  }
  
  #dice-panel {
    width: 100%;
    height: 50vh;
  }
  
  .modal-content,
  .manage-characters-modal-content,
  .confirmation-modal .modal-content {
    width: 95%;
    max-height: 85vh;
  }
}
</style>
