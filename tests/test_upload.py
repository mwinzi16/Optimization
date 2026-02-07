"""Tests for POST /api/v1/upload endpoint."""

from __future__ import annotations

import io

import numpy as np
import pandas as pd
from flask.testing import FlaskClient


def _make_csv(n_assets: int = 3, n_scenarios: int = 150) -> bytes:
    """Generate a valid CSV file as bytes."""
    rng = np.random.default_rng(42)
    cols = [f"Asset_{i}" for i in range(n_assets)]
    df = pd.DataFrame(
        rng.normal(0.04, 0.05, size=(n_scenarios, n_assets)), columns=cols
    )
    buf = io.BytesIO()
    df.to_csv(buf, index=True)
    return buf.getvalue()


class TestUpload:
    """Upload endpoint tests."""

    def test_upload_valid_csv_returns_200(
        self, client: FlaskClient, sample_csv_bytes: bytes
    ) -> None:
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(sample_csv_bytes), "data.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["status"] == "success"

    def test_upload_no_file_returns_400(self, client: FlaskClient) -> None:
        resp = client.post("/api/v1/upload", content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_upload_too_few_columns_returns_error(
        self, client: FlaskClient, sample_invalid_csv_bytes: bytes
    ) -> None:
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(sample_invalid_csv_bytes), "one_col.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422)

    def test_upload_too_few_rows_returns_error(self, client: FlaskClient) -> None:
        csv_bytes = _make_csv(n_assets=3, n_scenarios=10)
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(csv_bytes), "small.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422)

    def test_upload_empty_file_returns_error(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(b""), "empty.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422, 500)

    def test_upload_invalid_extension_returns_error(
        self, client: FlaskClient
    ) -> None:
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(b"some data"), "bad.txt")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422)

    def test_upload_formula_injection_blocked(self, client: FlaskClient) -> None:
        """CSV with formula-like cells (=CMD) should be rejected."""
        csv_content = "idx,Asset_A,Asset_B\n0,=CMD('calc'),0.05\n"
        # Pad to 150 rows
        for i in range(1, 150):
            csv_content += f"{i},0.03,0.04\n"
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(csv_content.encode()), "inject.csv")},
            content_type="multipart/form-data",
        )
        # Should be rejected (either as formula injection or data parse issue)
        assert resp.status_code in (400, 422, 500)
