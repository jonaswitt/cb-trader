import cbpro
import dotenv
import math
import os
import sys
import datetime
import pandas as pd
import numpy as np

dotenv.load_dotenv(dotenv_path=".env.local")

client = cbpro.AuthenticatedClient(os.environ["CB_KEY"], os.environ["CB_SECRET"], os.environ["CB_PASSPHRASE"])
live = os.environ.get("LIVE", "false") == "true"

curr_fiat = "EUR"
curr_crypto = "BTC"
product_id = "{}-{}".format(curr_crypto, curr_fiat)

def assertValidResponse(response):
    if isinstance(response, dict):
        if "message" in response:
            raise Exception(response["message"])
    return response

def run():
    # -------------------------
    # Print Prices
    # -------------------------

    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc, microsecond=0)

    period = datetime.timedelta(days=1)
    history_period_count = 50

    end = now
    start = end - period * history_period_count
    rates = client.get_product_historic_rates(product_id=product_id, start=start.isoformat(), end=end.isoformat(), granularity=int(period.total_seconds()))
    assertValidResponse(rates)
    df = pd.DataFrame(data=rates, columns=["StartOfPeriod", "Low", "High", "Open", "Close", "Volume"]).set_index("StartOfPeriod")
    df.index = pd.to_datetime(df.index, unit="s", utc=True)
    df.drop(["Volume"], axis=1, inplace=True)
    df.sort_index(inplace=True)
    df["EndOfPeriod"] = df.index + period - datetime.timedelta(seconds=1)

    df.loc[df.index[-1], "EndOfPeriod"] = pd.Timestamp(end)
    df = df.loc[df.index[:-1]]

    df = df.set_index("EndOfPeriod")[["Close"]]
    end = pd.Timestamp(df.index[-1])

    df["EMA12"] = df["Close"].ewm(span=12, min_periods=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, min_periods=26, adjust=False).mean()
    df["EMA12Perc26"] = (df["EMA12"] / df["EMA26"])
    ema12 = df.loc[end, "EMA12"]
    ema26 = df.loc[end, "EMA26"]
    ema12perc26 = df.loc[end, "EMA12Perc26"]
    lastClose = df.loc[end, "Close"]

    print("{} Prices (in {}):".format(curr_crypto, curr_fiat))
    print(df[~np.isnan(df["EMA12Perc26"])][["Close", "EMA12Perc26"]])
    print()

    # -------------------------
    # Print Balances
    # -------------------------

    balance_fiat = None
    balance_crypto = None
    accounts = client.get_accounts()
    assertValidResponse(accounts)
    for acc in accounts:
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
    print("Sum: {:9,.2f} {}".format(balance_fiat + balance_crypto * lastClose, curr_fiat))
    print()

    # -------------------------
    # Print Last Trades
    # -------------------------

    last_sell = None
    last_buy = None
    fills = client.get_fills(product_id=product_id, limit=1)
    assertValidResponse(fills)
    for fill in fills:
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
    if last_sell is None and last_buy is None:
        print("None")
    print()

    # -------------------------
    # Print Orders
    # -------------------------

    orders = client.get_orders(product_id=product_id)
    assertValidResponse(orders)
    orders = list(orders)
    sell_orders = list(filter(lambda o: o["side"] == "sell", orders))
    buy_orders = list(filter(lambda o: o["side"] == "buy", orders))

    print("Open Orders:")
    if len(sell_orders) > 0:
        print("SELL: {} orders @ {}".format(len(sell_orders), ", ".join(map(lambda o: "{:9,.2f}".format(o["price"]), sell_orders))))
    if len(buy_orders) > 0:
        print("BUY:  {} orders @ {}".format(len(buy_orders), ", ".join(map(lambda o: "{:9,.2f}".format(o["price"]), buy_orders))))
    if len(sell_orders) == 0 and len(buy_orders) == 0:
        print("None")
    print()

    # -------------------------
    # EMA12/EMA26 Trend Analysis
    # -------------------------

    # Determine date when linear extrapolation of EMA12 and EMA26 will cross
    # If crossing in the future, EMA12 and EMA26 are converging
    # If crossing in the past, EMA12 and EMA26 are diverging
    numDataPoints = 3
    p_time = list(map(lambda t: pd.Timestamp(t).timestamp(), df.index[-numDataPoints:].values))
    p_ema12 = df["EMA12"][-numDataPoints:].values
    p_ema26 = df["EMA26"][-numDataPoints:].values

    A = np.vstack([p_time,np.ones(len(p_time))]).T
    eq_ema12 = np.linalg.lstsq(A, p_ema12, rcond=None)[0]
    eq_ema26 = np.linalg.lstsq(A, p_ema26, rcond=None)[0]

    t_intersect = (eq_ema26[1] - eq_ema12[1]) / (eq_ema12[0] - eq_ema26[0])
    d_interset = datetime.datetime.utcfromtimestamp(t_intersect).replace(tzinfo=datetime.timezone.utc)
    ema_converging = d_interset > end

    print("EMA Trend:")
    if ema_converging:
        print("EMA12 and EMA26 are converging")
    else:
        print("EMA12 and EMA26 are diverging")
    print()

    # -------------------------
    # EMA12/EMA26 Trading Suggestions
    # -------------------------

    buyMarket = False
    sellMarket = False

    print("Trading Actions:")
    if ema12perc26 > 1:
        print("EMA12 > EMA26 ({:+5.1f}%) -- BUY".format((ema12perc26 - 1) * 100))
        if balance_fiat > 10:
            if last_sell is not None and float(last_sell["price"]) > lastClose * 1.01:
                print("Last sell {:f} too close to market {:f} to buy".format(last_sell["price"], lastClose))
            else:
                buyMarket = True
        else:
            print("All in, no {} left in portfolio".format(curr_fiat))

    elif ema12perc26 < 1:
        print("EMA12 < EMA26 ({:+5.1f}%) -- SELL".format((ema12perc26 - 1) * 100))
        if balance_crypto > 0:
            if last_buy is not None and float(last_buy["price"]) * 1.01 > lastClose:
                print("Last buy {:f} too close to market {:f} to sell".format(last_buy["price"], lastClose))
            else:
                sellMarket = True
        else:
            print("All out, no {} left in portfolio".format(curr_crypto))

    print()
    print("New Orders:")
    if buyMarket:
        print("BUY  {:9,.2f} {} @ market price (ca. {:9,.2f} {})".format(balance_fiat, curr_fiat, lastClose, curr_fiat))
    elif sellMarket:
        print("SELL {:12,.5f} {} @ market price (ca. {:9,.2f} {})".format(balance_crypto, curr_crypto, lastClose, curr_fiat))
    else:
        print("None")
    print("")

    if not live:
        print("DRY RUN, stopping here without any orders created (set LIVE=true)")
        sys.exit(0)

    if len(orders) > 0:
        print("There are open orders, aborting")
        sys.exit(1)

    orderReq = None
    if buyMarket:
        orderReq = dict(product_id=product_id, side="buy", order_type="market", funds=math.floor(balance_fiat * 100.0) / 100.0)
    elif sellMarket:
        orderReq = dict(product_id=product_id, side="sell", order_type="market", size=math.floor(balance_crypto * 100000.0) / 100000.0)

    if orderReq is not None:
        orderRes = client.place_order(**orderReq)
        assertValidResponse(orderRes)
        print("Placed order", orderRes)


def handler(event, context):
    run()

if __name__ == '__main__' and "AWS_LAMBDA_FUNCTION_VERSION" not in os.environ:
    run()

