import re

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.query_builder import build_expert_query


def test_build_query_includes_all_selected_filters():
    q = build_expert_query(
        full_text="Krankenhaus",
        notice_type="cn-standard",
        cpv="45000000",
        place_of_performance="DE1",
        contract_type="works",
        value_min=100000,
        value_max=500000,
        pub_date_from="20250101",
        pub_date_to="20250131",
        deadline_from="20250201",
        deadline_to="20250215",
        buyer_name="Stadt Kassel",
        buyer_town="Kassel",
        buyer_country="DE",
        buyer_type="ministry",
        authority_activity="education",
    )

    assert 'FT~("Krankenhaus")' in q
    assert 'NT="cn-standard"' in q
    assert 'PC="45000000"' in q
    assert 'RC="DE1"' in q
    assert 'NC="works"' in q
    assert 'VR=[100000 TO 500000]' in q
    assert 'PD>=20250101' in q and 'PD<=20250131' in q
    assert 'DD>=20250201' in q and 'DD<=20250215' in q
    assert 'AU~("Stadt Kassel")' in q
    assert 'buyer-town~("Kassel")' in q
    assert 'CY="DE"' in q
    assert 'buyer-type="ministry"' in q
    assert 'authority-main-activity="education"' in q


def test_value_range_variants():
    q_min_only = build_expert_query(value_min=123)
    assert 'VR>=' in q_min_only and '123' in q_min_only
    assert 'VR<=' not in q_min_only and 'TO' not in q_min_only

    q_max_only = build_expert_query(value_max=456)
    assert 'VR<=' in q_max_only and '456' in q_max_only
    assert 'VR>=' not in q_max_only and 'TO' not in q_max_only

    q_between = build_expert_query(value_min=10, value_max=20)
    assert 'VR=[10 TO 20]' in q_between
