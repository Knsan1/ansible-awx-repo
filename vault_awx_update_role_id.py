#!/usr/bin/env python3
"""
Script: vault_awx_update.py
Purpose: Retrieve a secret from HashiCorp Vault (via userpass login) 
         and update an AWX credential with that secret.

Usage Example:
  python vault_awx_update.py \
    --cred-name my-credential \
    --key credentials \
    --subkey password

Environment Variables (optional):
  VAULT_ADDR       Vault server URL (e.g. https://vaulturl.com)
  VAULT_SECRET     Vault secret path (e.g. secret/user1)
  VAULT_USERNAME   Vault userpass username
  VAULT_PASSWORD   Vault userpass password (⚠️ optional; if not set, will prompt)
  AWX_URL          AWX API base URL (e.g. https://awxurl.com)
  AWX_CRED_NAME    AWX credential name
"""

import hvac
import requests
import getpass
import sys
import json
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Update AWX credentials with secrets from Vault (userpass login).")
    parser.add_argument("--vault-addr", default=os.getenv("VAULT_ADDR"), help="Vault server URL")
    parser.add_argument("--vault-secret", default=os.getenv("VAULT_SECRET"), help="Vault secret path (e.g. secret/user1)")
    parser.add_argument("--key", default=os.getenv("VAULT_KEY"), help="Top-level key in the Vault secret (e.g. credentials)")
    parser.add_argument("--subkey", default=os.getenv("VAULT_SUBKEY"), help="Nested key under 'key' (e.g. password)")
    parser.add_argument("--awx-url", default=os.getenv("AWX_URL"), help="AWX API base URL")
    parser.add_argument("--cred-name", default=os.getenv("AWX_CRED_NAME"), help="Name of AWX credential to update")
    parser.add_argument("--username", default=os.getenv("VAULT_USERNAME"), help="Vault userpass username (also used for AWX login)")
    parser.add_argument("--password", default=os.getenv("VAULT_PASSWORD"), help="Vault userpass password (⚠️ not recommended in plain env)")
    parser.add_argument("--no-verify-tls", action="store_true", help="Disable TLS verification for Vault/AWX connections")
    return parser.parse_args()

def main():
    args = parse_args()
    verify_tls = not args.no_verify_tls

    # Ensure required parameters
    required = ["vault_addr", "vault_secret", "key", "subkey", "awx_url", "cred_name", "username"]
    for param in required:
        if getattr(args, param) is None:
            print(f"❌ Missing required parameter: {param}. Use --{param.replace('_','-')} or environment variable.")
            sys.exit(1)

    # Prompt password if not supplied
    login_pass = args.password or getpass.getpass(f"Enter Vault userpass password for {args.username}: ")

    # ========== Vault Client ==========
    client = hvac.Client(url=args.vault_addr, verify=verify_tls)
    try:
        client.auth.userpass.login(username=args.username, password=login_pass)
        if not client.is_authenticated():
            print("❌ Vault authentication failed.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Vault auth error: {e}")
        sys.exit(1)

    # ========== Read Vault Secret ==========
    try:
        read_response = client.secrets.kv.v2.read_secret_version(path=args.vault_secret)
        secret_data = read_response["data"]["data"]
        role_id = secret_data.get(args.key, {}).get(args.subkey)
        if not role_id:
            print(f"❌ Failed to retrieve '{args.key}.{args.subkey}' from Vault.")
            sys.exit(1)
        print("✅ Retrieved role_id from Vault")
    except Exception as e:
        print(f"❌ Error reading Vault secret: {e}")
        sys.exit(1)

    # ========== AWX Session ==========
    session = requests.Session()
    session.auth = (args.username, login_pass)  # same creds for AWX
    session.headers.update({"Content-Type": "application/json"})

    # ========== Find Credential ==========
    try:
        response = session.get(f"{args.awx_url}/api/v2/credentials/?name={args.cred_name}", verify=verify_tls)
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            print(f"❌ Credential '{args.cred_name}' not found.")
            sys.exit(1)
        cred_id = results[0]["id"]
        print(f"✅ Found credential '{args.cred_name}' with ID {cred_id}")
    except Exception as e:
        print(f"❌ Error fetching credential: {e}")
        sys.exit(1)

    # ========== Fetch Current Inputs ==========
    cred_url = f"{args.awx_url}/api/v2/credentials/{cred_id}/"
    try:
        cred_response = session.get(cred_url, verify=verify_tls)
        cred_response.raise_for_status()
        current_inputs = cred_response.json().get("inputs", {})
    except Exception as e:
        print(f"❌ Failed to fetch credential details: {e}")
        sys.exit(1)

    # ========== Update role_id ==========
    current_inputs["role_id"] = role_id
    try:
        patch_resp = session.patch(cred_url, json={"inputs": current_inputs}, verify=verify_tls)
        if patch_resp.status_code in (200, 202):
            print(f"✅ Successfully updated 'role_id' for credential '{args.cred_name}' (ID {cred_id})")
        else:
            print(f"❌ Failed to update credential: {patch_resp.status_code} {patch_resp.text}")
    except Exception as e:
        print(f"❌ Error during update: {e}")

if __name__ == "__main__":
    main()
