import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# Initialize the app
app = Flask(__name__)
CORS(app) 

# --- CONFIGURATION ---
# 1. The User Access Key (The $9.99 Unlock Code)
# Set this in Render Environment Variables as 'ACCESS_KEY'
ACCESS_KEY = os.environ.get("ACCESS_KEY", "default-key")

# 2. The OpenAI API Key (Your paid key)
# Set this in Render Environment Variables as 'OPENAI_API_KEY'
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

@app.route('/')
def home():
    return "Financial Coach AI Backend is Running."

@app.route('/api/coach', methods=['POST'])
def coach_endpoint():
    # --- 1. SECURITY GATE ---
    # Check for the Authorization header
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing access key"}), 401
    
    # Extract the key
    token = auth_header.split(" ")[1]
    
    # Compare with your Secret Key
    if token != ACCESS_KEY:
        return jsonify({"error": "Invalid Access Key"}), 403

    # --- 2. DATA PREPARATION ---
    data = request.json
    user_msg = data.get('message', '')
    # The frontend sends the entire budget state in this 'context' object
    context = data.get('context', {}) 
    
    # Safety check: Do we actually have an OpenAI Key?
    if not OPENAI_API_KEY:
        return jsonify({"reply": "Error: Server is missing OpenAI API Key configuration."}), 500

    # --- 3. OPENAI CALL ---
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # We explicitly tell the AI how to interpret the JSON data
        system_prompt = f"""
        You are an expert Financial Coach.
        You have access to the user's live financial data in JSON format below.
        
        USER DATA:
        {json.dumps(context)}

        INSTRUCTIONS:
        1. Analyze their Income vs Outflow, specific Debts, and Business expenses (if any).
        2. Answer their specific question based on these numbers.
        3. Be encouraging but realistic.
        4. Keep the answer concise (under 150 words) unless they ask for a detailed plan.
        """

        completion = client.chat.completions.create(
            model="gpt-4o", # Or "gpt-4-turbo" or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        
        ai_reply = completion.choices[0].message.content
        
        return jsonify({
            "reply": ai_reply
        })

    except Exception as e:
        print(f"OpenAI Error: {e}")
        return jsonify({"reply": "I'm having trouble connecting to my brain right now. Please try again in a moment."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
