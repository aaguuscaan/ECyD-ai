"""
Orquestación de una consulta:

  mensaje del responsable
    → conversación (se crea si no existe) + historial persistente
    → perfil y memoria del equipo + encuentros anteriores del grupo
    → programa de la etapa y momento del año (guía)
    → RAG (dos etapas, respetando la progresión de etapas)
    → prompt formativo ECyD
    → Groq (streaming)
    → se guarda la respuesta con sus fuentes
    → actualización de memoria del equipo y notas de la conversación
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date
from typing import Dict, Iterator, List, Optional

from . import programas, prompts
from .config import settings
from .llm import RequestTooLarge, get_llm, parse_json, small_model
from .memory import MemoryStore, get_store
from .retrieval import Hit, Retriever, get_retriever

log = logging.getLogger("ecyd.assistant")

MAX_HISTORY_CHARS_PER_MSG = 2500


def parse_etapa(value) -> Optional[int]:
    m = re.search(r"[1-4]", str(value or ""))
    return int(m.group(0)) if m else None


def make_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:60].rsplit(" ", 1)[0] + "…") if len(text) > 60 else text


def cited_numbers(answer: str) -> set:
    # acepta [F1], [F1][F3], **F1**, (F1) o F1 suelto
    return {int(n) for n in re.findall(r"(?<![A-Za-z0-9])F(\d{1,2})(?![0-9])", answer)}


class Assistant:
    def __init__(self, store: Optional[MemoryStore] = None, retriever: Optional[Retriever] = None, llm=None):
        self.store = store or get_store()
        self._retriever = retriever
        self._llm = llm

    @property
    def retriever(self) -> Retriever:
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    # ------------------------------------------------------------------
    def _retrieval_query(self, message: str, history: List[Dict]) -> str:
        """Para preguntas de seguimiento cortas ("¿y para 2da etapa?") se suma
        la pregunta anterior, así la búsqueda no pierde el tema."""
        prev_user = [m["content"] for m in history if m["role"] == "user"]
        if prev_user and len(message.split()) < 14:
            return f"{prev_user[-1][:400]}\n{message}"
        return message

    def prepare(self, message: str, conversation_id: Optional[str], team_id: Optional[str],
                user_id: Optional[str] = None) -> Dict:
        message = message.strip()
        conv = self.store.get_conversation(conversation_id) if conversation_id else None
        if conv and team_id and conv["team_id"] != team_id:
            conv = self.store.update_conversation(conv["id"], team_id=team_id)
        if not conv:
            conv = self.store.create_conversation(team_id, make_title(message), user_id=user_id)
        team = self.store.get_team(conv["team_id"]) if conv["team_id"] else None
        memories = self.store.list_memories(team["id"]) if team else []
        history = self.store.get_messages(conv["id"], limit=settings.history_messages)

        etapa = parse_etapa((team or {}).get("perfil", {}).get("etapa"))
        hits = self.retriever.search(self._retrieval_query(message, history), etapa=etapa)
        team_ctx = prompts.format_team_context(team)
        encuentros = self._encuentros_del_grupo(team)

        ctx = {"conversation": conv, "team": team, "memories": memories, "hits": hits,
               "weak": Retriever.is_weak(hits), "message": message, "history": history,
               "team_context": team_ctx, "etapa": etapa,
               "programa": programas.contexto_programa(etapa) if team else "",
               "encuentros": prompts.format_encuentros(encuentros, 4) if team else ""}
        ctx["messages"], ctx["max_tokens"] = self.build_messages(ctx, level=0)
        return ctx

    # Niveles de recorte si el pedido no entra en el límite de tokens por minuto:
    # (mensajes de historial, caracteres por respuesta previa, caracteres de fuentes)
    LEVELS = [(6, 1200, 7000), (2, 600, 4500), (0, 0, 2800)]

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return int(len(text) / 3.6) + 4  # estimación conservadora para español

    def build_messages(self, ctx: Dict, level: int = 0):
        """Arma los mensajes para el nivel pedido; si no queda lugar suficiente
        para la respuesta (≥ 2200 tokens), pasa solo al siguiente nivel."""
        for lvl in range(level, len(self.LEVELS)):
            messages, max_tokens = self._build_level(ctx, lvl)
            if max_tokens >= 2200:
                break
        ctx["level"] = lvl
        return messages, max_tokens

    def _build_level(self, ctx: Dict, level: int):
        n_hist, hist_chars, ctx_chars = self.LEVELS[level]
        rag_context = self.retriever.build_context(ctx["hits"], max_chars=ctx_chars)
        user_msg = prompts.build_user_message(
            query=ctx["message"], team_context=ctx["team_context"],
            memory=prompts.format_memory(ctx["memories"][-25:]),
            notes=ctx["conversation"].get("notas", ""), rag_context=rag_context,
            programa=ctx.get("programa", ""), encuentros=ctx.get("encuentros", ""))
        messages = [{"role": "system", "content": prompts.system_prompt()}]
        for m in (ctx["history"][-n_hist:] if n_hist else []):
            content = m["content"]
            if m["role"] == "assistant" and len(content) > hist_chars:
                content = content[:hist_chars] + "\n[…respuesta recortada…]"
            messages.append({"role": m["role"], "content": content})
        messages.append({"role": "user", "content": user_msg})
        used = sum(self.estimate_tokens(m["content"]) for m in messages)
        room = settings.token_budget - used - 250
        max_tokens = max(900, min(settings.max_output_tokens, room))
        return messages, max_tokens

    @staticmethod
    def sources_payload(hits: List[Hit], answer: str = "") -> List[Dict]:
        cited = cited_numbers(answer)
        out = []
        for h in hits:
            p = h.public()
            p["citada"] = h.n in cited
            out.append(p)
        return out

    # ------------------------------------------------------------------
    def _encuentros_del_grupo(self, team: Optional[Dict]) -> List[Dict]:
        if not team or not hasattr(self.store, "list_encuentros"):
            return []
        try:
            return self.store.list_encuentros(team_id=team["id"], limit=12)
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudieron leer los encuentros: %s", e)
            return []

    def stream(self, message: str, conversation_id: Optional[str] = None,
               team_id: Optional[str] = None, user_id: Optional[str] = None) -> Iterator[Dict]:
        ctx = self.prepare(message, conversation_id, team_id, user_id=user_id)
        conv = ctx["conversation"]
        self.store.add_message(conv["id"], "user", ctx["message"])
        yield {"type": "meta", "conversation": conv, "weak_evidence": ctx["weak"],
               "sources": self.sources_payload(ctx["hits"])}

        parts: List[str] = []
        try:
            level = 0
            while True:
                try:
                    for piece in self.llm.stream(ctx["messages"], max_tokens=ctx["max_tokens"]):
                        parts.append(piece)
                        yield {"type": "delta", "text": piece}
                    break
                except RequestTooLarge:
                    # no entró en el límite de tokens: se recorta historial y fuentes
                    level = max(level, ctx.get("level", 0)) + 1
                    if parts or level >= len(self.LEVELS):
                        raise
                    log.warning("Pedido demasiado grande para Groq: recortando (nivel %d)", level)
                    ctx["messages"], ctx["max_tokens"] = self.build_messages(ctx, level)
        except Exception as e:  # noqa: BLE001
            log.exception("Error generando respuesta")
            partial = "".join(parts)
            if partial:
                partial += "\n\n_(La respuesta se interrumpió.)_"
                self.store.add_message(conv["id"], "assistant", partial,
                                       self.sources_payload(ctx["hits"], partial), {"error": str(e)})
            yield {"type": "error", "message": str(e)}
            return

        answer = "".join(parts).strip()
        sources = self.sources_payload(ctx["hits"], answer)
        saved = self.store.add_message(conv["id"], "assistant", answer, sources,
                                       {"provider": getattr(self.llm, "provider", ""),
                                        "model": getattr(self.llm, "model", ""),
                                        "weak_evidence": ctx["weak"]})
        yield {"type": "done", "message": saved, "sources": sources}

        mem = self.update_memory(ctx, answer)
        if mem:
            yield {"type": "memory", **mem}

    def answer(self, message: str, conversation_id: Optional[str] = None, team_id: Optional[str] = None,
               user_id: Optional[str] = None) -> Dict:
        result: Dict = {"text": ""}
        for ev in self.stream(message, conversation_id, team_id, user_id=user_id):
            if ev["type"] == "meta":
                result["conversation"] = ev["conversation"]
            elif ev["type"] == "delta":
                result["text"] += ev["text"]
            elif ev["type"] == "done":
                result["sources"] = ev["sources"]
            elif ev["type"] == "memory":
                result["memory"] = ev
            elif ev["type"] == "error":
                result["error"] = ev["message"]
        return result

    # ------------------------------------------------------------------
    # Preparación de encuentros
    # ------------------------------------------------------------------
    ENC_LEVELS = [7000, 4800, 3000]   # caracteres de fuentes por nivel de recorte

    def prepare_encuentro(self, team: Dict, req: Dict, user_id: Optional[str] = None) -> Dict:
        """Reúne todo el contexto para preparar un encuentro:
        grupo → etapa → programa y momento del año → tema → fichas → historial."""
        perfil = team.get("perfil") or {}
        etapa = parse_etapa(perfil.get("etapa"))
        fecha = _parse_date(req.get("fecha")) or date.today()
        tema = (req.get("tema") or "").strip()
        fichas_ids = [d for d in (req.get("fichas") or []) if d in self.retriever.doc_by_id][:3]

        # fichas elegidas: dónde están en el programa y su relación con la etapa del grupo
        fichas, lines = [], []
        for did in fichas_ids:
            d = self.retriever.doc_by_id[did]
            etapas_doc = list(d.get("etapas") or [])
            for dup in d.get("fuente", {}).get("duplicados", []):
                etapas_doc += [e for e in dup.get("etapas", []) if e not in etapas_doc]
            ubic = programas.ficha_en_programa(etapa, did)
            rel = "de la etapa del grupo" if (etapa and etapa in etapas_doc) else (
                f"de otra etapa ({', '.join(map(str, etapas_doc))})" if etapas_doc else "material general")
            if etapa and etapas_doc and min(etapas_doc) > etapa + 1:
                rel += " — MÁS AVANZADA que la del grupo: advertilo y adaptá con cuidado"
            lugar = f"; en el programa: {ubic['label']}" if ubic else ""
            lines.append(f"- «{d['titulo']}» ({rel}{lugar})")
            fichas.append({"doc_id": did, "titulo": d["titulo"]})
        fichas_info = "\n".join(lines) or "Ninguna: el responsable no eligió una ficha concreta."

        # historial del grupo y posible repetición
        anteriores = [e for e in self._encuentros_del_grupo(team) if e.get("id") != req.get("encuentro_id")]
        aviso = _aviso_repeticion(tema, fichas_ids, anteriores)

        cantidad = req.get("cantidad") or perfil.get("cantidad_chicos") or ""
        composicion = req.get("composicion") or perfil.get("composicion") or ""
        edades = req.get("edades") or perfil.get("edades") or ""
        duracion = req.get("duracion") or perfil.get("duracion") or ""
        grupo = "\n".join(x for x in [
            f"- Equipo: {team.get('nombre')}",
            f"- Etapa: {perfil.get('etapa') or 'sin definir'}",
            f"- Cantidad de chicos: {cantidad or 'sin dato'}",
            f"- Composición: {composicion or 'sin dato'}",
            f"- Edades: {edades or 'sin dato'}",
            f"- Duración disponible: {duracion or 'sin dato'}",
            f"- Tipo de encuentro: {perfil.get('tipo_encuentro')}" if perfil.get("tipo_encuentro") else "",
            f"- Situación del equipo: {perfil.get('situacion_equipo')}" if perfil.get("situacion_equipo") else "",
        ] if x)

        origen = "programa" if req.get("origen_tema") == "programa" else "otro"
        pedido = (f"Fecha prevista: {fecha.isoformat()}. Tema: {tema or '(a definir con el programa)'} "
                  f"({'sugerido por el programa' if origen == 'programa' else 'elegido por el responsable'}).")
        if req.get("notas"):
            pedido += f"\nIndicaciones del responsable: {req['notas']}"

        query = " ".join([tema] + [f["titulo"] for f in fichas]) or "encuentro formativo"
        hits = self.retriever.search(query, etapa=etapa, top_k=7, focus_docs=fichas_ids, focus_k=3)

        ctx = {"team": team, "etapa": etapa, "fecha": fecha, "tema": tema, "origen_tema": origen,
               "fichas": fichas, "fichas_info": fichas_info, "hits": hits, "weak": Retriever.is_weak(hits),
               "programa": programas.contexto_programa(etapa, fecha, detallado=True),
               "encuentros": prompts.format_encuentros(anteriores, 6), "aviso": aviso,
               "grupo": grupo, "pedido": pedido, "user_id": user_id,
               "memories": self.store.list_memories(team["id"])[-12:],
               "datos": {"cantidad": cantidad, "composicion": composicion, "edades": edades,
                         "duracion": duracion}}
        ctx["messages"], ctx["max_tokens"] = self._build_encuentro(ctx, 0)
        return ctx

    def _build_encuentro(self, ctx: Dict, level: int):
        for lvl in range(level, len(self.ENC_LEVELS)):
            rag = self.retriever.build_context(ctx["hits"], max_chars=self.ENC_LEVELS[lvl])
            user = prompts.build_encuentro_message(
                programa=ctx["programa"], fichas_info=ctx["fichas_info"], rag_context=rag, grupo=ctx["grupo"],
                encuentros=ctx["encuentros"], aviso=ctx["aviso"], pedido=ctx["pedido"],
                memory=prompts.format_memory(ctx["memories"]) if ctx["memories"] and lvl == 0 else "")
            messages = [{"role": "system", "content": prompts.system_prompt()},
                        {"role": "user", "content": user}]
            used = sum(self.estimate_tokens(m["content"]) for m in messages)
            max_tokens = max(900, min(settings.max_output_tokens, settings.token_budget - used - 250))
            if max_tokens >= 2400:
                break
        ctx["level"] = lvl
        return messages, max_tokens

    def stream_encuentro(self, team: Dict, req: Dict, user_id: Optional[str] = None) -> Iterator[Dict]:
        ctx = self.prepare_encuentro(team, req, user_id)
        yield {"type": "meta", "sources": self.sources_payload(ctx["hits"]), "aviso": ctx["aviso"],
               "weak_evidence": ctx["weak"], "etapa": ctx["etapa"], "fichas": ctx["fichas"]}
        parts: List[str] = []
        try:
            level = 0
            while True:
                try:
                    for piece in self.llm.stream(ctx["messages"], max_tokens=ctx["max_tokens"]):
                        parts.append(piece)
                        yield {"type": "delta", "text": piece}
                    break
                except RequestTooLarge:
                    level = max(level, ctx.get("level", 0)) + 1
                    if parts or level >= len(self.ENC_LEVELS):
                        raise
                    ctx["messages"], ctx["max_tokens"] = self._build_encuentro(ctx, level)
        except Exception as e:  # noqa: BLE001
            log.exception("Error preparando encuentro")
            yield {"type": "error", "message": str(e)}
            return

        propuesta = "".join(parts).strip()
        sources = self.sources_payload(ctx["hits"], propuesta)
        m = re.search(r"^#\s+(.+)$", propuesta, re.M)
        titulo = (req.get("titulo") or (m.group(1).strip() if m else "") or ctx["tema"] or "Encuentro")[:140]
        data = {
            "titulo": titulo, "fecha": ctx["fecha"].isoformat(), "etapa": ctx["etapa"], "tema": ctx["tema"],
            "origen_tema": ctx["origen_tema"], "periodo": req.get("periodo") or "", "fichas": ctx["fichas"],
            "cantidad": ctx["datos"]["cantidad"], "composicion": ctx["datos"]["composicion"],
            "edades": ctx["datos"]["edades"], "duracion": ctx["datos"]["duracion"],
            "propuesta": propuesta, "team_id": ctx["team"]["id"],
            "meta": {"sources": sources, "aviso": ctx["aviso"], "notas_pedido": req.get("notas", ""),
                     "modelo": getattr(self.llm, "model", "")},
        }
        try:
            if req.get("encuentro_id"):
                enc = self.store.update_encuentro(req["encuentro_id"], data)
            else:
                data["estado"] = "borrador"
                enc = self.store.create_encuentro(user_id, data)
        except Exception as e:  # noqa: BLE001
            log.exception("No se pudo guardar el encuentro")
            yield {"type": "error", "message": f"La propuesta se generó pero no se pudo guardar: {e}"}
            return
        yield {"type": "done", "encuentro": enc, "sources": sources}

    # ------------------------------------------------------------------
    AJUSTE_LEVELS = [3600, 1800, 0]   # caracteres de fuentes al ajustar

    def prepare_ajuste(self, enc: Dict, team: Optional[Dict], instruccion: str, propuesta: str) -> Dict:
        perfil = (team or {}).get("perfil") or {}
        etapa = enc.get("etapa") or parse_etapa(perfil.get("etapa"))
        fecha = _parse_date(enc.get("fecha")) or date.today()
        fichas_ids = [f.get("doc_id") for f in (enc.get("fichas") or []) if f.get("doc_id") in self.retriever.doc_by_id]
        query = " ".join([instruccion, enc.get("tema") or ""] + [f.get("titulo", "") for f in enc.get("fichas") or []])
        hits = self.retriever.search(query, etapa=etapa, top_k=4, focus_docs=fichas_ids, focus_k=2)
        grupo = "\n".join(x for x in [
            f"- Equipo: {(team or {}).get('nombre', '')}", f"- Etapa: {etapa or 'sin definir'}",
            f"- Cantidad de chicos: {enc.get('cantidad') or perfil.get('cantidad_chicos') or 'sin dato'}",
            f"- Composición: {enc.get('composicion') or perfil.get('composicion') or 'sin dato'}",
            f"- Edades: {enc.get('edades') or perfil.get('edades') or 'sin dato'}",
            f"- Duración: {enc.get('duracion') or perfil.get('duracion') or 'sin dato'}",
        ] if x)
        ajustes = (enc.get("meta") or {}).get("ajustes") or []
        historial = "\n".join(f"- {a.get('instruccion', '')}" for a in ajustes[-4:])
        ctx = {"hits": hits, "grupo": grupo, "historial": historial, "instruccion": instruccion.strip(),
               "propuesta": propuesta.strip()[:14000],
               "programa": programas.contexto_programa(etapa, fecha)}
        ctx["messages"], ctx["max_tokens"] = self._build_ajuste(ctx, 0)
        return ctx

    def _build_ajuste(self, ctx: Dict, level: int):
        for lvl in range(level, len(self.AJUSTE_LEVELS)):
            chars = self.AJUSTE_LEVELS[lvl]
            rag = self.retriever.build_context(ctx["hits"], max_chars=chars) if chars else ""
            user = prompts.build_ajuste_message(
                propuesta=ctx["propuesta"], instruccion=ctx["instruccion"], grupo=ctx["grupo"],
                programa=ctx["programa"] if lvl < 2 else "", rag_context=rag, historial=ctx["historial"])
            messages = [{"role": "system", "content": prompts.AJUSTE_SYSTEM}, {"role": "user", "content": user}]
            used = sum(self.estimate_tokens(m["content"]) for m in messages)
            max_tokens = max(900, min(settings.max_output_tokens, settings.token_budget - used - 250))
            if max_tokens >= max(1800, self.estimate_tokens(ctx["propuesta"]) + 300):
                break
        ctx["level"] = lvl
        return messages, max_tokens

    def stream_ajuste(self, enc: Dict, team: Optional[Dict], instruccion: str, propuesta: str) -> Iterator[Dict]:
        """Reescribe una propuesta de encuentro según las aclaraciones del responsable
        y guarda la nueva versión (la anterior queda para poder deshacer)."""
        ctx = self.prepare_ajuste(enc, team, instruccion, propuesta)
        yield {"type": "meta", "sources": self.sources_payload(ctx["hits"])}
        parts: List[str] = []
        try:
            level = 0
            while True:
                try:
                    for piece in self.llm.stream(ctx["messages"], max_tokens=ctx["max_tokens"]):
                        parts.append(piece)
                        yield {"type": "delta", "text": piece}
                    break
                except RequestTooLarge:
                    level = max(level, ctx.get("level", 0)) + 1
                    if parts or level >= len(self.AJUSTE_LEVELS):
                        raise
                    ctx["messages"], ctx["max_tokens"] = self._build_ajuste(ctx, level)
        except Exception as e:  # noqa: BLE001
            log.exception("Error ajustando el encuentro")
            yield {"type": "error", "message": str(e)}
            return
        nueva = "".join(parts).strip()
        if not nueva:
            yield {"type": "error", "message": "La IA no devolvió una propuesta."}
            return
        # la sección "Qué cambié" no forma parte de la propuesta: queda como nota del ajuste
        cambios = ""
        mc = re.search(r"\n#{1,4}\s*\**\s*Qu[eé] cambi[eé][^\n]*\n(.*)$", "\n" + nueva, re.S | re.I)
        if mc:
            cambios = mc.group(1).strip()[:800]
            nueva = ("\n" + nueva)[:mc.start()].strip()
        sources = self.sources_payload(ctx["hits"], nueva)
        meta = dict(enc.get("meta") or {})
        ajustes = list(meta.get("ajustes") or [])
        ajustes.append({"instruccion": ctx["instruccion"][:500], "cambios": cambios,
                        "fecha": date.today().isoformat()})
        meta.update({"ajustes": ajustes[-20:], "version_anterior": propuesta, "sources": sources})
        data = {"propuesta": nueva, "meta": meta}
        m = re.search(r"^#\s+(.+)$", nueva, re.M)
        if m:
            data["titulo"] = m.group(1).strip()[:140]
        try:
            saved = self.store.update_encuentro(enc["id"], data)
        except Exception as e:  # noqa: BLE001
            log.exception("No se pudo guardar el ajuste")
            yield {"type": "error", "message": f"Se generó el cambio pero no se pudo guardar: {e}"}
            return
        yield {"type": "done", "encuentro": saved, "sources": sources}

    # ------------------------------------------------------------------
    def update_memory(self, ctx: Dict, answer: str) -> Optional[Dict]:
        """Extrae hechos duraderos del equipo y actualiza las notas de la
        conversación. Nunca rompe el flujo principal si falla."""
        team = ctx["team"]
        conv = ctx["conversation"]
        use_team_memory = bool(team and team.get("auto_memoria") and settings.auto_memory)
        try:
            raw = self.llm.complete(
                [{"role": "system", "content": prompts.MEMORY_SYSTEM_PROMPT},
                 {"role": "user", "content": prompts.build_memory_prompt(
                     team_context=ctx["team_context"], memories=ctx["memories"],
                     previous_summary=conv.get("notas", ""), user_message=ctx["message"],
                     assistant_message=answer)}],
                model=small_model(), max_tokens=900, temperature=0.1, json_mode=True)
            data = parse_json(raw)
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudo actualizar la memoria: %s", e)
            return None

        resumen = str(data.get("resumen_conversacion") or "").strip()
        if resumen:
            self.store.update_conversation(conv["id"], notas=resumen[:1500])

        added, updated, removed = [], [], []
        if use_team_memory:
            own = {m["id"]: m for m in ctx["memories"]}
            for item in (data.get("nuevas") or [])[:3]:
                texto = str((item or {}).get("texto") or "").strip()
                if len(texto) < 8 or any(texto.lower() == m["texto"].lower() for m in own.values()):
                    continue
                added.append(self.store.add_memory(team["id"], texto, item.get("categoria", "general"),
                                                   origen="auto", conversation_id=conv["id"]))
            for item in data.get("actualizar") or []:
                try:
                    mid = int(item.get("id"))
                except (TypeError, ValueError, AttributeError):
                    continue
                if mid in own and str(item.get("texto") or "").strip():
                    r = self.store.update_memory(mid, texto=item["texto"], team_id=team["id"])
                    if r:
                        updated.append(r)
            for mid in data.get("olvidar") or []:
                try:
                    mid = int(mid)
                except (TypeError, ValueError):
                    continue
                # solo se olvidan automáticamente recuerdos que también fueron automáticos
                if mid in own and own[mid]["origen"] == "auto" and self.store.delete_memory(mid, team["id"]):
                    removed.append(mid)
        return {"added": added, "updated": updated, "removed": removed, "notas": resumen}


def _parse_date(value) -> Optional[date]:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _norm_words(text: str) -> set:
    t = unicodedata.normalize("NFD", (text or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    stop = {"el", "la", "los", "las", "de", "del", "y", "en", "un", "una", "con", "para", "por", "que", "a", "mi",
            "sobre", "encuentro", "tema"}
    return {w for w in re.findall(r"[a-z]{3,}", t) if w not in stop}


def _aviso_repeticion(tema: str, fichas_ids: List[str], anteriores: List[Dict]) -> str:
    """Detecta si el grupo ya trabajó esta ficha o un tema muy parecido."""
    tw = _norm_words(tema)
    for e in anteriores:
        usadas = {f.get("doc_id") for f in e.get("fichas") or []}
        fecha = (e.get("fecha") or e.get("created_at") or "")[:10]
        if usadas & set(fichas_ids):
            return (f"Este grupo ya usó esta ficha en «{e.get('titulo')}» ({fecha}). Proponé una continuación "
                    f"o una forma diferente de abordarla, en lugar de repetirla.")
        ew = _norm_words(e.get("tema") or e.get("titulo") or "")
        if tw and ew and len(tw & ew) / max(1, min(len(tw), len(ew))) >= 0.6:
            return (f"Este grupo ya trabajó un tema parecido: «{e.get('titulo')}» ({fecha}). Ofrecé una "
                    f"continuación o un enfoque diferente.")
    return ""


_assistant: Optional[Assistant] = None


def get_assistant() -> Assistant:
    global _assistant
    if _assistant is None:
        _assistant = Assistant()
    return _assistant
