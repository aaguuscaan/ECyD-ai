"""
Orquestación de una consulta:

  mensaje del responsable
    → conversación (se crea si no existe) + historial persistente
    → perfil y memoria del equipo
    → RAG (dos etapas, sesgado a la etapa del equipo)
    → prompt formativo ECyD
    → Groq (streaming)
    → se guarda la respuesta con sus fuentes
    → actualización de memoria del equipo y notas de la conversación
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Iterator, List, Optional

from . import prompts
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

    def prepare(self, message: str, conversation_id: Optional[str], team_id: Optional[str]) -> Dict:
        message = message.strip()
        conv = self.store.get_conversation(conversation_id) if conversation_id else None
        if conv and team_id and conv["team_id"] != team_id:
            conv = self.store.update_conversation(conv["id"], team_id=team_id)
        if not conv:
            conv = self.store.create_conversation(team_id, make_title(message))
        team = self.store.get_team(conv["team_id"]) if conv["team_id"] else None
        memories = self.store.list_memories(team["id"]) if team else []
        history = self.store.get_messages(conv["id"], limit=settings.history_messages)

        etapa = parse_etapa((team or {}).get("perfil", {}).get("etapa"))
        hits = self.retriever.search(self._retrieval_query(message, history), etapa=etapa)
        team_ctx = prompts.format_team_context(team)

        ctx = {"conversation": conv, "team": team, "memories": memories, "hits": hits,
               "weak": Retriever.is_weak(hits), "message": message, "history": history,
               "team_context": team_ctx, "etapa": etapa}
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
            notes=ctx["conversation"].get("notas", ""), rag_context=rag_context)
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
    def stream(self, message: str, conversation_id: Optional[str] = None,
               team_id: Optional[str] = None) -> Iterator[Dict]:
        ctx = self.prepare(message, conversation_id, team_id)
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

    def answer(self, message: str, conversation_id: Optional[str] = None, team_id: Optional[str] = None) -> Dict:
        result: Dict = {"text": ""}
        for ev in self.stream(message, conversation_id, team_id):
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


_assistant: Optional[Assistant] = None


def get_assistant() -> Assistant:
    global _assistant
    if _assistant is None:
        _assistant = Assistant()
    return _assistant
