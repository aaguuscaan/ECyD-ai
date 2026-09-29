"""
Asistente ECyD en consola (misma lógica que la web, con memoria persistente).

    python cli.py
"""

from __future__ import annotations

import sys

from app import prompts
from app.assistant import get_assistant
from app.memory import get_store

HELP = """
COMANDOS
  /ayuda              Muestra esta ayuda
  /equipos            Lista los equipos
  /equipo <n|nombre>  Elige un equipo (o lo crea si no existe)
  /contexto           Muestra el perfil del equipo actual
  /configurar         Configura el perfil del equipo actual
  /memoria            Muestra la memoria del equipo
  /recordar <texto>   Agrega un recuerdo a mano
  /olvidar <id>       Borra un recuerdo
  /historial          Lista conversaciones del equipo
  /abrir <n>          Continúa una conversación del historial
  /nueva  (/limpiar)  Empieza una conversación nueva
  /notas              Notas temporales de la conversación actual
  /salir              Cierra el asistente
"""


def main():
    store = get_store()
    assistant = get_assistant()
    team = None
    conv_id = None
    listed = []

    print("=" * 70)
    print("🤖 ASISTENTE ECyD (consola)  ·  /ayuda para ver comandos")
    print("=" * 70)
    teams = store.list_teams()
    if len(teams) == 1:
        team = teams[0]
        print(f"Equipo actual: {team['nombre']}")

    while True:
        try:
            q = input(f"\n[{team['nombre'] if team else 'sin equipo'}] 🔎 ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Hasta luego.")
            break
        if not q:
            continue
        cmd, _, arg = q.partition(" ")
        cmd = cmd.lower()

        if cmd in ("/salir", "salir", "exit", "quit"):
            print("👋 Hasta luego.")
            break
        elif cmd == "/ayuda":
            print(HELP)
        elif cmd == "/equipos":
            for i, t in enumerate(store.list_teams(), 1):
                print(f"{i}. {t['nombre']}  ({t['perfil'].get('etapa', 'sin etapa')})")
        elif cmd == "/equipo":
            teams = store.list_teams()
            if arg.isdigit() and 0 < int(arg) <= len(teams):
                team = teams[int(arg) - 1]
            elif arg:
                team = next((t for t in teams if t["nombre"].lower() == arg.lower()), None) \
                    or store.create_team(arg)
            conv_id = None
            print(f"Equipo actual: {team['nombre'] if team else 'ninguno'}")
        elif cmd == "/contexto":
            print(prompts.format_team_context(team))
        elif cmd == "/configurar":
            if not team:
                team = store.create_team(input("Nombre del equipo: ").strip() or "Mi equipo")
            perfil = dict(team["perfil"])
            print("Dejá vacío para mantener el valor actual ('-' para borrarlo).")
            for key, label in prompts.TEAM_FIELDS:
                cur = perfil.get(key, "")
                v = input(f"{label}{f' [{cur}]' if cur else ''}: ").strip()
                if v == "-":
                    perfil.pop(key, None)
                elif v:
                    perfil[key] = v
            team = store.update_team(team["id"], perfil=perfil)
            print(prompts.format_team_context(team))
        elif cmd == "/memoria":
            if not team:
                print("Elegí un equipo con /equipo")
                continue
            mems = store.list_memories(team["id"])
            print("\n".join(f"[{m['id']}] ({m['categoria']}, {m['origen']}) {m['texto']}" for m in mems)
                  or "Sin recuerdos.")
        elif cmd == "/recordar" and arg:
            if team:
                store.add_memory(team["id"], arg)
                print("🧠 Guardado.")
        elif cmd == "/olvidar" and arg.isdigit():
            print("🗑️ Borrado." if store.delete_memory(int(arg), team["id"] if team else None) else "No existe.")
        elif cmd == "/historial":
            listed = store.list_conversations(team["id"] if team else None, limit=20)
            for i, c in enumerate(listed, 1):
                print(f"{i}. {c['titulo']}  ({c['mensajes']} mensajes, {c['updated_at'][:10]})")
        elif cmd == "/abrir" and arg.isdigit() and 0 < int(arg) <= len(listed):
            conv_id = listed[int(arg) - 1]["id"]
            for m in store.get_messages(conv_id)[-4:]:
                print(f"\n{'🧑' if m['role'] == 'user' else '🤖'} {m['content'][:500]}")
        elif cmd in ("/nueva", "/limpiar"):
            conv_id = None
            print("🧹 Nueva conversación.")
        elif cmd == "/notas":
            c = store.get_conversation(conv_id) if conv_id else None
            print((c or {}).get("notas") or "Sin notas todavía.")
        elif cmd.startswith("/"):
            print("Comando desconocido. /ayuda")
        else:
            print()
            sources = []
            for ev in assistant.stream(q, conv_id, team["id"] if team else None):
                if ev["type"] == "meta":
                    conv_id = ev["conversation"]["id"]
                    if ev["weak_evidence"]:
                        print("⚠️  Poco material relacionado en el corpus.\n")
                elif ev["type"] == "delta":
                    sys.stdout.write(ev["text"])
                    sys.stdout.flush()
                elif ev["type"] == "done":
                    sources = ev["sources"]
                elif ev["type"] == "error":
                    print(f"\n❌ {ev['message']}")
                elif ev["type"] == "memory" and ev.get("added"):
                    print("\n🧠 Memoria: " + "; ".join(m["texto"] for m in ev["added"]))
            if sources:
                print("\n\n📚 FUENTES")
                for s in sources:
                    print(f"  [F{s['n']}] {s['titulo']} ({s['tipo']}, etapas {s['etapas'] or '-'})"
                          f"{'  ← citada' if s['citada'] else ''}")


if __name__ == "__main__":
    main()
