"""API: cuentas, aislamiento entre responsables, encuentros y programa."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app import main, memory, assistant, auth
    from app.memory import MemoryStore
    from app.retrieval import Retriever
    from tests.test_backend import FakeLLM
    monkeypatch.setattr(memory.settings, "app_password", "codigo-ecyd")
    store = MemoryStore(tmp_path / "m.db")
    # datos "viejos" sin dueño (antes de que existieran cuentas)
    old = store.create_team("Equipo viejo", {"etapa": "1ra etapa"})
    store.create_conversation(old["id"], "Charla vieja")
    monkeypatch.setattr(memory, "_store", store)
    R = Retriever(embed_fn=None)
    R._embed_fn = lambda t: R.chunk_vectors[5:6]

    class EncLLM(FakeLLM):
        def stream(self, messages, **kw):
            self.calls.append(messages)
            yield "# Encuentro sobre la amistad\n\n## Despertar\nSegún el programa [F1]…"

    assistant._assistant = assistant.Assistant(store=store, retriever=R, llm=EncLLM())
    main._state.update(rag="listo")
    monkeypatch.setattr(main, "get_retriever", lambda: R)
    return TestClient(main.app)


def register(c, email, nombre="Resp", codigo="codigo-ecyd"):
    return c.post("/api/register", json={"email": email, "password": "clave-segura", "nombre": nombre,
                                         "codigo": codigo})


def test_flujo_completo(client):
    c = client
    assert c.get("/api/teams").status_code == 401
    assert register(c, "a@x.com", codigo="mal").status_code == 403
    r = register(c, "agus@x.com", "Agus")
    assert r.status_code == 200 and r.json()["datos_asignados"]["equipos"] == 1   # adopta lo existente
    teams = c.get("/api/teams").json()
    assert [t["nombre"] for t in teams] == ["Equipo viejo"]
    assert len(c.get("/api/conversations").json()) == 1

    # programa
    p = c.get("/api/programa", params={"team_id": teams[0]["id"], "fecha": "2026-10-05"}).json()
    assert p["disponible"] and p["etapa"] == 1 and p["fichas"]
    assert set(c.get("/api/programas").json()["etapas"]) == {"1", "2", "3", "4"}

    # generar encuentro (stream) → queda guardado como borrador
    ficha = p["fichas"][0]["doc_id"]
    body = {"team_id": teams[0]["id"], "tema": "La amistad", "origen_tema": "programa", "fichas": [ficha],
            "fecha": "2026-10-10", "cantidad": 8, "composicion": "mixto", "duracion": "1 h 30 min"}
    with c.stream("POST", "/api/encuentros/generar", json=body) as r:
        evs = [json.loads(l[5:]) for l in r.iter_lines() if l.startswith("data:")]
    done = next(e for e in evs if e["type"] == "done")
    enc = done["encuentro"]
    assert enc["titulo"] == "Encuentro sobre la amistad" and enc["etapa"] == 1
    assert enc["fichas"][0]["doc_id"] == ficha and enc["cantidad"] == 8 and enc["composicion"] == "mixto"
    prompt = client.app  # noqa
    # editar y guardar observaciones
    r = c.put(f"/api/encuentros/{enc['id']}", json={"observaciones": "Funcionó bien", "estado": "realizado"})
    assert r.json()["estado"] == "realizado"
    # segundo encuentro con la misma ficha → aviso de repetición
    with c.stream("POST", "/api/encuentros/generar", json=body) as r:
        evs = [json.loads(l[5:]) for l in r.iter_lines() if l.startswith("data:")]
    assert "ya usó esta ficha" in evs[0]["aviso"]
    assert len(c.get("/api/encuentros").json()) == 2

    # otro responsable no ve nada de Agus
    c2 = TestClient(client.app)
    assert register(c2, "otro@x.com", "Otro").json()["datos_asignados"] == {}
    assert c2.get("/api/teams").json() == []
    assert c2.get("/api/encuentros").json() == []
    assert c2.get(f"/api/encuentros/{enc['id']}").status_code == 404
    assert c2.get(f"/api/teams/{teams[0]['id']}/memories").status_code == 404
    assert c2.post("/api/chat", json={"message": "hola", "team_id": teams[0]["id"]}).status_code == 404

    # login / logout
    c.post("/api/logout")
    c.cookies.clear()
    assert c.get("/api/teams").status_code == 401
    assert c.post("/api/login", json={"email": "agus@x.com", "password": "otra"}).status_code == 401
    assert c.post("/api/login", json={"email": "AGUS@x.com", "password": "clave-segura"}).status_code == 200
    assert len(c.get("/api/teams").json()) == 1


def test_prompt_de_encuentro_incluye_contexto(client):
    from app import assistant
    c = client
    register(c, "agus@x.com", "Agus")
    team = c.get("/api/teams").json()[0]
    c.put(f"/api/teams/{team['id']}", json={"perfil": {"etapa": "1ra etapa", "cantidad_chicos": "5",
                                                         "composicion": "solo chicas"}})
    with c.stream("POST", "/api/encuentros/generar", json={"team_id": team["id"], "tema": "amistad"}) as r:
        list(r.iter_lines())
    sent = assistant._assistant.llm.calls[-1][-1]["content"]
    assert "PROGRAMA DE LA ETAPA" in sent and "Primera etapa" in sent
    assert "solo chicas" in sent and "Cantidad de chicos: 5" in sent
    assert "PREPARAR UN ENCUENTRO" in sent
