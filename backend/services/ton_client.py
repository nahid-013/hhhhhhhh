"""
TON Client - для взаимодействия с TON Service

Расширенная версия для Sprint 7 с поддержкой:
- Mint NFT
- Burn NFT
- Transfer NFT
- Send TON
- Check deposits
"""
import httpx
from typing import Optional, Dict, List
from decimal import Decimal
from backend.core.config import settings


# URL TON Service (можно настроить в .env)
TON_SERVICE_URL = getattr(settings, "TON_SERVICE_URL", "http://localhost:8001")


async def mint_nft(
    player_spirit_id: int,
    owner_address: str,
    metadata: Dict
) -> Dict[str, any]:
    """
    Минт NFT через TON Service

    Args:
        player_spirit_id: ID спирита в БД
        owner_address: TON адрес владельца
        metadata: Метаданные NFT (имя, описание, атрибуты и т.д.)

    Returns:
        {
            "nft_id": str,
            "tx_hash": str,
            "collection_address": str,
            "token_id": int,
            "owner_address": str
        }

    Raises:
        Exception если минт не удался
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TON_SERVICE_URL}/nft/mint",
                json={
                    "player_spirit_id": player_spirit_id,
                    "owner_address": owner_address,
                    "metadata": metadata
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                error = result.get("error", {})
                raise Exception(f"NFT mint failed: {error.get('message', 'Unknown error')}")

            return result["data"]
        except httpx.HTTPError as e:
            raise Exception(f"NFT mint HTTP error: {str(e)}")
        except Exception as e:
            raise Exception(f"NFT mint failed: {str(e)}")


async def burn_nft(
    nft_id: str,
    owner_address: str
) -> Dict[str, any]:
    """
    Burn NFT через TON Service

    Args:
        nft_id: ID NFT для сжигания
        owner_address: TON адрес владельца

    Returns:
        {
            "tx_hash": str,
            "nft_id": str,
            "burned": bool
        }

    Raises:
        Exception если burn не удался
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TON_SERVICE_URL}/nft/burn",
                json={
                    "nft_id": nft_id,
                    "owner_address": owner_address
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                error = result.get("error", {})
                raise Exception(f"NFT burn failed: {error.get('message', 'Unknown error')}")

            return result["data"]
        except httpx.HTTPError as e:
            raise Exception(f"NFT burn HTTP error: {str(e)}")
        except Exception as e:
            raise Exception(f"NFT burn failed: {str(e)}")


async def transfer_nft(
    nft_id: str,
    from_address: str,
    to_address: str
) -> Dict[str, any]:
    """
    Transfer NFT через TON Service

    Args:
        nft_id: ID NFT
        from_address: TON адрес отправителя
        to_address: TON адрес получателя

    Returns:
        {
            "tx_hash": str,
            "nft_id": str,
            "from_address": str,
            "to_address": str
        }
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TON_SERVICE_URL}/nft/transfer",
                json={
                    "nft_id": nft_id,
                    "from_address": from_address,
                    "to_address": to_address
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                error = result.get("error", {})
                raise Exception(f"NFT transfer failed: {error.get('message', 'Unknown error')}")

            return result["data"]
        except httpx.HTTPError as e:
            raise Exception(f"NFT transfer HTTP error: {str(e)}")
        except Exception as e:
            raise Exception(f"NFT transfer failed: {str(e)}")


async def send_ton(
    to_address: str,
    amount: Decimal,
    memo: Optional[str] = None
) -> Dict[str, any]:
    """
    Отправить TON через TON Service

    Используется для:
    - Withdrawals
    - Выплат игрокам
    - Рефералок

    Args:
        to_address: TON адрес получателя
        amount: Сумма в TON
        memo: Опциональная заметка

    Returns:
        {
            "tx_hash": str,
            "from_address": str,
            "to_address": str,
            "amount": str,
            "confirmed": bool
        }
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TON_SERVICE_URL}/ton/send",
                json={
                    "to_address": to_address,
                    "amount": str(amount),
                    "memo": memo
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                error = result.get("error", {})
                raise Exception(f"TON send failed: {error.get('message', 'Unknown error')}")

            return result["data"]
        except httpx.HTTPError as e:
            raise Exception(f"TON send HTTP error: {str(e)}")
        except Exception as e:
            raise Exception(f"TON send failed: {str(e)}")


async def check_deposit(
    address: str,
    memo: Optional[str] = None
) -> List[Dict]:
    """
    Проверить депозиты на адрес

    Args:
        address: TON адрес для проверки
        memo: Опциональный memo для фильтрации

    Returns:
        Список депозитов [{
            "tx_hash": str,
            "amount": str,
            "from_address": str,
            "timestamp": int,
            "memo": str
        }]
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TON_SERVICE_URL}/ton/check_deposit",
                json={
                    "address": address,
                    "memo": memo
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                error = result.get("error", {})
                raise Exception(f"Check deposit failed: {error.get('message', 'Unknown error')}")

            return result["data"].get("deposits", [])
        except httpx.HTTPError as e:
            raise Exception(f"Check deposit HTTP error: {str(e)}")
        except Exception as e:
            raise Exception(f"Check deposit failed: {str(e)}")


async def get_nft_info(nft_id: str) -> Optional[Dict]:
    """
    Получить информацию о NFT

    Args:
        nft_id: ID NFT

    Returns:
        Информация о NFT или None если не найден
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{TON_SERVICE_URL}/nft/{nft_id}",
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                return None

            return result["data"]
        except:
            return None


async def get_transaction(tx_hash: str) -> Optional[Dict]:
    """
    Получить информацию о транзакции

    Args:
        tx_hash: Hash транзакции

    Returns:
        Информация о транзакции или None если не найдена
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{TON_SERVICE_URL}/transaction/{tx_hash}",
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                return None

            return result["data"]
        except:
            return None
