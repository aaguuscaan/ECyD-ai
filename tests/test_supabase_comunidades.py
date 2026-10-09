"""Comunidades y co-responsables en SupabaseMemoryStore, contra un PostgREST simulado
que entiende eq./in./is.null, or=(), embebidos users(...) y upserts."""
import json, re, sys
from pathlib import Path
from urllib.parse import parse_qsl
import httpx
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.memory import SupabaseMemoryStore

SECRET = "s3cr3t"


def _cond(col, expr):
    if expr.startswith("eq."):
        return lambda r: str(r.get(col)) == expr[3:]
    if expr.startswith("in.("):
        vals = set(expr[4:-1].split(","))
        return lambda r: str(r.get(col)) in vals
    if expr == "is.null":
        return lambda r: r.get(col) is None
    if expr.startswith("neq."):
        return lambda r: str(r.get(col)) != expr[4:]
    if expr.startswith("gt."):
        return lambda r: str(r.get(col)) > expr[3:]
    if expr.startswith("lt."):
        return lambda r: str(r.get(col)) < expr[3:]
    raise AssertionError(f"filtro no soportado: {col}={expr}")


class Fake:
    KEYS = {"community_members": ("community_id", "user_id"), "team_members": ("team_id", "user_id"),
            "chat_reads": ("user_id", "canal")}

    def __init__(self):
        self.t = {k: [] for k in ("users", "teams", "communities", "community_members", "team_members", "encuentros",
                                  "chat_messages", "chat_reads")}

    def __call__(self, req: httpx.Request):
        assert req.headers.get("x-ecyd-key") == SECRET
        table = req.url.path.rsplit("/", 1)[-1]
        params = dict(parse_qsl(req.url.query.decode()))
        conds = []
        for k, v in params.items():
            if k in ("select", "order", "limit", "on_conflict"):
                continue
            if k == "or":
                subs = [_cond(*p.split(".", 1)) for p in re.findall(r"\w+\.(?:n?eq\.[^,()]+|in\.\([^)]*\)|is\.null)", v[1:-1])]
                conds.append(lambda r, subs=subs: any(s(r) for s in subs))
            else:
                conds.append(_cond(k, v))
        rows = self.t[table]
        match = lambda r: all(c(r) for c in conds)
        prefer = req.headers.get("prefer", "")
        ret = "return=representation" in prefer
        if req.method == "GET":
            out = [dict(r) for r in rows if match(r)]
            for part in reversed((params.get("order") or "").split(",")):
                if part:
                    col, _, d = part.partition(".")
                    out.sort(key=lambda r: (r.get(col) is None, r.get(col)), reverse=d.startswith("desc"))
            if "limit" in params:
                out = out[: int(params["limit"])]
            sel = params.get("select", "*")
            m = re.search(r"(users|communities)\(([^)]*)\)", sel)
            if m:
                ref, cols = m.group(1), m.group(2)
                fk = "user_id" if ref == "users" else "community_id"
                for r in out:
                    tgt = next((x for x in self.t[ref] if x["id"] == r[fk]), None)
                    r[ref] = None if tgt is None else (dict(tgt) if cols == "*" else {c: tgt.get(c) for c in cols.split(",")})
            return httpx.Response(200, json=out)
        if req.method == "POST":
            body = json.loads(req.content)
            for row in body if isinstance(body, list) else [body]:
                key = self.KEYS.get(table)
                dup = next((r for r in rows if key and all(r[k] == row[k] for k in key)), None)
                if dup is not None:
                    assert "resolution=" in prefer, "duplicado sin upsert"
                    if "merge-duplicates" in prefer:
                        dup.update(row)
                else:
                    rows.append(row)
            return httpx.Response(201, json=(body if isinstance(body, list) else [body]) if ret else None)
        if req.method == "PATCH":
            patch = json.loads(req.content)
            hit = [r for r in rows if match(r)]
            for r in hit:
                r.update(patch)
            return httpx.Response(200, json=hit if ret else None)
        if req.method == "DELETE":
            hit = [r for r in rows if match(r)]
            self.t[table] = [r for r in rows if not match(r)]
            return httpx.Response(200, json=hit if ret else None)


def test_comunidades_supabase():
    fake = Fake()
    s = SupabaseMemoryStore(url="https://x.supabase.co", key="sb_publishable_x", secret=SECRET)
    s.http = httpx.Client(base_url=s.base, headers=dict(s.http.headers), transport=httpx.MockTransport(fake))
    a = s.create_user("a@x.com", "Ana", "h")
    b = s.create_user("b@x.com", "Beto", "h")
    com = s.create_community("ECyD Mano Amiga", "Pilar", a["id"])
    assert s.get_community_by_code(com["codigo"].replace("-", "").lower())["id"] == com["id"]
    s.set_community_member(com["id"], b["id"])
    s.set_community_member(com["id"], b["id"], "coordinador")         # upsert, no duplica
    mem = s.list_community_members(com["id"])
    assert [(m["nombre"], m["rol"]) for m in mem] == [("Ana", "coordinador"), ("Beto", "coordinador")]
    assert s.list_user_communities(b["id"])[0]["nombre"] == "ECyD Mano Amiga"

    t1 = s.create_team("Etapa 1", {"etapa": "Etapa 1"}, user_id=a["id"])
    t2 = s.create_team("Etapa 3", {"etapa": "Etapa 3"}, user_id=a["id"])
    for t in (t1, t2):
        s.update_team(t["id"], community_id=com["id"])
    assert {t["nombre"] for t in s.list_teams(community_id=com["id"])} == {"Etapa 1", "Etapa 3"}
    assert s.update_team(t1["id"], nombre="Etapa 1 · A")["community_id"] == com["id"]   # no se pierde
    s.set_team_members(t1["id"], [b["id"], b["id"]])
    s.add_team_member(t1["id"], b["id"])                               # ignora duplicado
    s.add_team_member(t2["id"], a["id"])
    assert s.member_team_ids(b["id"]) == [t1["id"]]
    assert [(m["team_id"], m["nombre"]) for m in s.list_team_members([t1["id"], t2["id"]])] == \
        [(t2["id"], "Ana"), (t1["id"], "Beto")]
    assert [t["id"] for t in s.list_teams(ids=[t2["id"]])] == [t2["id"]] and s.list_teams(ids=[]) == []

    e1 = s.create_encuentro(a["id"], {"team_id": t1["id"], "titulo": "Uno"})
    e2 = s.create_encuentro(b["id"], {"team_id": t2["id"], "titulo": "Dos"})
    s.create_encuentro(a["id"], {"team_id": None, "titulo": "Suelto"})
    vis = {e["titulo"] for e in s.list_encuentros(user_id=b["id"], team_ids=[t1["id"]])}
    assert vis == {"Uno", "Dos"}
    assert {e["id"] for e in s.list_encuentros(team_ids=[t1["id"], t2["id"]])} == {e1["id"], e2["id"]}

    s.remove_community_member(com["id"], b["id"])
    assert s.member_team_ids(b["id"]) == [] and len(s.list_community_members(com["id"])) == 1
    s.delete_community(com["id"])
    assert all(t["community_id"] is None for t in fake.t["teams"]) and fake.t["communities"] == []


def test_chat_supabase():
    fake = Fake()
    s = SupabaseMemoryStore(url="https://x.supabase.co", key="sb_publishable_x", secret=SECRET)
    s.http = httpx.Client(base_url=s.base, headers=dict(s.http.headers), transport=httpx.MockTransport(fake))
    a = s.create_user("a@x.com", "Ana", "h")
    b = s.create_user("b@x.com", "Beto", "h")
    m1 = s.add_chat_message("eq-t1", a["id"], "hola")
    m2 = s.add_chat_message("eq-t1", b["id"], "qué tal")
    s.add_chat_message("eq-otro", b["id"], "otro canal")
    assert m1["nombre"] == "Ana" and [m["texto"] for m in s.list_chat_messages("eq-t1")] == ["hola", "qué tal"]
    assert [m["id"] for m in s.list_chat_messages("eq-t1", after=m1["created_at"])] == [m2["id"]]
    assert [m["id"] for m in s.list_chat_messages("eq-t1", before=m2["created_at"])] == [m1["id"]]
    res = s.chat_summary(a["id"], ["eq-t1", "eq-otro"])
    assert res["eq-t1"]["no_leidos"] == 1 and res["eq-t1"]["ultimo"]["texto"] == "qué tal"
    s.set_chat_read(a["id"], "eq-t1", m2["created_at"])
    s.set_chat_read(a["id"], "eq-t1", m1["created_at"])          # no retrocede
    assert s.get_chat_read(a["id"], "eq-t1") == m2["created_at"]
    assert s.chat_summary(a["id"], ["eq-t1"])["eq-t1"]["no_leidos"] == 0
    assert s.delete_chat_message(m1["id"]) and s.get_chat_message(m1["id"]) is None
