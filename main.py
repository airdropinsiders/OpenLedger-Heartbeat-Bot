import json
import os
import time
import asyncio
import websockets
import aiohttp
import random
from typing import Dict, List
import logging
from datetime import datetime

# Color and style constants
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")

def log_message(msg_type: str, message: str, color: str = Colors.WHITE):
    timestamp = f"{Colors.CYAN}[{get_timestamp()}]{Colors.END}"
    type_color = {
        'INFO': Colors.BLUE,
        'SUCCESS': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'SYSTEM': Colors.CYAN,
        'HEARTBEAT': Colors.GREEN,
        'WEBSOCKET': Colors.YELLOW
    }.get(msg_type, Colors.WHITE)
    
    msg_type_formatted = f"{type_color}{Colors.BOLD}[{msg_type}]{Colors.END}"
    print(f"{timestamp} {msg_type_formatted} {color}{message}{Colors.END}")

def display_header():
    ascii_art = f"""{Colors.CYAN}
        █████╗ ██╗██████╗ ██████╗ ██████╗  ██████╗ ██████╗ 
       ██╔══██╗██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔══██╗
       ███████║██║██████╔╝██║  ██║██████╔╝██║   ██║██████╔╝
       ██╔══██║██║██╔══██╗██║  ██║██╔══██╗██║   ██║██╔═══╝ 
       ██║  ██║██║██║  ██║██████╔╝██║  ██║╚██████╔╝██║     
       ╚═╝  ╚═╝╚═╝╚═╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     
                                                          
       ██╗███╗   ██╗███████╗██╗██████╗ ███████╗██████╗     
       ██║████╗  ██║██╔════╝██║██╔══██╗██╔════╝██╔══██╗    
       ██║██╔██╗ ██║███████╗██║██║  ██║█████╗  ██████╔╝    
       ██║██║╚██╗██║╚════██║██║██║  ██║██╔══╝  ██╔══██╗    
       ██║██║ ╚████║███████║██║██████╔╝███████╗██║  ██║    
       ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝    {Colors.END}
    """

    separator = f"{Colors.CYAN}{'=' * 60}{Colors.END}"
    version = f"{Colors.YELLOW}v1.0.0{Colors.END}"
    
    header_lines = [
        separator,
        f"{Colors.CYAN}{Colors.BOLD} OpenLedger Auto Send Heartbeat Bot {version}{Colors.END}",
        f"{Colors.BLUE} Join Us : https://t.me/AirdropInsiderID {Colors.END}",
        separator
    ]

    os.system('cls' if os.name == 'nt' else 'clear')
    print(ascii_art)
    print()
    for line in header_lines:
        print(line)
    print()

class OpenLedgerBot:
    def __init__(self):
        self.account_ids = {}
        self.data_assignments = self.load_data_assignments()
        self.tokens = self.load_tokens()
        self.proxies = self.load_proxies()
        self.gpu_list = self.load_gpu_list()
        self.session = None
        self.use_proxy = False
        self.start_time = datetime.now()

    def load_tokens(self) -> List[dict]:
        try:
            with open('account.txt', 'r') as f:
                tokens = [
                    dict(zip(['token', 'workerID', 'id', 'ownerAddress'], line.strip().split(':')))
                    for line in f.readlines()
                ]
            log_message('SUCCESS', f'Successfully loaded {len(tokens)} accounts')
            return tokens
        except Exception as e:
            log_message('ERROR', f'Failed to load accounts: {e}')
            return []

    def load_proxies(self) -> List[str]:
        try:
            with open('proxy.txt', 'r') as f:
                proxies = f.read().strip().split()
            log_message('SUCCESS', f'Successfully loaded {len(proxies)} proxies')
            return proxies
        except Exception as e:
            log_message('ERROR', f'Error reading proxy.txt: {e}')
            return []

    def load_gpu_list(self) -> List[str]:
        try:
            with open('src/gpu.json', 'r') as f:
                gpus = json.load(f)
            log_message('SUCCESS', f'Successfully loaded {len(gpus)} GPUs')
            return gpus
        except Exception as e:
            log_message('ERROR', f'Failed to load GPU list: {e}')
            return []

    def load_data_assignments(self) -> Dict:
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
            log_message('SUCCESS', 'Successfully loaded existing data assignments')
            return data
        except Exception:
            log_message('INFO', 'Initializing new data assignments')
            return {}

    def get_or_assign_resources(self, worker_id: str) -> Dict:
        if worker_id not in self.data_assignments:
            self.data_assignments[worker_id] = {
                'gpu': random.choice(self.gpu_list),
                'storage': f"{random.uniform(0, 500):.2f}"
            }
            with open('data.json', 'w') as f:
                json.dump(self.data_assignments, f, indent=2)
            log_message('INFO', f'Assigned new resources to worker {worker_id}')
        return self.data_assignments[worker_id]

    async def ask_use_proxy(self) -> bool:
        while True:
            response = input(f'{Colors.YELLOW}Do You Want To Use Proxy? (y/n): {Colors.END}').lower()
            if response == 'y':
                log_message('SYSTEM', 'Proxy enabled')
                return True
            elif response == 'n':
                log_message('SYSTEM', 'Proxy disabled')
                return False
            log_message('WARNING', 'Please answer with y or n')

    async def get_account_id(self, token: str, index: int):
        try:
            proxy = self.proxies[index] if self.use_proxy else None
            proxy_text = proxy if self.use_proxy else 'Disabled'
            
            async with self.session.get(
                'https://apitn.openledger.xyz/api/v1/users/me',
                headers={'Authorization': f'Bearer {token}'},
                proxy=proxy if self.use_proxy else None
            ) as response:
                data = await response.json()
                account_id = data['data']['id']
                self.account_ids[token] = account_id
                log_message('SUCCESS', 
                    f"Account #{index + 1} | ID: {Colors.CYAN}{account_id}{Colors.END} | "
                    f"Proxy: {Colors.YELLOW}{proxy_text}{Colors.END}")
                return account_id
        except Exception as e:
            log_message('ERROR', f"Failed to get account ID for index {index}: {str(e)}")
            return None

    def format_number(self, num):
        return f"{num:,.2f}" if isinstance(num, float) else f"{num:,}"

    async def get_account_details(self, token: str, index: int):
        try:
            proxy = self.proxies[index] if self.use_proxy else None
            proxy_text = proxy if self.use_proxy else 'Disabled'
            headers = {'Authorization': f'Bearer {token}'}

            async with self.session.get(
                'https://rewardstn.openledger.xyz/api/v1/reward_realtime',
                headers=headers,
                proxy=proxy if self.use_proxy else None
            ) as response:
                realtime_data = await response.json()

            async with self.session.get(
                'https://rewardstn.openledger.xyz/api/v1/reward_history',
                headers=headers,
                proxy=proxy if self.use_proxy else None
            ) as response:
                history_data = await response.json()

            async with self.session.get(
                'https://rewardstn.openledger.xyz/api/v1/reward',
                headers=headers,
                proxy=proxy if self.use_proxy else None
            ) as response:
                reward_data = await response.json()

            total_heartbeats = int(realtime_data['data'][0]['total_heartbeats'])
            total_points = int(history_data['data'][0]['total_points'])
            total_point_from_reward = float(reward_data['data']['totalPoint'])
            epoch_name = reward_data['data']['name']
            total = total_heartbeats + total_point_from_reward

            log_message('INFO', 
                f"\n{Colors.BOLD}Account #{index + 1} Summary:{Colors.END}\n"
                f"├─ ID: {Colors.CYAN}{self.account_ids[token]}{Colors.END}\n"
                f"├─ Heartbeats: {Colors.GREEN}{self.format_number(total_heartbeats)}{Colors.END}\n"
                f"├─ Total Points: {Colors.GREEN}{self.format_number(total)}{Colors.END}\n"
                f"├─ Epoch: {Colors.YELLOW}{epoch_name}{Colors.END}\n"
                f"└─ Proxy: {Colors.BLUE}{proxy_text}{Colors.END}")

        except Exception as e:
            log_message('ERROR', f"Failed to get account details for index {index}: {str(e)}")

    async def handle_websocket(self, token: str, worker_id: str, id_: str, owner_address: str, index: int):
        ws_url = f"wss://apitn.openledger.xyz/ws/v1/orch?authToken={token}"
        proxy_text = self.proxies[index] if self.use_proxy else 'Disabled'

        while True:
            try:
                async with websockets.connect(ws_url) as websocket:
                    log_message('WEBSOCKET', 
                        f"Connected | Worker: {Colors.YELLOW}{worker_id}{Colors.END} | "
                        f"Account: {Colors.CYAN}{self.account_ids[token]}{Colors.END}")

                    register_message = {
                        "workerID": worker_id,
                        "msgType": "REGISTER",
                        "workerType": "LWEXT",
                        "message": {
                            "id": id_,
                            "type": "REGISTER",
                            "worker": {
                                "host": "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc",
                                "identity": worker_id,
                                "ownerAddress": owner_address,
                                "type": "LWEXT"
                            }
                        }
                    }
                    await websocket.send(json.dumps(register_message))

                    while True:
                        resources = self.get_or_assign_resources(worker_id)
                        heartbeat_message = {
                            "message": {
                                "Worker": {
                                    "Identity": worker_id,
                                    "ownerAddress": owner_address,
                                    "type": "LWEXT",
                                    "Host": "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc"
                                },
                                "Capacity": {
                                    "AvailableMemory": f"{random.uniform(0, 32):.2f}",
                                    "AvailableStorage": resources['storage'],
                                    "AvailableGPU": resources['gpu'],
                                    "AvailableModels": []
                                }
                            },
                            "msgType": "HEARTBEAT",
                            "workerType": "LWEXT",
                            "workerID": worker_id
                        }
                        
                        log_message('HEARTBEAT', 
                            f"Sent | Worker: {Colors.YELLOW}{worker_id}{Colors.END} | "
                            f"Account: {Colors.CYAN}{self.account_ids[token]}{Colors.END}")
                        
                        await websocket.send(json.dumps(heartbeat_message))
                        
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=30)
                            log_message('WEBSOCKET', 
                                f"Message received | Worker: {Colors.YELLOW}{worker_id}{Colors.END} | "
                                f"Response: {Colors.WHITE}{message}{Colors.END}")
                        except asyncio.TimeoutError:
                            pass
                        
                        await asyncio.sleep(30)

            except Exception as e:
                log_message('ERROR', 
                    f"WebSocket error | Worker: {Colors.YELLOW}{worker_id}{Colors.END} | "
                    f"Error: {str(e)}")
                log_message('WEBSOCKET', 
                    f"Reconnecting | Worker: {Colors.YELLOW}{worker_id}{Colors.END} | "
                    f"Account: {Colors.CYAN}{self.account_ids[token]}{Colors.END}")
                await asyncio.sleep(30)

    async def update_account_details_periodically(self):
        while True:
            log_message('SYSTEM', f"{Colors.BOLD}Updating all account details...{Colors.END}")
            tasks = [
                self.get_account_details(token['token'], index)
                for index, token in enumerate(self.tokens)
            ]
            await asyncio.gather(*tasks)
            log_message('SUCCESS', 'Account details updated successfully')
            await asyncio.sleep(5 * 60)

    def display_runtime_stats(self):
        runtime = datetime.now() - self.start_time
        hours, remainder = divmod(runtime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        log_message('SYSTEM', 
            f"\n{Colors.BOLD}Runtime Statistics:{Colors.END}\n"
            f"├─ Uptime: {Colors.GREEN}{hours}h {minutes}m {seconds}s{Colors.END}\n"
            f"├─ Active Accounts: {Colors.CYAN}{len(self.tokens)}{Colors.END}\n"
            f"├─ Active Workers: {Colors.YELLOW}{len(self.account_ids)}{Colors.END}\n"
            f"└─ Proxy Status: {Colors.BLUE}{'Enabled' if self.use_proxy else 'Disabled'}{Colors.END}")

    async def run(self):
        display_header()
        
        if not self.tokens:
            log_message('ERROR', 'No accounts loaded. Please check account.txt file')
            return

        if self.proxies and len(self.proxies) < len(self.tokens):
            log_message('ERROR', 'The number of proxies is less than the number of accounts. Please provide enough proxies.')
            return

        self.use_proxy = await self.ask_use_proxy()
        
        log_message('SYSTEM', f"{Colors.BOLD}Initializing OpenLedger Bot...{Colors.END}")
        
        async with aiohttp.ClientSession() as self.session:
            # Get initial account IDs
            log_message('SYSTEM', 'Getting account IDs...')
            for index, token_data in enumerate(self.tokens):
                await self.get_account_id(token_data['token'], index)

            log_message('SYSTEM', f"{Colors.BOLD}Starting WebSocket connections...{Colors.END}")
            
            # Start WebSocket connections and periodic updates
            websocket_tasks = [
                self.handle_websocket(
                    token_data['token'],
                    token_data['workerID'],
                    token_data['id'],
                    token_data['ownerAddress'],
                    index
                )
                for index, token_data in enumerate(self.tokens)
            ]
            
            # Add stats display task
            async def display_stats_periodically():
                while True:
                    self.display_runtime_stats()
                    await asyncio.sleep(60)  # Update stats every minute

            all_tasks = websocket_tasks + [
                self.update_account_details_periodically(),
                display_stats_periodically()
            ]

            try:
                await asyncio.gather(*all_tasks)
            except KeyboardInterrupt:
                log_message('SYSTEM', f"\n{Colors.BOLD}Shutting down...{Colors.END}")
                self.display_runtime_stats()
                return
            except Exception as e:
                log_message('ERROR', f"Unexpected error: {str(e)}")
                self.display_runtime_stats()
                return

if __name__ == "__main__":
    try:
        bot = OpenLedgerBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        log_message('SYSTEM', f"\n{Colors.BOLD}Bot stopped by user{Colors.END}")
    except Exception as e:
        log_message('ERROR', f"Critical error: {str(e)}")
    finally:
        log_message('SYSTEM', f"{Colors.BOLD}Bot shutdown complete{Colors.END}")