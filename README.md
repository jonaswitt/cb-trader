# Coinbase Pro Trader

Retrieves market details for a selected fiat/crypto pair from Coinbase Pro, 
makes trading decisions based on market conditions and creates orders.

## Development goals

* Place limit orders at estimated change of trading conditions
* Set up for scheduled execution on AWS Lambda

## Setup

Create an `.env.local` file containing the details of a [Coinbase Pro API key](https://pro.coinbase.com/profile/api):

```
CB_KEY=...
CB_SECRET=...
CB_PASSPHRASE=...
```

## Run

Trades will only be executed with `LIVE=true` environment variable, 
otherwise trades are printed and the program exits.

```
LIVE=true python trade.py
```

## Example Output

```
$ LIVE=true python trade.py
BTC Prices (in EUR):
                                     Close  EMA12Perc26
EndOfPeriod                                            
2020-10-22 23:59:00+00:00         10966.08     1.033372
2020-10-23 23:59:00+00:00         10891.89     1.037453
2020-10-24 23:59:00+00:00         11059.50     1.041427
2020-10-25 23:59:00+00:00         11001.91     1.043521
2020-10-26 23:59:00+00:00         11071.38     1.045121
2020-10-27 23:59:00+00:00         11627.69     1.049967
2020-10-28 23:59:00+00:00         11319.10     1.050759
2020-10-29 23:59:00+00:00         11530.00     1.052284
2020-10-30 23:59:00+00:00         11647.39     1.053653
2020-10-31 23:59:00+00:00         11849.18     1.055479
2020-11-01 23:59:00+00:00         11833.96     1.056071
2020-11-02 23:59:00+00:00         11658.15     1.054584
2020-11-03 23:59:00+00:00         11940.96     1.054747
2020-11-04 23:59:00+00:00         12065.96     1.055056
2020-11-05 23:59:00+00:00         13193.03     1.062310
2020-11-06 23:59:00+00:00         13127.84     1.066560
2020-11-07 23:59:00+00:00         12402.78     1.064145
2020-11-08 23:59:00+00:00         12966.19     1.065190
2020-11-09 23:59:00+00:00         12967.67     1.065168
2020-11-10 23:59:00+00:00         12957.33     1.064259
2020-11-11 23:59:00+00:00         13317.11     1.065045
2020-11-12 23:59:00+00:00         13821.85     1.067991
2020-11-13 23:59:00+00:00         13796.86     1.069201
2020-11-14 23:59:00+00:00         13602.60     1.068046
2020-11-15 17:40:54.503509+00:00  13516.11     1.065772

Balances:
EUR:      0.00
BTC:      0.00735

Sum:     99.34 EUR

Last fills:
Last BUY  @ 13,558.75

Open Orders:
None

EMA Trend:
EMA12 and EMA26 are converging

EMA12 > EMA26 ( +6.6%) -- BUY
All in, no EUR left in portfolio

New Orders:
None
```
