#!/bin/sh
curl -f http://localhost:8002/health || exit 1 