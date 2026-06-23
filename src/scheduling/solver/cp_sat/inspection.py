import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, cast

from ortools.sat.python import cp_model


class _NamedProto(Protocol):
    name: str


class _CpModelProtoView(Protocol):
    variables: Sequence[object]
    constraints: Sequence[_NamedProto]


@dataclass(frozen=True, slots=True)
class CpSatInspection:
    proto_variable_count: int
    proto_constraint_count: int
    constraint_type_counts: dict[str, int]
    constraint_names: tuple[str, ...]
    unnamed_constraint_count: int
    model_stats: str
    validation_error: str | None

    @property
    def is_valid(self) -> bool:
        return self.validation_error is None


def inspect_cp_sat_model(*, model: cp_model.CpModel) -> CpSatInspection:
    """Inspect a built CP-SAT model without logging or mutating it.

    OR-Tools exposes CP-SAT protos through cp_model_helper pybind types.
    Those objects do not expose normal protobuf reflection methods like
    WhichOneof(), so constraint type counts are derived from model_stats().
    """
    proto = _model_proto_view(model)
    model_stats = model.model_stats()

    constraint_names = tuple(_constraint_name(constraint) for constraint in proto.constraints)

    return CpSatInspection(
        proto_variable_count=len(proto.variables),
        proto_constraint_count=len(proto.constraints),
        constraint_type_counts=_constraint_type_counts_from_model_stats(model_stats),
        constraint_names=constraint_names,
        unnamed_constraint_count=sum(name == "<unnamed>" for name in constraint_names),
        model_stats=model_stats,
        validation_error=model.validate() or None,
    )


def _model_proto_view(model: cp_model.CpModel) -> _CpModelProtoView:
    raw_proto: object = model.proto
    return cast(_CpModelProtoView, raw_proto)


def _constraint_name(constraint: _NamedProto) -> str:
    return constraint.name or "<unnamed>"


def _constraint_type_counts_from_model_stats(
    model_stats: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for line in model_stats.splitlines():
        match = re.compile(r"^\s*#(k[A-Za-z0-9_]+):\s+([0-9']+)").match(line)
        if match is None:
            continue

        constraint_type, count = match.groups()
        counts[constraint_type] = int(count.replace("'", ""))

    return counts
