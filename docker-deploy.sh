#!/bin/bash
# Pull latest image from GHCR
docker pull ghcr.io/mscodemonkey/overtalkerr:latest

# Stop the old container
docker stop overtalkerr || true
docker rm overtalkerr || true

# Recreate container with same settings
docker run -d \
  --name=overtalkerr \
  -e PUID=1000 -e PGID=1000 \
  -v /volume1/docker/overtalkerr:/config \
  -p 5000:5000 \
  ghcr.io/mscodemonkey/overtalkerr:latest
