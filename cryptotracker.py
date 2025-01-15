import requests

def get_prices(symbols=None):
    """Get cryptocurrency prices for specified symbols"""
    if symbols is None:
        symbols = ["BTC", "ETH", "XMR", "ERG"]

    try:
        crypto_data = requests.get(
            "https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms=USD".format(",".join(symbols))).json()

        if "RAW" not in crypto_data:
            return {}

        crypto_data = crypto_data["RAW"]
        
        data = {}
        for i in crypto_data:
            data[i] = {
                "coin": i,
                "price": crypto_data[i]["USD"]["PRICE"],
                "change_day": crypto_data[i]["USD"]["CHANGEPCT24HOUR"],
                "change_hour": crypto_data[i]["USD"]["CHANGEPCTHOUR"]
            }

        return data
    except Exception as e:
        print(f"Error fetching crypto data: {str(e)}")
        return {}

if __name__ == "__main__":
    print(get_prices())
