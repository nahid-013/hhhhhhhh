"""
NFT Service Stub - для тестирования mint/burn/transfer

В Sprint 7 будет заменен на реальную TON SDK интеграцию
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="HUNT NFT Service (Stub)")


class MintRequest(BaseModel):
    """Запрос на минт NFT"""
    player_spirit_id: int
    owner_address: str
    metadata: dict


class MintResponse(BaseModel):
    """Ответ на минт NFT"""
    nft_id: str
    tx_hash: str
    collection_address: str
    token_id: int


class BurnRequest(BaseModel):
    """Запрос на burn NFT"""
    nft_id: str


class BurnResponse(BaseModel):
    """Ответ на burn NFT"""
    tx_hash: str
    success: bool


class TransferRequest(BaseModel):
    """Запрос на transfer NFT"""
    nft_id: str
    from_address: str
    to_address: str


class TransferResponse(BaseModel):
    """Ответ на transfer NFT"""
    tx_hash: str
    success: bool


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "nft_service", "mode": "stub"}


@app.post("/nft/mint", response_model=MintResponse)
async def mint_nft(request: MintRequest):
    """
    Минт NFT (STUB)

    В реальной реализации:
    1. Создает NFT в TON blockchain
    2. Возвращает nft_id (collection_address + token_id)
    3. Возвращает tx_hash

    Сейчас возвращает fake данные для тестирования
    """
    # Генерируем fake данные
    fake_collection = "EQD0vdSA_NedR9uvbgN9EikRX-suesDxGeFg69XQMavfLqIw"
    fake_token_id = request.player_spirit_id  # Используем spirit_id как token_id
    fake_nft_id = f"{fake_collection}:{fake_token_id}"
    fake_tx_hash = f"0x{uuid.uuid4().hex}"

    return MintResponse(
        nft_id=fake_nft_id,
        tx_hash=fake_tx_hash,
        collection_address=fake_collection,
        token_id=fake_token_id
    )


@app.post("/nft/burn", response_model=BurnResponse)
async def burn_nft(request: BurnRequest):
    """
    Burn NFT (STUB)

    В реальной реализации:
    1. Вызывает burn метод NFT контракта
    2. Возвращает tx_hash
    """
    fake_tx_hash = f"0x{uuid.uuid4().hex}"

    return BurnResponse(
        tx_hash=fake_tx_hash,
        success=True
    )


@app.post("/nft/transfer", response_model=TransferResponse)
async def transfer_nft(request: TransferRequest):
    """
    Transfer NFT (STUB)

    В реальной реализации:
    1. Вызывает transfer метод NFT контракта
    2. Возвращает tx_hash
    """
    fake_tx_hash = f"0x{uuid.uuid4().hex}"

    return TransferResponse(
        tx_hash=fake_tx_hash,
        success=True
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
