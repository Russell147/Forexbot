from typing import Literal

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class RiskIn(BaseModel):
    perTrade: float | None = Field(None, gt=0, le=5)
    maxDaily: float | None = Field(None, gt=0, le=20)
    maxDD: float | None = Field(None, gt=0, le=50)
    maxPos: int | None = Field(None, ge=1, le=20)
    minRR: float | None = Field(None, ge=1, le=10)
    maxSpread: float | None = Field(None, gt=0, le=20)
    session: Literal["All sessions", "London", "New York", "London + New York"] | None = None
    closeOnStop: bool | None = None
    trailingEnabled: bool | None = None
    trailingAtrMult: float | None = Field(None, gt=0, le=10)
    maxDailyTrades: int | None = Field(None, ge=1, le=100)
    maxConsecutiveLosses: int | None = Field(None, ge=1, le=10)
    lotMode: Literal["risk", "fixed"] | None = None
    fixedLot: float | None = Field(None, gt=0, le=100)
    maxLotSize: float | None = Field(None, gt=0, le=100)
    breakEvenAfterR: float | None = Field(None, ge=0, le=10)
    partialTpR: float | None = Field(None, ge=0, le=10)
    partialTpPct: float | None = Field(None, ge=0, le=100)
    maxHoldHours: float | None = Field(None, ge=0, le=720)
    maxCurrencyExposure: int | None = Field(None, ge=0, le=10)


class BotSettingsIn(BaseModel):
    telegramEnabled: bool | None = None
    aiEnabled: bool | None = None


class AccountIn(BaseModel):
    login: int = Field(gt=0)
    server: str = Field("", max_length=100)
    broker: str = Field("", max_length=100)
    account_type: Literal["demo", "live"] = "demo"
    currency: str = Field("USD", max_length=8)
    model_config = {"extra": "forbid"}  # rejects any attempt to send a password field


class EnabledIn(BaseModel):
    on: bool


class EmergencyIn(BaseModel):
    closePositions: bool | None = None
