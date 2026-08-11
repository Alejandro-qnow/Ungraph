"""Integration: oleada-2 H_I mínima (none vs ner) si hay Neo4j + spaCy.

Se omite sin credenciales o sin modelo spaCy. No marca D3 del plan; solo valida cableado.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DOMAIN = Path(__file__).resolve().parents[2] / "benchmarks" / "domains" / "knowledge_graphs"

pytestmark = pytest.mark.integration


@pytest.fixture
def spacy_en_available():
    try:
        import spacy

        spacy.load("en_core_web_sm")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"spaCy en_core_web_sm no disponible: {exc}")


def test_hi_wave_online_none_vs_ner(neo4j_clean_bundle, spacy_en_available):
    from ungraph.evaluation.domain_pipeline import hi_wave_configs, run_architecture_online

    corpus = DOMAIN / "corpus" / "kg_survey.md"
    gold = DOMAIN / "gold.json"
    if not corpus.exists() or not gold.exists():
        pytest.skip("dominio knowledge_graphs incompleto")

    db = neo4j_clean_bundle["database"]
    configs = hi_wave_configs(chunk_size=512, chunk_overlap=50, top_k=3)
    runs = []
    for cfg in configs:
        run, _ = run_architecture_online(
            domain="knowledge_graphs",
            architecture=cfg,
            corpus_paths=[corpus],
            gold_path=gold,
            database=db,
            design_id="hi-wave-integration",
            design_row_id=str(cfg["design_row_id"]),
            wipe=True,
            setup_indexes=True,
        )
        runs.append(run)
        sc = run.scorecard or {}
        assert "transform" in sc and "rag_qa" in sc
        assert sc["rag_qa"].get("eval_mode") == "topk_retrieved" or "answer_correctness" in sc["rag_qa"]

    by_inf = {r.architecture["inference"]: r for r in runs}
    assert "none" in by_inf and "ner" in by_inf
    er_none = float(by_inf["none"].scorecard["transform"].get("entity_recall") or 0)
    er_ner = float(by_inf["ner"].scorecard["transform"].get("entity_recall") or 0)
    # Con gold alineado al corpus, ner debe materializar al menos alguna Entity
    assert er_ner >= er_none
    assert by_inf["none"].scorecard["transform"].get("n_graph_entities", 0) == 0 or er_none == 0.0
