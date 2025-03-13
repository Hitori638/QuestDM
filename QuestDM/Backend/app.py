from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import ollama
import re
import json
import traceback
from tinydb import TinyDB, Query
from difflib import SequenceMatcher
import time 


app = Flask(__name__)
CORS(app)
app.debug = True


current_model = "llama3.2-vision:latest"
model_accuracy_threshold = 3     
current_context_size = 4096      

conversations = {} 
llm_conversations = {}  

db = TinyDB('stories.json')
stories_table = db.table('stories')
character_creation_table = db.table('character_creation')
story_creation_table = db.table('story_creation')
StoryQuery = Query()

last_story_summary = ""

def construct_summary_prompt(conversation_text):
    print("DEBUG: Constructing summary prompt with conversation of length:", len(conversation_text))
    return [
        {
            "role": "system",
            "content": (
                "You are an assistant tasked with analyzing the conversation history of a D&D story. "
                "Your job is to generate:\n\n"
                "1. A comprehensive **summary** of the story so far as a simple string\n"
                "2. An **updated character_creation dictionary** containing ANY AND ALL characters\n\n"
                "CRITICAL INSTRUCTIONS FOR JSON OUTPUT:\n"
                "- Output ONLY valid, parseable JSON with NO explanations before or after\n"
                "- Do NOT prefix your response with ```json or any other markdown\n"
                "- Return EXACTLY this structure with NO modifications:\n"
                "{\n"
                '  "summary": "A detailed summary of the story progression.",\n'
                '  "character_creation": {\n'
                '    "CharacterName": {\n'
                '      "name": "CharacterName",\n'
                '      "race": "Race (if known, or \\"Unknown\\" if not)",\n'
                '      "class": "Class (if known, or \\"Unknown\\" if not)",\n'
                '      "backstory": "Character backstory based on available information",\n'
                '      "status": "Current physical/mental state and location"\n'
                "    }\n"
                "  }\n"
                "}\n\n"
                "STRICT FORMAT REQUIREMENTS:\n"
                "- The 'summary' field MUST be a single string with proper escaping for quotes (\\\")\n"
                "- Character names as keys MUST EXACTLY MATCH the corresponding 'name' field values\n"
                "- DO NOT include newlines within strings - use spaces instead\n"
                "- All strings MUST be properly quoted with double quotes and escaped where needed\n"
                "- Every property except the last in each object MUST have a comma after it\n"
                "- DO NOT add any extra fields, comments, or explanations outside the JSON structure\n"
                "- The output should start with a { character and end with a } character\n\n"
                "SPECIAL CHARACTER HANDLING:\n"
                "- Avoid using apostrophes in the summary text (use 'the crews mission' instead of 'crew's mission')\n"
                "- If you must include character nicknames with quotes, use single quotes instead of double quotes\n"
                "- Keep character names simple in the character_creation dictionary keys (e.g., use 'Sam Johnson' instead of 'Dr. Samuel \"Sam\" Johnson')\n"
                "- Use character full names including titles in the 'name' field, not in the dictionary key\n\n"
                "Your output MUST be machine-parseable JSON that can be processed by json.loads() in Python."
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
    """
    Merge character dictionaries with fuzzy name matching.
    
    Args:
        existing_chars (dict): Existing characters dictionary
        new_chars (dict): New characters dictionary to merge
    
    Returns:
        dict: Merged characters dictionary
    """
    if not isinstance(existing_chars, dict):
        existing_chars = {}
    if not isinstance(new_chars, dict):
        new_chars = {}
   
    merged_characters = existing_chars.copy()
   
    for new_char_id, new_char in new_chars.items():
   
        matched = False
        for existing_char_id, existing_char in merged_characters.items():
            if fuzzy_match_name(new_char_id, existing_char_id):
        
                for key, val in new_char.items():
                    if key == 'backstory' and existing_char.get('backstory'):
                        original_backstory = existing_char['backstory']
                        if val != original_backstory and val:
                            merged_characters[existing_char_id]['backstory'] = val
                    elif key == 'status' and val:
                        merged_characters[existing_char_id][key] = val
                    else:
                        merged_characters[existing_char_id][key] = val
                matched = True
                break
        
  
        if not matched:
            merged_characters[new_char_id] = new_char
   
    return merged_characters

def process_summary_json(summary_text):
 
    
    print("\n" + "="*50)
    print("DEBUG: Starting JSON parsing process")
    print(f"DEBUG: Raw summary text preview: {summary_text[:150]}...")
    print(f"DEBUG: Summary text length: {len(summary_text)} characters")
    print("="*50 + "\n")

    default_result = {
        "summary": "Summarization failed, this doesn't happen very often, you are on your own LLM. Continue the story naturally using the limited context you have. When dealing with characters whose background you're uncertain about, use dialogue to reconstruct history - have characters say things like 'Remember what we've been through together?' or 'After all that happened in the forest, I still can't believe we made it out.' This will encourage the player to mention past events in their response, helping you rebuild the narrative context. NPCs can also ask questions like 'How did you solve that problem with the dragon again?' to prompt the player to recount important story elements while maintaining the illusion of continuity.",
        "character_creation": {}
    }
    
    def clean_text(text):
        original_text = text
        
        for prefix in ["SUMMARY:", "Here's the summary:", "JSON:", "Output:"]:
            if text.strip().startswith(prefix):
                text = text[len(prefix):].strip()
                print(f"DEBUG: Removed prefix: '{prefix}'")
        
        if "```" in text:
            text = re.sub(r'```(?:json)?\n?([\s\S]*?)\n?```', r'\1', text)
            print("DEBUG: Removed markdown code blocks")
        
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1:
            text = text[first_brace:last_brace+1]
            print(f"DEBUG: Extracted JSON between braces (chars {first_brace}-{last_brace})")
        
        result = text.strip()
        if result != original_text:
            print(f"DEBUG: Cleaned text preview: {result[:100]}...")
        
        return result

 
    try:
        print("\nDEBUG: ATTEMPTING METHOD 1 - Ask LLM to fix malformed JSON")
        start_time = time.time()
        import ollama
        
    
        cleaned_text = clean_text(summary_text)
        
      
        try:
            data = json.loads(cleaned_text)
            if "summary" in data and "character_creation" in data:
                if isinstance(data["summary"], str) and isinstance(data["character_creation"], dict):
                    print(f"DEBUG: JSON is already valid, no repair needed")
                    print(f"DEBUG: Found summary of length: {len(data['summary'])} chars")
                    print(f"DEBUG: Found {len(data['character_creation'])} characters")
                    if data['character_creation']:
                        print(f"DEBUG: Characters: {', '.join(list(data['character_creation'].keys()))}")
                    end_time = time.time()
                    print(f"DEBUG: Direct parsing succeeded in {end_time-start_time:.3f}s")
                    return data
        except json.JSONDecodeError as json_err:
            print(f"DEBUG: JSON is invalid, attempting repair. Error: {json_err}")
            error_position = json_err.pos
            error_msg = str(json_err)
            surrounding_text = cleaned_text[max(0, error_position-30):min(len(cleaned_text), error_position+30)]
            error_details = (
                f"Error details from Python's json parser:\n"
                f"- Error message: {error_msg}\n"
                f"- Error at position {error_position}\n"
                f"- Surrounding text: '{surrounding_text}'\n"
                f"- The ^ indicates approximately where the error occurred: "
                f"{surrounding_text[:min(30, error_position)]}^{surrounding_text[min(30, error_position):]}\n\n"
            )
        except Exception as e:
            print(f"DEBUG: Error during direct parsing: {str(e)}")
            error_details = f"Error during parsing: {str(e)}\n\n"


        global current_model
        global current_context_size
        
  
        max_attempts = 3
        attempt = 0
        last_error = None
        
        while attempt < max_attempts:
            attempt += 1
            try:
                print(f"DEBUG: LLM repair attempt {attempt}/{max_attempts}")
                
                fix_prompt = [
                    {
                        "role": "system",
                        "content": (
                            "You are a JSON repair specialist. You will be given a malformed JSON string. "
                            "Your task is to fix this JSON and return ONLY the fixed, valid JSON with no explanation or commentary. "
                            "The output must be properly formatted JSON that can be parsed by Python's json.loads() function. "
                            "The JSON should contain:\n"
                            "1. A 'summary' field (string)\n"
                            "2. A 'character_creation' field (object) with character data\n\n"
                            "Here is the expected JSON structure:\n"
                            "{\n"
                            '  "summary": "A detailed summary of the story progression.",\n'
                            '  "character_creation": {\n'
                            '    "CharacterName": {\n'
                            '      "name": "CharacterName",\n'
                            '      "race": "Race (if known, or \\"Unknown\\" if not)",\n'
                            '      "class": "Class (if known, or \\"Unknown\\" if not)",\n'
                            '      "backstory": "Character backstory based on available information",\n'
                            '      "status": "Current physical/mental state and location"\n'
                            "    },\n"
                            '    "AnotherCharacter": {\n'
                            '      "name": "AnotherCharacter",\n'
                            '      "race": "Race",\n'
                            '      "class": "Class",\n'
                            '      "backstory": "Backstory",\n'
                            '      "status": "Status"\n'
                            "    }\n"
                            "  }\n"
                            "}\n\n"
                            "Common issues to look for and fix:\n"
                            "- Unquoted property names\n"
                            "- Single quotes instead of double quotes\n"
                            "- Trailing commas\n"
                            "- Missing commas between properties\n"
                            "- Unclosed brackets/braces\n"
                            "- Unescaped quotes in strings\n"
                            "- Missing quotes around property values\n"
                            "- The 'summary' field MUST be a single string with proper escaping for quotes (\\\")\n"
                            "- Character names as keys MUST EXACTLY MATCH the corresponding 'name' field values\n"
                            "- All strings MUST be properly quoted with double quotes and escaped where needed\n"
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Fix this malformed JSON:\n\n{summary_text}\n\n"
                            f"{error_details if 'error_details' in locals() else ''}"
                            f"This is attempt {attempt} out of {max_attempts}. "
                            "Remember to return ONLY the fixed JSON with no explanations or extra text. "
                            "Ensure the output is valid JSON that can be parsed with json.loads(). "
                            "Make sure all property names and string values use double quotes."
                        )
                    }
                ]
                
       
                if attempt > 1 and last_error:
                    fix_prompt[1]["content"] += f"\n\nPrevious attempt failed with error: {last_error}"
                
                print(f"DEBUG: Sending JSON repair request to model (attempt {attempt})")
                response = ollama.chat(
                    model=current_model,
                    messages=fix_prompt,
                    stream=False,
                    options={"num_ctx": current_context_size}
                )
                
                if hasattr(response, "message"):
                    fixed_json_text = response.message.content
                elif isinstance(response, dict):
                    fixed_json_text = response.get("message", {}).get("content", "")
                else:
                    fixed_json_text = ""
                
                print(f"DEBUG: Received fixed JSON of length: {len(fixed_json_text)} chars")
                print(f"DEBUG: Fixed JSON preview: {fixed_json_text[:100]}...")
                
                cleaned_fixed_json = clean_text(fixed_json_text)
                data = json.loads(cleaned_fixed_json)
                
                if "summary" in data and "character_creation" in data:
                    if isinstance(data["summary"], str) and isinstance(data["character_creation"], dict):
                        end_time = time.time()
                        print(f"DEBUG: Method 1 (LLM fix) SUCCEEDED on attempt {attempt} in {end_time-start_time:.3f}s")
                        print(f"DEBUG: Found summary of length: {len(data['summary'])} chars")
                        print(f"DEBUG: Found {len(data['character_creation'])} characters")
                        if data['character_creation']:
                            print(f"DEBUG: Characters: {', '.join(list(data['character_creation'].keys()))}")
                        return data
                    else:
                        raise ValueError("Invalid data structure from LLM fix (wrong types)")
                else:
                    raise ValueError("Missing required fields in LLM-fixed JSON")
                    
            except json.JSONDecodeError as json_err:
                print(f"DEBUG: Attempt {attempt} - JSON decode error: {json_err}")
                last_error = f"JSON decode error: {json_err}"
                if attempt == max_attempts:
                    print(f"DEBUG: All {max_attempts} LLM repair attempts failed with JSON decode errors")
            except Exception as e:
                print(f"DEBUG: Attempt {attempt} - Error: {str(e)}")
                last_error = str(e)
                if attempt == max_attempts:
                    print(f"DEBUG: All {max_attempts} LLM repair attempts failed")
        
        print(f"DEBUG: Method 1 (LLM fix) exhausted all {max_attempts} attempts")
        
    except Exception as e:
        print(f"DEBUG: Method 1 (LLM fix) overall process failed: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
    

    try:
        print("\nDEBUG: ATTEMPTING METHOD 2 - Regex extraction fallback")
        start_time = time.time()
        result = default_result.copy()
        cleaned_text = clean_text(summary_text)
        
        print("DEBUG: Extracting summary field...")
        summary_pattern = r'"summary"\s*:\s*"((?:\\"|[^"])*)"'
        summary_match = re.search(summary_pattern, cleaned_text, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1)
            
            summary = summary.replace('\\"', '"').replace('\\\\', '\\')
            result["summary"] = summary
            print(f"DEBUG: Successfully extracted summary ({len(summary)} chars)")
        else:

            print("DEBUG: Looking for any summary-like content...")
            summary_lines = re.findall(r'summary.*?["\']([^"\']+)["\']', summary_text, re.IGNORECASE | re.DOTALL)
            if summary_lines:
                result["summary"] = summary_lines[0]
                print(f"DEBUG: Found possible summary: {summary_lines[0][:50]}...")
            else:
 
                fallback_summary = summary_text[:min(200, len(summary_text))]
                if len(summary_text) > 200:
                    fallback_summary += "..."
                result["summary"] = fallback_summary
                print(f"DEBUG: Using fallback summary: {fallback_summary[:50]}...")
        
        print("DEBUG: Extracting character_creation section...")
        char_section_pattern = r'"character_creation"\s*:\s*{([\s\S]*?)}'
        char_section_match = re.search(char_section_pattern, cleaned_text, re.DOTALL)
        
        if char_section_match:
            char_section = char_section_match.group(1)
            print(f"DEBUG: Found character_creation section ({len(char_section)} chars)")
            
            char_pattern = r'"([^"]+)"\s*:\s*{([^{}]*)(?:{[^{}]*}[^{}]*)*?}'
            char_matches = list(re.finditer(char_pattern, char_section))
            print(f"DEBUG: Found {len(char_matches)} potential character entries")
            
            for char_match in char_matches:
                char_name = char_match.group(1).replace('\\', '').strip()
                char_content = char_match.group(2)
                
                print(f"DEBUG: Processing character: {char_name}")
                
                char_data = {
                    "name": char_name,
                    "race": "Unknown",
                    "class": "Unknown",
                    "backstory": "",
                    "status": ""
                }
                
                for field in ["name", "race", "class", "backstory", "status"]:
                    field_pattern = fr'"{field}"\s*:\s*"((?:\\"|[^"])*)"'
                    field_match = re.search(field_pattern, char_content, re.DOTALL)
                    if field_match:
                        value = field_match.group(1).replace('\\"', '"').replace('\\\\', '\\')
                        char_data[field] = value
                        print(f"DEBUG:   - Found {field}: {value[:30]}..." if len(value) > 30 else f"DEBUG:   - Found {field}: {value}")
                
                result["character_creation"][char_name] = char_data
            
            print(f"DEBUG: Successfully extracted {len(result['character_creation'])} characters")
        else:
            print("DEBUG: Could not find character_creation section with regex")
            

            print("DEBUG: Looking for character names in text...")
            char_matches = re.findall(r'(?:name|character)["\'\s:]+([A-Z][a-zA-Z\s]+)', summary_text)
            print(f"DEBUG: Found {len(char_matches)} potential character names")
            
            for char_name in char_matches:
                char_name = char_name.strip()
                if not char_name:
                    continue
                
                print(f"DEBUG: Processing potential character: {char_name}")    
                char_data = {
                    "name": char_name,
                    "race": "Unknown",
                    "class": "Unknown",
                    "backstory": "",
                    "status": ""
                }
                
                char_vicinity = summary_text[max(0, summary_text.find(char_name)-100):
                                          min(len(summary_text), summary_text.find(char_name)+200)]
                
                for field in ["race", "class"]:
                    field_match = re.search(fr'{field}["\'\s:]+([A-Za-z]+)', char_vicinity, re.IGNORECASE)
                    if field_match:
                        char_data[field] = field_match.group(1)
                        print(f"DEBUG:   - Found {field}: {field_match.group(1)}")
                
                result["character_creation"][char_name] = char_data
        
        end_time = time.time()
        print(f"DEBUG: Method 2 (regex extraction) completed in {end_time-start_time:.3f}s")
        print(f"DEBUG: Created summary of length: {len(result['summary'])} chars")
        print(f"DEBUG: Extracted {len(result['character_creation'])} characters")
        if result['character_creation']:
            print(f"DEBUG: Characters: {', '.join(list(result['character_creation'].keys()))}")
        

        return result
    except Exception as e:
        print(f"DEBUG: Method 2 (regex extraction) failed: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
    
 
    print("\nDEBUG: ALL PARSING METHODS FAILED, using raw text fallback")
    default_result["summary"] = summary_text[:min(200, len(summary_text))]
    if len(summary_text) > 200:
        default_result["summary"] += "..."
    
    print("="*50)
    print(f"DEBUG: Returning fallback summary: {default_result['summary'][:50]}...")
    print("DEBUG: No characters extracted")
    print("="*50 + "\n")
    
    return default_result

def summarize_and_save(story_name, threshold=None):
    if threshold is None:
        threshold = model_accuracy_threshold
    
    print(f"DEBUG: Starting summarization check for story '{story_name}'")
    llm_conv = llm_conversations.get(story_name, [])
    

    if len(llm_conv) < 3:
        print("DEBUG: Not enough messages for summarization (< 3)")
        return llm_conv

    has_summary = (
        len(llm_conv) > 3 and
        llm_conv[3]["role"] == "assistant" and
        "SUMMARY:" in llm_conv[3]["content"]
    )
    
    print(f"DEBUG: Has existing summary: {has_summary}")
    
    if has_summary:

        messages_after_summary = llm_conv[4:]
        user_messages_after_summary = [msg for msg in messages_after_summary if msg["role"] == "user"]
        
        print(f"DEBUG: Messages since last summary: {len(messages_after_summary)}")
        print(f"DEBUG: User messages since last summary: {len(user_messages_after_summary)}")
        

        if len(user_messages_after_summary) < threshold:
            print(f"DEBUG: Not enough new messages for re-summarization ({len(user_messages_after_summary)} < {threshold})")
            return llm_conv

        print(f"DEBUG: Threshold reached, re-summarizing {len(user_messages_after_summary)} new user messages")

        existing_summary = llm_conv[3]["content"].replace("SUMMARY:", "", 1).strip()
        

        new_content = "\n\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in messages_after_summary
        )
        

        conversation_text = f"PREVIOUS SUMMARY: {existing_summary}\n\n{new_content}"
    else:
   
        messages_to_summarize = llm_conv[3:]
        user_messages_to_summarize = [msg for msg in messages_to_summarize if msg["role"] == "user"]
        
        print(f"DEBUG: Total non-system messages: {len(messages_to_summarize)}")
        print(f"DEBUG: User messages: {len(user_messages_to_summarize)}")
        

        if len(user_messages_to_summarize) < threshold:
            print(f"DEBUG: Not enough messages for first summarization ({len(user_messages_to_summarize)} < {threshold})")
            return llm_conv
            
  
        print(f"DEBUG: Threshold reached, creating first summary for {len(user_messages_to_summarize)} user messages")
        
   
        conversation_text = "\n\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in messages_to_summarize
        )
    

    print(f"DEBUG: Constructing summary prompt with conversation text of length: {len(conversation_text)}")
    summarization_prompt = construct_summary_prompt(conversation_text)
    
    print(f"DEBUG: Sending summarization request to model: {current_model}")
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
    
    print(f"DEBUG: Received raw summary response of length: {len(new_summary)}")
    

    processed_summary = process_summary_json(new_summary)
    summary_text = processed_summary.get("summary", "")
    
    print(f"DEBUG: Extracted summary text of length: {len(summary_text)}")
    

    summary_message = {"role": "assistant", "content": f"SUMMARY: {summary_text}"}
    

    recent_messages_to_keep = threshold
    

    new_llm_conv = llm_conv[:3] + [summary_message]
    

    if has_summary:
   
        if len(llm_conv) > 4 + recent_messages_to_keep:

            new_llm_conv += llm_conv[-(recent_messages_to_keep):]
            print(f"DEBUG: Keeping {recent_messages_to_keep} most recent messages in the new conversation")
        else:

            new_llm_conv += llm_conv[4:]
            print(f"DEBUG: Keeping all {len(llm_conv) - 4} messages after the existing summary")
    else:

        if len(llm_conv) > 3 + recent_messages_to_keep:
   
            new_llm_conv += llm_conv[-(recent_messages_to_keep):]
            print(f"DEBUG: Keeping {recent_messages_to_keep} most recent messages for first summary")
        else:

            new_llm_conv += llm_conv[3:]
            print(f"DEBUG: Keeping all {len(llm_conv) - 3} messages after system prompts for first summary")
    
    print(f"DEBUG: New conversation structure: {len(new_llm_conv)} messages total")
    print(f"DEBUG: - System prompts: 3 messages")
    print(f"DEBUG: - Summary: 1 message")
    print(f"DEBUG: - Recent messages: {len(new_llm_conv) - 4} messages")
    

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

def fuzzy_match_name(name1, name2, threshold=0.8):


    normalized_name1 = name1.lower().replace(' ', '')
    normalized_name2 = name2.lower().replace(' ', '')
    
    similarity = SequenceMatcher(None, normalized_name1, normalized_name2).ratio()
    
    return similarity >= threshold
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
        print(f"DEBUG: Using existing in-memory conversation for story '{story_name}'")
    else:

        print(f"DEBUG: Loading conversation for story '{story_name}' from database")
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
    

    user_message = {"role": "user", "content": user_input}
    conversations[story_name].append(user_message)
    llm_conversations[story_name].append(user_message)
    

    should_summarize = False
    if len(llm_conversations[story_name]) >= 3:
  
        has_summary = (
            len(llm_conversations[story_name]) > 3 and
            llm_conversations[story_name][3]["role"] == "assistant" and
            "SUMMARY:" in llm_conversations[story_name][3]["content"]
        )
        
        if has_summary:
            messages_after_summary = llm_conversations[story_name][4:]
            user_messages = [msg for msg in messages_after_summary if msg["role"] == "user"]
            should_summarize = len(user_messages) >= model_accuracy_threshold
            
            print(f"DEBUG: Found existing summary sandwich structure")
            print(f"DEBUG: User messages since last summary: {len(user_messages)}/{model_accuracy_threshold}")
        else:

            messages_after_system = llm_conversations[story_name][3:]
            user_messages = [msg for msg in messages_after_system if msg["role"] == "user"]
            should_summarize = len(user_messages) >= model_accuracy_threshold
            
            print(f"DEBUG: No existing summary found")
            print(f"DEBUG: Total user messages: {len(user_messages)}/{model_accuracy_threshold}")
        
        print(f"DEBUG: Should summarize: {should_summarize}")
    

    if should_summarize:
        print("DEBUG: Threshold reached, summarizing before generating response")
        updated_conv = summarize_and_save(story_name)
        
    
        if updated_conv:
            llm_conversations[story_name] = updated_conv
            print(f"DEBUG: Summarization complete, new conversation length: {len(llm_conversations[story_name])}")
            
   
            story_creation_table.update(
                {
                    "llm_memory": llm_conversations[story_name]
                },
                StoryQuery.name == story_name
            )
        else:
            print("DEBUG: Summarization failed or returned empty conversation")
        
        print("DEBUG: Proceeding with response generation")
    
    def generate():
        print("DEBUG: Starting stream for story:", story_name)
        stream = ollama.chat(
            model=current_model,
            messages=llm_conversations[story_name],
            stream=True,
            options={"num_ctx": current_context_size}
        )
        
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
                print("DEBUG: Saving response for story:", story_name)
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