import json
import requests
from helpme import save_json, extract_data

class Commit():
    
    def __init__(self , username , project_id , sha):
        self.username = username
        self.project_id = project_id
        self.sha = sha

    def get_commit_stats(self):
        CommitURL = 'https://api.github.com/repos/{}/{}/commits/{}'.format(self.username, self.project_id, self.sha)
        CommitDataFromGithub = requests.get(CommitURL).json()
        commit_block = CommitDataFromGithub.get('commit', {})
        DataNeeded = ['committer', 'message']
        CommitData = extract_data(DataNeeded, commit_block)
        CommitData['sha'] = CommitDataFromGithub.get('sha', self.sha)
        save_json('output_of_commit', CommitData)
        return json.dumps(CommitData, indent=True)


if __name__ == "__main__":
    project = Commit('avikantsrivastava' , '100-days-of-ML-Code' , '339992040d807f1c382c858b53e35ed2699518d9') 
    project.get_commit_stats()
        
        
