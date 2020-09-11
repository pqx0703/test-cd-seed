#!/bin/bash
set -e

patterns=(
    "img.ones.pro/dev/*"
    "img.ones.pro/release/*"
    "img.ones.ai/dev/*"
    "img.ones.ai/release/*"
    "project-migration"
    "wiki-migration"
)
for pattern in ${patterns[@]}; do
    images=$(docker images "$pattern" --format "{{.Repository}}:{{.Tag}}")
    for image in $images; do
        docker rmi $image || true
    done
done

docker container prune
docker image prune