from os import environ
import requests

def create_github_repo():
    headers = {
        'Authorization': f'token {environ["GITHUB_TOKEN"]}',
        'Accept': 'application/vnd.github.v3+json'
    }

    data = {
        'name': 'location-optimizer',
        'description': 'A location optimization system for housing and rental search that ranks potential locations based on proximity to key amenities.',
        'private': False,
        'has_issues': True,
        'has_projects': True,
        'has_wiki': True
    }

    return requests.post('https://api.github.com/user/repos', headers=headers, json=data)

if __name__ == "__main__":
    response = create_github_repo()
    if response.status_code == 201:
        print("SUCCESS")
        print(response.json()['clone_url'])
    else:
        print("ERROR")
        print(response.status_code)
        print(response.json())
