#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.parse
import ssl
import base64

def main():
    config_path = "/home/node-user/.gemini/tmp/jarvis-2/memory/jira_config.json"
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
        
    with open(config_path, "r") as f:
        try:
            config = json.load(f)
        except Exception as json_err:
            print(f"Error parsing JSON from {config_path}: {json_err}")
            sys.exit(1)
        
    jira_url = config.get("jira_url")
    cookie = config.get("cookie")
    jira_user = config.get("jira_user")
    jira_token = config.get("jira_token")
    
    if not jira_url or jira_url.startswith("https://TUTAJ_LINK_DO_JIRY"):
        print("Error: Please set your actual Jira URL (e.g. https://psi.atlassian.net) in jira_config.json")
        sys.exit(1)
        
    # Standardize URL
    if not jira_url.startswith("http"):
        jira_url = "https://" + jira_url
        
    # We will query rest/api/2/myself to verify authentication
    api_url = urllib.parse.urljoin(jira_url, "/rest/api/2/myself")
    req = urllib.request.Request(api_url)
    req.add_header("accept", "application/json")
    
    using_cookie = False
    if cookie and cookie != "TUTAJ_WKLEJ_CAŁY_NAGŁÓWEK_COOKIE_JEŚLI_API_TOKEN_JEST_ZABLOKOWANY":
        # Use Cookie header directly
        req.add_header("Cookie", cookie)
        using_cookie = True
        print(f"Connecting to Jira at: {jira_url} using raw Browser Cookie header...")
    elif jira_user and jira_token and jira_token != "TUTAJ_API_TOKEN_JEŚLI_MASZ":
        # Use Basic auth (user + token)
        auth_str = f"{jira_user}:{jira_token}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        req.add_header("Authorization", f"Basic {b64_auth}")
        print(f"Connecting to Jira at: {jira_url} using API Token (Basic Auth)...")
    else:
        print("Error: No authentication method configured in jira_config.json.")
        print("Please configure either ('jira_user' and 'jira_token') OR the raw browser 'cookie'.")
        sys.exit(1)
        
    # Disable SSL verification due to self-signed enterprise certificates
    ssl_context = ssl._create_unverified_context()
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            user_data = json.loads(response.read().decode("utf-8"))
            print("\n✅ SUCCESS! Authenticated to Jira successfully!")
            print(f"User Display Name : {user_data.get('displayName')}")
            print(f"Email Address     : {user_data.get('emailAddress')}")
            print(f"Active Status     : {user_data.get('active')}")
            sys.exit(0)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"\n❌ Error: Jira API request failed with status {e.code}", file=sys.stderr)
        print(f"Message: {err_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error connecting to Jira API: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
