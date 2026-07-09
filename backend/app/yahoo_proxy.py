import requests
from flask import Blueprint, request, jsonify

yahoo_proxy = Blueprint('yahoo_proxy', __name__)

@yahoo_proxy.route('/api/yahoo-price/<ticker>', methods=['GET'])
def get_yahoo_price(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500