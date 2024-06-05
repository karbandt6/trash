import requests
import random
import time
import threading
import logging

# Konfigurasi logger
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levellevel)s - %(message)s')

TELEGRAM_BOT_TOKEN = '7428190461:AAGtodGBdWJpbPVDwCc8ojkhmLdw5OOzEl0'
TELEGRAM_CHAT_ID = '5113903601'

def send_telegram_message(message):
    # Kirim pesan ke Telegram
    logging.info(f'Sending message: {message}')
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        logging.error('Failed to send message to Telegram!')

def read_tokens(file_path):
    # Baca token dari file
    logging.info(f'Reading tokens from file: {file_path}')
    response = requests.get(file_path)
    if response.status_code == 200:
        tokens = response.text.splitlines()
        return tokens
    else:
        logging.error("Failed to fetch account list from GitHub Raw.")
        return []

TOKENS_FILE = 'https://raw.githubusercontent.com/karbandt6/inery-testnet-faucet-tasks/main/jdijejixjwiejd.txt'
tokens = read_tokens(TOKENS_FILE)

BASE_URL = 'https://api.hamsterkombat.io/clicker'
TAP_URL = f'{BASE_URL}/tap'
SYNC_URL = f'{BASE_URL}/sync'
BUY_BOOST_URL = f'{BASE_URL}/buy-boost'
CHECK_TASK_URL = f'{BASE_URL}/check-task'

total_taps = 0  # Variable to track total taps
finished_event = threading.Event()  # Event to signal that all threads are finished

def generate_headers(token):
    # Generate headers for API requests
    return {
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Host': 'api.hamsterkombat.io',
        'Origin': 'https://hamsterkombat.io',
        'Referer': 'https://hamsterkombat.io/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/125.0.0.0 Safari/537.36',
        'accept': 'application/json',
        'authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

def buy_boost(boost_id, headers, account_number):
    # Buy boost for a specific account
    payload = {
        "boostId": boost_id,
        "timestamp": int(time.time())
    }
    response = requests.post(BUY_BOOST_URL, headers=headers, json=payload)
    if response.status_code == 200:
        logging.info(f'Account number: {account_number} - Request to buy boost: {boost_id}, response: {response.status_code}')
    else:
        logging.error(f'Account number: {account_number} - Failed to buy boost: {boost_id}, response: {response.status_code}, message: {response.text}')

def daily_check(headers, account_number):
    # Perform daily task check for a specific account
    payload = {
        "taskId": "streak_days",
    }
    response = requests.post(CHECK_TASK_URL, headers=headers, json=payload)
    logging.info(f'Account number: {account_number} - Request for daily reward, response: {response.status_code}')

def process_taps_for_token(token, account_number):
    global total_taps  # Access the global variable
    # Process taps for a specific token
    headers = generate_headers(token)
    response = requests.post(SYNC_URL, headers=headers)
    info = response.json()
    user = info.get("clickerUser")
    available_taps = int(user.get("availableTaps"))
    passive_sec = user.get("earnPassivePerSec")
    passive_hour = user.get("earnPassivePerHour")

    if available_taps > 500:
        available_taps = random.randint(200, 500)

    payload = {
        "count": available_taps,
        "availableTaps": 0,
        "timestamp": int(time.time())
    }
    response = requests.post(TAP_URL, headers=headers, json=payload)
    json_data = response.json()
    balance = int(json_data.get('clickerUser').get('balanceCoins'))
    logging.info("=" * 5 + f"Account number: {account_number}" + "=" * 5)
    logging.info(f"Balance: {balance} coins | Earn per sec/hour: {int(passive_sec)}/{int(passive_hour)} coins.")
    logging.info(f"Taps sent: {available_taps}")

    if response.status_code == 200:
        total_taps += available_taps  # Update the total taps count
    else:
        logging.warning(f"Warning! Account number: {account_number} - Status code: {response.status_code}! Error message: {response.text}")
    
    if account_number == len(tokens):
        finished_event.set()  # Set the event when all accounts are processed

def process_all_tokens():
    global total_taps
    total_taps = 0  # Reset total taps count
    finished_event.clear()  # Clear the event before starting processing
    # Process all tokens concurrently
    for i, token in enumerate(tokens, start=1):
        threading.Thread(target=process_taps_for_token, args=(token, i)).start()
    finished_event.wait()  # Wait for all threads to finish

def main_loop():
    while True:
        process_all_tokens()
        message = f"Account processing has finished.\nTotal accounts: {len(tokens)}\nTotal taps: {total_taps}\nStarting 10-minute pause."
        send_telegram_message(message)
        logging.info("Waiting for 10 minutes before starting again...")
        for remaining in range(600, 0, -1):  # 10 minutes = 600 seconds
            time.sleep(1)
        logging.info("Back to processing accounts...")

if __name__ == "__main__":
    main_loop()
