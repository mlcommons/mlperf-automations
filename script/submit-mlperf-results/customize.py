import requests
from mlc import utils
import os
import json


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    meta = i['meta']
    automation = i['automation']
    logger = automation.logger
    server = env['MLC_MLPERF_SUBMISSION_URL']
    benchmark = env['MLC_MLPERF_BENCHMARK']
    submitter_id = env['MLC_MLPERF_SUBMITTER_ID']
    file_path = env['MLC_MLPERF_SUBMISSION_FILE']
    submitter_name = env.get('MLC_MLPERF_SUBMITTER', '')

    # check the file_path is absolute or relative
    # if it is relative, convert to absolute
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(
            os.path.join(
                env['MLC_TMP_CURRENT_PATH'],
                file_path))

    r = get_signed_url(
        server,
        benchmark,
        submitter_id,
        submitter_name,
        file_path)
    if r['return'] > 0:
        return r

    signed_url = r['signed_url']
    submission_id = r['submission_id']

    r = upload_file_to_signed_url(file_path, signed_url, logger)
    if r['return'] > 0:
        return r

    r = trigger_submission_checker(
        server, submitter_id, benchmark, submission_id, logger)
    if r['return'] > 0:
        return r

    return {'return': 0}


def get_signed_url(server, benchmark, submitter_id, submitter_name, file_path):
    # Define the URL
    url = f"{server}/index/url"

    # Define the headers
    headers = {
        "Content-Type": "application/json"
    }

    # Define the payload
    payload = {
        "submitter_id": submitter_id,
        "benchmark": benchmark,
        "filename": file_path
    }

    try:
        # Make the POST request
        response = requests.post(url, json=payload, headers=headers)

        # Check the response status
        if response.status_code == 200:
            # print("Request successful!")
            # print("Response:", response.json())
            pass
        else:
            return {"return": 1,
                    "error": f"HTTP status code: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"return": 1,
                "error": f"An error occurred in connecting to the server: {e}"}

    response_json = response.json()
    try:
        signed_url = response_json['signed_url']
        submission_id = response_json['submission_id']
        submitter_name_from_id = response_json['submitter_name']
    except Exception as e:
        return {
            "return": 1, "error": f"An error occurred while processing the response: {e}"}

    if submitter_name != '':
        if submitter_name != submitter_name_from_id:
            return {'return': 1, 'error': f"""Submitter name mismatch, given = {submitter_name}, name mapped to ID = {submitter_name_from_id}"""}

    return {'return': 0, 'signed_url': signed_url,
            'submission_id': submission_id}


def upload_file_to_signed_url(file_path, signed_url, logger):
    """
    Uploads a file to a signed URL using HTTP PUT.

    Parameters:
        file_path (str): The path to the file you want to upload.
        signed_url (str): The pre-signed URL for uploading the file.

    Returns:
        dict: A dictionary with 'status_code' and 'response' keys.
    """
    headers = {
        'Content-Type': 'application/octet-stream',
        'Access-Control-Allow-Headers': '*'
    }

    try:
        # Open the file in binary mode
        with open(file_path, 'rb') as file:
            response = requests.put(
                signed_url,
                data=file,
                headers=headers
            )

        if response.status_code in [200, 201, 204]:
            logger.info("File uploaded successfully!")
            return {
                'return': 0
            }
        else:
            print(
                f"Failed to upload file. Status code: {response.status_code}")
            logger.info("Response:", response.text)

            return {
                'return': response.status_code,
                'error': response.text
            }

    except FileNotFoundError:
        logger.error("Error: File not found.")
        return {
            'return': 400,
            'error': f'''File {file_path} not found'''
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {
            'return': 500,
            'error': str(e)
        }


def trigger_submission_checker(
        server_url, submitter_id, benchmark, submission_id, logger):
    """
    Sends a POST request with URL-encoded form data.

    Parameters:
        server_url (str): The server endpoint URL (e.g., https://example.com/index).
        submitter_id (str): The ID of the submitter.
        benchmark (str): The benchmark identifier.
        submission_id (str): The submission ID.

    Returns:
        dict: A dictionary containing status code and response content.
    """
    url = f"{server_url}/index"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "submitter_id": submitter_id,
        "benchmark": benchmark,
        "submission_id": submission_id
    }

    try:
        # Make the POST request with URL-encoded data
        response = requests.post(url, data=payload, headers=headers)

        if response.ok:
            logger.info("Submission Check Request successful!")
            pass
        else:
            logger.error(
                f"Submission Check Request failed with status code: {response.status_code}")
            logger.error("Response:", response.text)

        return {
            "return": 0,
            "response": response.text
        }

    except requests.exceptions.RequestException as e:
        logger.error("An error occurred:", e)
        return {
            "return": 500,
            "error": str(e)
        }
