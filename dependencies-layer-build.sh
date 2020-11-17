#! /bin/bash

yarn run serverless package || exit 1

rm -rf dependencies-layer dependencies-layer.zip
mkdir -p dependencies-layer/python/lib/python3.7/site-packages || exit 1 
unzip -q -o .serverless/cb-trader.zip -d dependencies-layer/python/lib/python3.7/site-packages/ || exit 1

rm -rf dependencies-layer/python/lib/python3.7/site-packages/pandas/tests || exit 1
cd dependencies-layer && zip -qr ../dependencies-layer.zip . && cd .. || exit 1
du -sh dependencies-layer.zip
