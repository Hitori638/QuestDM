from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import ollama
import re
import json
import threading
from tinydb import TinyDB, Query

app = Flask(__name__)
CORS(app)
app.debug = True


current_model = "llama3.2-vision:latest"
model_accuracy_threshold = 3     
current_context_size = 4096      

conversations = {} 
llm_conversations = {}  

message_count_since_cleanup = {}  
cleanup_interval_messages = 5 

db = TinyDB('stories.json')
stories_table = db.table('stories')
character_creation_table = db.table('character_creation')
story_creation_table = db.table('story_creation')
StoryQuery = Query()

last_story_summary = ""

def construct_summary_prompt(conversation_text):
    return [
        {
            "role": "system",
            "content": (
                "You are an assistant tasked with analyzing the conversation history of a D&D story. "
                "Your job is to generate:\n\n"
                "1. A comprehensive **summary** of the story so far, including key events, decisions, and character development.\n"
                "2. An **updated character_creation dictionary** containing ANY AND ALL characters mentioned in the story.\n\n"
                "Important guidelines:\n"
                "- Include EVERY character that appears in the conversation, even if they only appear briefly\n"
                "- For new characters, create a complete entry with as much information as available\n"
                "- Include all significant character changes (physical changes, injuries, status effects, personality developments)\n"
                "- Update character backstories to reflect new developments in the story\n"
                "- Maintain continuity from previous summaries\n"
                "- Track relationships between characters\n\n"
                "Output Format:\n"
                "{\n"
                '  "summary": "A detailed summary of the story progression.",\n'
                '  "character_creation": {\n'
                '    "CharacterName": {\n'
                '      "name": "CharacterName",\n'
                '      "race": "Race (if known, or \"Unknown\" if not)",\n'
                '      "class": "Class (if known, or \"Unknown\" if not)",\n'
                '      "backstory": "Character backstory based on available information",\n'
                '      "status": "Current physical/mental state and location"\n'
                "    },\n"
                '    "AnotherCharacter": {\n'
                '      "name": "AnotherCharacter",\n'
                '      ... other character details\n'
                "    }\n"
                "  }\n"
                "}\n\n"
                "Ensure your output uses double quotes for all keys and string values, "
                "so it conforms to JSON standards and is parsable by Python's json.loads().\n\n"
                "IMPORTANT: You MUST include ALL characters that appear in the story, even minor ones.\n"
                "Do not include any additional text, only the JSON."
            )
        },
        {
            "role": "user",
            "content": conversation_text
        }
    ]

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
        "- **Keep Pacing Steady:** Balance description with game flow to maintain engagement.\n\n"
        "Your role is to provide an engaging and authentic D&D experience by following these principles and ensuring the player's immersion and enjoyment."
    )
}

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
            for key, val in new_char.items():
                if key == 'backstory' and merged_characters[char_id].get('backstory'):
   
                    original_backstory = merged_characters[char_id]['backstory']
                    if val != original_backstory and val:
  
                        merged_characters[char_id]['backstory'] = val
                elif key == 'status' and val:
 
                    merged_characters[char_id][key] = val
                else:
        
                    merged_characters[char_id][key] = val
        else:

            merged_characters[char_id] = new_char
    
    return merged_characters

def process_summary_json(summary_text):
    try:

        json_match = re.search(r'({.*})', summary_text, re.DOTALL)
        if json_match:
            summary_data = json.loads(json_match.group(1))
            return summary_data
        else:

            return {
                "summary": summary_text,
                "character_creation": {}
            }
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON decode error: {e}")
        return {
            "summary": summary_text,
            "character_creation": {}
        }

def cleanup_inactive_characters(story_name, threshold=10):
    """
    Removes characters from the story that haven't been mentioned in the last N user prompts.
    
    Args:
        story_name (str): The name of the story to clean up
        threshold (int): Number of recent prompts to check for character mentions
    """
    story = story_creation_table.get(StoryQuery.name == story_name)
    if not story:
        print(f"DEBUG: Story '{story_name}' not found for character cleanup.")
        return
    

    characters = story.get("characters", {})
    if not characters or not isinstance(characters, dict) or len(characters) == 0:
        print(f"DEBUG: No characters to clean up for story '{story_name}'.")
        return
    

    llm_conv = llm_conversations.get(story_name, [])

    start_idx = 4 if len(llm_conv) > 3 and "SUMMARY:" in llm_conv[3].get("content", "") else 3
    recent_messages = llm_conv[start_idx:]
    

    user_messages = [msg for msg in recent_messages if msg["role"] == "user"]
    

    recent_user_messages = user_messages[-threshold:] if len(user_messages) > threshold else user_messages
    
    if not recent_user_messages:
        print(f"DEBUG: No recent user messages found for story '{story_name}'.")
        return
    

    recent_text = " ".join([msg["content"] for msg in recent_user_messages])
    recent_text = recent_text.lower()  
    

    characters_to_keep = {}
    characters_to_remove = {}
    

    for char_name, char_data in characters.items():

        if 'template_origin' in char_data:
            characters_to_keep[char_name] = char_data
            continue
            

        actual_name = char_data.get('name', char_name).lower()
        

        if actual_name in recent_text:
            characters_to_keep[char_name] = char_data
        else:
            characters_to_remove[char_name] = char_data
    
    if not characters_to_remove:
        print(f"DEBUG: No characters to remove from story '{story_name}'.")
        return
    
    print(f"DEBUG: Removing {len(characters_to_remove)} inactive characters from story '{story_name}'.")
    print(f"DEBUG: Removed characters: {', '.join(characters_to_remove.keys())}")
    

    story_creation_table.update(
        {'characters': characters_to_keep},
        StoryQuery.name == story_name
    )
    

    try:
        current_summary = story.get('current_summary', '{}')
        summary_data = json.loads(current_summary)
        
        if isinstance(summary_data, dict) and 'character_creation' in summary_data:

            filtered_characters = {
                k: v for k, v in summary_data['character_creation'].items() 
                if k in characters_to_keep
            }
            summary_data['character_creation'] = filtered_characters
            

            story_creation_table.update(
                {'current_summary': json.dumps(summary_data)},
                StoryQuery.name == story_name
            )
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"DEBUG: Error updating summary during character cleanup: {e}")


def summarize_and_save(story_name, threshold=None):
    if threshold is None:
        threshold = model_accuracy_threshold
    
    llm_conv = llm_conversations.get(story_name, [])
    

    if len(llm_conv) < 3:
        return llm_conv
    

    user_messages = [msg for msg in llm_conv[3:] if msg["role"] == "user"]
    

    if len(user_messages) < threshold:
        return llm_conv
    

    has_summary = (
        len(llm_conv) > 3 and
        llm_conv[3]["role"] == "assistant" and
        "SUMMARY:" in llm_conv[3]["content"]
    )
    

    start_index = 4 if has_summary else 3
    

    existing_summary = ""
    if has_summary:
        existing_summary = llm_conv[3]["content"].replace("SUMMARY:", "", 1).strip()
    

    new_content = "\n\n".join(
        f"{msg['role'].upper()}: {msg['content']}" for msg in llm_conv[start_index:]
    )
    

    if existing_summary:
        conversation_text = f"PREVIOUS SUMMARY: {existing_summary}\n\n{new_content}"
    else:
        conversation_text = new_content

    summarization_prompt = construct_summary_prompt(conversation_text)
    
    response = ollama.chat(
        model=current_model,
        messages=summarization_prompt,
        stream=False,
        options={"num_ctx": current_context_size}
    )
    

    if hasattr(response, "message"):
        new_summary = response.message.content
    elif isinstance(response, dict):
        new_summary = response.get("message", {}).get("content", "")
    else:
        new_summary = "Failed to generate summary."
    
    print(f"DEBUG: Raw summary response: {new_summary}")
    

    processed_summary = process_summary_json(new_summary)

    summary_text = processed_summary.get("summary", "")
    

    summary_message = {"role": "assistant", "content": f"SUMMARY: {summary_text}"}
    

    recent_messages_to_keep = threshold 
    

    new_llm_conv = llm_conv[:3] + [summary_message]
    

    if len(llm_conv) > start_index + recent_messages_to_keep:
        new_llm_conv += llm_conv[-(recent_messages_to_keep):]
    else:
        new_llm_conv += llm_conv[start_index:]
    

    story = story_creation_table.get(StoryQuery.name == story_name)
    if story:

        if 'character_creation' in processed_summary and processed_summary['character_creation']:
            existing_characters = story.get('characters', {})
            if not isinstance(existing_characters, dict):
                existing_characters = {}
            

            if isinstance(existing_characters, list):
                char_dict = {}
                for char in existing_characters:
                    if isinstance(char, dict) and 'name' in char:
                        char_dict[char['name']] = char
                existing_characters = char_dict
            

            merged_characters = merge_characters(existing_characters, processed_summary['character_creation'])
            

            story_creation_table.update(
                {'characters': merged_characters},
                StoryQuery.name == story_name
            )


        story_creation_table.update(
            {
                "conversation_history": conversations.get(story_name, []),
                "llm_memory": new_llm_conv,
                "current_summary": json.dumps(processed_summary)  
            },
            StoryQuery.name == story_name
        )
    
    return new_llm_conv

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


message_count_since_cleanup = {} 
cleanup_interval_messages = 5    


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
    if isinstance(characters, dict):
        characters = list(characters.values())
    
    character_details = "Story Characters:\n"
    for char in characters:
        if isinstance(char, dict):
            details = f"{char.get('name', 'Unknown')} (Race: {char.get('race', 'Unknown')}, Class: {char.get('class', 'Unknown')})\n"
            details += f"Backstory: {char.get('backstory', 'No backstory')}\n"
            advanced_info = []
            for key in char:
                if key not in ['name', 'race', 'class', 'backstory']:
                    advanced_info.append(f"{key}: {char[key]}")
            if advanced_info:
                details += "Advanced: " + ", ".join(advanced_info) + "\n"
            character_details += details
        else:
            character_details += f"{char}\n"
    
    character_prompt = {
        "role": "system",
        "content": character_details
    }
    

    if story_name in llm_conversations and llm_conversations[story_name]:
        llm_conversations[story_name][1] = story_details_prompt
        llm_conversations[story_name][2] = character_prompt
    else:
        saved_llm_memory = story.get("llm_memory", [])
        if saved_llm_memory and len(saved_llm_memory) >= 3:
            llm_conversations[story_name] = saved_llm_memory
            llm_conversations[story_name][0] = initial_prompt
            llm_conversations[story_name][1] = story_details_prompt
            llm_conversations[story_name][2] = character_prompt
        else:
            llm_conversations[story_name] = [initial_prompt, story_details_prompt, character_prompt]
    

    if story_name not in conversations:
        conversations[story_name] = story.get("conversation_history", [])
        if not conversations[story_name]:
            conversations[story_name] = [initial_prompt, story_details_prompt, character_prompt]
    

    if story_name not in message_count_since_cleanup:
        message_count_since_cleanup[story_name] = 0
    

    message_count_since_cleanup[story_name] += 1
    

    user_message = {"role": "user", "content": user_input}
    conversations[story_name].append(user_message)
    llm_conversations[story_name].append(user_message)

    def generate():
        print("DEBUG: Starting stream for story:", story_name)
        stream = ollama.chat(
        model=current_model,
        messages=llm_conversations[story_name],
        stream=True,
        options={"num_ctx": current_context_size})
        response_accumulated = ""
        inside_think = False
        think_buffer = ""
        aborted = False
        try:
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
                                try:
                                    yield f"data: {json.dumps({'content': extracted_think.group(1)[i:i+50]})}\n\n"
                                except GeneratorExit:
                                    print("DEBUG: Client aborted during <think> chunk.")
                                    aborted = True
                                    break
                            if aborted:
                                break
                        think_buffer = ""
                    continue
                try:
                    yield f"data: {json.dumps({'content': content})}\n\n"
                except GeneratorExit:
                    print("DEBUG: Client aborted during regular chunk.")
                    aborted = True
                    break
        except GeneratorExit:
            print("DEBUG: GeneratorExit caught; client disconnected.")
            aborted = True
        except Exception as e:
            print("DEBUG: Exception in stream generator:", e)
        finally:
            if response_accumulated:
                print("DEBUG: Saving partial response for story:", story_name)
                assistant_msg = {"role": "assistant", "content": response_accumulated}
                conversations[story_name].append(assistant_msg)
                llm_conversations[story_name].append(assistant_msg)
                
                story_creation_table.update(
                    {
                        "conversation_history": conversations[story_name],
                        "llm_memory": llm_conversations[story_name]
                    },
                    StoryQuery.name == story_name
                )
                
                def background_tasks():
                    updated_conv = summarize_and_save(story_name)
                    llm_conversations[story_name] = updated_conv
                    print("DEBUG: LLM Conversation after summarization:")
                    print(json.dumps(llm_conversations[story_name], indent=2))
                    

                    if message_count_since_cleanup[story_name] >= cleanup_interval_messages:
                        print(f"DEBUG: Running character cleanup for story '{story_name}'")
                        cleanup_inactive_characters(story_name, threshold=10)  
                        message_count_since_cleanup[story_name] = 0
                
                threading.Thread(target=background_tasks).start()
                
            print("DEBUG: Stream complete for story:", story_name)

    return Response(generate(), mimetype='text/event-stream')


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

    character_copies = {}
    for char_name in selected_characters:
        char = character_creation_table.get(StoryQuery.name == char_name)
        if char:
            char_copy = char.copy()
            char_copy['template_origin'] = char_name
            character_copies[char_name] = char_copy

    existing_story = story_creation_table.get(StoryQuery.name == story_name)
    if existing_story:
        story_creation_table.update(
            {
                'description': description or existing_story.get('description'),
                'genre': genre or existing_story.get('genre'),
                'mode': mode or existing_story.get('mode'),
                'characters': character_copies,
                'conversation_history': existing_story.get('conversation_history', []),
                'llm_memory': existing_story.get('llm_memory', []),
                'current_summary': existing_story.get('current_summary', '')
            },
            StoryQuery.name == story_name,
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
            'llm_memory': [],
            'current_summary': ''
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

    full_conversation = story.get("conversation_history", [])
    conversations[story_name] = full_conversation.copy()
    

    llm_memory = story.get("llm_memory", [])
    

    if story['mode'] == 'dnd':
        initial_prompt = dnd_mode_prompt
    elif story['mode'] == 'novel':
        initial_prompt = novel_mode_prompt
    else:
        initial_prompt = dnd_mode_prompt 
    
    story_details_prompt = {
        "role": "system",
        "content": (
            f"Story Details:\n"
            f"Name: {story.get('name', 'Unknown')}\n"
            f"Description: {story.get('description', 'No description')}\n"
            f"Genre: {story.get('genre', 'N/A')}\n"
        )
    }
    
    characters = story.get("characters", {})
    if isinstance(characters, list):
        char_dict = {}
        for char in characters:
            if isinstance(char, dict) and 'name' in char:
                char_dict[char['name']] = char
        characters = char_dict
    
    character_details = "Story Characters:\n"
    for char_name, char in characters.items():
        if isinstance(char, dict):
            details = f"{char.get('name', 'Unknown')} (Race: {char.get('race', 'Unknown')}, Class: {char.get('class', 'Unknown')})\n"
            details += f"Backstory: {char.get('backstory', 'No backstory')}\n"
            advanced_info = []
            for key in char:
                if key not in ['name', 'race', 'class', 'backstory']:
                    advanced_info.append(f"{key}: {char[key]}")
            if advanced_info:
                details += "Advanced: " + ", ".join(advanced_info) + "\n"
            character_details += details
    
    character_prompt = {
        "role": "system",
        "content": character_details
    }
    
    if llm_memory:
        if len(llm_memory) >= 3:
            llm_memory[0] = initial_prompt
            llm_memory[1] = story_details_prompt
            llm_memory[2] = character_prompt
            llm_conversations[story_name] = llm_memory.copy()
        else:
            llm_conversations[story_name] = [initial_prompt, story_details_prompt, character_prompt]
            if len(llm_memory) > 0:
                llm_conversations[story_name].extend(llm_memory)
    else:
        llm_conversations[story_name] = [initial_prompt, story_details_prompt, character_prompt]
    

    display_conversation = transform_conversation_for_display(full_conversation)
    
    return jsonify({
        'story': story,
        'conversation': display_conversation
    })

@app.route('/create_character', methods=['POST'])
def create_character():
    data = request.get_json()
    new_character_name = data.get('name', '').strip()
    new_character_race = data.get('race', '').strip()
    new_character_class = data.get('class', '').strip()
    new_character_backstory = data.get('backstory', '').strip()

    if not new_character_name or not new_character_race or not new_character_class:
        return jsonify({'error': 'Character name, race, and class are required.'}), 400

    character_data = {
        'name': new_character_name,
        'race': new_character_race,
        'class': new_character_class,
        'backstory': new_character_backstory,
    }

    advanced_keys = [
        "ability_scores", "skills", "proficiencies", "equipment",
        "spells", "class_features", "background", "alignment",
        "level", "experience"
    ]
    for key in advanced_keys:
        if key in data:
            character_data[key] = data[key]

    existing_character = character_creation_table.search(StoryQuery.name == new_character_name)
    if existing_character:
        return jsonify({'error': f"A character with the name '{new_character_name}' already exists."}), 400

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

    payload_characters = data.get('characters', {})

    stored_characters = story.get('characters', {})
    

    if isinstance(stored_characters, list):
        char_dict = {}
        for char in stored_characters:
            if isinstance(char, dict) and 'name' in char:
                char_dict[char['name']] = char
        stored_characters = char_dict

    merged_characters = {}

    for char_name, char_payload in payload_characters.items():
        if char_name in stored_characters:
            merged_characters[char_name] = stored_characters[char_name]
        else:
            char = character_creation_table.get(StoryQuery.name == char_name)
            if char:
                char_copy = char.copy()
                char_copy['template_origin'] = char_name
                merged_characters[char_name] = char_copy
            else:
                merged_characters[char_name] = char_payload

    updated_data = {
        'name': data.get('name', story['name']),
        'description': data.get('description', story['description']),
        'genre': data.get('genre', story['genre']),
        'mode': data.get('mode', story['mode']),
        'characters': merged_characters,
        'conversation_history': story.get('conversation_history', []),
        'llm_memory': story.get('llm_memory', []),
        'current_summary': story.get('current_summary', '')
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
        'backstory': data.get('backstory', character.get('backstory', '')),
    }

    advanced_keys = [
        "ability_scores", "skills", "proficiencies", "equipment",
        "spells", "class_features", "background", "alignment",
        "level", "experience"
    ]
    for key in advanced_keys:
        if key in data:
            updated_data[key] = data[key]

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
    all_models_response = ollama.list()
    models = getattr(all_models_response, 'models', None)
    if models is None or not isinstance(models, list) or len(models) == 0:
        return jsonify({'error': 'No models found.'}), 500

    model_names = [getattr(m, 'model', None) for m in models if getattr(m, 'model', None)]
    global current_model
    if current_model not in model_names:
        current_model = model_names[0]
        print(f"DEBUG: current_model not found; updated to {current_model}")

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


@app.route('/update_settings', methods=['POST'])
def update_settings():
    global model_accuracy_threshold, current_context_size
    data = request.get_json()
    new_accuracy = data.get('model_accuracy')
    new_context = data.get('context_size')
    if new_accuracy is not None:
        try:
            new_accuracy = int(new_accuracy)
            if new_accuracy < 3:
                return jsonify({'error': 'Model accuracy must be at least 3.'}), 400
            model_accuracy_threshold = new_accuracy
        except ValueError:
            return jsonify({'error': 'Invalid model accuracy value.'}), 400
    if new_context is not None:
        try:
            new_context = int(new_context)
            current_context_size = new_context
        except ValueError:
            return jsonify({'error': 'Invalid context size value.'}), 400
    return jsonify({
        'message': 'Settings updated successfully.',
        'model_accuracy': model_accuracy_threshold,
        'context_size': current_context_size
    })

if __name__ == "__main__":
    app.run(debug=True)