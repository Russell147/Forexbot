import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"
os.environ["SECRET_KEY"] = "test-secret"

from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import BotSettings, Trade

CRED = {"email": "me@example.com", "password": "correct-horse-battery"}


def test_full_flow():
    with TestClient(app) as c:
        assert c.get("/state").status_code == 401
        assert c.post("/auth/register", json=CRED).status_code == 201
        assert c.post("/auth/register", json={**CRED, "email": "b@example.com"}).status_code == 403
        assert c.post("/auth/login", json={**CRED, "password": "wrong-password"}).status_code == 401
        assert c.post("/auth/login", json=CRED).status_code == 200  # sets cookie
        s = c.get("/state").json()
        assert s["engineOnline"] is False and s["risk"]["perTrade"] == 0.5 and len(s["on"]) == 7
        assert c.post("/bot/start").status_code == 409  # engine offline -> refuses
        with SessionLocal() as db:
            b = db.get(BotSettings, 1); b.heartbeat = datetime.now(timezone.utc); b.balance = b.equity = 1000
            db.add(Trade(ticket=1, symbol="EURUSD", type="BUY", volume=.01, entry_price=1.1, stop_loss=1.09, take_profit=1.12, strategy="Scalping"))
            db.commit()
        assert c.post("/bot/start").json()["desired"] == "running"
        assert c.put("/settings/risk", json={"perTrade": 99}).status_code == 422
        assert c.put("/settings/risk", json={"perTrade": 1.0, "session": "London"}).json()["perTrade"] == 1.0
        assert c.put("/strategies/Swing Trading", json={"on": True}).json()["on"] is True
        assert c.put("/settings/pairs/usdjpy", json={"on": False}).json()["enabled"] is False
        assert c.post("/accounts", json={"login": 1, "password": "x"}).status_code == 422  # passwords rejected
        assert len(c.get("/positions").json()) == 1
        assert c.post("/bot/emergency-stop", json={"closePositions": True}).json()["emg"] is True
        assert c.get("/analytics").status_code == 200
