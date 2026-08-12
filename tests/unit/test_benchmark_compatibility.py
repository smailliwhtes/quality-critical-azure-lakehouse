from qcal.benchmark import _query_partition_count, _query_plan_text, _runtime_conf_value


class _SparkConnectLikeConf:
    def get(self, key: str, default: str | None = None) -> str:
        if default is None:
            raise RuntimeError(f"SQL_CONF_NOT_FOUND: {key}")
        return default


class _SparkConnectLikeSession:
    conf = _SparkConnectLikeConf()


class _SparkConnectLikeQuery:
    def _explain_string(self, *, mode: str) -> str:
        assert mode == "formatted"
        return "BroadcastHashJoin [formatted plan]"

    @property
    def rdd(self):
        raise RuntimeError("RDD is not supported with Spark Connect")


def test_runtime_config_read_supplies_a_default_for_spark_connect() -> None:
    assert _runtime_conf_value(
        _SparkConnectLikeSession(), "spark.sql.adaptive.enabled", "true"
    ) == "true"


def test_plan_and_partition_helpers_degrade_truthfully_on_spark_connect() -> None:
    query = _SparkConnectLikeQuery()

    assert _query_plan_text(query) == "BroadcastHashJoin [formatted plan]"
    assert _query_partition_count(query) is None
