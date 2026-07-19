import requests
import yaml
import os
import json


def openai_call(message=None):
    try:
        api_key = os.environ['MLC_OPENAI_API_KEY']
        url = os.environ['MLC_OPENAI_API_URL']
        config_path = os.environ.get('MLC_OPENAI_CONFIG_PATH')

        # Load config if it exists
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as file:
                    data = yaml.safe_load(file)
            except Exception as e:
                return {"error": f"Error reading config file: {str(e)}"}

            if os.environ.get('MLC_OPENAI_CONFIG_MODIFY', '') == 'yes':
                try:
                    data['messages'][1]['content'] = data['messages'][1]['content'].replace(
                        "{{ MESSAGE }}", message or "")
                except Exception as e:
                    return {"error": f"Config format issue: {str(e)}"}
        else:
            system_prompt = os.environ.get(
                'MLC_OPENAI_SYSTEM_PROMPT',
                'You are an AI agent expected to correctly answer the asked question')
            user_prompt = message or os.environ.get(
                'MLC_OPENAI_USER_PROMPT', '')
            data = {
                "model": os.environ.get('MLC_OPENAI_MODEL', 'gpt-4.1'),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']

        with open('tmp-openai-results.json', 'w', encoding='utf-8') as f:
            json.dump({'content': content}, f, ensure_ascii=False, indent=2)

        return {"content": content}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}

    except KeyError as e:
        return {"error": f"Missing key in response: {str(e)}"}

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def main():
    result = openai_call()
    if 'error' in result:
        raise Exception(result['error'])


if __name__ == '__main__':
    main()
