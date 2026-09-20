# Software architecture

```
Claude Code session(s)
   |  hooks: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse,
   |         Notification, Stop, SubagentStop, PreCompact, SessionEnd
   v
hooks/emit.js  -- POST 127.0.0.1:7327 -->  daemon  (TypeScript, Win + macOS)
                                              |  scrub, classify, aggregate
                                              |  HTTP over USB ethernet 10.55.0.1
                                              v
                                    firmware (Python, Pi Zero 2 W)
                                              |
                              panel backend: real  |  sim
```

## Daemon, TypeScript, runs on Windows and macOS

One codebase, one binary per platform, same behaviour. Responsibilities:

- **Ingest.** Local HTTP endpoint the hook scripts POST to. Hooks stay trivial
  one-liners so they add no measurable latency to your session.
- **Scrub.** Truncate and redact before anything leaves the machine. See SAFETY.md.
- **Classify.** Map raw events onto deck states. Run the denylist over pending
  permission requests and mark each approvable or not.
- **Aggregate.** Track every live session. Serve either the one the rotary switch
  selects, or the highest-priority state across all of them when set to ALL.
- **Act.** Receive button events, verify them against the rules, then focus the
  right window and perform the action. Windows via Win32 calls, macOS via
  AppleScript and Accessibility.
- **Enrich.** Push weather, clock and git status for the idle dashboard, since
  the Pi has no internet.
- **Audit.** SQLite log of every action the deck took.

```
daemon/src/
  index.ts          bootstrap, host detection for the action backend
  http.ts           hook ingest endpoint
  scrub.ts          redaction and truncation
  classify.ts       event -> state, denylist evaluation
  sessions.ts       multi-session registry and priority
  guard.ts          approval verification rules
  link/
    transport.ts    HTTP to the Pi over the USB link
    hotkeys.ts      F13-F20 global hotkey registration
  actions/
    windows.ts      focus, send keys, launch
    macos.ts        same, via osascript
  enrich/           weather, git status
  store.ts          SQLite audit log
```

## Firmware, Python, runs on the Pi

```
firmware/deck/
  main.py             event loop
  state.py            state machine, priority, latching, timeouts
  link.py             talks to the daemon, heartbeat drives the LINK lamp
  menu.py             encoder-driven settings menu, writes /var/deck/settings.yaml
  panel/
    base.py           abstract Panel: lamps, meters, pixels, inputs, screen surface
    real.py           GPIO, SPI, I2C, PCA9685, MCP23017, rpi_ws281x
    sim.py            pygame window drawing the whole panel on your desktop
  ui/
    render.py         scene compositor, dirty-rect blitting, CRT post effect
    sprites.py        code-defined pixel grids -> PNG sprite sheets
    scenes/
      ready.py        sits, blinks, stretches
      working.py      types at a tiny desk, glyphs fly, speed tracks tool-call rate
      subagents.py    one mini mascot per live subagent
      blocked.py      turns, looks at you, holds a question sign
      done.py         victory hop and confetti
      compacting.py   sweeps papers into a box
      idle.py         clock, date, your name, weather, git status, today's totals
      snake.py        playable on the encoder after a few minutes idle
      boot.py         covers the ~25s Pi boot so it never looks broken
  audio/
    chiptune.py       generated blips, one per event, mute switch respected
```

## The simulator

`SimPanel` implements the same interface as `RealPanel` and renders the entire
front panel into a pygame window: five lamps, both needles, the NeoPixel halo and
underglow, the arcade buttons, the toggles, the rotary switch. Mouse clicks and
keyboard shortcuts drive the inputs.

The screen area inside the simulated bezel runs the **exact same rendering code**
as the real display. Nothing about the animation, the scenes, the timing or the
snake game is written twice.

```bash
python -m deck.main --panel sim
```

This means the software is finished and tuned before any part arrives, and the
project stays testable in CI forever.

## States

| State | Entered by | Lamp | Screen |
|---|---|---|---|
| `READY` | SessionStart, Stop | READY | mascot sits, blinks |
| `WORKING` | UserPromptSubmit, PreToolUse | WORKING | typing, glyphs, speed tracks tool rate |
| `SUBAGENTS` | PreToolUse on Task | WORKING | one mini mascot per live subagent |
| `BLOCKED_PERMISSION` | Notification, permission variant | BLOCKED | turns to face you, question sign |
| `BLOCKED_INPUT` | Notification, idle variant | BLOCKED | taps foot, checks watch |
| `COMPACTING` | PreCompact | WORKING | sweeping papers |
| `DONE` | Stop after work | DONE | victory hop, confetti, auto-clears |
| `ERROR` | PostToolUse failure, SessionEnd error | BLOCKED | storm cloud |
| `IDLE` | no session for N minutes | none | dashboard, then snake |
| `OFFLINE` | daemon heartbeat lost | LINK dark | connection lost card |

Aggregation priority when the selector is on ALL:

```
BLOCKED_PERMISSION > BLOCKED_INPUT > ERROR > WORKING > SUBAGENTS
                   > COMPACTING > DONE > READY > IDLE
```

`DONE` auto-clears back to `READY` after a few minutes, per the chosen behaviour.

## Rendering

- Logical canvas 160x120, nearest-neighbour scaled 2x to the 320x240 panel.
  Pixel art stays crisp and the drawing cost drops to a quarter.
- Dirty-rect blitting: the mascot moves, the background does not.
- A light CRT post pass, scanlines and slight bloom, to sell the enclosure.
- Target 20 to 30 fps on a Zero 2 W, which is above classic handheld animation.

## Sprites

Sprites are authored as code-defined pixel grids in `sprites.py` and rendered to
PNG sheets at build time. They live in the repo as both source and output, so
they are diffable, regenerable, and any frame can be opened in Piskel or Aseprite
and hand-tweaked.

The mascot is an original pixel character based on a starburst silhouette. It is
not Anthropic artwork.

## Testing

- `pytest` over the state machine, which is pure logic and decides when the
  approve button is live. It gets real tests.
- `tools/record.py` captures live hook events from your normal work into JSONL.
- `tools/replay.py` plays a recorded session into the simulator at up to 10x, so
  every transition is tuned against how you actually work.
