from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


QUALI_POINTS = {1: 10, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1}
SPRINT_RESULT_POINTS = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
RACE_RESULT_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
PENALTY_STATUSES = {"DNF", "DSQ", "NC", "NO_TIME"}


@dataclass
class ScoreResult:
    total: int
    breakdown: dict[str, int]
    missing_components: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "breakdown": self.breakdown,
            "missing_components": self.missing_components,
        }


def _positions_delta(start: int | None, finish: int | None) -> int:
    if start is None or finish is None:
        return 0
    return start - finish


def _overtake_points(overtakes: int | None, missing: list[str]) -> int:
    if overtakes is None:
        missing.append("overtakes")
        return 0
    return overtakes


def score_qualifying_driver(position: int | None, status: str = "OK", no_time_set: bool = False) -> ScoreResult:
    status_u = status.upper()
    penalty = -5 if status_u in PENALTY_STATUSES or no_time_set else 0
    result_points = QUALI_POINTS.get(position or 0, 0)
    breakdown = {
        "result": result_points,
        "penalty": penalty,
    }
    return ScoreResult(total=result_points + penalty, breakdown=breakdown)


def _constructor_q_bonus(q2_a: bool, q2_b: bool, q3_a: bool, q3_b: bool) -> int:
    both_q3 = q3_a and q3_b
    one_q3 = q3_a ^ q3_b
    both_q2 = q2_a and q2_b
    one_q2 = q2_a ^ q2_b
    if both_q3:
        return 10
    if one_q3:
        return 5
    if both_q2:
        return 3
    if one_q2:
        return 1
    return -1


def score_qualifying_constructor(
    driver_a: ScoreResult,
    driver_b: ScoreResult,
    q2_a: bool,
    q2_b: bool,
    q3_a: bool,
    q3_b: bool,
    driver_a_dsq: bool = False,
    driver_b_dsq: bool = False,
) -> ScoreResult:
    q_bonus = _constructor_q_bonus(q2_a, q2_b, q3_a, q3_b)
    dsq_pen = (-5 if driver_a_dsq else 0) + (-5 if driver_b_dsq else 0)
    total = driver_a.total + driver_b.total + q_bonus + dsq_pen
    return ScoreResult(total=total, breakdown={"driver_sum": driver_a.total + driver_b.total, "q_bonus": q_bonus, "dsq_penalty": dsq_pen})


def score_sprint_driver(
    start_pos: int | None,
    finish_pos: int | None,
    overtakes: int | None,
    fastest_lap: bool = False,
    status: str = "OK",
) -> ScoreResult:
    missing: list[str] = []
    delta = _positions_delta(start_pos, finish_pos)
    overtake_pts = _overtake_points(overtakes, missing)
    fastest = 5 if fastest_lap else 0
    result = SPRINT_RESULT_POINTS.get(finish_pos or 0, 0)
    status_penalty = -10 if status.upper() in {"DNF", "DSQ", "NC"} else 0
    total = delta + overtake_pts + fastest + result + status_penalty
    return ScoreResult(
        total=total,
        breakdown={
            "position_delta": delta,
            "overtakes": overtake_pts,
            "fastest_lap": fastest,
            "result": result,
            "status_penalty": status_penalty,
        },
        missing_components=missing,
    )


def score_sprint_constructor(driver_a: ScoreResult, driver_b: ScoreResult, driver_a_dsq: bool = False, driver_b_dsq: bool = False) -> ScoreResult:
    dsq_pen = (-10 if driver_a_dsq else 0) + (-10 if driver_b_dsq else 0)
    total = driver_a.total + driver_b.total + dsq_pen
    return ScoreResult(total=total, breakdown={"driver_sum": driver_a.total + driver_b.total, "dsq_penalty": dsq_pen})


def pitstop_points(stop_time_seconds: float, fastest_pitstop: bool, world_record_threshold: float, is_world_record: bool = False) -> ScoreResult:
    if stop_time_seconds < 2.0:
        bucket = 20
    elif stop_time_seconds <= 2.19:
        bucket = 10
    elif stop_time_seconds <= 2.49:
        bucket = 5
    elif stop_time_seconds <= 2.99:
        bucket = 2
    else:
        bucket = 0

    fastest = 5 if fastest_pitstop else 0
    world_record = 15 if (is_world_record or stop_time_seconds <= world_record_threshold) else 0
    total = bucket + fastest + world_record
    return ScoreResult(total=total, breakdown={"bucket": bucket, "fastest_pitstop": fastest, "world_record": world_record})


def score_race_driver(
    start_pos: int | None,
    finish_pos: int | None,
    overtakes: int | None,
    fastest_lap: bool = False,
    dotd: bool = False,
    status: str = "OK",
) -> ScoreResult:
    missing: list[str] = []
    delta = _positions_delta(start_pos, finish_pos)
    overtake_pts = _overtake_points(overtakes, missing)
    fastest = 10 if fastest_lap else 0
    dotd_pts = 10 if dotd else 0
    result = RACE_RESULT_POINTS.get(finish_pos or 0, 0)
    status_penalty = -20 if status.upper() in {"DNF", "DSQ", "NC"} else 0
    total = delta + overtake_pts + fastest + dotd_pts + result + status_penalty
    return ScoreResult(
        total=total,
        breakdown={
            "position_delta": delta,
            "overtakes": overtake_pts,
            "fastest_lap": fastest,
            "dotd": dotd_pts,
            "result": result,
            "status_penalty": status_penalty,
        },
        missing_components=missing,
    )


def score_race_constructor(
    driver_a_race_ex_dotd: int,
    driver_b_race_ex_dotd: int,
    pitstop: ScoreResult,
    driver_a_dsq: bool = False,
    driver_b_dsq: bool = False,
) -> ScoreResult:
    dsq_pen = (-20 if driver_a_dsq else 0) + (-20 if driver_b_dsq else 0)
    driver_sum = driver_a_race_ex_dotd + driver_b_race_ex_dotd
    total = driver_sum + pitstop.total + dsq_pen
    return ScoreResult(
        total=total,
        breakdown={
            "driver_sum_ex_dotd": driver_sum,
            "pitstop": pitstop.total,
            "dsq_penalty": dsq_pen,
        },
    )


def transfer_penalty(transfers_used: int, free_transfers: int) -> ScoreResult:
    extra = max(0, transfers_used - free_transfers)
    penalty = -10 * extra
    return ScoreResult(total=penalty, breakdown={"extra_transfers": extra, "penalty": penalty})
