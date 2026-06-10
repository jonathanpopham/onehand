"""macOS input synthesis via Quartz CGEvents.

All coordinates are in global display space (origin top-left of main display).
Requires the running process to be trusted for Accessibility.
"""

import time

import Quartz
from ApplicationServices import AXIsProcessTrusted

_dragging = False


def trusted() -> bool:
    return bool(AXIsProcessTrusted())


def _cursor_pos():
    ev = Quartz.CGEventCreate(None)
    loc = Quartz.CGEventGetLocation(ev)
    return loc.x, loc.y


def _screen_bounds():
    rect = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    return rect.size.width, rect.size.height


def _post_mouse(ev_type, x, y, button=Quartz.kCGMouseButtonLeft, clicks=1):
    ev = Quartz.CGEventCreateMouseEvent(None, ev_type, (x, y), button)
    Quartz.CGEventSetIntegerValueField(ev, Quartz.kCGMouseEventClickState, clicks)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def move_relative(dx: float, dy: float) -> None:
    x, y = _cursor_pos()
    w, h = _screen_bounds()
    nx = min(max(x + dx, 0), w - 1)
    ny = min(max(y + dy, 0), h - 1)
    if _dragging:
        _post_mouse(Quartz.kCGEventLeftMouseDragged, nx, ny)
    else:
        _post_mouse(Quartz.kCGEventMouseMoved, nx, ny)


def click(button: str = "left") -> None:
    x, y = _cursor_pos()
    if button == "right":
        _post_mouse(Quartz.kCGEventRightMouseDown, x, y, Quartz.kCGMouseButtonRight)
        time.sleep(0.02)
        _post_mouse(Quartz.kCGEventRightMouseUp, x, y, Quartz.kCGMouseButtonRight)
    elif button == "double":
        for n in (1, 2):
            _post_mouse(Quartz.kCGEventLeftMouseDown, x, y, clicks=n)
            time.sleep(0.02)
            _post_mouse(Quartz.kCGEventLeftMouseUp, x, y, clicks=n)
            time.sleep(0.04)
    else:
        # a real click has nonzero duration; zero-length clicks get ignored
        # by some apps (terminals, TUIs, games)
        _post_mouse(Quartz.kCGEventLeftMouseDown, x, y)
        time.sleep(0.03)
        _post_mouse(Quartz.kCGEventLeftMouseUp, x, y)


def mouse_down() -> None:
    global _dragging
    _dragging = True
    x, y = _cursor_pos()
    _post_mouse(Quartz.kCGEventLeftMouseDown, x, y)


def mouse_up() -> None:
    global _dragging
    _dragging = False
    x, y = _cursor_pos()
    _post_mouse(Quartz.kCGEventLeftMouseUp, x, y)


def scroll(dx: float, dy: float) -> None:
    ev = Quartz.CGEventCreateScrollWheelEvent(
        None, Quartz.kCGScrollEventUnitPixel, 2, int(dy), int(dx)
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def type_text(text: str) -> None:
    """Type unicode text into the focused app.

    Uses small chunks with generous inter-event delays; macOS drops
    rapid-fire unicode keyboard events otherwise.
    """
    src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
    for i in range(0, len(text), 8):
        chunk = text[i : i + 8]
        down = Quartz.CGEventCreateKeyboardEvent(src, 0, True)
        Quartz.CGEventKeyboardSetUnicodeString(down, len(chunk), chunk)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        time.sleep(0.012)
        up = Quartz.CGEventCreateKeyboardEvent(src, 0, False)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        time.sleep(0.012)


_KEYCODES = {
    "enter": 36,
    "tab": 48,
    "space": 49,
    "backspace": 51,
    "esc": 53,
    "left": 123,
    "right": 124,
    "down": 125,
    "up": 126,
}

# keys sent with a modifier held
_COMBO = {
    "ctrl-c": (8, Quartz.kCGEventFlagMaskControl),    # 8 = 'c'
    "cmd-a": (0, Quartz.kCGEventFlagMaskCommand),     # 0 = 'a'
    "cmd-c": (8, Quartz.kCGEventFlagMaskCommand),
    "cmd-v": (9, Quartz.kCGEventFlagMaskCommand),     # 9 = 'v'
    "cmd-x": (7, Quartz.kCGEventFlagMaskCommand),     # 7 = 'x'
    "cmd-z": (6, Quartz.kCGEventFlagMaskCommand),     # 6 = 'z'
}


def press_key(name: str) -> None:
    combo = _COMBO.get(name)
    if combo:
        code, flags = combo
        down = Quartz.CGEventCreateKeyboardEvent(None, code, True)
        Quartz.CGEventSetFlags(down, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        time.sleep(0.02)
        up = Quartz.CGEventCreateKeyboardEvent(None, code, False)
        Quartz.CGEventSetFlags(up, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        return
    code = _KEYCODES.get(name)
    if code is None:
        return
    for is_down in (True, False):
        ev = Quartz.CGEventCreateKeyboardEvent(None, code, is_down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
