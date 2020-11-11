import cbpro
import dotenv
import os
import sys

dotenv.load_dotenv(dotenv_path=".env.local")

client = cbpro.AuthenticatedClient(os.environ["CB_KEY"], os.environ["CB_SECRET"], os.environ["CB_PASSPHRASE"])

product_id = "BTC-EUR"

last_sell = None
last_buy = None
for fill in client.get_fills(product_id=product_id, limit=1):
    if last_sell is None and fill["side"] == "sell":
        last_sell = fill
    elif last_buy is None and fill["side"] == "buy":
        last_buy = fill
    if last_sell is not None and last_buy is not None:
        break

if last_sell is not None:
    print("Last sell @ {}".format(last_sell["price"]))
if last_buy is not None:
    print("Last buy @ {}".format(last_buy["price"]))


orders = list(client.get_orders(product_id=product_id))
# print(orders)
print("{} orders @ {}".format(len(orders), ", ".join([o["price"] for o in orders])))

# client.buy(product_id=product_id, price="5000", order_type='limit', size="0.1")
