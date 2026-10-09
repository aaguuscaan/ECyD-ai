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
    auth._attempts.clear()
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
            if "PEDIDO DE CAMBIOS" in messages[-1]["content"]:
                yield "\n\n## Qué cambié\n- Lo acorté a 45 minutos."

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


def test_ajustar_encuentro(client):
    from app import assistant
    c = client
    register(c, "agus@x.com", "Agus")
    team = c.get("/api/teams").json()[0]
    body = {"team_id": team["id"], "tema": "La amistad", "fichas": [], "duracion": "1 h"}
    with c.stream("POST", "/api/encuentros/generar", json=body) as r:
        enc = next(e for e in (json.loads(l[5:]) for l in r.iter_lines() if l.startswith("data:"))
                   if e["type"] == "done")["encuentro"]
    llm = assistant._assistant.llm
    llm.calls.clear()
    editada = enc["propuesta"] + "\n\nNota del responsable"
    with c.stream("POST", f"/api/encuentros/{enc['id']}/ajustar",
                  json={"instruccion": "Hacelo más corto, 45 minutos", "propuesta": editada}) as r:
        evs = [json.loads(l[5:]) for l in r.iter_lines() if l.startswith("data:")]
    done = next(e for e in evs if e["type"] == "done")["encuentro"]
    prompt = llm.calls[-1][-1]["content"]
    assert "Hacelo más corto, 45 minutos" in prompt and "Nota del responsable" in prompt  # usa la versión editada
    assert llm.calls[-1][0]["content"].startswith("Sos el Asistente ECyD")
    assert done["meta"]["ajustes"][-1]["instruccion"] == "Hacelo más corto, 45 minutos"
    assert done["meta"]["version_anterior"] == editada
    assert "Qué cambié" not in done["propuesta"] and "45 minutos" in done["meta"]["ajustes"][-1]["cambios"]
    # otro responsable no puede ajustar
    c2 = TestClient(c.app)
    register(c2, "otro@x.com", "Otro")
    assert c2.post(f"/api/encuentros/{enc['id']}/ajustar", json={"instruccion": "x y"}).status_code == 404


def test_comunidades_y_permisos(client):
    c = client
    register(c, "coord@x.com", "Coordi")
    resp = TestClient(c.app); register(resp, "resp@x.com", "Resp")
    otro = TestClient(c.app); register(otro, "otro@x.com", "Otro")
    ajeno = TestClient(c.app); register(ajeno, "ajeno@x.com", "Ajeno")

    com = c.post("/api/comunidades", json={"nombre": "ECyD Mano Amiga", "lugar": "Pilar"}).json()
    assert com["rol"] == "coordinador" and len(com["codigo"]) == 9
    assert resp.post("/api/comunidades/unirse", json={"codigo": "XXXX-XXXX"}).status_code == 404
    j = resp.post("/api/comunidades/unirse", json={"codigo": com["codigo"].lower().replace("-", "")}).json()
    assert j["rol"] == "responsable" and "codigo" not in j        # solo la coordinación ve el código
    otro.post("/api/comunidades/unirse", json={"codigo": com["codigo"]})
    ids = {m["nombre"]: m["user_id"] for m in c.get(f"/api/comunidades/{com['id']}").json()["miembros"]}

    # la coordinación crea un equipo de etapa 2 con dos co-responsables
    t = c.post(f"/api/comunidades/{com['id']}/equipos",
               json={"nombre": "Etapa 2 · varones", "etapa": 2, "responsables": [ids["Resp"], ids["Otro"]]}).json()
    assert t["perfil"]["etapa"] == "Etapa 2" and t["perfil"]["edades"] == "12-13 años"
    assert {r["nombre"] for r in t["responsables"]} == {"Resp", "Otro"}
    # no se puede asignar a alguien de afuera
    assert c.put(f"/api/comunidades/{com['id']}/equipos/{t['id']}",
                 json={"responsables": [ids["Resp"], "zzz"]}).status_code == 400

    # los co-responsables lo ven y comparten memoria y encuentros
    assert [x["id"] for x in resp.get("/api/teams").json()] == [t["id"]]
    resp.post(f"/api/teams/{t['id']}/memories", json={"texto": "Juan está pasando un momento difícil"})
    assert len(otro.get(f"/api/teams/{t['id']}/memories").json()) == 1
    enc = resp.post("/api/encuentros", json={"team_id": t["id"], "titulo": "La amistad", "fecha": "2026-10-20",
                                            "propuesta": "# La amistad", "observaciones": "Juan no vino"}).json()
    assert [e["id"] for e in otro.get("/api/encuentros").json()] == [enc["id"]]
    assert otro.put(f"/api/encuentros/{enc['id']}", json={"estado": "planificado"}).status_code == 200

    # la coordinación ve la planificación pero no la memoria ni las observaciones
    assert t["id"] not in [x["id"] for x in c.get("/api/teams").json()]
    assert c.get(f"/api/teams/{t['id']}/memories").status_code == 404
    e = c.get(f"/api/encuentros/{enc['id']}").json()
    assert e["solo_lectura"] and e["observaciones"] == "" and e["propuesta"] == "# La amistad"
    assert c.put(f"/api/encuentros/{enc['id']}", json={"estado": "realizado"}).status_code == 404
    panel = c.get(f"/api/comunidades/{com['id']}", params={"mes": "2026-10"}).json()
    eq = panel["equipos"][0]
    assert eq["etapa"] == 2 and eq["encuentros_mes"][0]["titulo"] == "La amistad" and eq["programa_mes"]
    assert panel["resumen"]["con_plan"] == 1 and "email" in panel["miembros"][0]
    assert "email" not in resp.get(f"/api/comunidades/{com['id']}").json()["miembros"][0]

    # PDF: el responsable lo baja con lo que tiene en pantalla; la coordinación, sin observaciones
    r = resp.post(f"/api/encuentros/{enc['id']}/pdf", json={"propuesta": "# La amistad\n\n## Despertar\n- Juego [F1]"})
    assert r.status_code == 200 and r.content.startswith(b"%PDF") and "la-amistad.pdf" in r.headers["content-disposition"]
    assert c.post(f"/api/encuentros/{enc['id']}/pdf", json={}).content.startswith(b"%PDF")
    assert ajeno.post(f"/api/encuentros/{enc['id']}/pdf", json={}).status_code == 404

    # alguien de afuera no ve nada
    assert ajeno.get(f"/api/comunidades/{com['id']}").status_code == 404
    assert ajeno.get(f"/api/encuentros/{enc['id']}").status_code == 404
    assert ajeno.get(f"/api/teams/{t['id']}/memories").status_code == 404

    # un responsable que crea un equipo queda como su responsable (no puede asignar a otros)
    t2 = resp.post(f"/api/comunidades/{com['id']}/equipos",
                   json={"nombre": "Etapa 1", "etapa": 1, "responsables": [ids["Otro"]]}).json()
    assert [r["nombre"] for r in t2["responsables"]] == ["Resp"]

    # mover un equipo personal a la comunidad
    p = ajeno.post("/api/teams", json={"nombre": "Mi equipo"}).json()
    assert ajeno.post(f"/api/teams/{p['id']}/comunidad", json={"community_id": com["id"]}).status_code == 404
    ajeno.post("/api/comunidades/unirse", json={"codigo": com["codigo"]})
    m = ajeno.post(f"/api/teams/{p['id']}/comunidad", json={"community_id": com["id"]}).json()
    assert m["comunidad"]["nombre"] == "ECyD Mano Amiga" and [r["nombre"] for r in m["responsables"]] == ["Ajeno"]

    # roles: no puede quedar sin coordinador; quitar a alguien lo saca de sus equipos
    assert c.delete(f"/api/comunidades/{com['id']}/miembros/{ids['Coordi']}").status_code == 400
    assert resp.delete(f"/api/comunidades/{com['id']}/miembros/{ids['Otro']}").status_code == 403
    assert c.delete(f"/api/comunidades/{com['id']}/miembros/{ids['Otro']}").json()["ok"]
    assert otro.get("/api/teams").json() == []
    assert c.put(f"/api/comunidades/{com['id']}/miembros/{ids['Resp']}", json={"rol": "coordinador"}).json()["ok"]
    assert "codigo" in resp.get("/api/comunidades").json()[0]
