import requests
import datetime

# --- Configuration ---
with open("input.txt", "r") as f:
    repo_names = [line.strip() for line in f if line.strip()]

days_threshold = 365
auth_token = "mykey"
bb_base_url = "https://bitbucket.mydomain/rest/api/latest/projects/MYPROJECT/repos"  # No trailing slash!
output_file = "stale_branches.txt"

IGNORE_BRANCHES = {"master", "main"}
IGNORE_PREFIXES = {"release/"}

cutoff_timestamp = int((datetime.datetime.now() - datetime.timedelta(days=days_threshold)).timestamp() * 1000)

def is_branch_ignored(branch_name):
    return branch_name in IGNORE_BRANCHES or any(branch_name.startswith(p) for p in IGNORE_PREFIXES)

def get_stale_branches(repo_name):
    url = f"{bb_base_url}/{repo_name}/branches"
    headers = {"Authorization": f"Bearer {auth_token}"}
    params = {
        "limit": 100,
        "details": "true"
    }
    stale_branches = []

    try:
        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Debug: Print API response structure
            print(f"API Response Keys: {data.keys()}")
            if "values" not in data:
                print(f"Unexpected response format: {data}")
                break

            for branch in data["values"]:
                if not isinstance(branch, dict):
                    print(f"Skipping non-dict branch: {branch}")
                    continue

                branch_name = branch.get("displayId", "")
                commit_data = branch.get("latestCommit", {})
                
                if not isinstance(commit_data, dict):
                    commit_data = {}  # Fallback if not a dictionary

                commit_ts = commit_data.get("authorTimestamp", 0)

                if not branch_name or is_branch_ignored(branch_name):
                    continue

                if commit_ts < cutoff_timestamp:
                    last_commit_date = datetime.datetime.fromtimestamp(commit_ts / 1000).strftime('%Y-%m-%d')
                    stale_branches.append((branch_name, last_commit_date))

            if data.get("isLastPage", True):
                break
            params["start"] = data.get("nextPageStart")

    except Exception as e:
        print(f"Error processing {repo_name}: {str(e)}")
    
    return stale_branches

# Main execution
with open(output_file, "w") as f:
    for repo_name in repo_names:
        print(f"\nProcessing {repo_name}...")
        stale_branches = get_stale_branches(repo_name)
        
        f.write(f"{repo_name}:\n")
        for branch_name, last_commit in stale_branches:
            print(f"  - {branch_name} (last commit: {last_commit})")
            f.write(f"  - {branch_name} (last commit: {last_commit})\n")
