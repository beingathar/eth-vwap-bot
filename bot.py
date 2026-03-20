import requests
import os
import sys
from datetime import datetime, timezone

# Load Secrets from GitHub Environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

SYMBOL = 'ETHUSD'
TIMEFRAME = '5m'
ALERT_THRESHOLD = 5.0
BASE_URL = "https://api.india.delta.exchange/v2"

def get_vwap_data():
    now = datetime.now(timezone.utc)
    start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    params = {
        'symbol': SYMBOL, 'resolution': TIMEFRAME,
        'start': int(start_of_day.timestamp()), 'end': int(now.timestamp())
    }
    
    try:
        # Get Price
        t_resp = requests.get(f"{BASE_URL}/tickers", timeout=10).json()
        price = next((float(t['mark_price']) for t in t_resp.get('result', []) if t.get('symbol') == SYMBOL), None)
        
        # Get VWAP
        h_resp = requests.get(f"{BASE_URL}/history/candles", params=params, timeout=10).json()
        candles = h_resp.get('result', [])
        
        if not candles or not price: return None, None
        
        cv, cpv = 0, 0
        for c in candles:
            h, l, cl, v = float(c['high']), float(c['low']), float(c['close']), float(c['volume'])
            cpv += ((h + l + cl) / 3) * v
            cv += v
        return price, (cpv / cv if cv > 0 else None)
    except: return None, None

def run_check():
    price, vwap = get_vwap_data()
    if price and vwap:
        diff = abs(price - vwap)
        print(f"Price: {price} | VWAP: {vwap} | Gap: {diff}")
        
        if diff <= ALERT_THRESHOLD:
            msg = f"🚨 ETH VWAP ALERT\nPrice: ${price:.2f}\nVWAP: ${vwap:.2f}\nGap: ${diff:.2f}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
            print("Alert Sent!")

if __name__ == "__main__":
    run_check()
