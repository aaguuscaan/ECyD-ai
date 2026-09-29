"""Pruebas sin red: embeddings y LLM simulados.  python -m pytest tests -q"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.memory import MemoryStore
from app.retrieval import Retriever
from app.assistant import Assistant


class FakeLLM:
    provider, model = "fake", "fake"
    def __init__(self): self.calls = []
    def stream(self, messages, **kw):
        self.calls.append(messages)
        yield "El material ECyD plantea que el equipo es lugar de amistad [F1]. "
        yield "Como propuesta práctica, podrías…"
    def complete(self, messages, **kw):
        return json.dumps({"nuevas": [{"texto": "El equipo tiene 8 chicos de 2da etapa", "categoria": "equipo"}],
                           "actualizar": [], "olvidar": [], "resumen_conversacion": "Se habló del clima del equipo."})


def make(tmp_path):
    R = Retriever(embed_fn=None)
    R._embed_fn = lambda t: R.chunk_vectors[5:6]
    return Assistant(store=MemoryStore(tmp_path / "m.db"), retriever=R, llm=FakeLLM())


def test_flow(tmp_path):
    a = make(tmp_path)
    team = a.store.create_team("Leones", {"etapa": "2da etapa", "edades": "12-13"})
    a.store.add_memory(team["id"], "Juan está más callado últimamente", "adolescente")
    evs = list(a.stream("¿Cómo mejorar el clima del equipo?", None, team["id"]))
    types = [e["type"] for e in evs]
    assert types[0] == "meta" and "done" in types and types[-1] == "memory"
    conv = evs[0]["conversation"]
    msgs = a.store.get_messages(conv["id"])
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[1]["sources"][0]["citada"] is True
    sent = a.llm.calls[0]
    assert sent[0]["role"] == "system" and "ASISTENTE FORMATIVO" in sent[0]["content"]
    assert "Juan está más callado" in sent[-1]["content"] and "[F1]" in sent[-1]["content"]
    assert "Etapa del ECyD: 2da etapa" in sent[-1]["content"]
    mem = a.store.list_memories(team["id"])
    assert any(m["origen"] == "auto" for m in mem)
    assert a.store.get_conversation(conv["id"])["notas"].startswith("Se habló")
    # segunda vuelta: el historial viaja como mensajes
    list(a.stream("¿y en 20 minutos?", conv["id"], team["id"]))
    sent2 = a.llm.calls[1]
    assert [m["role"] for m in sent2] == ["system", "user", "assistant", "user"]
    assert "Se habló del clima" in sent2[-1]["content"]
    # persistencia: otro store sobre el mismo archivo
    s2 = MemoryStore(tmp_path / "m.db")
    assert len(s2.get_messages(conv["id"])) == 4
    # borrar equipo borra memoria y conversaciones
    s2.delete_team(team["id"])
    assert s2.list_memories(team["id"]) == [] and s2.get_conversation(conv["id"]) is None


def test_no_team(tmp_path):
    a = make(tmp_path)
    evs = list(a.stream("¿Qué es el ECyD?"))
    assert evs[-1]["type"] == "memory" and evs[-1]["added"] == []


def test_index_consistency():
    R = Retriever(embed_fn=lambda t: np.ones((1, 384), dtype="float32"))
    assert len(R.chunks) == R.chunk_index.ntotal
    assert all(c["doc_id"] in R.doc_by_id for c in R.chunks)


def test_retry_when_request_too_large(tmp_path):
    from app.llm import RequestTooLarge

    class TightLLM(FakeLLM):
        def __init__(self):
            super().__init__(); self.sizes = []
        def stream(self, messages, **kw):
            size = sum(len(m["content"]) for m in messages)
            self.sizes.append((size, kw.get("max_tokens")))
            if len(self.sizes) == 1:
                raise RequestTooLarge("Error code: 413 - Request too large")
            yield "Respuesta corta [F1]"

    a = make(tmp_path)
    a._llm = TightLLM()
    evs = list(a.stream("¿Cómo preparo la reunión?"))
    assert any(e["type"] == "done" for e in evs)
    (s1, _), (s2, _) = a.llm.sizes
    assert s2 < s1  # segundo intento con menos contexto


def test_budget_respects_tpm(tmp_path):
    from app.config import settings
    a = make(tmp_path)
    ctx = a.prepare("x " * 10, None, None)
    used = sum(a.estimate_tokens(m["content"]) for m in ctx["messages"])
    assert used + ctx["max_tokens"] <= settings.token_budget
