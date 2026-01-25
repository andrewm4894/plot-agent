"""UCI ML Repository dataset service."""

import pandas as pd
from typing import Optional
import httpx
from io import StringIO

# Try to import ucimlrepo, but make it optional
try:
    from ucimlrepo import fetch_ucirepo
    UCIMLREPO_AVAILABLE = True
except ImportError:
    UCIMLREPO_AVAILABLE = False


# Curated list of popular/interesting datasets for the UI
FEATURED_DATASETS = [
    {"id": 53, "name": "Iris", "task": "Classification", "instances": 150},
    {"id": 45, "name": "Heart Disease", "task": "Classification", "instances": 303},
    {"id": 186, "name": "Wine Quality", "task": "Regression", "instances": 4898},
    {"id": 17, "name": "Breast Cancer Wisconsin", "task": "Classification", "instances": 569},
    {"id": 9, "name": "Auto MPG", "task": "Regression", "instances": 398},
    {"id": 109, "name": "Wine", "task": "Classification", "instances": 178},
    {"id": 73, "name": "Mushroom", "task": "Classification", "instances": 8124},
    {"id": 19, "name": "Car Evaluation", "task": "Classification", "instances": 1728},
    {"id": 2, "name": "Adult", "task": "Classification", "instances": 48842},
    {"id": 14, "name": "Abalone", "task": "Regression", "instances": 4177},
]


class DatasetService:
    """Service for loading datasets from UCI or custom URLs."""

    @staticmethod
    def get_featured_datasets() -> list[dict]:
        """Return curated list of featured datasets."""
        return FEATURED_DATASETS

    @staticmethod
    def load_uci_dataset(dataset_id: int) -> tuple[pd.DataFrame, dict]:
        """
        Load a UCI dataset by ID.

        Args:
            dataset_id: The UCI dataset ID.

        Returns:
            tuple: (DataFrame with all data, metadata dict)

        Raises:
            ImportError: If ucimlrepo is not installed.
            Exception: If dataset loading fails.
        """
        if not UCIMLREPO_AVAILABLE:
            raise ImportError(
                "ucimlrepo is required to load UCI datasets. "
                "Install it with: pip install ucimlrepo"
            )

        dataset = fetch_ucirepo(id=dataset_id)

        # Combine features and targets into single DataFrame
        if dataset.data.targets is not None:
            df = pd.concat([dataset.data.features, dataset.data.targets], axis=1)
        else:
            df = dataset.data.features.copy()

        # Build metadata
        metadata = {
            "name": dataset.metadata.name,
            "abstract": getattr(dataset.metadata, "abstract", ""),
            "num_instances": len(df),
            "num_features": len(df.columns),
            "task": getattr(dataset.metadata, "task", "Unknown"),
            "source": "UCI ML Repository",
            "uci_id": dataset_id,
        }

        # Add variable info if available
        if hasattr(dataset, "variables") and dataset.variables is not None:
            metadata["variables"] = dataset.variables.to_dict(orient="records")

        return df, metadata

    @staticmethod
    async def load_csv_from_url(url: str) -> tuple[pd.DataFrame, dict]:
        """
        Load a CSV file from a URL asynchronously.

        Args:
            url: URL pointing to a CSV file.

        Returns:
            tuple: (DataFrame, metadata dict)

        Raises:
            httpx.HTTPError: If the URL request fails.
            pd.errors.ParserError: If the CSV cannot be parsed.
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))

        # Extract filename from URL for the name
        filename = url.split("/")[-1].split("?")[0]
        if filename.endswith(".csv"):
            filename = filename[:-4]

        metadata = {
            "name": filename or "Custom Dataset",
            "abstract": f"Dataset loaded from: {url}",
            "num_instances": len(df),
            "num_features": len(df.columns),
            "source": url,
            "task": "Unknown",
        }

        return df, metadata

    @staticmethod
    def load_csv_from_url_sync(url: str) -> tuple[pd.DataFrame, dict]:
        """
        Load a CSV file from a URL synchronously.

        Args:
            url: URL pointing to a CSV file.

        Returns:
            tuple: (DataFrame, metadata dict)

        Raises:
            httpx.HTTPError: If the URL request fails.
            pd.errors.ParserError: If the CSV cannot be parsed.
        """
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))

        # Extract filename from URL for the name
        filename = url.split("/")[-1].split("?")[0]
        if filename.endswith(".csv"):
            filename = filename[:-4]

        metadata = {
            "name": filename or "Custom Dataset",
            "abstract": f"Dataset loaded from: {url}",
            "num_instances": len(df),
            "num_features": len(df.columns),
            "source": url,
            "task": "Unknown",
        }

        return df, metadata
