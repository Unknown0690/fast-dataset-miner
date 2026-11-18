#!/usr/bin/env python3
"""
High-throughput distributed dataset generator with rotating proxy pool.
"""
import hmac
import hashlib
import json
import time
import random
import string
import requests
import sys
import os
import urllib.parse
import urllib3

urllib3.disable_warnings()

HKey = '2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3'
AKey = HKey.encode()
MSDK_UA = "GarenaMSDK/4.0.42(NX809J ;Android 9;en;US;app 1.132.9 2024010012;)"

def GenSig(payload):
    return hmac.new(AKey, payload.encode(), hashlib.sha256).hexdigest()

def generate_clean_password(length=18):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

def parse_proxy(raw):
    raw = raw.strip()
    parts = raw.split(":")
    if len(parts) == 4:
        host, port, user, pwd = parts
        safe_u = urllib.parse.quote(user)
        safe_p = urllib.parse.quote(pwd)
        return {"http": f"http://{safe_u}:{safe_p}@{host}:{port}", "https": f"http://{safe_u}:{safe_p}@{host}:{port}"}
    elif len(parts) == 2:
        host, port = parts
        return {"http": f"http://{host}:{port}", "https": f"http://{host}:{port}"}
    return None

def load_proxies():
    p_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxies.json")
    if os.path.exists(p_file):
        with open(p_file, "r") as f:
            raw_list = json.load(f)
            return [parse_proxy(r) for r in raw_list if parse_proxy(r)]
    return []

def create_single_guest(proxy_dict=None):
    pwd = generate_clean_password(18)
    url = 'https://100067.connect.garena.com/api/v2/oauth/guest:register'
    payload = {'app_id': 100067, 'client_type': 2, 'password': pwd, 'source': 2}
    text = json.dumps(payload, separators=(',', ':'))
    sig = GenSig(text)
    hdr = {
        'User-Agent': MSDK_UA,
        'Authorization': f"Signature {sig}",
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': '100067.connect.garena.com',
        'Connection': 'Keep-Alive'
    }
    try:
        r = requests.post(url, headers=hdr, data=text, proxies=proxy_dict, timeout=6, verify=False)
        if r.status_code == 200:
            j = r.json()
            if 'data' in j and 'uid' in j['data']:
                return {
                    'uid': str(j['data']['uid']),
                    'password': pwd,
                    'name': 'VAYZON',
                    'account_id': '',
                    'region': 'NON_ACTIVE',
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
    except Exception:
        pass
    return None

def main():
    node_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    target_count = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    
    proxies = load_proxies()
    print(f"=== [STREAM-MINER] Node #{node_id} Online. Target: {target_count} | Proxies: {len(proxies)} ===")
    
    # Randomize starting proxy index per node to distribute load
    random.seed(int(node_id) * 999 + int(time.time()))
    proxy_idx = random.randint(0, max(0, len(proxies) - 1)) if proxies else 0
    
    accounts = []
    t0 = time.time()
    attempts = 0
    consecutive_fails = 0
    
    while len(accounts) < target_count and attempts < target_count * 5:
        attempts += 1
        p = proxies[proxy_idx % len(proxies)] if proxies else None
        proxy_idx += 1
        
        acc = create_single_guest(p)
        if acc:
            accounts.append(acc)
            consecutive_fails = 0
            if len(accounts) % 25 == 0 or len(accounts) == target_count:
                elapsed = max(1.0, time.time() - t0)
                rate = round(len(accounts) / elapsed, 2)
                eta_s = round((target_count - len(accounts)) / max(0.01, rate))
                print(f"[STREAM-MINER] Node #{node_id}: {len(accounts)}/{target_count} generated ({rate} acc/s, ETA: {eta_s}s)")
            time.sleep(0.1)
        else:
            consecutive_fails += 1
            if consecutive_fails > 10:
                time.sleep(0.5)
            else:
                time.sleep(0.05)
                
    out_file = f"accounts_chunk_node_{node_id}.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2)
        
    print(f"=== [STREAM-MINER] Node #{node_id} Complete. Saved {len(accounts)} accounts to {out_file} in {round(time.time()-t0, 1)}s ===")

if __name__ == "__main__":
    main()
