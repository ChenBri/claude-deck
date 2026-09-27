# Global F13-F20 hotkeys for the daemon on Windows (docs/SAFETY.md rule 1).
# RegisterHotKey claims each key system-wide, so a press from the deck's HID
# gadget reaches nothing but this process. Prints one line per event on
# stdout for daemon/src/link/hotkeys.ts:
#   READY F13 / FAILED F13   once per key at start-up
#   KEY F13                  on every press
# Needs no admin rights. Runs until the daemon kills it.

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class DeckHotkeys {
    [StructLayout(LayoutKind.Sequential)]
    public struct MSG {
        public IntPtr hwnd;
        public uint message;
        public IntPtr wParam;
        public IntPtr lParam;
        public uint time;
        public int x;
        public int y;
    }

    [DllImport("user32.dll", SetLastError = true)]
    static extern bool RegisterHotKey(IntPtr hWnd, int id, uint modifiers, uint vk);

    [DllImport("user32.dll")]
    static extern int GetMessage(out MSG msg, IntPtr hWnd, uint min, uint max);

    const uint MOD_NOREPEAT = 0x4000;
    const uint VK_F13 = 0x7C;
    const uint WM_HOTKEY = 0x0312;

    public static void Run() {
        // id 1..8 is F13..F20. Registered with no window, so WM_HOTKEY lands
        // on this thread's own message queue.
        for (int i = 0; i < 8; i++) {
            bool ok = RegisterHotKey(IntPtr.Zero, i + 1, MOD_NOREPEAT, VK_F13 + (uint)i);
            Console.WriteLine((ok ? "READY F" : "FAILED F") + (13 + i));
        }
        MSG msg;
        while (GetMessage(out msg, IntPtr.Zero, 0, 0) > 0) {
            if (msg.message == WM_HOTKEY) {
                Console.WriteLine("KEY F" + (12 + msg.wParam.ToInt32()));
            }
        }
    }
}
"@

[DeckHotkeys]::Run()
