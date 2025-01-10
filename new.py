import asyncio
import json
import base64
import uuid
import random
import signal
import websockets
import aiohttp
import datetime
from typing import Optional, Dict, List, Any
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class Logger:
    def __init__(self):
        self.colors = {
            'info': Fore.GREEN,
            'warn': Fore.YELLOW,
            'error': Fore.RED,
            'success': Fore.BLUE,
            'debug': Fore.MAGENTA
        }

    def log(self, level: str, message: str, value: Any = ''):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        color = self.colors.get(level, Fore.WHITE)
        level_tag = f"[ {level.upper()} ]"
        timestamp = f"[ {now} ]"

        formatted_message = (
            f"{Fore.GREEN}[ OpenLedger ]{Style.RESET_ALL} "
            f"{Fore.CYAN}{timestamp}{Style.RESET_ALL} "
            f"{color}{level_tag}{Style.RESET_ALL} "
            f"{message}"
        )

        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
            if level == 'error':
                formatted_value = f" {Fore.RED}{value_str}{Style.RESET_ALL}"
            elif level == 'warn':
                formatted_value = f" {Fore.YELLOW}{value_str}{Style.RESET_ALL}"
            else:
                formatted_value = f" {Fore.GREEN}{value_str}{Style.RESET_ALL}"
        else:
            if level == 'error':
                formatted_value = f" {Fore.RED}{value}{Style.RESET_ALL}"
            elif level == 'warn':
                formatted_value = f" {Fore.YELLOW}{value}{Style.RESET_ALL}"
            else:
                formatted_value = f" {Fore.GREEN}{value}{Style.RESET_ALL}"

        print(f"{formatted_message}{formatted_value}")

    def info(self, message: str, value: Any = ''):
        self.log('info', message, value)

    def warn(self, message: str, value: Any = ''):
        self.log('warn', message, value)

    def error(self, message: str, value: Any = ''):
        self.log('error', message, value)

    def success(self, message: str, value: Any = ''):
        self.log('success', message, value)

    def debug(self, message: str, value: Any = ''):
        self.log('debug', message, value)

logger = Logger()

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A_Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

def read_file(path_file: str) -> List[str]:
    try:
        with open(path_file, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as error:
        logger.error(f"Error reading file: {str(error)}")
        return []

def generate_random_capacity() -> Dict:
    return {
        "AvailableMemory": float(f"{random.uniform(10, 64):.2f}"),
        "AvailableStorage": float(f"{random.uniform(10, 500):.2f}"),
        "AvailableGPU": "",
        "AvailableModels": []
    }

class WebSocketClient:
    def __init__(self, auth_token: str, address: str, proxy: Optional[str], index: int):
        self.url = f"wss://apitn.openledger.xyz/ws/v1/orch?authToken={auth_token}"
        self.proxy = proxy
        self.address = address
        self.index = index
        self.reconnect = True
        self.registered = False
        self.identity = base64.b64encode(address.encode()).decode()
        self.capacity = generate_random_capacity()
        self.id = str(uuid.uuid4())
        
        self.heartbeat = {
            "message": {
                "Worker": {
                    "Identity": self.identity,
                    "ownerAddress": self.address,
                    "type": "LWEXT",
                    "Host": "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc"
                },
                "Capacity": self.capacity
            },
            "msgType": "HEARTBEAT",
            "workerType": "LWEXT",
            "workerID": self.identity
        }

        self.reg_worker_id = {
            "workerID": self.identity,
            "msgType": "REGISTER",
            "workerType": "LWEXT",
            "message": {
                "id": self.id,
                "type": "REGISTER",
                "worker": {
                    "host": "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc",
                    "identity": self.identity,
                    "ownerAddress": self.address,
                    "type": "LWEXT"
                }
            }
        }

    async def handle_job_data(self, message: Dict):
        if message.get("MsgType") == "JOB":
            response = {
                "workerID": self.identity,
                "msgType": "JOB_ASSIGNED",
                "workerType": "LWEXT",
                "message": {
                    "Status": True,
                    "Ref": message.get("UUID"),
                },
            }
            await self.websocket.send(json.dumps(response))

    async def connect(self):
        while self.reconnect:
            try:
                async with websockets.connect(self.url) as websocket:
                    self.websocket = websocket
                    logger.info(f"WebSocket connection established for account {self.index}")

                    if not self.registered:
                        logger.info(f"Trying to register worker ID for account {self.index}...")
                        await websocket.send(json.dumps(self.reg_worker_id))
                        self.registered = True

                    while True:
                        try:
                            message = await websocket.recv()
                            message_data = json.loads(message)
                            logger.info(f"Account {self.index} Received message:", message_data)

                            if message_data.get("MsgType") == "JOB":
                                await self.handle_job_data(message_data)

                            # Send heartbeat every 30 seconds
                            await websocket.send(json.dumps(self.heartbeat))
                            await asyncio.sleep(30)

                        except websockets.exceptions.ConnectionClosed:
                            break

            except Exception as error:
                logger.error(f"WebSocket error for Account {self.index}:", str(error))
                if self.reconnect:
                    logger.warn(f"WebSocket connection closed for Account {self.index}, reconnecting...")
                    await asyncio.sleep(5)
                else:
                    logger.warn(f"WebSocket connection closed for Account {self.index}")
                    break

    def close(self):
        self.reconnect = False

async def generate_token(data: Dict, proxy: Optional[str]) -> Optional[Dict]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'https://apitn.openledger.xyz/api/v1/auth/generate_token',
                json=data,
                headers={**HEADERS, 'Content-Type': 'application/json'},
                proxy=proxy
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('data')
                return None
        except Exception:
            return None

async def get_user_info(token: str, proxy: Optional[str], index: int) -> Optional[Dict]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                'https://rewardstn.openledger.xyz/api/v1/reward_realtime',
                headers={**HEADERS, 'Authorization': f'Bearer {token}'},
                proxy=proxy
            ) as response:
                if response.status == 401:
                    logger.error('Unauthorized, token is invalid or expired')
                    return 'unauthorized'
                
                if response.status == 200:
                    result = await response.json()
                    data = result.get('data', [{}])[0]
                    total_heartbeats = data.get('total_heartbeats', '0')
                    logger.info(f"Account {index} has gained points today:", {"PointsToday": total_heartbeats})
                    return result.get('data')
                return None
        except Exception as error:
            logger.error('Error fetching user info:', str(error))
            return None

async def get_claim_details(token: str, proxy: Optional[str], index: int) -> Optional[Dict]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                'https://rewardstn.openledger.xyz/api/v1/claim_details',
                headers={**HEADERS, 'Authorization': f'Bearer {token}'},
                proxy=proxy
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get('data', {})
                    logger.info(f"Details for Account {index}:", {
                        "tier": data.get('tier'),
                        "dailyPoint": data.get('dailyPoint'),
                        "claimed": data.get('claimed'),
                        "nextClaim": data.get('nextClaim', 'Not Claimed')
                    })
                    return data
                return None
        except Exception as error:
            logger.error('Error fetching claim info:', str(error))
            return None

async def claim_rewards(token: str, proxy: Optional[str], index: int) -> Optional[Dict]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                'https://rewardstn.openledger.xyz/api/v1/claim_reward',
                headers={**HEADERS, 'Authorization': f'Bearer {token}'},
                proxy=proxy
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Daily Rewards Claimed for Account {index}:", result.get('data'))
                    return result.get('data')
                return None
        except Exception as error:
            logger.error('Error claiming daily reward:', str(error))
            return None

async def process_account(address: str, proxy: Optional[str], index: int):
    is_connected = False
    
    while not is_connected:
        try:
            response = await generate_token({'address': address}, proxy)
            while not response or not response.get('token'):
                response = await generate_token({'address': address}, proxy)
                await asyncio.sleep(3)

            token = response['token']
            logger.info(f"login success for Account {index}:", f"{token[:36]}-{token[-24:]}")
            
            logger.info(f"Getting user info and claim details for account {index}...")
            claim_daily = await get_claim_details(token, proxy, index)
            if claim_daily and not claim_daily.get('claimed'):
                logger.info(f"Trying to Claim Daily rewards for Account {index}...")
                await claim_rewards(token, proxy, index)
            
            await get_user_info(token, proxy, index)

            socket = WebSocketClient(token, address, proxy, index)
            await socket.connect()
            is_connected = True

            # Start background tasks for periodic checks
            while True:
                await asyncio.sleep(600)  # Check user info every 10 minutes
                logger.info(f"Fetching total points gained today for account {index}...")
                user = await get_user_info(token, proxy, index)
                
                if user == 'unauthorized':
                    logger.info(f"Unauthorized: Token is invalid or expired for account {index}, reconnecting...")
                    is_connected = False
                    socket.close()
                    break

                await asyncio.sleep(3000)  # Check claim details every hour
                logger.info(f"Checking Daily Rewards for Account {index}...")
                claim_details = await get_claim_details(token, proxy, index)
                
                if claim_details and not claim_details.get('claimed'):
                    logger.info(f"Trying to Claim Daily rewards for Account {index}...")
                    await claim_rewards(token, proxy, index)

        except Exception as error:
            logger.error(f"Failed to start WebSocket client for Account {index}:", str(error))
            is_connected = False
            await asyncio.sleep(3)

async def main():
    # Print banner
    print("""
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
       ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝    

             OPEN LEDGER AUTO SENT HEARTBEAT - BOT                
     📢  Telegram Channel: https://t.me/AirdropInsiderID 
     
        """)

    # Read wallets and proxies
    wallets = read_file("wallets.txt")
    if not wallets:
        logger.error('No wallets found in wallets.txt')
        return

    proxies = read_file("proxy.txt")
    logger.info("Starting Program for all accounts:", len(wallets))

    # Handle SIGINT and SIGTERM
    def signal_handler(signum, frame):
        logger.warn(f"Process received signal {signal.Signals(signum).name}, cleaning up and exiting program...")
        for task in asyncio.all_tasks():
            task.cancel()
        asyncio.get_event_loop().stop()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create tasks for each account
    tasks = []
    for index, address in enumerate(wallets, 1):
        proxy = proxies[index % len(proxies)] if proxies else None
        logger.info(f"Processing Account {index} with proxy: {proxy or 'No proxy'}")
        task = asyncio.create_task(process_account(address, proxy, index))
        tasks.append(task)

    # Wait for all tasks to complete
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.warn("Tasks cancelled, cleaning up...")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        logger.info("Program finished")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warn("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program encountered an error: {str(e)}")