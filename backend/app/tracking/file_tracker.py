from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class FileActivityHandler(FileSystemEventHandler):
    def __init__(self, on_event):
        self.on_event = on_event

    def on_modified(self, event):
        if not event.is_directory:
            self.on_event("file_modified", event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.on_event("file_created", event.src_path)

    def on_opened(self, event):
        if not event.is_directory:
            self.on_event("file_opened", event.src_path)


class FileTracker:
    def __init__(self, on_event):
        self.on_event = on_event
        self.observer = None
        self.is_running = False

    def start(self, folders: list[str]):
        if self.is_running:
            return

        self.observer = Observer()
        handler = FileActivityHandler(self.on_event)
        for folder in folders:
            path = Path(folder).expanduser()
            if path.exists() and path.is_dir():
                self.observer.schedule(handler, str(path), recursive=True)

        if self.observer.emitters:
            self.observer.start()
            self.is_running = True

    def stop(self):
        if not self.is_running:
            return
        self.observer.stop()
        self.observer.join(timeout=2)
        self.observer = None
        self.is_running = False
