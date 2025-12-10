"""
TON Service - FastAPI приложение для работы с TON blockchain

ВАЖНО: Это mock/stub версия для разработки и тестирования.
В production необходимо интегрировать реальный TON SDK (pytoniq, tonutils и т.д.)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import hashlib
import time
from decimal import Decimal

app = FastAPI(
    title="TON Service",
    description="Mock TON blockchain service для разработки",
    version="0.1.0"
)

# Mock данные для тестирования
TREASURY_WALLET = "EQDtFpEwcFAEcRe5mLVh2N6C0x-_hJEM7W61_JLnSF74p4q2"
COLLECTION_ADDRESS = "EQAXUIBbQhMqZ04eUpP3RZ8kS5Y8lEb_BgbhIqZ7uxLBLMsg"

# Простое хранилище для mock данных
mock_nfts = {}
mock_transactions = {}
mock_balances = {}


class MintRequest(BaseModel):
    """Запрос на минт NFT"""
    player_spirit_id: int
    owner_address: str
    metadata: Dict


class BurnRequest(BaseModel):
    """Запрос на burn NFT"""
    nft_id: str
    owner_address: str


class TransferRequest(BaseModel):
    """Запрос на transfer NFT"""
    nft_id: str
    from_address: str
    to_address: str


class SendRequest(BaseModel):
    """Запрос на отправку TON"""
    to_address: str
    amount: str  # Decimal в виде строки
    memo: Optional[str] = None


class DepositCheckRequest(BaseModel):
    """Запрос на проверку депозита"""
    address: str
    memo: Optional[str] = None


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "TON Service Mock",
        "version": "0.1.0",
        "mode": "development",
        "treasury": TREASURY_WALLET,
        "collection": COLLECTION_ADDRESS
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "blockchain": "TON (mock)"}


@app.post("/nft/mint")
async def mint_nft(request: MintRequest):
    """
    Минт NFT (mock)

    В production:
    1. Подписать транзакцию treasury wallet
    2. Вызвать смарт-контракт collection для минта
    3. Дождаться подтверждения транзакции
    4. Вернуть nft_id и tx_hash
    """
    try:
        # Генерируем fake nft_id и tx_hash
        nft_id = f"nft_{request.player_spirit_id}_{int(time.time())}"
        tx_hash = hashlib.sha256(
            f"{nft_id}{request.owner_address}{time.time()}".encode()
        ).hexdigest()

        # Генерируем token_id
        token_id = len(mock_nfts) + 1

        # Сохраняем в mock хранилище
        mock_nfts[nft_id] = {
            "nft_id": nft_id,
            "player_spirit_id": request.player_spirit_id,
            "owner_address": request.owner_address,
            "metadata": request.metadata,
            "token_id": token_id,
            "collection_address": COLLECTION_ADDRESS,
            "minted_at": int(time.time())
        }

        mock_transactions[tx_hash] = {
            "type": "mint",
            "nft_id": nft_id,
            "status": "confirmed",
            "timestamp": int(time.time())
        }

        return {
            "ok": True,
            "data": {
                "nft_id": nft_id,
                "tx_hash": tx_hash,
                "collection_address": COLLECTION_ADDRESS,
                "token_id": token_id,
                "owner_address": request.owner_address
            },
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "MINT_FAILED", "message": str(e)}
        }


@app.post("/nft/burn")
async def burn_nft(request: BurnRequest):
    """
    Burn NFT (mock)

    В production:
    1. Проверить ownership
    2. Подписать транзакцию на burn
    3. Вызвать метод burn смарт-контракта
    4. Дождаться подтверждения
    """
    try:
        # Проверяем существование NFT
        if request.nft_id not in mock_nfts:
            raise ValueError("NFT not found")

        nft = mock_nfts[request.nft_id]

        # Проверяем ownership
        if nft["owner_address"] != request.owner_address:
            raise ValueError("Not the owner of this NFT")

        # Генерируем tx_hash
        tx_hash = hashlib.sha256(
            f"burn_{request.nft_id}{time.time()}".encode()
        ).hexdigest()

        # Удаляем из хранилища
        del mock_nfts[request.nft_id]

        mock_transactions[tx_hash] = {
            "type": "burn",
            "nft_id": request.nft_id,
            "status": "confirmed",
            "timestamp": int(time.time())
        }

        return {
            "ok": True,
            "data": {
                "tx_hash": tx_hash,
                "nft_id": request.nft_id,
                "burned": True
            },
            "error": None
        }
    except ValueError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "BURN_FAILED", "message": str(e)}
        }


@app.post("/nft/transfer")
async def transfer_nft(request: TransferRequest):
    """
    Transfer NFT (mock)

    В production:
    1. Проверить ownership
    2. Подписать транзакцию transfer
    3. Дождаться подтверждения
    """
    try:
        if request.nft_id not in mock_nfts:
            raise ValueError("NFT not found")

        nft = mock_nfts[request.nft_id]

        if nft["owner_address"] != request.from_address:
            raise ValueError("Not the owner")

        # Генерируем tx_hash
        tx_hash = hashlib.sha256(
            f"transfer_{request.nft_id}{request.to_address}{time.time()}".encode()
        ).hexdigest()

        # Обновляем владельца
        mock_nfts[request.nft_id]["owner_address"] = request.to_address

        mock_transactions[tx_hash] = {
            "type": "transfer",
            "nft_id": request.nft_id,
            "from": request.from_address,
            "to": request.to_address,
            "status": "confirmed",
            "timestamp": int(time.time())
        }

        return {
            "ok": True,
            "data": {
                "tx_hash": tx_hash,
                "nft_id": request.nft_id,
                "from_address": request.from_address,
                "to_address": request.to_address
            },
            "error": None
        }
    except ValueError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "TRANSFER_FAILED", "message": str(e)}
        }


@app.post("/ton/send")
async def send_ton(request: SendRequest):
    """
    Отправка TON (mock)

    В production:
    1. Проверить баланс treasury
    2. Подписать транзакцию
    3. Отправить TON
    4. Дождаться подтверждения

    Используется для withdrawals
    """
    try:
        amount = Decimal(request.amount)

        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Генерируем tx_hash
        tx_hash = hashlib.sha256(
            f"send_{request.to_address}{amount}{time.time()}".encode()
        ).hexdigest()

        mock_transactions[tx_hash] = {
            "type": "send",
            "from": TREASURY_WALLET,
            "to": request.to_address,
            "amount": str(amount),
            "memo": request.memo,
            "status": "confirmed",
            "timestamp": int(time.time())
        }

        return {
            "ok": True,
            "data": {
                "tx_hash": tx_hash,
                "from_address": TREASURY_WALLET,
                "to_address": request.to_address,
                "amount": str(amount),
                "confirmed": True
            },
            "error": None
        }
    except ValueError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "SEND_FAILED", "message": str(e)}
        }


@app.post("/ton/check_deposit")
async def check_deposit(request: DepositCheckRequest):
    """
    Проверка депозита (mock)

    В production:
    1. Запросить транзакции для адреса через indexer
    2. Фильтровать по memo (если указан)
    3. Вернуть список новых депозитов
    """
    # Mock: возвращаем пустой список или fake депозит для тестирования
    return {
        "ok": True,
        "data": {
            "address": request.address,
            "deposits": []  # В реальности здесь список депозитов
        },
        "error": None
    }


@app.get("/nft/{nft_id}")
async def get_nft_info(nft_id: str):
    """Получить информацию о NFT"""
    if nft_id not in mock_nfts:
        raise HTTPException(status_code=404, detail="NFT not found")

    return {
        "ok": True,
        "data": mock_nfts[nft_id],
        "error": None
    }


@app.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str):
    """Получить информацию о транзакции"""
    if tx_hash not in mock_transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "ok": True,
        "data": mock_transactions[tx_hash],
        "error": None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
