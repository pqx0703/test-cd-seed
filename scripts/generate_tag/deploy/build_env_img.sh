#!/bin/bash
set -e

rm -rf ./mars
git clone git@github.com:BangWork/mars.git

cd mars
git checkout master
echo "build mars"
echo "$(go version)"
GOOS=linux GOARCH=amd64 GO111MODULE=on go build -o mars cli/main.go
echo "finish build mars"

cd ..
docker build -t img.ones.pro/release/release-product-env:latest .
docker push img.ones.pro/release/release-product-env:latest
