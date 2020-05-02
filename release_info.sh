#!/usr/bin/env bash

LATEST_RELEASE="$(curl -s https://api.github.com/repos/GeorgOhneH/ethz-document-fetcher/releases/latest | jq -r '.tag_name')"
CURRENT_VERSION="$(cat version.txt)"

echo "::set-env name=latest_release::$LATEST_RELEASE"
echo "::set-env name=current_version::$CURRENT_VERSION"