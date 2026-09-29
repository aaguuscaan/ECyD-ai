"""
Cliente LLM. Groq es el proveedor principal (API compatible con OpenAI).
Gemini queda como alternativa opcional (LLM_PROVIDER=gemini).

La API key se lee SOLO en el servidor (variables de entorno); nunca llega al
navegador.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Dict, Iterator, List, Optional

from .config import settings

log = logging.getLogger("ecyd.llm")

TRANSIENT = ("429", "500", "502", "503", "504", "timeout", "timed out", "rate limit",
             "temporarily", "overloaded", "connection", "unavailable")


class LLMError(RuntimeError):
    pass


def _is_transient(err: Exception) -> bool:
    text = str(err).lower()
    return any(t in text for t in TRANSIENT)


def _is_model_problem(err: Exception) -> bool:
    text = str(err).lower()
    return any(t in text for t in ("model_decommissioned", "decommissioned", "model_not_found",
                                   "does not exist", "not found", "404"))


class GroqLLM:
    provider = "groq"

    def __init__(self):
        if not settings.groq_api_key:
            raise LLMError("Falta GROQ_API_KEY en el archivo .env / variables de entorno del servidor.")
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url,
                             timeout=120, max_retries=0)
        self.model = settings.groq_model

    def _extra(self, model: str, effort: Optional[str] = None) -> dict:
        if "gpt-oss" in model:
            return {"reasoning_effort": effort or settings.reasoning_effort, "include_reasoning": False}
        return {}

    def _models(self, model: Optional[str]) -> List[str]:
        first = model or self.model
        models = [first]
        if settings.groq_fallback_model and settings.groq_fallback_model not in models:
            models.append(settings.groq_fallback_model)
        return models

    def _create(self, *, model, messages, stream, max_tokens, temperature, json_mode=False):
        kwargs = dict(model=model, messages=messages, temperature=temperature,
                      max_tokens=max_tokens, stream=stream)
        # tareas auxiliares (memoria) con razonamiento bajo: más rápidas y baratas
        extra = self._extra(model, "low" if json_mode else None)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            return self.client.chat.completions.create(**kwargs, extra_body=extra or None)
        except Exception as e:  # si el modelo no acepta algún parámetro opcional, reintenta sin él
            msg = str(e).lower()
            retry = False
            if extra and "reasoning" in msg:
                extra, retry = {}, True
            if json_mode and ("response_format" in msg or "json" in msg):
                kwargs.pop("response_format", None)
                retry = True
            if retry:
                return self.client.chat.completions.create(**kwargs, extra_body=extra or None)
            raise

    def _run(self, fn, model):
        last = None
        for m in self._models(model):
            for attempt in range(3):
                try:
                    return fn(m)
                except Exception as e:
                    last = e
                    log.warning("Groq %s intento %d: %s", m, attempt + 1, e)
                    if _is_model_problem(e) or not _is_transient(e):
                        break
                    time.sleep(2 ** attempt)
        raise LLMError(f"No fue posible generar la respuesta con Groq. Último error: {last}")

    def complete(self, messages: List[Dict], *, model=None, max_tokens=None, temperature=None,
                 json_mode=False) -> str:
        def fn(m):
            r = self._create(model=m, messages=messages, stream=False,
                             max_tokens=max_tokens or settings.max_output_tokens,
                             temperature=settings.temperature if temperature is None else temperature,
                             json_mode=json_mode)
            text = (r.choices[0].message.content or "").strip()
            if not text:
                raise LLMError("Groq devolvió una respuesta vacía (timeout)")
            return text
        return self._run(fn, model)

    def stream(self, messages: List[Dict], *, model=None, max_tokens=None, temperature=None) -> Iterator[str]:
        """Devuelve fragmentos de texto. Reintenta/cambia de modelo solo si
        todavía no se emitió nada."""
        last = None
        for m in self._models(model):
            for attempt in range(3):
                emitted = False
                try:
                    resp = self._create(model=m, messages=messages, stream=True,
                                        max_tokens=max_tokens or settings.max_output_tokens,
                                        temperature=settings.temperature if temperature is None else temperature)
                    for chunk in resp:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        piece = getattr(delta, "content", None)
                        if piece:
                            emitted = True
                            yield piece
                    if emitted:
                        return
                    raise LLMError("respuesta vacía (timeout)")
                except Exception as e:
                    if emitted:
                        raise LLMError(f"Se cortó la respuesta: {e}")
                    last = e
                    log.warning("Groq stream %s intento %d: %s", m, attempt + 1, e)
                    if _is_model_problem(e) or not _is_transient(e):
                        break
                    time.sleep(2 ** attempt)
        raise LLMError(f"No fue posible generar la respuesta con Groq. Último error: {last}")


class GeminiLLM:
    provider = "gemini"

    def __init__(self):
        if not settings.gemini_api_key:
            raise LLMError("Falta GEMINI_API_KEY.")
        from google import genai
        self.genai = genai
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def _convert(self, messages):
        from google.genai import types
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = [types.Content(role="user" if m["role"] == "user" else "model",
                                  parts=[types.Part(text=m["content"])])
                    for m in messages if m["role"] != "system"]
        return system, contents

    def complete(self, messages, *, model=None, max_tokens=None, temperature=None, json_mode=False):
        from google.genai import types
        system, contents = self._convert(messages)
        cfg = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=settings.temperature if temperature is None else temperature,
            max_output_tokens=max_tokens or settings.max_output_tokens,
            response_mime_type="application/json" if json_mode else None)
        r = self.client.models.generate_content(model=self.model, contents=contents, config=cfg)
        if not getattr(r, "text", None):
            raise LLMError("Gemini no devolvió texto.")
        return r.text.strip()

    def stream(self, messages, *, model=None, max_tokens=None, temperature=None):
        from google.genai import types
        system, contents = self._convert(messages)
        cfg = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=settings.temperature if temperature is None else temperature,
            max_output_tokens=max_tokens or settings.max_output_tokens)
        for chunk in self.client.models.generate_content_stream(model=self.model, contents=contents, config=cfg):
            if getattr(chunk, "text", None):
                yield chunk.text


_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = GeminiLLM() if settings.llm_provider == "gemini" else GroqLLM()
    return _llm


def small_model() -> Optional[str]:
    return settings.groq_small_model if settings.llm_provider != "gemini" else None


def parse_json(text: str) -> dict:
    """Parsea JSON aunque venga envuelto en ```json ... ```."""
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("No se encontró JSON")
    return json.loads(m.group(0))
