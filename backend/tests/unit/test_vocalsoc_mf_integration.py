def test_parse_intent_with_fake_mf_pipeline():
    from backend.core.vocalsoc import nlu_processor as nlu

    text = "Investigate alert for 10.0.1.23 and block 10.0.1.0/24"

    # Fake MindFormers pipeline that returns NER-like output
    def fake_mf(text_in):
        return [
            {"entity": "ip_address", "value": "10.0.1.23", "start": None, "end": None},
            {"entity": "network", "value": "10.0.1.0/24", "start": None, "end": None},
        ]

    res = nlu.parse_intent(text, mf_pipeline=fake_mf)
    assert res.intent is not None
    # should include both ip and network entities
    types = {e["entity"] for e in res.entities}
    assert "ip_address" in types
    assert "network" in types
