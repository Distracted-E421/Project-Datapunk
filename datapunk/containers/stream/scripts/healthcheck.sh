#!/bin/sh
curl -f http://localhost:8001/health || exit 1 