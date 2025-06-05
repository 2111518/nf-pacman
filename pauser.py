from typing import Optional, Callable

class Pause:
    def __init__(self, paused: bool = False) -> None:
        self.paused: bool = paused
        self.timer: float = 0.0
        self.pauseTime: Optional[float] = None
        self.func: Optional[Callable] = None

    def update(self, dt: float) -> Optional[Callable]:
        if self.paused and self.pauseTime is not None: # Only decrement timer if it's a timed pause and actually paused
            self.timer += dt
            if self.timer >= self.pauseTime:
                self.timer = 0.0
                self.paused = False # Automatically unpause after timed duration
                expired_func = self.func
                self.func = None # Clear function after it's returned
                # self.pauseTime = None # Keep pauseTime to indicate it was a timed pause, or clear it if one-shot
                return expired_func
        return None

    def setPause(self, should_be_paused: bool, pauseTime: Optional[float] = None, func: Optional[Callable] = None) -> None:
        self.paused = should_be_paused
        self.timer = 0.0 # Reset timer whenever pause state is explicitly set
        self.func = func
        self.pauseTime = pauseTime
        # No flip() here, state is set directly by should_be_paused

    def flip(self) -> None: # Keep flip if manual toggle is needed elsewhere, though risky
        self.paused = not self.paused
        self.timer = 0.0 # Reset timer on flip too
