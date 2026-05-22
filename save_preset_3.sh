#!/bin/bash
curl -s -X POST http://localhost:8000/api/projection/preset/save \
  -H "Content-Type: application/json" \
  -d '{"name":"flores-blancas-3"}'
