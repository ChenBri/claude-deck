# Safety model

A box that can approve permission prompts is, by construction, pointed at
everything your agent can reach. On the work machine that includes production
database access. This document is the argument for why the approve button is
defensible, and the rules that make it so.

## Threats being designed against

1. **Stray press.** Elbow, cat, reaching for a mug. Must never approve anything.
2. **Wrong window.** A USB keyboard types into whatever has focus. A blind
   keystroke could land in a terminal, a browser, a chat.
3. **Stale prompt.** Approving something that appeared after you last looked.
4. **Network reach.** Anything on the LAN being able to press the button remotely.
5. **Data leaking onto the box.** The Pi renders text to a screen and writes
   history to a card. Secrets must never get that far.

## The rules

### 1. HID can only emit F13 to F20

The USB HID gadget never sends a printable character, never sends Enter, never
sends `y`. It emits function keys F13 through F20, which exist in the HID spec
and which essentially nothing binds by default. The daemon registers them as
global hotkeys.

Consequence: if the daemon is not running, or the wrong window has focus, or
someone plugs the deck into a stranger's laptop, the keystrokes land nowhere and
do nothing. **The box is physically incapable of typing a destructive character.**

The cost is that the deck does nothing without the daemon. That trade is correct.

### 2. Approve means "approve request X", never "type yes"

A press sends a request id, not a keystroke intent. The daemon acts only if all
of these hold:

- a permission request is genuinely pending
- its id matches exactly what the deck currently has on screen
- it arrived less than 90 seconds ago
- the ARM state permits actions
- the target window is where the daemon expects it

Any mismatch discards the press and the deck plays the rejection tone. A stray
press cannot approve something you have not seen, because the deck can only
approve the thing it is currently displaying.

### 3. The deck shows what it is approving

Before the buttons light, the screen displays the tool and a sanitized target.
You approve what you read. This is stricter than clicking approve in a terminal,
where nothing forces the text past your eyes.

### 4. Dangerous calls are un-approvable from the box

When a pending request matches the denylist, the deck lights BLOCKED red, shows
the call, and the approve button stays dark and dead. You walk to the keyboard.

Denylist categories, all four enabled:

| Category | Matches |
|---|---|
| Database | psql, mysql, mongosh, redis-cli, any connection string, any remote DB host |
| Destructive fs and git | rm -rf, force push, hard reset, branch delete, history rewrite, filter-branch |
| Infrastructure | terraform apply/destroy, kubectl against a non-local context, aws writes, eksctl |
| Secrets | reads or writes touching .env, credentials, keychains, private keys, tokens |

Patterns live in the settings file, not the encoder menu, because you cannot type
a regex on a knob. The menu can enable and disable whole categories.

**The deck makes the safe path fast and the dangerous path slower.** That is the
opposite of what a convenience gadget usually does, and it is the point.

### 5. Same capabilities on both machines

The deck performs the full action set on the Windows desktop and on the work Mac
alike: approve, deny, interrupt, keys, push to talk.

| Machine | Actions | Action path |
|---|---|---|
| Windows desktop | Full | Win32 window focus and key send |
| Mac | Full | osascript, Accessibility permission granted once |

This is safe because the protection against the production-database case was
never the profile. It is **rule 4**: database commands are on the denylist, so
the approve button is dark and dead for them on every machine. Combined with
rules 1 through 3, the worst a misfire can do is approve a call that is already
on screen, already classified safe, and already less than 90 seconds old.

The daemon still identifies its host at handshake, because the action
implementations differ per platform and the audit log records which machine
approved what.

### 6. No route to the outside world

Normal operation is USB point-to-point only: 10.55.0.1 to 10.55.0.2, a private
two-node link that is not on your LAN and not routable. The radio is off unless
the `WIFI` toggle says otherwise, so "is this thing online" is answered by
looking at the panel rather than trusting a config file.

Weather on the idle dashboard comes from the daemon, which already has internet
on your PC. The Pi never needs a route out.

### 7. Nothing sensitive reaches the Pi

Hook payloads are truncated and scrubbed before leaving the daemon. Anything
shaped like a token, password, private key or connection string is replaced with
a placeholder. Paths are shortened to the last two segments. The Pi renders
these to a screen and writes state transitions to its card, so it must never
hold anything worth stealing.

### 8. Audit trail

Every deck-originated action is logged on the PC side with a timestamp, the
request id, the full tool call, and the outcome. If the box ever approves
something surprising, there is a record of exactly what and when.

## What is deliberately not protected

- Someone with physical access to your desk can press interrupt. That is fine.
- Someone with physical access can flip ARM and approve a pending safe call.
  If an attacker is at your keyboard, the deck is not your problem.
- The deck trusts the daemon completely. The daemon runs as you, on your machine,
  and already has everything.
