"""DOIP client for aFDO-to-aFDO and aFDO-to-Registry communication."""

import httpx
from typing import Dict, Any, Optional, List
from .utils import current_timestamp


class DOIPClient:
    """Client for making DOIP requests."""

    def __init__(self, base_url: str):
        """
        Initialize DOIP client.

        Args:
            base_url: Base URL of target service (e.g., "http://localhost:8000")
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_fdo(self, fdo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create FDO in registry.

        Args:
            fdo_data: FDO record data

        Returns:
            Response data
        """
        response = await self.client.post(
            f"{self.base_url}/doip/create/fdo",
            json=fdo_data
        )
        response.raise_for_status()
        return response.json()

    async def create_metadata(self, metadata_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata record in registry."""
        response = await self.client.post(
            f"{self.base_url}/doip/create/metadata",
            json=metadata_data
        )
        response.raise_for_status()
        return response.json()

    async def create_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create operation in registry."""
        response = await self.client.post(
            f"{self.base_url}/doip/create/operation",
            json=operation_data
        )
        response.raise_for_status()
        return response.json()

    async def update_operation(self, pid: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update operation in registry."""
        response = await self.client.put(
            f"{self.base_url}/doip/update/operation/{pid}",
            json=operation_data
        )
        response.raise_for_status()
        return response.json()

    async def read_fdo(self, pid: str) -> Dict[str, Any]:
        """
        Read FDO by PID.

        Args:
            pid: FDO persistent identifier

        Returns:
            FDO data
        """
        response = await self.client.get(f"{self.base_url}/doip/read/fdo/{pid}")
        response.raise_for_status()
        return response.json()

    async def search_fdos(
        self,
        fdo_type: Optional[str] = None,
        operation: Optional[str] = None,
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for FDOs by criteria.

        Args:
            fdo_type: Filter by FDO type
            operation: Filter by operation
            profile: Filter by profile

        Returns:
            List of matching FDOs
        """
        params = {}
        if fdo_type:
            params['fdo_type'] = fdo_type
        if operation:
            params['operation'] = operation
        if profile:
            params['profile'] = profile

        response = await self.client.post(
            f"{self.base_url}/doip/search/fdos",
            params=params
        )
        response.raise_for_status()
        result = response.json()
        return result.get('data', [])

    async def search_operations(
        self,
        name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for operations by name.

        Args:
            name: Filter by operation name

        Returns:
            List of matching operations
        """
        params = {}
        if name:
            params['name'] = name

        response = await self.client.post(
            f"{self.base_url}/doip/search/operations",
            params=params
        )
        response.raise_for_status()
        result = response.json()
        return result.get('data', [])

    async def extend_operation(
        self,
        target_url: str,
        operation: str,
        caller_pid: str,
        data: Dict[str, Any],
        parent_request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call extended operation on another aFDO.

        Args:
            target_url: URL of target aFDO
            operation: Operation name
            caller_pid: PID of calling aFDO
            data: Operation parameters
            parent_request_id: Optional parent trace request ID for nested tracing

        Returns:
            Operation result
        """
        # Build authentication object
        authentication = {
            "caller_pid": caller_pid
        }

        # Include parent_request_id for nested tracing
        if parent_request_id:
            authentication["parent_request_id"] = parent_request_id

        request_data = {
            "protocol_version": "2.0",
            "operation": f"0.DOIP/Op.Extend/{operation}",
            "authentication": authentication,
            "parameters": data
        }

        response = await self.client.post(
            f"{target_url}/doip/extend/{operation}",
            json=request_data
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
