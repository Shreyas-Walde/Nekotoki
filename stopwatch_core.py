import sys
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

class StopwatchCore(QObject):
    """ Handles the core timing logic and state of the stopwatch. """
    # Signals
    # Emits: time_str (HH:MM:SS), centiseconds_str (.CC)
    time_updated = pyqtSignal(str, str)
    # Emits: is_running (bool)
    status_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.centiseconds = 0
        self._is_running = False

        self.timer = QTimer(self)
        # Update every 50ms (20 Hz) - Lower frequency for less CPU usage
        self.timer.setInterval(50) # Was 10ms
        self.timer.timeout.connect(self._update_time)

    @property
    def is_running(self):
        return self._is_running

    def _update_time(self):
        """ Internal method to advance time and emit signal. """
        # Adjust calculation for 50ms interval (increment by 5 centiseconds)
        self.centiseconds += 5 # Interval is 50ms (0.05 seconds)
        if self.centiseconds >= 100:
            carry_seconds = self.centiseconds // 100
            self.centiseconds %= 100
            self.seconds += carry_seconds
            if self.seconds == 60:
                self.seconds = 0
                self.minutes += 1
                if self.minutes == 60:
                    self.minutes = 0
                    self.hours += 1 # Reset hours if needed? Or let it run? Let's let it run for now.

        time_str = f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}"
        centiseconds_str = f".{self.centiseconds:02d}"
        self.time_updated.emit(time_str, centiseconds_str)

    def start(self):
        """ Starts the timer if not already running. """
        if not self._is_running:
            self.timer.start()
            self._is_running = True
            self.status_changed.emit(self._is_running)

    def pause(self):
        """ Pauses the timer if running. """
        if self._is_running:
            self.timer.stop()
            self._is_running = False
            self.status_changed.emit(self._is_running)

    def toggle(self):
        """ Toggles the timer between running and paused states. """
        if self._is_running:
            self.pause()
        else:
            self.start()

    def reset(self):
        """ Resets the timer to zero and stops it. """
        was_running = self._is_running
        self.timer.stop()
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.centiseconds = 0
        self._is_running = False
        # Emit initial time state after reset
        self.time_updated.emit("00:00:00", ".00")
        # Emit status change only if it was running before reset
        if was_running:
            self.status_changed.emit(self._is_running)

# Removed the __main__ block as this module is not intended to be run directly. 