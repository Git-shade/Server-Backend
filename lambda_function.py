import os
import requests
import zipfile
import shutil
import sys
from GitShade.emerge.main import run 
import yaml
import json
import shared_module
import uuid
from GitShade.utils.constants import LANG_EXT_DICT,IGNORE_DIRECTORIES
from dotenv import load_dotenv
from supabase import create_client, Client
import threading

load_dotenv()


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
database: str = os.environ.get("SUPABASE_DATABASE")
storage_bucket: str = os.environ.get("SUPABASE_STORAGE")
supabase: Client = create_client(url, key)


# This code helps to create the project structure
class File:
    def __init__(self, name, path, type, children=None):
        self.name = name
        self.path = path
        self.type = type
        self.children = children or []
        
    def to_dict(self):
        return {
            'name': self.name,
            'path': self.path,
            'type': self.type,
            'children': [child.to_dict() for child in self.children] if self.children else []
        }
        
def traverse_directory(dir_path):
    result = []
    for file_name in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file_name)
        if os.path.isdir(file_path):
            children = traverse_directory(file_path)
            result.append(File(name=file_name, path=file_path, type='dir', children=children))
        else:
            result.append(File(name=file_name, path=file_path, type='file'))
    return result
    
def print_file_structure(files, indent=0):
    for file in files:
        if file.type == 'dir':
            print_file_structure(file.children, indent + 1)
#Here this ends

def sendMessage(msg, status, task_id):
                
    if(status==200):

        supabase.table(database).update({
            'status': 'COMPLETED'
        }).eq('task_id', task_id).execute()
        
    else:
        supabase.table(database).update({
            'status': 'FAILED',
            'error': msg
        }).eq('task_id', task_id).execute()

        
    return {
                "statusCode": status,
                "headers": {
                    "Access-Control-Allow-Headers" : "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
                },
                "body": msg
            }
        
            
def github2s_worker(event: dict):
    
    task_id = event.get('task_id')
    error = {"error": "error"}
    try:
        print(event)
    
        # Replace these values with your GitHub repository details
        if event.get('owner') == None:
            error["error"] = "OWNER_PARAM_NOT_PROVIDED"
            return sendMessage(error,404, task_id)
        owner = event['owner']
        
        if event.get('repo') == None:
            error["error"] = "REPO_PARAM_NOT_PROVIDED"
            return sendMessage(error,404, task_id)
        repo = event['repo']
        
        root = ""
        if event.get('root') != None:
            root = event['root']
        
        ref = ""
        if event.get('branch') != None:
            ref = event['branch']
            
        ignore_folders = []
        if event.get('ignore_folders') != None:
            ignore_folders = event['ignore_folders']
            
          # or any other branch/tag/commit ref
    
        # URL for the zip file
        repoExistsURL = f"https://api.github.com/repos/{owner}/{repo}"
        langURL = f"https://api.github.com/repos/{owner}/{repo}/languages"
        ZipFileURL = f"https://api.github.com/repos/{owner}/{repo}/zipball/{ref}"
    
        repoExistsResponse = requests.get(repoExistsURL)
        if repoExistsResponse.status_code != 200:
            error["error"] = "UNABLE_TO_FIND_REPO"
            return sendMessage(error,404,task_id)
    
        # Make a GET request to get languages and download the zip file
        # if language is not supported the return error without processing anything
        # else go for parsing
        langResponse = requests.get(langURL)
        if langResponse.status_code != 200:
            error["error"] = "UNABLE_TO_DETECT_LANGUAGE"
            return sendMessage(error,404,task_id)
        
        langNeeded = (next(iter(langResponse.json()))).lower()
        if LANG_EXT_DICT.get(langNeeded) == None:
            error["error"] = "LANGUAGE_NOT_SUPPORTED"
            return sendMessage(error,404,task_id)
        
        response = requests.get(ZipFileURL)
        if response.status_code != 200:
            error["error"] = "FAILED_TO_DOWNLOAD_REPO"
            return sendMessage(error,404,task_id)
    
        allowedExtension = LANG_EXT_DICT[langNeeded]
        if langNeeded == 'python':
            langNeeded = 'py'
        allowedLanguages = [langNeeded]
    

        # Set the temporary directory
        temp_dir = "tmp"
    
        # Create a folder named "random_uuid" in the temporary directory
        folder_name = str(uuid.uuid4())
        shared_module.set_variable(folder_name)
        folder_path = os.path.join(temp_dir, folder_name)
        
        # Check if the folder already exists, if not, create it
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Save the zip file to the newly created folder
        zip_file_path = os.path.join(folder_path, "downloaded_file.zip")
        with open(zip_file_path, "wb") as zip_file:
            zip_file.write(response.content)
    
        # Extract the contents of the zip file
        extracted_folder_path = os.path.join(folder_path, "extracted")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_folder_path)
        
        repositoryName = ''
        extracted_files = os.listdir(extracted_folder_path)
        newRepoName = ''
        for file_name in extracted_files:
            repositoryName = file_name
            newRepoName = '-'.join(file_name.split('-')[:-1])
            os.rename(f'tmp/{folder_name}/extracted/{repositoryName}',f'tmp/{folder_name}/extracted/{newRepoName}')
            repositoryName = newRepoName
    
        source_directory_yaml = f'tmp/{folder_name}/extracted/{repositoryName}/{root}'
        if(root==''):
            source_directory_yaml = f'tmp/{folder_name}/extracted/{repositoryName}'
            
        ignore_directories = []
        if IGNORE_DIRECTORIES.get(langNeeded) != None:
            ignore_directories = IGNORE_DIRECTORIES[langNeeded]
        
        ignore_directories.extend(ignore_folders)
    
        d = {  'project_name':'GitShade',
                'loglevel':'info',
                'analyses': 
                    [{ 
                        'analysis_name':'self-check',
                        'source_directory': source_directory_yaml,
                        'only_permit_languages': allowedLanguages,
                        'only_permit_file_extensions': allowedExtension,
                        'ignore_directories_containing': ignore_directories,
                        'ignore_files_containing': [],
                        'file_scan': ['number_of_methods'],
                        'export': [{ 'directory' : './emerge/export/emerge'}]
                    }]
            }

            
        with open(f'tmp/{folder_name}/extracted/emerge.yaml', 'w') as yaml_file:
            yaml.dump(d, yaml_file, sort_keys=False)
        os.sync()
    
        run()
        nodesPath = 'tmp/initNodes.json'
        edgesPath = 'tmp/initEdges.json'
        infoPath = 'tmp/info.json'
        
        nodes = []
        with open(nodesPath, "r") as file:
            nodes = json.load(file)
        edges = []
        with open(edgesPath, "r") as file:
            edges = json.load(file)
        
        info = {}
        with open(infoPath, "r") as file:
            info = json.load(file)
            
        repo_contents =  traverse_directory(f'tmp/{folder_name}/extracted/{repositoryName}/')
        file_dicts = [file.to_dict() for file in repo_contents]
    
        # extracted_files = os.listdir('/tmp')
        # for file_name in extracted_files:
        #     print(file_name)
        # print(nodes)
        
        
        data = {
            'nodes' : nodes, 
            'edges': edges,
            'projectStructure':file_dicts,
            'info': info,
        }
        
        json_data = json.dumps(data)
        filepath = f'tmp/{task_id}.json'
        storage_bucket_filepath = f'{task_id}.json'
        with open(filepath, 'w') as json_file:
            json_file.write(json_data)

        with open(filepath, 'rb') as f:
            res = supabase.storage.from_(storage_bucket).upload(file=f,path=storage_bucket_filepath)
            print(res)
        


        cleanup_thread = threading.Thread(target=remove_directory_contents,kwargs={'folder_path': 'tmp'})
        cleanup_thread.start()
        
        return sendMessage(data,200,task_id);

        
    except Exception as e:

        error["error"] = "ERROR_OCCURED"
        return sendMessage(error,404,task_id );


def remove_directory_contents(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

export = github2s_worker