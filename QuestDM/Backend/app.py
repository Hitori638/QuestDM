from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import ollama
import re
import logging
import json
import threading
from tinydb import TinyDB, Query

app = Flask(__name__)
CORS(app)
app.debug = True

current_model = "mistral-small:latest"

conversations = {}
llm_conversations = {}

db = TinyDB('stories.json')
stories_table = db.table('stories')
character_creation_table = db.table('character_creation')
story_creation_table = db.table('story_creation')
StoryQuery = Query()

last_story_summary = ""

# -----------------------------
# SYSTEM PROMPT FOR SUMMARIZING
# -----------------------------
def construct_summary_prompt(conversation_text):
    return [
        {
            "role": "system",
            "content": (
                "You are an assistant tasked with analyzing the conversation history of a story. "
                "Your job is to generate:\n\n"
                "1. A concise **summary** of the story so far.\n"
                "2. An **updated character_creation dictionary** containing any new or modified character details.\n\n"
                "Output Format:\n"
                "{\n"
                '  "summary": "A concise summary of the story so far.",\n'
                '  "character_creation": {\n'
                '    "CharacterName": {\n'
                '      "name": "CharacterName",\n'
                '      "race": "Race",\n'
                '      "class": "Class",\n'
                '      "backstory": "Character backstory."\n'
                "    }\n"
                "  }\n"
                "}\n\n"
                "Ensure your output uses double quotes for all keys and string values, "
                "so it conforms to JSON standards and is parsable by Python's json.loads().\n\n"
                "Do not include any additional text, such as interactive prompts or action choices. "
                "Only provide the summary and updated character details."
            )
        },
        {
            "role": "user",
            "content": conversation_text
        }
    ]

# -----------------------------
# MODE PROMPTS
# -----------------------------
novel_mode_prompt = {
    "role": "system",
    "content": (
        "You are an expert storyteller and game master, dedicated to crafting an immersive, detailed, and impressive adventure for the player. "
        "Additionally, you should always stay in-character as the Dungeon Master. Do not break the immersive storytelling by providing real-life programming code, instructions to develop software, or any other out-of-character (OOC) content that is not directly related to the ongoing story. "
        "If a user requests you to provide real-world code, or to behave as a general coding assistant, politely refuse or redirect to continue the narrative context of the game."
    )
}

dnd_mode_prompt = {
    "role": "system",
    "content": (
        "You are a Dungeon Master (DM) for a Dungeons & Dragons (D&D) 5th Edition game. Your goal is to create an immersive and engaging experience while strictly following D&D mechanics. Always stay in-character as the DM and do not provide real-world coding instructions or unrelated content.\n\n"
        "**Core Principles:**\n"
        "- **Player Agency:** Allow players to decide their actions freely and react with logical, consistent consequences.\n"
        "- **Immersion:** Describe the world vividly using all five senses and maintain a consistent setting.\n"
        "- **Rules Enforcement:** Follow D&D 5e mechanics, prompting the player for rolls when required.\n"
        "- **Explicit Player Confirmation:** Before advancing major scenes, ask: \"Is there anything else you'd like to do?\"\n\n"
        "**Combat Guidelines:**\n"
        "- **Initiative:** Prompt the player to roll for initiative and determine turn order.\n"
        "- **Turn Structure:** Each turn, the player can take one Action, one Bonus Action (if applicable), Movement, and possible Reactions.\n"
        "- **Attack Rolls & Damage:** Ask the player to roll for attacks and damage, comparing results to AC.\n"
        "- **Enemy Actions:** Describe NPC actions clearly, rolling attacks and saving throws internally.\n"
        "- **Status Effects & Conditions:** Track status effects and explain how they impact the player.\n"
        "- **Spellcasting:** Enforce spell slot usage, components, and concentration rules.\n"
        "- **Advantage/Disadvantage:** Apply when appropriate, explaining the reason.\n"
        "- **Critical Hits & Failures:** Describe critical rolls dramatically.\n\n"
        "**NPC & World Management:**\n"
        "- **Logical Reactions:** NPCs should behave according to their intelligence, goals, and past interactions.\n"
        "- **Dialogue & Roleplay:** Provide distinct personalities for NPCs and encourage player interaction.\n"
        "- **Environment Interaction:** Use terrain, cover, and environmental hazards dynamically in combat.\n\n"
        "**Gameplay Flow & Assistance:**\n"
        "- **Encourage Rolling:** Ask for skill checks, attack rolls, and saving throws as needed.\n"
        "- **Describe Outcomes Vividly:** Use engaging descriptions to show the results of actions.\n"
        "- **Resource Tracking:** Remind the player to manage spell slots, ammunition, and consumables.\n"
        "- **Resting & Recovery:** Implement short and long rest rules properly.\n\n"
        "**Ethical & Meta Guidelines:**\n"
        "- **Stay In-Character:** Do not break immersion with out-of-game references.\n"
        "- **Adapt to Player Comfort:** If a topic causes discomfort, shift the narrative.\n"
        "- **Keep Pacing Steady:** Balance description with game flow to maintain engagement.\n\n"
        "Your role is to provide an engaging and authentic D&D experience by following these principles and ensuring the player's immersion and enjoyment."
    )
}

# -----------------------------
# MERGE AND SUMMARIZE FUNCTIONS
# -----------------------------
def merge_conversation(existing_conversation, new_conversation):
    seen_messages = {json.dumps(msg, sort_keys=True) for msg in existing_conversation}
    for msg in new_conversation:
        if json.dumps(msg, sort_keys=True) not in seen_messages:
            existing_conversation.append(msg)
    return existing_conversation

def merge_characters(existing_chars, new_chars):
    if not isinstance(existing_chars, dict):
        existing_chars = {}
    if not isinstance(new_chars, dict):
        new_chars = {}
    merged_characters = existing_chars.copy()
    for char_id, new_char in new_chars.items():
        if char_id in merged_characters:
            merged_characters[char_id].update(new_char)
        else:
            merged_characters[char_id] = new_char
    return merged_characters

def summarize_and_save(story_name, llm_conv, threshold=10):
    """
    Summarizes user/assistant messages from index 3 onward,
    preserving the first three system messages in the conversation.
    """

    if len(llm_conv) <= 3:
        return llm_conv


    new_user_msgs = [msg for msg in llm_conv[3:] if msg["role"] == "user"]
    if len(new_user_msgs) < threshold:
        return llm_conv


    summary_exists = (
        len(llm_conv) > 3
        and llm_conv[3]["role"] == "assistant"
        and llm_conv[3]["content"].startswith("SUMMARY:")
    )


    start_index = 4 if summary_exists else 3

    base_summary = ""
    if summary_exists:
        base_summary = llm_conv[3]["content"].replace("SUMMARY:", "", 1).strip()


    new_text = "\n\n".join(
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in llm_conv[start_index:]
    )


    if base_summary:
        conversation_text = f"SUMMARY: {base_summary}\n\n{new_text}"
    else:
        conversation_text = new_text


    summarization_prompt = construct_summary_prompt(conversation_text)
    response_chunks = ollama.chat(
        model=current_model,
        messages=summarization_prompt,
        stream=False,
    )
    if hasattr(response_chunks, "message"):
        response_accumulated = response_chunks.message.content
    elif isinstance(response_chunks, dict):
        response_accumulated = response_chunks.get("message", {}).get("content", "")
    elif isinstance(response_chunks, (list, tuple)):
        response_accumulated = "".join(
            chunk.get("message", {}).get("content", "") for chunk in response_chunks if isinstance(chunk, dict)
        )
    else:
        response_accumulated = ""

    try:
        if response_accumulated.strip().startswith("{"):
            response_data = json.loads(response_accumulated)
        else:
            response_data = {"summary": response_accumulated.strip(), "character_creation": {}}
    except Exception:
        response_data = {"summary": response_accumulated.strip(), "character_creation": {}}

    new_summary = response_data.get("summary", "")
    new_characters = response_data.get("character_creation", {})

 
    story = story_creation_table.get(StoryQuery.name == story_name)
    if story:
        existing_conversation = story.get("conversation_history", [])
        updated_conversation = merge_conversation(existing_conversation, llm_conv)
        existing_characters = story.get("characters", {})
        merged_characters = merge_characters(existing_characters, new_characters)
        story_creation_table.update(
            {
                "conversation_history": updated_conversation,
                "summary": new_summary,
                "characters": merged_characters,
            },
            StoryQuery.name == story_name,
        )


    summarized_message = {"role": "assistant", "content": f"SUMMARY: {new_summary}"}
    new_llm_conv = llm_conv[:3] + [summarized_message]
    return new_llm_conv



# -----------------------------
# ROLE TRANSFORMATION FOR DISPLAY
# -----------------------------
def transform_conversation_for_display(conversation):
    transformed = []
    for msg in conversation:
        if msg["role"] == "assistant":
            new_msg = msg.copy()
            new_msg["role"] = "DM"
            transformed.append(new_msg)
        elif msg["role"] == "user":
            new_msg = msg.copy()
            new_msg["role"] = "You"
            transformed.append(new_msg)
    return transformed

# -----------------------------
# ENDPOINTS
# -----------------------------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    story_name = data.get('story_name')
    user_input = data.get('message')
    story = story_creation_table.get(StoryQuery.name == story_name)
    if not story:
        return jsonify({'error': f"Story '{story_name}' not found."}), 404


    if story['mode'] == 'dnd':
        initial_prompt = dnd_mode_prompt
    elif story['mode'] == 'novel':
        initial_prompt = novel_mode_prompt
    else:
        return jsonify({'error': 'Invalid story mode.'}), 400

    if not user_input:
        return jsonify({'error': 'No message provided.'}), 400


    if story_name not in conversations or not conversations[story_name]:

        mode_prompt = initial_prompt


        story_details_prompt = {
            "role": "system",
            "content": (
                f"Story Details:\n"
                f"Name: {story.get('name', 'Unknown')}\n"
                f"Description: {story.get('description', 'No description')}\n"
                f"Genre: {story.get('genre', 'N/A')}\n"
            )
        }


        characters = story.get("characters", [])
        character_details = "NPC Story Characters:\n"
        for char in characters:
            char_name = char.get("name", "Unknown")
            char_race = char.get("race", "Unknown")
            char_class = char.get("class", "Unknown")
            char_backstory = char.get("backstory", "No backstory")
            character_details += f"{char_name} (Race: {char_race}, Class: {char_class}): {char_backstory}\n"
        character_prompt = {
            "role": "system",
            "content": character_details
        }


        conversations[story_name] = [mode_prompt, story_details_prompt, character_prompt]
        llm_conversations[story_name] = [mode_prompt, story_details_prompt, character_prompt]


    user_message = {"role": "user", "content": user_input}
    conversations[story_name].append(user_message)
    llm_conversations[story_name].append(user_message)

    try:
        def generate():
            app.logger.debug(
                f"LLM Conversation for {story_name}:\n{json.dumps(llm_conversations[story_name], indent=2)}"
            )
            stream = ollama.chat(
                model=current_model,
                messages=llm_conversations[story_name],
                stream=True,
            )
            response_accumulated = ""
            inside_think = False
            think_buffer = ""
            for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    response_accumulated += content
                if content.lstrip().startswith("<think>"):
                    inside_think = True
                    think_buffer = content
                    continue
                if inside_think:
                    think_buffer += content
                    if "</think>" in content:
                        inside_think = False
                        extracted_think = re.search(r"<think>(.*?)</think>", think_buffer, re.DOTALL)
                        if extracted_think:
                            for i in range(0, len(extracted_think.group(1)), 50):
                                yield f"data: {json.dumps({'content': extracted_think.group(1)[i:i+50]})}\n\n"
                        think_buffer = ""
                    continue
                yield f"data: {json.dumps({'content': content})}\n\n"

            assistant_msg = {"role": "assistant", "content": response_accumulated}
            conversations[story_name].append(assistant_msg)
            llm_conversations[story_name].append(assistant_msg)

   
            story_creation_table.update(
                {"conversation_history": llm_conversations[story_name]},
                StoryQuery.name == story_name
            )

 
            def background_summary():
                updated_conv = summarize_and_save(story_name, llm_conversations[story_name])
                llm_conversations[story_name] = updated_conv

            threading.Thread(target=background_summary).start()

        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500




@app.route('/list_models', methods=['GET'])
def list_models():
    try:
        all_models_response = ollama.list()
        models = getattr(all_models_response, 'models', None)
        if models is None:
            return jsonify({"error": "Unexpected response format from ollama.list()."}), 500
        if not isinstance(models, list):
            return jsonify({"error": "Unexpected type for 'models' attribute."}), 500
        def serialize_model(model):
            try:
                model_name = getattr(model, 'model', 'N/A')
                details = getattr(model, 'details', None)
                parameter_size = getattr(details, 'parameter_size', 'N/A') if details else 'N/A'
                return {"model_name": model_name, "parameter_size": parameter_size}
            except Exception as e:
                return {"model_name": getattr(model, 'model', 'N/A'), "parameter_size": 'N/A'}
        models_list = [serialize_model(model) for model in models]
        return jsonify(models_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create_story', methods=['POST'])
def create_story():
    data = request.get_json()
    story_name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    genre = data.get('genre', '').strip()
    mode = data.get('mode', '').strip()

    selected_characters = data.get('characters', [])
    
    if not story_name or not description or not genre or not mode:
        return jsonify({'error': 'Story name, description, genre, and mode are required.'}), 400


    character_copies = []
    for char_name in selected_characters:
        char = character_creation_table.get(StoryQuery.name == char_name)
        if char:
            character_copies.append(char)

    existing_story = story_creation_table.get(StoryQuery.name == story_name)
    if existing_story:
 
        story_creation_table.update(
            {
                'description': description or existing_story.get('description'),
                'genre': genre or existing_story.get('genre'),
                'mode': mode or existing_story.get('mode'),
                'characters': character_copies
            },
            StoryQuery.name == story_name
        )
        message = f"Story '{story_name}' updated successfully!"
        updated_story = story_creation_table.get(StoryQuery.name == story_name)
    else:
        new_story = {
            'name': story_name,
            'description': description,
            'genre': genre,
            'mode': mode,
            'characters': character_copies,
            'conversation_history': [],
            'summary': ''
        }
        story_creation_table.insert(new_story)
        message = f"Story '{story_name}' created successfully!"
        updated_story = new_story
    return jsonify({'message': message, 'story': updated_story})


@app.route('/load_story', methods=['POST'])
def load_story():
    data = request.get_json()
    story_name = data.get('name', '').strip()
    if not story_name:
        return jsonify({'error': 'Story name is required.'}), 400
    story = story_creation_table.get(StoryQuery.name == story_name)
    if not story:
        return jsonify({'error': f"Story with the name '{story_name}' does not exist."}), 404
    conversation = story.get("conversation_history", [])
    conversations[story_name] = conversation.copy()
    llm_conversations[story_name] = conversation.copy()
    display_conversation = transform_conversation_for_display(conversation)
    return jsonify({'story': story, 'conversation': display_conversation})

@app.route('/create_character', methods=['POST'])
def create_character():
    data = request.get_json()
    new_character_name = data.get('name', '').strip()
    new_character_race = data.get('race', '').strip()
    new_character_class = data.get('class', '').strip()
    new_character_backstory = data.get('backstory', '').strip()
    if not new_character_name or not new_character_race or not new_character_class:
        return jsonify({'error': 'Character name, race, and class are required.'}), 400
    existing_character = character_creation_table.search(StoryQuery.name == new_character_name)
    if existing_character:
        return jsonify({'error': f"A character with the name '{new_character_name}' already exists."}), 400
    character_data = {
        'name': new_character_name,
        'race': new_character_race,
        'class': new_character_class,
        'backstory': new_character_backstory
    }
    character_creation_table.insert(character_data)
    return jsonify({'message': 'Character created successfully!', 'character': character_data})

@app.route('/get_stories', methods=['GET'])
def get_stories():
    all_stories = story_creation_table.all()
    return jsonify({'stories': all_stories})

@app.route('/get_characters', methods=['GET'])
def get_characters():
    all_characters = character_creation_table.all()
    return jsonify({'characters': all_characters})

@app.route('/edit_story', methods=['PUT'])
def edit_story():
    data = request.get_json()
    original_name = data.get('originalName', '').strip() or data.get('name', '').strip()
    if not original_name:
        return jsonify({'error': 'Original story name is required.'}), 400
    story = story_creation_table.get(StoryQuery.name == original_name)
    if not story:
        return jsonify({'error': f"Story '{original_name}' not found."}), 404
    

    selected_characters = data.get('characters', [])
    character_copies = []
    for char_name in selected_characters:
        char = character_creation_table.get(StoryQuery.name == char_name)
        if char:
            character_copies.append(char)
    
    updated_data = {
        'name': data.get('name', story['name']),
        'description': data.get('description', story['description']),
        'genre': data.get('genre', story['genre']),
        'mode': data.get('mode', story['mode']),
        'characters': character_copies
    }
    story_creation_table.update(updated_data, StoryQuery.name == original_name)
    return jsonify(updated_data)


@app.route('/edit_character', methods=['PUT'])
def edit_character():
    data = request.get_json()
    original_name = data.get('originalName', '').strip() or data.get('name', '').strip()
    if not original_name:
        return jsonify({'error': 'Character name is required.'}), 400
    character = character_creation_table.get(StoryQuery.name == original_name)
    if not character:
        return jsonify({'error': f"Character '{original_name}' not found."}), 404
    updated_data = {
        'name': data.get('name', character['name']),
        'race': data.get('race', character['race']),
        'class': data.get('class', character['class']),
        'backstory': data.get('backstory', character['backstory']),
    }
    character_creation_table.update(updated_data, StoryQuery.name == original_name)
    return jsonify(updated_data)

@app.route('/delete_character', methods=['DELETE'])
def delete_character():
    data = request.get_json()
    character_name = data.get('name', '').strip()
    if not character_name:
        return jsonify({'error': 'Character name is required.'}), 400
    existing_character = character_creation_table.search(StoryQuery.name == character_name)
    if not existing_character:
        return jsonify({'error': f"Character with the name '{character_name}' does not exist."}), 404
    character_creation_table.remove(StoryQuery.name == character_name)
    return jsonify({'message': f"Character '{character_name}' deleted successfully."})

@app.route('/delete_story', methods=['DELETE'])
def delete_story():
    data = request.get_json()
    story_name = data.get('name', '').strip()
    if not story_name:
        return jsonify({'error': 'Story name is required.'}), 400
    story = story_creation_table.get(StoryQuery.name == story_name)
    if not story:
        return jsonify({'error': f"Story with the name '{story_name}' does not exist."}), 404
    story_creation_table.remove(StoryQuery.name == story_name)
    return jsonify({'message': f"Story '{story_name}' and its conversation history deleted successfully."})

@app.route('/get_model', methods=['GET'])
def get_model():
    return jsonify({'model': current_model})

@app.route('/set_model', methods=['POST'])
def set_model():
    global current_model
    data = request.get_json()
    model_name = data.get('model_name')
    if not model_name:
        return jsonify({'error': 'Model name is required.'}), 400
    current_model = model_name
    return jsonify({'message': f'Model updated to {model_name}', 'model': current_model}), 200

if __name__ == "__main__":
    app.run(debug=True)
