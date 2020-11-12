# Coinbase Pro Trader

Retrieves market details for a selected fiat/crypto pair from Coinbase Pro, and your last fills and open orders.

## Development goals

* Make trading decisions based on market conditions
* Place limit orders
* Set up for scheduled execution on AWS Lambda

## Setup

Create an `.env.local` file containing the details of a [Coinbase Pro API key](https://pro.coinbase.com/profile/api):

```
CB_KEY=...
CB_SECRET=...
CB_PASSPHRASE=...
```

## Run

```
python trade.py
```
