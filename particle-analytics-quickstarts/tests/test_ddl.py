"""Tests for DDL generation module."""

from observatory.ddl import DDLDialect, generate_create_table, generate_ddl
from observatory.schema import ResourceSchema


def _make_schema(
    resource_type: str = "labs",
    table_name: str = "labs",
    columns: list[str] | None = None,
    record_count: int = 111,
    is_empty: bool = False,
) -> ResourceSchema:
    if columns is None:
        columns = ["lab_id", "lab_name", "lab_value"]
    return ResourceSchema(
        resource_type=resource_type,
        table_name=table_name,
        columns=columns,
        record_count=record_count,
        is_empty=is_empty,
    )


class TestDDLDialectEnum:
    def test_duckdb_value(self):
        assert DDLDialect.DUCKDB == "duckdb"

    def test_postgres_value(self):
        assert DDLDialect.POSTGRES == "postgres"

    def test_bigquery_value(self):
        assert DDLDialect.BIGQUERY == "bigquery"


class TestGenerateCreateTablePostgres:
    def test_basic_create_table(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "postgres")
        assert "CREATE TABLE IF NOT EXISTS labs (" in sql
        assert '"lab_id" TEXT' in sql
        assert '"lab_name" TEXT' in sql
        assert '"lab_value" TEXT' in sql
        assert sql.rstrip().endswith(");")

    def test_column_count(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "postgres")
        assert sql.count("TEXT") == 3

    def test_header_comment(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "postgres")
        assert "-- labs: 111 records, 3 columns" in sql


class TestGenerateCreateTableBigQuery:
    def test_basic_create_table(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "bigquery")
        assert "CREATE TABLE IF NOT EXISTS labs (" in sql
        assert "`lab_id` STRING" in sql
        assert "`lab_name` STRING" in sql
        assert "`lab_value` STRING" in sql
        assert sql.rstrip().endswith(");")

    def test_column_count(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "bigquery")
        assert sql.count("STRING") == 3


class TestGenerateCreateTableDuckDB:
    def test_basic_create_table(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "duckdb")
        assert "CREATE TABLE IF NOT EXISTS labs (" in sql
        assert '"lab_id" TEXT' in sql
        assert '"lab_name" TEXT' in sql
        assert '"lab_value" TEXT' in sql
        assert sql.rstrip().endswith(");")

    def test_column_count(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "duckdb")
        assert sql.count("TEXT") == 3

    def test_header_comment(self):
        schema = _make_schema()
        sql = generate_create_table(schema, "duckdb")
        assert "-- labs: 111 records, 3 columns" in sql


class TestGenerateCreateTableEmpty:
    def test_commented_out_placeholder(self):
        schema = _make_schema(
            resource_type="allergies",
            table_name="allergies",
            columns=[],
            record_count=0,
            is_empty=True,
        )
        sql = generate_create_table(schema, "postgres")
        assert "-- Table: allergies" in sql
        assert "-- No records found in sample data" in sql
        assert "-- CREATE TABLE allergies ();" in sql
        # Should NOT have an actual CREATE TABLE (only commented one)
        assert "CREATE TABLE IF NOT EXISTS" not in sql


class TestGenerateDDLMultipleTables:
    def test_all_tables_present(self):
        schemas = [
            _make_schema(resource_type="labs", table_name="labs"),
            _make_schema(
                resource_type="allergies",
                table_name="allergies",
                columns=[],
                record_count=0,
                is_empty=True,
            ),
            _make_schema(
                resource_type="patients",
                table_name="patients",
                columns=["patient_id", "name"],
                record_count=50,
            ),
        ]
        sql = generate_ddl(schemas, "postgres")
        assert "CREATE TABLE IF NOT EXISTS labs" in sql
        assert "-- Table: allergies" in sql
        assert "CREATE TABLE IF NOT EXISTS patients" in sql


class TestReservedWordColumns:
    def test_postgres_reserved_words_quoted(self):
        schema = _make_schema(columns=["text", "type", "status", "name"])
        sql = generate_create_table(schema, "postgres")
        assert '"text" TEXT' in sql
        assert '"type" TEXT' in sql
        assert '"status" TEXT' in sql
        assert '"name" TEXT' in sql

    def test_bigquery_reserved_words_quoted(self):
        schema = _make_schema(columns=["text", "type", "status", "name"])
        sql = generate_create_table(schema, "bigquery")
        assert "`text` STRING" in sql
        assert "`type` STRING" in sql
        assert "`status` STRING" in sql
        assert "`name` STRING" in sql


class TestColumnOrderPreserved:
    def test_order_matches_input(self):
        columns = ["zebra", "alpha", "middle", "first"]
        schema = _make_schema(columns=columns)
        sql = generate_create_table(schema, "postgres")
        # Find positions of each column in the output
        positions = [sql.index(f'"{col}"') for col in columns]
        assert positions == sorted(positions), "Column order must match input order"


class TestGenerateDDLHeader:
    def test_header_contains_dialect(self):
        schemas = [_make_schema()]
        sql = generate_ddl(schemas, "postgres")
        assert "DDL for postgres" in sql

    def test_header_contains_duckdb_dialect(self):
        schemas = [_make_schema()]
        sql = generate_ddl(schemas, "duckdb")
        assert "DDL for duckdb" in sql

    def test_header_contains_bigquery_dialect(self):
        schemas = [_make_schema()]
        sql = generate_ddl(schemas, "bigquery")
        assert "DDL for bigquery" in sql

    def test_header_contains_resource_count(self):
        schemas = [
            _make_schema(),
            _make_schema(
                resource_type="allergies",
                table_name="allergies",
                columns=[],
                record_count=0,
                is_empty=True,
            ),
        ]
        sql = generate_ddl(schemas, "postgres")
        assert "2 total" in sql
        assert "1 with data" in sql
        assert "1 empty" in sql

    def test_header_contains_elt_note(self):
        schemas = [_make_schema()]
        sql = generate_ddl(schemas, "postgres")
        assert "ELT approach" in sql

    def test_header_contains_generated_timestamp(self):
        schemas = [_make_schema()]
        sql = generate_ddl(schemas, "postgres")
        assert "Generated:" in sql
