import ctypes
import sys

import psutil
import pyautogui


browser_names = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}


class WindowTracker:
    def get_active_window(self):
        if sys.platform.startswith("win"):
            return self._get_windows_active_window()
        return self._get_pyautogui_window()

    def is_browser(self, app_name: str):
        return app_name.lower() in browser_names

    def is_excluded(self, app_name: str, title: str, excluded_apps: list[str]):
        target = f"{app_name} {title}".lower()
        return any(item.lower() in target for item in excluded_apps)

    def _get_windows_active_window(self):
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()

        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value

        process_id = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

        app_name = "unknown"
        try:
            app_name = psutil.Process(process_id.value).name()
        except psutil.Error:
            pass

        return {"app_name": app_name, "window_title": title, "is_browser": self.is_browser(app_name)}

    def _get_pyautogui_window(self):
        window = pyautogui.getActiveWindow()
        title = window.title if window else ""
        return {"app_name": "unknown", "window_title": title, "is_browser": False}
