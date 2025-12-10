"""
NFT Client - для взаимодействия с NFT Service

В Sprint 7 будет расширен для реальной TON SDK интеграции
"""
import httpx
from typing import Optional, Dict
from decimal import Decimal


# URL NFT Service (stub)
NFT_SERVICE_URL = "http://localhost:8001"


async def mint_nft(
    player_spirit_id: int,
    owner_address: str,
    metadata: Dict
) -> Dict[str, str]:
    """
    Вызывает NFT Service для минта NFT

    Returns:
        {
            "nft_id": str,
            "tx_hash": str,
            "collection_address": str,
            "token_id": int
        }

    Raises:
        Exception если минт не удался
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NFT_SERVICE_URL}/nft/mint",
                json={
                    "player_spirit_id": player_spirit_id,
                    "owner_address": owner_address,
                    "metadata": metadata
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"NFT mint failed: {str(e)}")


async def burn_nft(nft_id: str) -> Dict[str, any]:
    """
    Вызывает NFT Service для burn NFT

    Returns:
        {
            "tx_hash": str,
            "success": bool
        }

    Raises:
        Exception если burn не удался
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NFT_SERVICE_URL}/nft/burn",
                json={"nft_id": nft_id},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"NFT burn failed: {str(e)}")


async def transfer_nft(
    nft_id: str,
    from_address: str,
    to_address: str
) -> Dict[str, any]:
    """
    Вызывает NFT Service для transfer NFT

    Returns:
        {
            "tx_hash": str,
            "success": bool
        }

    Raises:
        Exception если transfer не удался
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NFT_SERVICE_URL}/nft/transfer",
                json={
                    "nft_id": nft_id,
                    "from_address": from_address,
                    "to_address": to_address
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"NFT transfer failed: {str(e)}")
