// Global F13-F20 hotkeys for the daemon on macOS (docs/SAFETY.md rule 1).
//
// UNTESTED: written on Windows without a Mac to run it on. Before relying
// on it, run it by hand and press F13 (fn+F13 on a laptop keyboard without
// one, or a deck): it should print READY F13..F20 and then KEY F13.
//
// Carbon's RegisterEventHotKey claims each key system-wide and, unlike an
// event tap, needs no Accessibility permission. Same stdout protocol as
// win-hotkeys.ps1, read by daemon/src/link/hotkeys.ts:
//   READY F13 / FAILED F13   once per key at start-up
//   KEY F13                  on every press
//
// Build once:  swiftc -O -o mac-hotkeys mac-hotkeys.swift
// The daemon runs the built binary if it exists, otherwise `swift` on this file.

import Carbon

// kVK_F13 ... kVK_F20 from HIToolbox/Events.h, in F13..F20 order.
let keyCodes: [UInt32] = [0x69, 0x6B, 0x71, 0x6A, 0x40, 0x4F, 0x50, 0x5A]
let signature: OSType = 0x4445_434B  // "DECK"

setvbuf(stdout, nil, _IOLBF, 0)

var pressedSpec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
var handlerRef: EventHandlerRef?
InstallEventHandler(GetApplicationEventTarget(), { _, event, _ in
    var hotKeyID = EventHotKeyID()
    let status = GetEventParameter(
        event,
        EventParamName(kEventParamDirectObject),
        EventParamType(typeEventHotKeyID),
        nil,
        MemoryLayout<EventHotKeyID>.size,
        nil,
        &hotKeyID
    )
    if status == noErr && hotKeyID.signature == signature {
        print("KEY F\(12 + Int(hotKeyID.id))")
    }
    return noErr
}, 1, &pressedSpec, nil, &handlerRef)

var refs: [EventHotKeyRef?] = []
for (i, code) in keyCodes.enumerated() {
    var ref: EventHotKeyRef?
    let id = EventHotKeyID(signature: signature, id: UInt32(i + 1))
    let status = RegisterEventHotKey(code, 0, id, GetApplicationEventTarget(), 0, &ref)
    print(status == noErr ? "READY F\(13 + i)" : "FAILED F\(13 + i)")
    refs.append(ref)
}

RunApplicationEventLoop()
