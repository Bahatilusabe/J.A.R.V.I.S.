from backend.core.pasm.tgnn_model import TGNNModel


def test_tgnn_fallback_empty():
    m = TGNNModel()
    res = m.predict({})
    assert isinstance(res, dict)
    assert "score" in res


def test_tgnn_fallback_graph():
    m = TGNNModel()
    graph = {
        "nodes": [
            {"id": 1, "features": [[0.1, 0.2], [0.2, 0.3]]},
            {"id": 2, "features": [[0.0, 0.0]]},
        ],
        "edges": [[1,2]]
    }
    res = m.predict(graph)
    assert res["score"] >= 0.0
    assert res["details"]["nodes"] == 2
