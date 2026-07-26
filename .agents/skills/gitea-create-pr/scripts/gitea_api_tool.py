#!/usr/bin/env python3
import os
import sys
import subprocess
import urllib.parse
import urllib.request
import json

def run_git_cmd(args):
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}\nStderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def get_git_remote_info():
    # Retrieve the remote origin URL
    remote_url = run_git_cmd(["remote", "get-url", "origin"])
    
    # Parse the remote URL
    # Support formats:
    # https://git.psi-mt.de/SP/sp-prod.git
    # git@git.psi-mt.de:SP/sp-prod.git
    if remote_url.startswith("git@"):
        # ssh format
        parts = remote_url.split(":")
        host = parts[0].split("@")[1]
        path = parts[1].replace(".git", "")
    else:
        # http/https format
        parsed = urllib.parse.urlparse(remote_url)
        host = parsed.hostname
        path = parsed.path.lstrip("/").replace(".git", "")
        
    path_parts = path.split("/")
    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = "/".join(path_parts[1:])
    else:
        owner = None
        repo = None
        
    return host, owner, repo

def extract_credentials(target_host):
    credentials_file = "/home/node-user/.gemini/.git-credentials"
    if not os.path.exists(credentials_file):
        print(f"Error: Git credentials file not found at {credentials_file}", file=sys.stderr)
        sys.exit(1)
        
    with open(credentials_file, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                parsed = urllib.parse.urlparse(line_str)
                # Matches if the hostname is identical or is a suffix of target_host
                if parsed.hostname == target_host:
                    return parsed.username, parsed.password
            except Exception:
                continue
                
    print(f"Error: No credentials found for host {target_host} in {credentials_file}", file=sys.stderr)
    sys.exit(1)

def create_pull_request(host, owner, repo, token, base, head, title, description):
    import ssl
    ssl_context = ssl._create_unverified_context()
    
    api_url = f"https://{host}/api/v1/repos/{owner}/{repo}/pulls"
    
    payload = {
        "base": base,
        "head": head,
        "title": title,
        "body": description
    }
    
    req_data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        api_url,
        data=req_data,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "accept": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            pr_url = res_data.get("html_url")
            pr_number = res_data.get("number")
            print(f"SUCCESS: Pull Request #{pr_number} created successfully!")
            print(f"PR_URL: {pr_url}")
            sys.exit(0)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"Error: Gitea API request failed with status {e.code}", file=sys.stderr)
        try:
            err_json = json.loads(err_msg)
            print(f"Message: {err_json.get('message', err_msg)}", file=sys.stderr)
        except Exception:
            print(f"Message: {err_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error connecting to Gitea API: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 5:
        print("Usage: gitea_api_tool.py <base_branch> <head_branch> <title> <description>", file=sys.stderr)
        sys.exit(1)
        
    base = sys.argv[1]
    head = sys.argv[2]
    title = sys.argv[3]
    description = sys.argv[4]
    
    host, owner, repo = get_git_remote_info()
    if not host or not owner or not repo:
        print(f"Error: Could not resolve repository ownership or structure from remote URL.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Detected repository: {owner}/{repo} on host {host}")
    
    username, token = extract_credentials(host)
    print(f"Extracted credentials for user: {username}")
    
    print(f"Creating Pull Request from '{head}' into '{base}'...")
    create_pull_request(host, owner, repo, token, base, head, title, description)

if __name__ == "__main__":
    main()
