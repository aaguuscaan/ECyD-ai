"""Prueba SupabaseMemoryStore contra un PostgREST simulado (sin red)."""
import itertools, json, sys
from pathlib import Path
from urllib.parse import parse_qsl
import httpx
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.memory import SupabaseMemoryStore

SECRET = "s3cr3t"


class FakePostgrest:
    def __init__(self):
        self.t = {"teams": [], "memories": [], "conversations": [], "messages": []}
        self.ids = itertools.count(1)

    def __call__(self, req: httpx.Request):
        if req.headers.get("x-ecyd-key") != SECRET:
            return httpx.Response(200, json=[])  # RLS: no ve nada
        table = req.url.path.rsplit("/", 1)[-1]
        params = dict(parse_qsl(req.url.query.decode()))
        rows = self.t[table]
        flt = {k: v[3:] for k, v in params.items() if v.startswith("eq.")}
        match = lambda r: all(str(r.get(k)) == v for k, v in flt.items())
        ret = "return=representation" in req.headers.get("prefer", "")
        if req.method == "GET":
            out = [dict(r) for r in rows if match(r)]
            for part in reversed((params.get("order") or "").split(",")):
                if part:
                    col, _, d = part.partition(".")
                    out.sort(key=lambda r: (r.get(col) is None, r.get(col)), reverse=(d == "desc"))
            if "limit" in params:
                out = out[: int(params["limit"])]
            if "messages(count)" in params.get("select", ""):
                for r in out:
                    r["messages"] = [{"count": sum(1 for m in self.t["messages"] if m["conversation_id"] == r["id"])}]
            return httpx.Response(200, json=out)
        if req.method == "POST":
            row = json.loads(req.content)
            if table in ("memories", "messages"):
                row["id"] = next(self.ids)
            rows.append(row)
            return httpx.Response(201, json=[row] if ret else None)
        if req.method == "PATCH":
            patch = json.loads(req.content)
            hit = [r for r in rows if match(r)]
            for r in hit:
                r.update(patch)
            return httpx.Response(200, json=hit if ret else None)
        if req.method == "DELETE":
            hit = [r for r in rows if match(r)]
            self.t[table] = [r for r in rows if not match(r)]
            if table == "teams":  # cascada
                ids = {r["id"] for r in hit}
                self.t["memories"] = [m for m in self.t["memories"] if m["team_id"] not in ids]
                self.t["conversations"] = [c for c in self.t["conversations"] if c["team_id"] not in ids]
            return httpx.Response(200, json=hit if ret else None)


def make_store(secret=SECRET):
    s = SupabaseMemoryStore(url="https://x.supabase.co", key="sb_publishable_x", secret=secret)
    fake = FakePostgrest()
    s.http = httpx.Client(base_url=s.base, headers=dict(s.http.headers), transport=httpx.MockTransport(fake))
    return s, fake


def test_supabase_store_roundtrip():
    s, fake = make_store()
    t = s.create_team("Leones", {"etapa": "2"})
    assert s.get_team(t["id"])["perfil"]["etapa"] == "2"
    assert s.update_team(t["id"], perfil={"etapa": "3"})["perfil"]["etapa"] == "3"
    m = s.add_memory(t["id"], "Juan está callado", "adolescente")
    assert s.update_memory(m["id"], texto="Juan mejoró", team_id=t["id"])["texto"] == "Juan mejoró"
    c = s.create_conversation(t["id"], "Hola")
    s.add_message(c["id"], "user", "hola")
    s.add_message(c["id"], "assistant", "respuesta", [{"n": 1}], {"x": 1})
    s.add_message(c["id"], "user", "otra")
    assert [x["content"] for x in s.get_messages(c["id"], limit=2)] == ["respuesta", "otra"]
    assert s.list_conversations(t["id"])[0]["mensajes"] == 3
    assert s.update_conversation(c["id"], notas="resumen")["notas"] == "resumen"
    assert s.delete_memory(m["id"], t["id"]) and not s.list_memories(t["id"])
    assert s.delete_team(t["id"]) and s.get_team(t["id"]) is None


def test_supabase_wrong_secret_sees_nothing():
    s, fake = make_store()
    s.create_team("Leones")
    bad, _ = make_store(secret="otra")
    bad.http = httpx.Client(base_url=s.base, headers={**dict(s.http.headers), "x-ecyd-key": "otra"},
                            transport=httpx.MockTransport(fake))
    assert bad.list_teams() == []


def test_assistant_with_supabase_store(tmp_path):
    from tests.test_backend import FakeLLM
    from app.retrieval import Retriever
    from app.assistant import Assistant
    s, _ = make_store()
    R = Retriever(embed_fn=None)
    R._embed_fn = lambda t: R.chunk_vectors[5:6]
    a = Assistant(store=s, retriever=R, llm=FakeLLM())
    team = s.create_team("Leones", {"etapa": "2da etapa"})
    evs = list(a.stream("¿Cómo mejorar el clima del equipo?", None, team["id"]))
    assert evs[-1]["type"] == "memory" and evs[-1]["added"]
    conv = evs[0]["conversation"]
    assert len(s.get_messages(conv["id"])) == 2
    assert s.get_conversation(conv["id"])["notas"]
