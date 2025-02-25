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
          <p>Select a story to begin your adventure!</p>
        </div>
        <div v-else>
          <h2>{{ selectedStory.name }}</h2>
          <StoryComponent :storySummary="selectedStory" :conversation="conversation" />
        </div>
      </main>
    </div>

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
            <button :class="{ active: activeTab === 'llm' }" @click="activeTab = 'llm'">LLM-Generated</button>
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


    <div v-if="showSettingsModal" id="settings-modal">
      <div class="modal-overlay" @click="closeSettingsModal"></div>
      <div class="modal-content">
        <h2>Settings</h2>
        <p>Select the LLM you wish to use:</p>
        <ul>
          <li
            v-for="(model, index) in installedLLMs"
            :key="index"
            :class="{ active: model.model_name === currentLLM }"
          >
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

      // ------------------------------
      //     DICE ROLLER PROPERTIES
      // ------------------------------
      showDicePanel: false,
      presetModifier: 0,
      customDiceNotation: '',
      diceResult: null,
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
    // ------------------------------
    //      FETCH METHODS
    // ------------------------------
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

    // ------------------------------
    //     OPEN/CLOSE MODALS & PANELS
    // ------------------------------
    openEditStoryModal(story) {
      fetch('http://localhost:5000/load_story', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: story.name }),
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Failed to load story: ${res.statusText}`);
          }
          return res.json();
        })
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

      // Reset Manage Characters modal state
      this.tempAssignedCharacters = [];
      this.manageCharactersMode = '';
      this.activeTab = 'user';

      // Reset advanced toggle states
      this.showAdvancedOptionsCreateCharacter = false;
      this.showAdvancedOptionsEditCharacter = false;
    },

    // ------------------------------
    //   MANAGE CHARACTERS LOGIC
    // ------------------------------
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
      fetch('http://localhost:5000/create_character', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: charObj.name,
          race: charObj.race || 'Unknown',
          class: charObj.class || 'Unknown',
          backstory: charObj.backstory || 'Generated by LLM',
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.character) {
            data.character.isLLM = false;
            this.characters.push(data.character);
            alert(`${charObj.name} has been added to your characters!`);
          }
        })
        .catch((error) => {
          console.error('Error importing character:', error);
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

    // ------------------------------
    //    STORY CREATION & EDITING
    // ------------------------------
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

        const response = await fetch('http://localhost:5000/create_story', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
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

        const response = await fetch('http://localhost:5000/edit_story', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (response.ok) {
          const updatedStory = await response.json();
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
        } else {
          throw new Error(`Failed to edit story: ${response.statusText}`);
        }
      } catch (error) {
        console.error('Error editing story:', error);
      }
    },

    // ------------------------------
    //   CHARACTER CREATION & EDITING
    // ------------------------------
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

    // ------------------------------
    //         STORY LOADING
    // ------------------------------
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

    // ------------------------------
    //         DELETION LOGIC
    // ------------------------------
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

    // ------------------------------
    //       SETTINGS & LLM
    // ------------------------------
    openSettingsModal() {
      this.fetchInstalledLLMs();
      this.showSettingsModal = true;
    },
    closeSettingsModal() {
      this.showSettingsModal = false;
    },
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

    // ------------------------------
    //       DICE ROLLER METHODS
    // ------------------------------
    toggleDicePanel() {
      this.showDicePanel = !this.showDicePanel;
      if (!this.showDicePanel) {
        this.diceResult = null;
        this.customDiceNotation = '';
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

    // ------------------------------
    //   Toggle Advanced Options
    // ------------------------------
    toggleAdvancedOptions(mode) {
      if (mode === 'create') {
        this.showAdvancedOptionsCreateCharacter = !this.showAdvancedOptionsCreateCharacter;
      } else if (mode === 'edit') {
        this.showAdvancedOptionsEditCharacter = !this.showAdvancedOptionsEditCharacter;
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
.settings-btn, .dice-btn {
  position: absolute;
  background: none;
  border: none;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  transition: transform 0.3s, color 0.3s;
}
.settings-btn { top: 20px; right: 20px; }
.settings-btn:hover { color: #ccc; transform: rotate(20deg); }
.dice-btn { top: 20px; right: 60px; }
.dice-btn:hover { transform: rotate(20deg); color: #ccc; }
.error-message { color: red; font-size: 12px; margin-top: 5px; }
#content { display: flex; height: calc(100vh - 80px); }
#sidebar { width: 300px; background-color: #222; padding: 15px; border-right: 2px solid #444; }
#tabs { display: flex; justify-content: space-around; margin-bottom: 20px; }
#tabs button { padding: 10px; background-color: #555; color: white; border: none; cursor: pointer; transition: background-color 0.3s; }
#tabs button:hover { background-color: #777; }
#stories ul, #characters ul { list-style: none; padding: 0; }
#stories li, #characters li { margin: 10px 0; padding: 10px; background-color: #333; border-radius: 5px; }
#stories button, #characters button { margin-top: 15px; padding: 10px; background-color: #555; color: white; border: none; cursor: pointer; border-radius: 5px; transition: background-color 0.3s; }
#stories button:hover, #characters button:hover { background-color: #777; }
#main-content { flex-grow: 1; padding: 20px; }

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
#conversation p { margin: 10px 0; padding: 10px; border-radius: 10px; line-height: 1.5; }
#conversation p strong { color: #4f4f4f; }
#conversation p:nth-child(odd) { background-color: rgba(190, 190, 190, 0.9); }
#conversation p:nth-child(even) { background-color: rgba(220, 220, 220, 0.9); }
#input-area { display: flex; justify-content: center; margin-top: 20px; }
#input-area input { width: 400px; padding: 10px; border: 2px solid #a8a8a8; border-radius: 5px; background: #eaeaea; color: #3c3c3c; font-size: 16px; }
#input-area button { padding: 10px 20px; margin-left: 10px; border: none; border-radius: 5px; background: #7f7f7f; color: #ffffff; font-size: 16px; cursor: pointer; transition: background 0.3s, transform 0.2s; }
#input-area button:hover { background: #5f5f5f; transform: scale(1.05); }
#input-area button:active { transform: scale(0.95); }

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-thumb { background: #a8a8a8; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #888888; }

#create-story-modal,
#edit-story-modal,
#create-character-modal,
#edit-character-modal,
#manage-characters-modal,
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
.modal-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); }
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
  max-height: 80vh;
  overflow-y: auto;
}
.modal-content h2 { font-size: 24px; margin-bottom: 15px; text-align: center; }
.modal-content label { display: block; margin-bottom: 10px; font-size: 16px; }
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
.modal-content textarea { resize: none; height: 80px; }
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
.modal-content button:hover { background-color: #777; }
.modal-content button:last-child { background-color: #333; }
.modal-content button:last-child:hover { background-color: #555; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }

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
.confirmation-modal button:hover { background-color: #777; }

#settings-modal .modal-content {
  background: #1c1c1c;
  border-radius: 12px;
  padding: 20px;
  max-width: 500px;
  width: 90%;
  text-align: left;
}
#settings-modal .modal-content ul { list-style: none; padding: 0; margin: 0; }
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
#settings-modal .modal-content li.active { background: #555; border: 2px solid #0a8; }
#settings-modal .modal-content li:hover { background: #444; }
#settings-modal .modal-content .model-info { flex-grow: 1; }
#settings-modal .modal-content .use-btn {
  background: #0a8;
  border: none;
  border-radius: 5px;
  color: #fff;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.3s;
}
#settings-modal .modal-content .use-btn:hover { background: #06c; }

.delete-btn {
  background: none;
  border: none;
  color: #f55;
  font-size: 18px;
  cursor: pointer;
  margin-left: 10px;
  transition: color 0.3s ease;
}
.delete-btn:hover { color: #d33; }

.manage-characters-modal-content { text-align: left; max-width: 700px; }
.assigned-characters, .available-characters { margin: 1rem 0; }
.character-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #3b3b3b;
  margin: 0.5rem 0;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}
.character-card button { margin-left: 1rem; }
.tabs { display: flex; gap: 1rem; margin-bottom: 1rem; }
.tabs button { background: #444; color: #fff; border: none; padding: 0.5rem 1rem; cursor: pointer; }
.tabs button.active { background: #666; font-weight: bold; }
.tab-content { border-top: 1px solid #444; padding-top: 1rem; }
.close-btn {
  background: #555;
  color: #fff;
  border: none;
  border-radius: 5px;
  padding: 0.6rem 1.2rem;
  cursor: pointer;
  transition: background 0.3s;
}
.close-btn:hover { background: #777; }
/* Dice Panel Styles */
#dice-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 320px;
  height: 100vh;
  background: #2b2b2b;
  border-left: 2px solid #444;
  padding: 20px;
  box-shadow: -4px 0 10px rgba(0, 0, 0, 0.5);
  overflow-y: auto;
  z-index: 1100;
}
#dice-panel h2 { margin-top: 0; text-align: center; }
.close-dice-btn { position: absolute; top: 10px; right: 10px; background: none; border: none; font-size: 20px; color: #fff; cursor: pointer; }
.dice-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
#dice-panel button {
  background-color: #555;
  color: #fff;
  border: none;
  border-radius: 5px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.3s;
}
#dice-panel button:hover { background-color: #777; }
#dice-panel input[type="text"],
#dice-panel input[type="number"] {
  width: 100%;
  padding: 8px;
  border: 1px solid #555;
  border-radius: 5px;
  background: #333;
  color: #fff;
  margin-top: 5px;
  margin-bottom: 10px;
  box-sizing: border-box;
}

.advanced-options {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid #555;
  border-radius: 5px;
  background-color: #2b2b2b;
}
.advanced-options label { font-size: 14px; }

.tooltip {
  background-color: #444;
  color: #fff;
  padding: 8px;
  border-radius: 5px;
  margin-bottom: 10px;
  font-size: 12px;
  text-align: left;
}
.tooltip a {
  color: #0af;
  text-decoration: underline;
}
.tooltip a:hover {
  color: #0cf;
}
</style>
