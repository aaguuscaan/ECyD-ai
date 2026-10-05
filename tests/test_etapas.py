"""La búsqueda respeta la progresión de etapas."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval import Retriever, etapas_mencionadas, relacion_etapa
from app import programas


def _retriever_with_query_from(etapa_fuente):
    R = Retriever(embed_fn=None)
    i = next(i for i, c in enumerate(R.chunks) if c.get("categoria") == "ficha" and c["etapas"] == [etapa_fuente])
    R._embed_fn = lambda t: R.chunk_vectors[i:i + 1]
    return R


def test_no_recomienda_etapas_posteriores():
    R = _retriever_with_query_from(4)        # consulta "parecida" a una ficha de 4ª etapa
    hits = R.search("consulta", etapa=1)      # pero el equipo es de 1ª etapa
    etapas = [e for h in hits for e in h.etapas]
    assert 3 not in etapas and 4 not in etapas
    assert sum(1 for h in hits if h.relacion == "siguiente") <= 2


def test_prioriza_etapa_actual():
    R = _retriever_with_query_from(2)
    hits = R.search("consulta", etapa=2)
    assert hits[0].relacion in ("actual", "general")
    assert any(h.relacion == "actual" for h in hits)


def test_etapa_explicita_en_la_consulta():
    assert etapas_mencionadas("ideas para 3ra etapa y la cuarta etapa") == {3, 4}
    assert relacion_etapa([4], 1, {4}) == "explicita"
    assert relacion_etapa([4], 1, set()) == "fuera"
    assert relacion_etapa([], 1, set()) == "general"


def test_ficha_elegida_siempre_entra():
    R = _retriever_with_query_from(1)
    doc4 = next(c["doc_id"] for c in R.chunks if c["etapas"] == [4] and c.get("categoria") == "ficha")
    hits = R.search("consulta", etapa=1, focus_docs=[doc4])
    assert any(h.doc_id == doc4 and h.relacion == "foco" for h in hits)


def test_programa_y_temas_por_mes():
    s = programas.sugerencias(1, date(2026, 10, 5))
    assert s["disponible"] and s["edades"] == "11-12 años"
    assert s["fichas"] and all("doc_id" in f for f in s["fichas"])
    assert "obediencia" in s["resumen"]["virtud"]
    lit = programas.sugerencias(2, date(2026, 11, 15))["liturgico"]
    assert lit and lit["clave"] == "cristo_rey"
    assert "receso" in programas.contexto_programa(3, date(2027, 2, 1))
