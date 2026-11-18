import hmac, hashlib, json, time, random, string, requests, sys, os

HKey = '2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3'
AKey = HKey.encode()
MSDK_UA = "GarenaMSDK/4.0.42(NX809J ;Android 9;en;US;app 1.132.9 2024010012;)"

def generate_clean_password(length=18):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

def GenSig(payload):
    return hmac.new(AKey, payload.encode(), hashlib.sha256).hexdigest()

def create_single_guest():
    pwd = generate_clean_password(18)
    url = 'https://100067.connect.garena.com/api/v2/oauth/guest:register'
    data = {'app_id': 100067, 'client_type': 2, 'password': pwd, 'source': 2}
    text = json.dumps(data, separators=(',', ':'))
    sig = GenSig(text)
    hdr = {
        'User-Agent': MSDK_UA,
        'Authorization': f"Signature {sig}",
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': '100067.connect.garena.com',
        'Connection': 'Keep-Alive'
    }
    r = requests.post(url, headers=hdr, data=text, timeout=12)
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
    elif r.status_code == 429:
        time.sleep(2.0)
    return None

def main():
    node_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    target_count = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    print(f"=== [DATASET-MINER] Node #{node_id} Started. Target: {target_count} records ===")
    accounts = []
    t0 = time.time()
    
    attempts = 0
    while len(accounts) < target_count and attempts < target_count * 3:
        attempts += 1
        acc = create_single_guest()
        if acc:
            accounts.append(acc)
            if len(accounts) % 50 == 0:
                rate = round(len(accounts) / max(1, (time.time() - t0)), 2)
                print(f"[DATASET-MINER] Node #{node_id}: {len(accounts)}/{target_count} generated ({rate} acc/s)")
        time.sleep(0.8) # Jitter to avoid rate limit
        
    out_file = f"accounts_chunk_node_{node_id}.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2)
        
    print(f"=== [DATASET-MINER] Node #{node_id} Complete. Saved {len(accounts)} accounts to {out_file} ===")

if __name__ == "__main__":
    main()
