from src.scoring_2026 import (
    pitstop_points,
    score_qualifying_constructor,
    score_qualifying_driver,
    score_race_constructor,
    score_race_driver,
    score_sprint_driver,
    transfer_penalty,
)


def test_qualifying_p1_to_p10_points():
    assert score_qualifying_driver(1).total == 10
    assert score_qualifying_driver(10).total == 1
    assert score_qualifying_driver(11).total == 0


def test_qualifying_nc_penalty():
    assert score_qualifying_driver(5, status="NC").total == 1


def test_qualifying_dsq_penalty():
    assert score_qualifying_driver(3, status="DSQ").total == 3


def test_constructor_q2_q3_bonus_logic_both_q3():
    d1 = score_qualifying_driver(1)
    d2 = score_qualifying_driver(2)
    res = score_qualifying_constructor(d1, d2, q2_a=True, q2_b=True, q3_a=True, q3_b=True)
    assert res.breakdown["q_bonus"] == 10


def test_constructor_q2_q3_bonus_logic_neither_q2():
    d1 = score_qualifying_driver(12)
    d2 = score_qualifying_driver(14)
    res = score_qualifying_constructor(d1, d2, q2_a=False, q2_b=False, q3_a=False, q3_b=False)
    assert res.breakdown["q_bonus"] == -1


def test_sprint_dnf_penalty():
    res = score_sprint_driver(start_pos=5, finish_pos=10, overtakes=2, status="DNF")
    assert res.breakdown["status_penalty"] == -10


def test_race_dnf_penalty():
    res = score_race_driver(start_pos=5, finish_pos=10, overtakes=2, status="DNF")
    assert res.breakdown["status_penalty"] == -20


def test_pitstop_bucket_fastest_world_record_bonus():
    pit = pitstop_points(1.95, fastest_pitstop=True, world_record_threshold=1.80, is_world_record=True)
    assert pit.breakdown["bucket"] == 20
    assert pit.breakdown["fastest_pitstop"] == 5
    assert pit.breakdown["world_record"] == 15


def test_race_constructor_with_pitstop_and_dsq():
    pit = pitstop_points(2.10, fastest_pitstop=False, world_record_threshold=1.80)
    res = score_race_constructor(20, 15, pit, driver_a_dsq=True)
    assert res.total == (35 + pit.total - 20)


def test_transfer_penalty_additional_transfers():
    res = transfer_penalty(transfers_used=4, free_transfers=2)
    assert res.total == -20


def test_missing_overtakes_component_defaults_to_zero():
    res = score_race_driver(start_pos=10, finish_pos=8, overtakes=None, fastest_lap=False, status="OK")
    assert "overtakes" in res.missing_components
    assert res.breakdown["overtakes"] == 0
