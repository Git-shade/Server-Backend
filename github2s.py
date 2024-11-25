import json
import os
import uuid
import requests
from dotenv import load_dotenv
from lambda_function import github2s_worker
from supabase import create_client, Client
import threading
load_dotenv()


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
database: str = os.environ.get("SUPABASE_DATABASE")
storage_bucket: str = os.environ.get("SUPABASE_STORAGE")
supabase: Client = create_client(url, key)

def send_message(msg, status):
    print(msg, status)
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
        },
        "body": msg
    }

def get_latest_commit_hash(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    response = requests.get(url)
    if response.status_code == 200:
        commits = response.json()
        if commits:
            return commits[0]['sha']
    return None

def download_file_from_storage(bucket_key):
    jsonData = {}
    print(bucket_key)
    with open(bucket_key, 'wb+') as f:
        res = supabase.storage.from_(storage_bucket).download(bucket_key)
        f.write(res)

    with open(bucket_key, 'r') as f:
        json_content = f.read()
        jsonData = json.loads(json_content)

    os.remove(bucket_key)
    return jsonData

def github2sCode(event):

    result = {}

    owner = event.get('owner')
    repo = event.get('repo')
    task_id = event.get('task_id')
    branch = event.get('branch')
    ignore_folders = event.get('ignore_folders')

    if task_id:
        ##################################
        get_task_id_result = supabase.table(database).select("*").eq('task_id',task_id).execute()
        ##################################
        detail = get_task_id_result.data
        data = get_task_id_result.data[0]

        if not len(detail):
            result['status'] = 'NOT_FOUND'
            return send_message(result, 404)

        if data.get('status') == 'IN_PROGRESS':
            result['status'] = 'IN_PROGRESS'
            return send_message(result, 200)

        if data.get('status') == 'FAILED':
            result['status'] = 'FAILED'
            result['error'] = detail.get('error', {}).get('error')
            return send_message(result, 404)

        bucket_key = f'{task_id}.json'

        jsonData = download_file_from_storage(bucket_key)
        result['data'] = jsonData
        result['status'] = 'COMPLETED'

        return send_message(result, 200)

    latest_commit_hash = get_latest_commit_hash(owner, repo)
    if latest_commit_hash is None:
        result['status'] = 'FAILED'
        result['error'] = 'Unable to fetch the latest commit hash'
        return send_message(result, 500)

    print(latest_commit_hash, owner, repo)
    # Query db for existing task with matching owner, repo, and commit hash

    responseData = supabase.table(database).select("*").eq('task_id',latest_commit_hash).execute()
    items = responseData.data

    print(items)
    if items and (branch == None and ignore_folders == None):
        print("#######################")
        existing_task = items[0]
        task_id = existing_task['task_id']
        bucket_key = f'{task_id}.json'

        jsonData = download_file_from_storage(bucket_key)
        result['data'] = jsonData
        result['status'] = 'COMPLETED'

        return send_message(result, 200)

    print(latest_commit_hash, owner, repo)
    # Insert initial task details in db
    supabase.table(database).insert(
        {
            "task_id": latest_commit_hash,
            "githubOwner": owner,
            "githubRepo": repo,
            "status": "IN_PROGRESS",
            "lastCommit": latest_commit_hash,
            "error": {},
        }
    ).execute()


    event['task_id'] = latest_commit_hash
    print(event)
    thread = threading.Thread(target=github2s_worker, kwargs={'event': event})
    thread.start()

    result['task_id'] = latest_commit_hash
    result['status'] = 'IN_PROGRESS'

    print(result)
    # Return the task ID to the client
    return send_message(result, 200)

export = github2sCode