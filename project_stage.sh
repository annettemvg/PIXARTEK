#!/bin/bash
curl -s -X POST http://localhost:8000/api/stages/flores-blancas/2/project \
  -H "Content-Type: application/json" \
  -d '{}'
