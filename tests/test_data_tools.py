"""Tests for ``tools.data_tools._generate_create_table_sql``.

This is the only pure function in ``data_tools`` — every other entry
point either calls a real ClickHouse client or runs a real Plotly /
matplotlib pipeline. Keeping the test surface tight here avoids
slow, flaky tests; the CREATE TABLE generator is the bug-prone piece
because pandas dtype inference changes between releases.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest

from tools.data_tools import DataLoader


@pytest.fixture
def loader() -> DataLoader:
    """A DataLoader whose client is None.

    ``_generate_create_table_sql`` does not touch ``self.client``, so
    passing None is safe and keeps the test independent of the
    ClickHouse client library.
    """
    return DataLoader(client=None)


class TestColumnTypeMapping:
    def test_unsigned_integer_column_maps_to_uint64(self, loader: DataLoader) -> None:
        df = pd.DataFrame({"x": [1, 2, 3]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "`x` UInt64" in sql

    def test_signed_integer_column_maps_to_int64(self, loader: DataLoader) -> None:
        df = pd.DataFrame({"x": [-1, 2, 3]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "`x` Int64" in sql

    def test_float_column_maps_to_float64(self, loader: DataLoader) -> None:
        df = pd.DataFrame({"x": [1.5, 2.5, 3.5]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "`x` Float64" in sql

    def test_bool_column_maps_to_bool(self, loader: DataLoader) -> None:
        df = pd.DataFrame({"x": [True, False, True]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "`x` Bool" in sql

    def test_datetime_column_maps_to_datetime(self, loader: DataLoader) -> None:
        df = pd.DataFrame(
            {"x": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])}
        )
        sql = loader._generate_create_table_sql(df, "t")
        assert "`x` DateTime" in sql

    def test_object_column_maps_to_string(self, loader: DataLoader) -> None:
        df = pd.DataFrame({"x": ["a", "b", "c"]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "`x` String" in sql

    def test_mixed_object_column_falls_back_to_string(self, loader: DataLoader) -> None:
        # Mixed-type object columns are common in CSV ingestion; they
        # must not crash the generator.
        df = pd.DataFrame({"x": ["a", 1, datetime(2024, 1, 1)]}, dtype=object)
        sql = loader._generate_create_table_sql(df, "t")
        assert "`x` String" in sql


class TestSqlStructure:
    def test_includes_if_not_exists_clause(self, loader: DataLoader) -> None:
        # The generator is called repeatedly during CSV ingestion;
        # IF NOT EXISTS is what makes that idempotent.
        df = pd.DataFrame({"x": [1]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "CREATE TABLE IF NOT EXISTS" in sql

    def test_uses_mergetree_engine(self, loader: DataLoader) -> None:
        df = pd.DataFrame({"x": [1]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "ENGINE = MergeTree()" in sql

    def test_orders_by_tuple_when_no_key_supplied(self, loader: DataLoader) -> None:
        # ORDER BY tuple() is ClickHouse's "I have no opinion about
        # ordering" idiom; the generator must emit it (an empty
        # ORDER BY would be a syntax error).
        df = pd.DataFrame({"x": [1]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "ORDER BY tuple()" in sql

    def test_table_name_is_substituted(self, loader: DataLoader) -> None:
        df = pd.DataFrame({"x": [1]})
        sql = loader._generate_create_table_sql(df, "my_events")
        assert "my_events" in sql

    def test_columns_are_backtick_quoted(self, loader: DataLoader) -> None:
        # Backticks let column names contain reserved words and
        # punctuation. The generator must use them unconditionally.
        df = pd.DataFrame({"order": [1], "select": ["x"]})
        sql = loader._generate_create_table_sql(df, "t")
        assert "`order`" in sql
        assert "`select`" in sql


class TestMixedSchemas:
    def test_multi_column_schema_emits_each_column(self, loader: DataLoader) -> None:
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "amount": [1.5, 2.5, 3.5],
                "active": [True, False, True],
                "name": ["a", "b", "c"],
            }
        )
        sql = loader._generate_create_table_sql(df, "t")
        assert "`id` UInt64" in sql
        assert "`amount` Float64" in sql
        assert "`active` Bool" in sql
        assert "`name` String" in sql

    def test_empty_dataframe_emits_a_table_with_no_columns(
        self, loader: DataLoader
    ) -> None:
        # An empty DataFrame is a degenerate case but must not crash;
        # ClickHouse will reject the resulting CREATE TABLE itself
        # with a clearer error than a Python traceback.
        df = pd.DataFrame()
        sql = loader._generate_create_table_sql(df, "t")
        assert "CREATE TABLE IF NOT EXISTS t" in sql
