import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

# Font Family Configuration
FONT_FAMILY = "Segoe UI"

# Premium modern themes
THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#0f172a",              # Deep Slate blue-black
        "card_bg": "#1e293b",         # Slate blue card background
        "input_bg": "#0f172a",        # Slate dark input area
        "input_text": "#f8fafc",      # Clean white text in inputs
        "text": "#f1f5f9",            # Main body text
        "text_secondary": "#94a3b8",   # Statuses and helper text
        "accent": "#38bdf8",          # Primary accent: Sky Cyber-Blue
        "accent_hover": "#0ea5e9",    # Accent hover
        "accent_text": "#0f172a",     # Text color on active buttons
        "secondary_btn": "#334155",   # Slate blue secondary buttons
        "secondary_btn_hover": "#475569", # Hover for secondary
        "border": "#334155",          # Border divider
        "success": "#34d399",         # Mint green success
        "danger": "#f87171",          # Salmon red danger
        "warning": "#fbbf24"          # Bright gold warning
    },
    "light": {
        "bg": "#fafafa",              # Pure snow-grey background
        "card_bg": "#ffffff",         # Clean white cards
        "input_bg": "#f4f4f5",        # Zinc light input area
        "input_text": "#18181b",      # Charcoal text in inputs
        "text": "#18181b",            # Main body text
        "text_secondary": "#71717a",   # Statuses and helper text
        "accent": "#6366f1",          # Primary accent: Indigo violet
        "accent_hover": "#4f46e5",    # Accent hover
        "accent_text": "#ffffff",     # Text color on active buttons
        "secondary_btn": "#e4e4e7",   # Zinc light secondary buttons
        "secondary_btn_hover": "#d4d4d8", # Hover for secondary
        "border": "#e4e4e7",          # Border divider
        "success": "#10b981",         # Emerald green success
        "danger": "#ef4444",          # Ruby red danger
        "warning": "#f59e0b"          # Amber gold warning
    }
}

class HoverButton(tk.Button):
    """
    Custom Tkinter Button that supports flat modern styling,
    hover highlights, and dynamic updates for theme switching.
    """
    def __init__(
        self, 
        master, 
        active_background: str, 
        active_foreground: str, 
        **kwargs
    ):
        # Apply standard modern visual configurations
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("borderwidth", 0)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("cursor", "hand2")
        
        super().__init__(master, **kwargs)
        
        self.default_bg = self.cget("background")
        self.default_fg = self.cget("foreground")
        self.active_bg = active_background
        self.active_fg = active_foreground
        
        # Bind hover events
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(background=self.active_bg, foreground=self.active_fg)

    def on_leave(self, event):
        self.configure(background=self.default_bg, foreground=self.default_fg)
        
    def update_colors(self, bg: str, fg: str, active_bg: str, active_fg: str):
        """Updates the default and active colors when themes change."""
        self.default_bg = bg
        self.default_fg = fg
        self.active_bg = active_bg
        self.active_fg = active_fg
        self.configure(background=bg, foreground=fg)


class PlaceholderText(tk.Text):
    """
    Custom Text area widget supporting native-feeling placeholder text
    and convenient text reading/clearing utilities.
    """
    def __init__(self, master, placeholder: str = "", placeholder_color: str = "#888888", **kwargs):
        super().__init__(master, **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.default_fg = self.cget("foreground")
        self.is_placeholder_active = False

        # Bind events
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
        self.show_placeholder()

    def show_placeholder(self):
        """Displays placeholder if the editor is empty."""
        if not self.get("1.0", tk.END).strip():
            self.is_placeholder_active = True
            self.insert("1.0", self.placeholder)
            self.configure(foreground=self.placeholder_color)

    def clear_placeholder(self):
        """Clears the placeholder when the widget gets focus."""
        if self.is_placeholder_active:
            self.delete("1.0", tk.END)
            self.configure(foreground=self.default_fg)
            self.is_placeholder_active = False

    def _on_focus_in(self, event):
        self.clear_placeholder()

    def _on_focus_out(self, event):
        if not self.get("1.0", tk.END).strip():
            self.show_placeholder()

    def get_clean_text(self) -> str:
        """Retrieves user text or returns empty string if placeholder is active."""
        if self.is_placeholder_active:
            return ""
        return self.get("1.0", tk.END).strip()

    def set_text(self, text: str):
        """Safely inserts new text, clearing placeholder if present."""
        self.clear_placeholder()
        self.delete("1.0", tk.END)
        if text:
            self.is_placeholder_active = False
            self.insert("1.0", text)
            self.configure(foreground=self.default_fg)
        else:
            self.show_placeholder()

    def update_placeholder_color(self, p_color: str, text_color: str):
        """Updates text colors dynamically when theme is switched."""
        self.placeholder_color = p_color
        self.default_fg = text_color
        if self.is_placeholder_active:
            self.configure(foreground=p_color)
        else:
            self.configure(foreground=text_color)
