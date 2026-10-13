# Touchline — Football Story Simulator

A Python/Pygame desktop simulator with a screenshot-inspired dark dashboard:
two eleven-player squads and seven substitutes each, stamina and ability ratings,
three formations, five tactics, animated top-down pitch, score and clock,
statistics, scrollable event timeline, and live commentary.

## Run

From /workspace/hello-world:

    python -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m football.app

Click a starter to inspect passing, shooting, defending and pace; click a bench
player to substitute. Keepers can replace keepers; each team gets five changes.
Click formation and tactic buttons to cycle choices.

Space pauses; Tab cycles 1/6/12/30/60/120x speed.
S saves, L restores, E exports, N starts a new match.
Buttons provide the same controls. Resize the window to scale the layout.

Saves live in exports/match.json and retain players, stamina, tactics, statistics,
events and random state. Exports contain every event in events.json and significant
moments in storyboard.md for manhwa scene planning. Use --seed NUMBER for a different
reproducible match. Export during play or after full time.

## Verify without a display

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m unittest discover -s tests -v
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m football.app --frames 30 --screenshot exports/dashboard.png
    .venv/bin/python -m football.app --simulate

The simulation uses passing and tactics to weight possession, shooting and stamina
to weight chances, defending and goalkeeper ability to resist goals, and pace
to control visual movement. The pitch is a tactical visualization rather than a
physics engine. Matches last 90 minutes; there are no injuries, cards, offside,
stoppage time or extra time. Fictional squads require no assets or credentials.

## AI chat and goal replays

Click the Story Director box, write the next scene (for example, "Akira beats
two defenders and scores a header"), then press Enter or Send. Escape leaves
typing. The match waits while you type and while AI plans the scene.
The AI selects a validated player/action and writes commentary; the match engine
updates the score and statistics. Both generated and directed goals show a
four-second buildup/shot replay, with the scoring method displayed. Replays use
illustrative paths rather than recorded football physics. Fast-forward stays
visible and replays use normal real-time speed.

Choose an AI provider using environment variables before launch. No key is
stored in code, match saves, or exports. Prompts and commentary are saved in
match events; online providers receive your prompt and on-pitch player names.

Local Ollama (default): install Ollama on your computer, then run:

    ollama pull llama3.2

Ollama must be running at localhost:11434. The default model is llama3.2.
You can set FOOTBALL_AI_MODEL to another installed model.

OpenAI, in Windows PowerShell:

    $env:FOOTBALL_AI_PROVIDER = "openai"
    $env:FOOTBALL_AI_MODEL = "gpt-4.1-mini"
    $env:FOOTBALL_AI_KEY = "<your API key>"
    python -m football.app

macOS/Linux:

    export FOOTBALL_AI_PROVIDER=openai
    export FOOTBALL_AI_MODEL=gpt-4.1-mini
    export FOOTBALL_AI_KEY="<your API key>"
    python -m football.app

Enter your actual key only on your own machine or in secure environment settings.
Online API usage may incur charges. Connection errors appear in the chat response
without changing the match. The provider connection must be configured separately;
automated tests use a mocked AI response.
