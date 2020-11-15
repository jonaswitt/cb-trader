import cbpro
import dotenv
import os
import sys
import datetime
import pandas as pd
import numpy as np

dotenv.load_dotenv(dotenv_path=".env.local")

client = cbpro.AuthenticatedClient(os.environ["CB_KEY"], os.environ["CB_SECRET"], os.environ["CB_PASSPHRASE"])

curr_fiat = "EUR"
curr_crypto = "BTC"
product_id = "{}-{}".format(curr_crypto, curr_fiat)

# -------------------------
# Print Balances
# -------------------------

balance_fiat = None
balance_crypto = None
for acc in client.get_accounts():
    if balance_fiat is None and acc["currency"] == curr_fiat:
        balance_fiat = float(acc["balance"])
    elif balance_crypto is None and acc["currency"] == curr_crypto:
        balance_crypto = float(acc["balance"])
    if balance_fiat is not None and balance_crypto is not None:
        break

print("Balances:")
print("{}: {:9,.2f}".format(curr_fiat, balance_fiat))
print("{}: {:12,.5f}".format(curr_crypto, balance_crypto))
print()

# -------------------------
# Print Last Trades
# -------------------------

last_sell = None
last_buy = None
for fill in client.get_fills(product_id=product_id, limit=1):
    if last_sell is None and fill["side"] == "sell":
        last_sell = fill
    elif last_buy is None and fill["side"] == "buy":
        last_buy = fill
    if last_sell is not None and last_buy is not None:
        break

print("Last fills:")
if last_sell is not None:
    print("Last SELL @ {:9,.2f}".format(float(last_sell["price"])))
if last_buy is not None:
    print("Last BUY  @ {:9,.2f}".format(float(last_buy["price"])))
print()

# -------------------------
# Print Orders
# -------------------------

orders = list(client.get_orders(product_id=product_id))
sell_orders = list(filter(lambda o: o["side"] == "sell", orders))
buy_orders = list(filter(lambda o: o["side"] == "buy", orders))

print("Orders:")
print("SELL: {} orders @ {}".format(len(sell_orders), ", ".join(map(lambda o: "{:9,.2f}".format(o["price"]), sell_orders))))
print("BUY:  {} orders @ {}".format(len(buy_orders), ", ".join(map(lambda o: "{:9,.2f}".format(o["price"]), buy_orders))))

# -------------------------
# Print Prices
# -------------------------

now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

end = now
start = end - datetime.timedelta(days=50)
rates = client.get_product_historic_rates(product_id=product_id, start=start.isoformat(), end=end.isoformat(), granularity=86400)
df = pd.DataFrame(data=rates, columns=["StartOfPeriod", "Low", "High", "Open", "Close", "Volume"]).set_index("StartOfPeriod")
df.index = pd.to_datetime(df.index, unit="s", utc=True)
df.drop(["Volume"], axis=1, inplace=True)
df.sort_index(inplace=True)
df["EndOfPeriod"] = df.index + datetime.timedelta(1) - datetime.timedelta(minutes=1)
df.loc[df.index[-1], "EndOfPeriod"] = end
df = df.set_index("EndOfPeriod")[["Close"]]

df["EMA12"] = df["Close"].ewm(span=12, min_periods=12, adjust=False).mean()
df["EMA26"] = df["Close"].ewm(span=26, min_periods=26, adjust=False).mean()
df["EMA12Perc26"] = (df["EMA12"] / df["EMA26"])

print("Prices:")
print(df[~np.isnan(df["EMA12Perc26"])][["Close", "EMA12Perc26"]])
print()

