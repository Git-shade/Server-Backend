import os
from dotenv import load_dotenv
from supabase import create_client, Client
load_dotenv()
import json

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
database: str = os.environ.get("SUPABASE_DATABASE")
supabase: Client = create_client(url, key)

try:

    # data = supabase.table(database).select("*").eq('task_id','c403282d-f2e6-46ca-a04a-35d3d873712d').execute()
    # if not len(data.data):
    #     print("Not Found")
    # print(data, data.data[0], len(data.data), data.data[0].get('task_id'))
    # data = supabase.table("github2s").insert(
    #         {
    #         "task_id":"c303282d-f2e6-46ca-a04a-35d3d873712d",
    #         "githubOwner":"Ritik",
    #         "githubRepo":"Ritik",
    #         "status":"IN_PROGRESS",
    #         "lastCommit":"c303282d-f2e6-46ca-a04a-35d3d873712d",
    #         "error":{},
    #         }
    #     ).execute()
    # print(data)

    bucket_name: str = database
    # filepath = "file.json"
    # with open(filepath, 'rb') as f:
    #     data = supabase.storage.from_(bucket_name).upload(file=f,path="c303282d-f2e6-46ca-a04a-35d3d873712d", )
    #     print(data)
    
    # destination = "fileDownload.json"
    # source = "c303282d-f2e6-46ca-a04a-35d3d873712d"
    # with open(destination, 'wb+') as f:
    #     res = supabase.storage.from_(bucket_name).download(source)
    #     f.write(res)
    
    # with open(destination, 'r') as f:
    #     json_content = f.read()
    #     result = {}
    #     result['data'] = json.loads(json_content)
    #     result['status'] = 'COMPLETED'
    #     print(result)
    
    # os.remove(destination)

    data = supabase.table(database).select().eq('task_id','c303282d-f2e6-46ca-a04a-35d3d873712d').execute()
    print(data)
except Exception as e:
    print(e)


print(supabase)
