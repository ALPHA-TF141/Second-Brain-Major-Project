import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database.init_db import init_database
from app.config import settings

print("=" * 60)
print("  JARVIS OS - FULL-STACK BACKEND COMPREHENSIVE TEST SUITE")
print("=" * 60)

# 1. Initialize Database
print("\n[TEST 1] Initializing Database...")
try:
    init_database()
    print("  --> [PASS] Database tables verified & initialized.")
except Exception as e:
    print(f"  --> [FAIL] Database init failed: {e}")
    sys.exit(1)

client = TestClient(app)

# 2. Test Health Endpoint
print("\n[TEST 2] Testing /api/health...")
resp = client.get("/api/health")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
data = resp.json()
assert data["status"] == "ok"
print(f"  --> [PASS] /api/health: {data}")

# 3. Test Authentication
print("\n[TEST 3] Testing /api/auth/login...")
resp = client.post("/api/auth/login", json={"username": "demo", "password": "secondbrain"})
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
auth_data = resp.json()
token = auth_data["access_token"]
assert token, "Token must not be empty"
headers = {"Authorization": f"Bearer {token}"}
print(f"  --> [PASS] /api/auth/login successful: Token acquired ({token[:20]}...)")

# 4. Test Live Activity & Viewfinder Fallback
print("\n[TEST 4] Testing /api/capture/live-preview & /api/capture/status...")
resp = client.get("/api/capture/status", headers=headers)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/capture/status: {resp.json()}")

# Create dummy preview image if not present to test file serving
preview_path = Path("data/screenshots/live_preview.jpg")
preview_path.parent.mkdir(parents=True, exist_ok=True)
if not preview_path.exists():
    from PIL import Image
    Image.new("RGB", (320, 240), color=(10, 15, 30)).save(str(preview_path), "JPEG")

resp = client.get(f"/api/capture/live-preview?token={token}")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert resp.headers["content-type"] == "image/jpeg"
print(f"  --> [PASS] /api/capture/live-preview: Valid JPEG served ({len(resp.content)} bytes)")

# 5. Test Knowledge Graph & Fallback
print("\n[TEST 5] Testing /api/graph/nodes, /api/graph/edges, /api/graph/stats...")
resp = client.get("/api/graph/nodes", headers=headers)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
nodes = resp.json()
print(f"  --> [PASS] /api/graph/nodes: {len(nodes)} nodes returned without 500 error")

resp = client.get("/api/graph/edges", headers=headers)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
edges = resp.json()
print(f"  --> [PASS] /api/graph/edges: {len(edges)} edges returned without 500 error")

resp = client.get("/api/graph/stats", headers=headers)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/graph/stats: {resp.json()}")

# 6. Test Memory Vault & Curated Cards
print("\n[TEST 6] Testing /api/graph/vault & /api/graph/vault/cards...")
resp = client.get("/api/graph/vault")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
vault_graph = resp.json()
assert "nodes" in vault_graph and "edges" in vault_graph
print(f"  --> [PASS] /api/graph/vault: Live graph loaded ({len(vault_graph['nodes'])} nodes)")

resp = client.get("/api/graph/vault/cards?limit=10")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/graph/vault/cards: {len(resp.json())} cards listed")

# 7. Test Self-Improving Wiki
print("\n[TEST 7] Testing /api/graph/vault/wiki...")
resp = client.get("/api/graph/vault/wiki")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/graph/vault/wiki: {len(resp.json())} master wiki articles discovered")

# 8. Test Daily Executive Briefing
print("\n[TEST 8] Testing /api/graph/briefing/today...")
resp = client.get("/api/graph/briefing/today")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
briefing = resp.json()
assert "spoken_script" in briefing and "date" in briefing
print(f"  --> [PASS] /api/graph/briefing/today: Script generated ({len(briefing['spoken_script'])} chars)")
print(f"      Spoken preview: \"{briefing['spoken_script'][:90]}...\"")

# 9. Test Deliverables Engine
print("\n[TEST 9] Testing /api/graph/deliverables...")
resp = client.get("/api/graph/deliverables")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/graph/deliverables: {len(resp.json())} deliverables currently archived")

# 10. Test Semantic & OCR Status
print("\n[TEST 10] Testing /api/semantic/status & /api/ocr/status...")
resp = client.get("/api/semantic/status", headers=headers)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/semantic/status: {resp.json()}")

resp = client.get("/api/ocr/status", headers=headers)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/ocr/status: {resp.json()}")

# 11. Test Voice Status
print("\n[TEST 11] Testing /api/voice/status...")
resp = client.get("/api/voice/status", headers=headers)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  --> [PASS] /api/voice/status: {resp.json()}")

print("\n" + "=" * 60)
print("  ALL 11 TEST SUITES PASSED WITH 100% SUCCESS (0 ERRORS, 0 LOCKUPS)!")
print("=" * 60)
