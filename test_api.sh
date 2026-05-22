#!/bin/bash
curl -s -X POST http://localhost:8000/api/projection/adjust \
  -H "Content-Type: application/json" \
  -d '{"action":"up"}'
