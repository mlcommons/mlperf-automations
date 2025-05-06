import requests
import os
import json
import yaml

import yaml

def extract_prompts(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    full_text = data['contents'][0]['parts'][0]['text']

    # Split at "Question Text:"
    if "Question Text:" not in full_text:
        raise ValueError("Expected 'Question Text:' marker not found.")

    system_prompt, question_part = full_text.split("Question Text:", 1)

    # Trim whitespace
    system_prompt = system_prompt.strip()
    user_prompt = question_part.strip()

    return system_prompt, user_prompt


def gemini_call(message=None):
    try:
        api_key = os.environ['MLC_GEMINI_API_KEY']
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        config_path = os.environ.get('MLC_GEMINI_CONFIG_PATH')
        # Load config if it exists
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as file:
                    data = yaml.safe_load(file)
            except Exception as e:
                return {"error": f"Error reading config file: {str(e)}"}
            
            if os.environ.get('MLC_GEMINI_CONFIG_MODIFY', '') == 'yes':
                try:
                    data['messages'][1]['content'] = data['messages'][1]['content'].replace(
                        "{{ MESSAGE }}", message or "")
                except Exception as e:
                    return {"error": f"Config format issue: {str(e)}"}
        # Load prompts
        system_prompt, user_prompt = extract_prompts(config_path)
        # Combine both in first message
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ]
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()

        content = result['candidates'][0]['content']['parts'][0]['text']

        with open('tmp-gemini-results.json', 'w', encoding='utf-8') as f:
            json.dump({'content': content}, f, ensure_ascii=False, indent=2)

        return {"content": content}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}

    except KeyError as e:
        return {"error": f"Missing key in response: {str(e)}"}

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def main():
    result = gemini_call()
    if 'error' in result:
        raise Exception(result['error'])


if __name__ == '__main__':
    main()
