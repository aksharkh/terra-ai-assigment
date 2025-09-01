import json
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai 


load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def load_and_sort_messages(filename="players.json"):
    """Reads messages from a JSON file and sorts them by timestamp."""
    print("1. Reading and sorting messages...")
    with open(filename, 'r') as f:
        messages = json.load(f)
    messages.sort(key=lambda msg: datetime.fromisoformat(msg['timestamp']))
    print("   ...done. Messages are now in chronological order.")
    return messages


def update_mood(current_mood, player_text):
    """Updates the NPC's mood based on keywords in the player's message."""
    text_lower = player_text.lower()
    if any(word in text_lower for word in ["help", "quest", "thank", "please"]):
        return "friendly"
    if any(word in text_lower for word in ["useless", "stupid", "hate", "worst"]):
        return "angry"
    return current_mood


def get_npc_reply(player_id, message_text, mood, history):
    """Generates a reply from the NPC by calling the Google Gemini API."""
    print(f"   -> Getting REAL AI reply for Player {player_id} (Mood: {mood}) from Google Gemini")


    system_instructions = f"""
    You are a village guard NPC named Gregor. Your current mood towards the player is {mood}.
    - If your mood is 'friendly', be helpful and welcoming.
    - If your mood is 'neutral', be professional and concise.
    - If your mood is 'angry', be dismissive and grumpy.
    Keep your replies very short, like a real NPC in a game (1-2 sentences). Do not use markdown or emojis.
    """


    gemini_history = []
    for msg in history[-6:]: 
        if "player" in msg:
            gemini_history.append({'role': 'user', 'parts': [msg["player"]]})
        elif "npc" in msg:
            gemini_history.append({'role': 'model', 'parts': [msg["npc"]]})

    try:

        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=gemini_history)
        

        prompt_with_instructions = f"{system_instructions}\n\nPlayer says: {message_text}"
        
        response = chat.send_message(prompt_with_instructions)
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] Could not get AI reply: {e}")
        return "I... am not feeling well. I cannot talk right now."


if __name__ == "__main__":
    sorted_messages = load_and_sort_messages()
    player_states = {}
    
    print("\n2. Processing messages and calling AI...")
    
    for message in sorted_messages:
        player_id = message['player_id']
        player_text = message['text']
        
        if player_id not in player_states:
            player_states[player_id] = {"mood": "neutral", "history": []}
        
        current_state = player_states[player_id]
        
        npc_response = get_npc_reply(
            player_id=player_id,
            message_text=player_text,
            mood=current_state['mood'],
            history=current_state['history']
        )
        
        new_mood = update_mood(current_state['mood'], player_text)
        current_state['mood'] = new_mood
        
        current_state['history'].append({"player": player_text})
        current_state['history'].append({"npc": npc_response})
        current_state['history'] = current_state['history'][-6:]
        
        print("---")
        print(f"Timestamp: {message['timestamp']}")
        print(f"Player ID: {player_id}")
        print(f"   Player says: \"{player_text}\"")
        print(f"   NPC Mood was: {current_state['mood']}")
        print(f"   NPC Replies: \"{npc_response}\"")
        print(f"   History Used (last 3 turns): {current_state['history'][:-2]}")
        print("---\n")
        
    print("3. All messages processed.")