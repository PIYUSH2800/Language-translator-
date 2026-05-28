import os
import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Dict, List, Optional

# Add the parent directory to system path if running directly, 
# but relative imports are handled cleanly.
from utils.translator import TranslatorService
from utils.speech import SpeechService
from utils.ui_helpers import THEMES, HoverButton, PlaceholderText, FONT_FAMILY

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HISTORY_FILE = "translation_history.json"


class TranslatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LingoFlux Translator")
        self.root.geometry("1050x700")
        self.root.minsize(950, 600)
        
        # Initialize services
        self.translator_service = TranslatorService()
        self.speech_service = SpeechService()
        
        # Application State
        self.current_theme = "dark"
        self.realtime_enabled = tk.BooleanVar(value=True)
        self.detected_lang_name = ""
        self.debounce_timer: Optional[threading.Timer] = None
        self.history: List[Dict[str, str]] = []
        
        # Fetch languages
        self.languages = self.translator_service.get_supported_languages()
        self.language_names = sorted(list(self.languages.values()))
        self.source_languages = ["Auto Detect"] + self.language_names
        self.target_languages = self.language_names
        
        # Custom elements to update during theme changes
        self.theme_widgets = []
        
        # Load history from file
        self.load_history()
        
        # Build UI
        self.setup_ui()
        self.apply_theme(self.current_theme)

        # Set default selection
        self.src_lang_combo.set("Auto Detect")
        self.dest_lang_combo.set("Spanish")
        
        # Configure keyboard shortcuts
        self.bind_shortcuts()

        # Handle window closure to clean up files
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_history(self):
        """Loads translation history from a local JSON file."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                self.history = []

    def save_history_entry(self, source: str, result: str, src_lang: str, dest_lang: str):
        """Appends a new translation entry to history and saves to disk."""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_lang": src_lang,
            "dest_lang": dest_lang,
            "source_text": source,
            "translated_text": result
        }
        self.history.insert(0, entry)  # Prepend newest
        # Cap history at 50 records
        if len(self.history) > 50:
            self.history = self.history[:50]
            
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def setup_ui(self):
        """Builds the main user interface grid and components."""
        # Main Frame setup
        self.main_container = tk.Frame(self.root, padx=20, pady=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self.theme_widgets.append((self.main_container, "bg"))

        # Configure weights for responsiveness
        self.main_container.columnconfigure(0, weight=4)  # Left panel
        self.main_container.columnconfigure(1, weight=1)  # Swap panel / middle
        self.main_container.columnconfigure(2, weight=4)  # Right panel
        self.main_container.rowconfigure(1, weight=1)     # Large textboxes row
        
        # --- ROW 0: Header Area ---
        self.setup_header()
        
        # --- ROW 1: Content Boxes ---
        self.setup_left_panel()
        self.setup_center_controls()
        self.setup_right_panel()
        
        # --- ROW 2: Bottom Status & Control Bar ---
        self.setup_footer()

    def setup_header(self):
        """Creates the header toolbar containing the title, status, and theme toggle."""
        header_frame = tk.Frame(self.main_container)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        self.theme_widgets.append((header_frame, "bg"))
        
        # App Title
        title_label = tk.Label(
            header_frame, 
            text="LingoFlux", 
            font=(FONT_FAMILY, 20, "bold")
        )
        title_label.pack(side=tk.LEFT)
        self.theme_widgets.append((title_label, "fg_bg"))
        
        subtitle_label = tk.Label(
            header_frame, 
            text="• Translator Engine", 
            font=(FONT_FAMILY, 10, "italic")
        )
        subtitle_label.pack(side=tk.LEFT, padx=(5, 0), pady=(8, 0))
        self.theme_widgets.append((subtitle_label, "fg_bg_sec"))
        
        # Theme Switcher Button
        self.theme_btn = HoverButton(
            header_frame,
            active_background="", active_foreground="", # Configured dynamically in theme applier
            text="🌙 Dark Mode",
            font=(FONT_FAMILY, 9, "bold"),
            padx=12, pady=6,
            command=self.toggle_theme
        )
        self.theme_btn.pack(side=tk.RIGHT)
        self.theme_widgets.append((self.theme_btn, "secondary_btn"))

    def setup_left_panel(self):
        """Sets up the source text area, language selection, and voice controls."""
        # Custom LabelWidget for the border title
        self.left_title_label = tk.Label(
            self.main_container,
            text="Source Text",
            font=(FONT_FAMILY, 10, "bold")
        )
        self.theme_widgets.append((self.left_title_label, "fg_card_title"))
        
        left_frame = tk.LabelFrame(
            self.main_container, 
            labelwidget=self.left_title_label, 
            padx=15, pady=15, 
            borderwidth=1, relief="solid"
        )
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.theme_widgets.append((left_frame, "card"))
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # Dropdown selection
        self.src_lang_combo = ttk.Combobox(
            left_frame, 
            values=self.source_languages, 
            state="readonly",
            font=(FONT_FAMILY, 10)
        )
        self.src_lang_combo.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.src_lang_combo.bind("<<ComboboxSelected>>", self.on_source_language_change)
        
        # Text Area with Placeholder
        self.src_text = PlaceholderText(
            left_frame, 
            placeholder="Type or paste text here to translate...",
            font=(FONT_FAMILY, 11),
            undo=True,
            borderwidth=0,
            highlightthickness=1,
            wrap=tk.WORD,
            height=12
        )
        self.src_text.grid(row=1, column=0, sticky="nsew")
        self.src_text.bind("<KeyRelease>", self.on_source_keypress)
        self.theme_widgets.append((self.src_text, "text_widget"))
        
        # Character & Detected Lang Counter Bar
        self.left_meta_frame = tk.Frame(left_frame)
        self.left_meta_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.theme_widgets.append((self.left_meta_frame, "bg_card"))
        
        self.detected_lang_label = tk.Label(
            self.left_meta_frame,
            text="",
            font=(FONT_FAMILY, 9, "italic")
        )
        self.detected_lang_label.pack(side=tk.LEFT)
        self.theme_widgets.append((self.detected_lang_label, "fg_card_sec"))

        self.char_count_label = tk.Label(
            self.left_meta_frame,
            text="0 characters",
            font=(FONT_FAMILY, 9)
        )
        self.char_count_label.pack(side=tk.RIGHT)
        self.theme_widgets.append((self.char_count_label, "fg_card_sec"))
        
        # Control Buttons
        self.left_actions_frame = tk.Frame(left_frame)
        self.left_actions_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.theme_widgets.append((self.left_actions_frame, "bg_card"))
        
        # Voice Input (Mic)
        self.mic_btn = HoverButton(
            self.left_actions_frame,
            active_background="", active_foreground="",
            text="🎤 Record Voice",
            font=(FONT_FAMILY, 9, "bold"),
            padx=10, pady=5,
            command=self.start_voice_input
        )
        self.mic_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.theme_widgets.append((self.mic_btn, "secondary_btn"))
        
        # TTS Speak Source
        self.speak_src_btn = HoverButton(
            self.left_actions_frame,
            active_background="", active_foreground="",
            text="🔊 Listen",
            font=(FONT_FAMILY, 9, "bold"),
            padx=10, pady=5,
            command=lambda: self.speak_text_thread(self.src_text.get_clean_text(), self.src_lang_combo.get())
        )
        self.speak_src_btn.pack(side=tk.LEFT)
        self.theme_widgets.append((self.speak_src_btn, "secondary_btn"))

    def setup_center_controls(self):
        """Sets up the interactive middle column between translator text areas."""
        center_frame = tk.Frame(self.main_container)
        center_frame.grid(row=1, column=1, sticky="nsew", padx=5)
        self.theme_widgets.append((center_frame, "bg"))
        
        # Center contents alignment
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_rowconfigure(1, weight=0)
        center_frame.grid_rowconfigure(2, weight=0)
        center_frame.grid_rowconfigure(3, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        
        # Swap Button
        self.swap_btn = HoverButton(
            center_frame,
            active_background="", active_foreground="",
            text="⇆ Swap",
            font=(FONT_FAMILY, 10, "bold"),
            padx=12, pady=8,
            command=self.swap_languages
        )
        self.swap_btn.grid(row=1, column=0, pady=(0, 15))
        self.theme_widgets.append((self.swap_btn, "secondary_btn"))
        
        # Real-time translation check
        self.realtime_chk = tk.Checkbutton(
            center_frame,
            text="Real-time",
            variable=self.realtime_enabled,
            font=(FONT_FAMILY, 9),
            cursor="hand2"
        )
        self.realtime_chk.grid(row=2, column=0)
        self.theme_widgets.append((self.realtime_chk, "check_widget"))

    def setup_right_panel(self):
        """Sets up the target translation text area, language selection, and action utilities."""
        # Custom LabelWidget for the border title
        self.right_title_label = tk.Label(
            self.main_container,
            text="Translation",
            font=(FONT_FAMILY, 10, "bold")
        )
        self.theme_widgets.append((self.right_title_label, "fg_card_title"))
        
        right_frame = tk.LabelFrame(
            self.main_container, 
            labelwidget=self.right_title_label, 
            padx=15, pady=15, 
            borderwidth=1, relief="solid"
        )
        right_frame.grid(row=1, column=2, sticky="nsew", padx=(10, 0))
        self.theme_widgets.append((right_frame, "card"))
        
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Dropdown selection
        self.dest_lang_combo = ttk.Combobox(
            right_frame, 
            values=self.target_languages, 
            state="readonly",
            font=(FONT_FAMILY, 10)
        )
        self.dest_lang_combo.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.dest_lang_combo.bind("<<ComboboxSelected>>", lambda e: self.trigger_translation())
        
        # Output Text Box (Read Only but allows copying/selecting text)
        self.dest_text = PlaceholderText(
            right_frame, 
            placeholder="Translation will appear here...",
            font=(FONT_FAMILY, 11),
            borderwidth=0,
            highlightthickness=1,
            wrap=tk.WORD,
            height=12
        )
        self.dest_text.grid(row=1, column=0, sticky="nsew")
        self.theme_widgets.append((self.dest_text, "text_widget"))
        
        # Spacer for structure alignment
        self.right_meta_frame = tk.Frame(right_frame)
        self.right_meta_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.theme_widgets.append((self.right_meta_frame, "bg_card"))
        
        right_spacer = tk.Label(self.right_meta_frame, text="", font=(FONT_FAMILY, 9))
        right_spacer.pack()
        self.theme_widgets.append((right_spacer, "fg_card_sec"))

        # Right Action Buttons
        self.right_actions_frame = tk.Frame(right_frame)
        self.right_actions_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.theme_widgets.append((self.right_actions_frame, "bg_card"))
        
        # Speak Output Text
        self.speak_dest_btn = HoverButton(
            self.right_actions_frame,
            active_background="", active_foreground="",
            text="🔊 Listen",
            font=(FONT_FAMILY, 9, "bold"),
            padx=10, pady=5,
            command=lambda: self.speak_text_thread(self.dest_text.get_clean_text(), self.dest_lang_combo.get())
        )
        self.speak_dest_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.theme_widgets.append((self.speak_dest_btn, "secondary_btn"))
        
        # Copy to Clipboard
        self.copy_btn = HoverButton(
            self.right_actions_frame,
            active_background="", active_foreground="",
            text="📋 Copy Text",
            font=(FONT_FAMILY, 9, "bold"),
            padx=10, pady=5,
            command=self.copy_translation
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.theme_widgets.append((self.copy_btn, "secondary_btn"))
        
        # Clear fields
        self.clear_btn = HoverButton(
            self.right_actions_frame,
            active_background="", active_foreground="",
            text="🧹 Clear All",
            font=(FONT_FAMILY, 9, "bold"),
            padx=10, pady=5,
            command=self.clear_all
        )
        self.clear_btn.pack(side=tk.RIGHT)
        self.theme_widgets.append((self.clear_btn, "secondary_btn"))

    def setup_footer(self):
        """Creates the bottom status bar and core actions (Translate/History/Save)."""
        footer_frame = tk.Frame(self.main_container)
        footer_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(15, 0))
        self.theme_widgets.append((footer_frame, "bg"))

        # Status Label Pill indicator
        self.status_bar = tk.Label(
            footer_frame,
            text=" Ready",
            font=(FONT_FAMILY, 9, "bold"),
            anchor="w",
            padx=10, pady=5,
            borderwidth=1,
            relief="solid"
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.theme_widgets.append((self.status_bar, "status_label"))
        
        # Bottom controls container
        actions_bottom_frame = tk.Frame(footer_frame)
        actions_bottom_frame.pack(side=tk.RIGHT)
        self.theme_widgets.append((actions_bottom_frame, "bg"))

        # View History
        self.history_btn = HoverButton(
            actions_bottom_frame,
            active_background="", active_foreground="",
            text="⏳ History",
            font=(FONT_FAMILY, 9, "bold"),
            padx=12, pady=6,
            command=self.show_history_modal
        )
        self.history_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.theme_widgets.append((self.history_btn, "secondary_btn"))

        # Save to file
        self.save_btn = HoverButton(
            actions_bottom_frame,
            active_background="", active_foreground="",
            text="💾 Save Translation",
            font=(FONT_FAMILY, 9, "bold"),
            padx=12, pady=6,
            command=self.save_translation_to_file
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.theme_widgets.append((self.save_btn, "secondary_btn"))

        # Big Action: Translate Button
        self.translate_btn = HoverButton(
            actions_bottom_frame,
            active_background="", active_foreground="",
            text="⚡ Translate Now",
            font=(FONT_FAMILY, 10, "bold"),
            padx=20, pady=6,
            command=self.trigger_translation
        )
        self.translate_btn.pack(side=tk.LEFT)
        self.theme_widgets.append((self.translate_btn, "accent_btn"))

    def bind_shortcuts(self):
        """Binds useful keyboard shortcuts to application functions."""
        self.root.bind("<Control-Return>", lambda event: self.trigger_translation())
        self.root.bind("<Control-t>", lambda event: self.toggle_theme())
        self.root.bind("<Control-l>", lambda event: self.start_voice_input())
        self.root.bind("<Control-s>", lambda event: self.speak_text_thread(self.dest_text.get_clean_text(), self.dest_lang_combo.get()))
        self.root.bind("<Control-h>", lambda event: self.show_history_modal())

    def update_status(self, message: str, state_type: str = "info"):
        """
        Updates the status bar text and borders reflecting current processes.
        State types: info, success, warning, danger.
        """
        colors = THEMES[self.current_theme]
        
        if state_type == "success":
            bg = colors["success"]
            fg = "#ffffff"
        elif state_type == "warning":
            bg = colors["warning"]
            fg = "#121212"
        elif state_type == "danger":
            bg = colors["danger"]
            fg = "#ffffff"
        else: # info / standard
            bg = colors["secondary_btn"]
            fg = colors["text"]

        self.status_bar.configure(
            text=f" Status: {message}",
            background=bg,
            foreground=fg,
            highlightcolor=colors["border"]
        )

    def apply_theme(self, theme_name: str):
        """Switches colors of all registered components to match the selected theme."""
        self.current_theme = theme_name
        colors = THEMES[theme_name]
        
        # Configure root window background
        self.root.configure(background=colors["bg"])
        
        # Configure global ttk combobox styling
        style = ttk.Style()
        style.theme_use("clam")
        
        # Match combobox listbox and buttons to the theme
        style.configure(
            "TCombobox", 
            fieldbackground=colors["input_bg"],
            background=colors["secondary_btn"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"],
            font=(FONT_FAMILY, 10)
        )
        
        # Map readonly state foreground/background colors for visibility
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["input_bg"])],
            foreground=[("readonly", colors["text"])],
            selectbackground=[("readonly", colors["accent"])],
            selectforeground=[("readonly", colors["accent_text"])]
        )
        
        # Configure option database for the dropdown popup listbox components
        self.root.option_add("*TCombobox*Listbox.background", colors["input_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", colors["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", colors["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", colors["accent_text"])
        self.root.option_add("*TCombobox*Listbox.font", (FONT_FAMILY, 10))
        
        # Loop through registered items
        for widget, style_type in self.theme_widgets:
            try:
                if style_type == "bg":
                    widget.configure(background=colors["bg"])
                elif style_type == "fg_card_title":
                    widget.configure(
                        foreground=colors["accent"],
                        background=colors["bg"]
                    )
                elif style_type == "card":
                    widget.configure(
                        background=colors["card_bg"],
                        foreground=colors["text"],
                        highlightbackground=colors["border"],
                        highlightcolor=colors["border"]
                    )
                elif style_type == "bg_card":
                    widget.configure(background=colors["card_bg"])
                elif style_type == "fg_bg":
                    widget.configure(foreground=colors["text"], background=colors["bg"])
                elif style_type == "fg_bg_sec":
                    widget.configure(foreground=colors["text_secondary"], background=colors["bg"])
                elif style_type == "fg_card_sec":
                    widget.configure(foreground=colors["text_secondary"], background=colors["card_bg"])
                elif style_type == "text_widget":
                    widget.configure(
                        background=colors["input_bg"],
                        highlightbackground=colors["border"],
                        highlightcolor=colors["accent"],
                        insertbackground=colors["input_text"] # Caret color
                    )
                    widget.update_placeholder_color(colors["text_secondary"], colors["input_text"])
                elif style_type == "check_widget":
                    widget.configure(
                        background=colors["bg"],
                        foreground=colors["text"],
                        activebackground=colors["bg"],
                        activeforeground=colors["text"],
                        selectcolor=colors["input_bg"]
                    )
                elif style_type == "status_label":
                    # Color is set dynamically, but update default border
                    widget.configure(
                        background=colors["secondary_btn"],
                        foreground=colors["text"],
                        highlightbackground=colors["border"]
                    )
                elif style_type == "secondary_btn":
                    widget.update_colors(
                        bg=colors["secondary_btn"],
                        fg=colors["text"],
                        active_bg=colors["secondary_btn_hover"],
                        active_fg=colors["text"]
                    )
                elif style_type == "accent_btn":
                    widget.update_colors(
                        bg=colors["accent"],
                        fg=colors["accent_text"],
                        active_bg=colors["accent_hover"],
                        active_fg=colors["accent_text"]
                    )
            except Exception as e:
                logger.error(f"Error coloring widget: {e}")

        # Update specific toggle text
        if theme_name == "dark":
            self.theme_btn.configure(text="☀️ Light Mode")
        else:
            self.theme_btn.configure(text="🌙 Dark Mode")

        # Force redrawing status bar matching theme
        self.update_status("Ready")

    def toggle_theme(self):
        """Action handler to cycle between dark and light themes."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(new_theme)

    def on_source_language_change(self, event=None):
        """Triggers updates when source language changes (like toggling detected language)."""
        src = self.src_lang_combo.get()
        if src != "Auto Detect":
            self.detected_lang_label.configure(text="")
        else:
            if self.detected_lang_name:
                self.detected_lang_label.configure(text=f"Detected: {self.detected_lang_name}")
        
        # Re-translate if active text exists
        self.trigger_translation()

    def on_source_keypress(self, event):
        """Monitors typing inside source text, handling char limits and real-time translation."""
        content = self.src_text.get_clean_text()
        char_len = len(content)
        self.char_count_label.configure(text=f"{char_len} characters")

        # Block translation checks if real-time translation is disabled or content is blank
        if not self.realtime_enabled.get():
            return

        # Debounce logic: cancel previous timer and schedule a translation in 700ms
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        self.debounce_timer = threading.Timer(0.7, self.trigger_translation)
        self.debounce_timer.start()

    def trigger_translation(self):
        """Launches a translation process in a background thread."""
        text = self.src_text.get_clean_text()
        if not text.strip():
            self.dest_text.set_text("")
            return

        src_lang = self.src_lang_combo.get()
        dest_lang = self.dest_lang_combo.get()

        self.update_status("Translating...", "info")
        
        # Start translation thread
        t = threading.Thread(
            target=self.perform_translation_thread, 
            args=(text, src_lang, dest_lang), 
            daemon=True
        )
        t.start()

    def perform_translation_thread(self, text: str, src_lang: str, dest_lang: str):
        """Async worker task executing the translation API call."""
        success, result, detected_src = self.translator_service.translate_text(
            text, src_lang, dest_lang
        )
        
        # Schedule GUI updates safely on main thread
        self.root.after(0, lambda: self.handle_translation_result(success, result, detected_src, text, src_lang, dest_lang))

    def handle_translation_result(self, success: bool, result: str, detected_src: str, original_text: str, src_lang: str, dest_lang: str):
        """Processes translation outputs and pushes updates to the GUI."""
        if success:
            self.dest_text.set_text(result)
            self.update_status("Translation completed successfully.", "success")
            
            # Show detected language if "Auto Detect" was selected
            if src_lang == "Auto Detect" and detected_src:
                self.detected_lang_name = detected_src
                self.detected_lang_label.configure(text=f"Detected: {detected_src}")
            else:
                self.detected_lang_name = ""
                self.detected_lang_label.configure(text="")
                
            # Log successful translation to history database
            self.save_history_entry(original_text, result, src_lang if src_lang != "Auto Detect" else f"Auto ({detected_src})", dest_lang)
        else:
            # Display error message in output and update status bar
            self.dest_text.set_text(result)
            self.update_status("Failed to translate.", "danger")

    def swap_languages(self):
        """Swaps source and target languages and shifts texts."""
        src = self.src_lang_combo.get()
        dest = self.dest_lang_combo.get()

        # Cannot swap to auto detect in destination
        if src == "Auto Detect":
            # If we have a detected language, use that instead of Auto Detect
            if self.detected_lang_name:
                src = self.detected_lang_name
            else:
                # Fallback to English
                src = "English"

        self.src_lang_combo.set(dest)
        self.dest_lang_combo.set(src)

        # Swap texts
        src_val = self.src_text.get_clean_text()
        dest_val = self.dest_text.get_clean_text()
        
        self.src_text.set_text(dest_val)
        self.dest_text.set_text(src_val)

        # Count character updates
        self.char_count_label.configure(text=f"{len(dest_val)} characters")
        
        # Run Translation
        self.trigger_translation()

    def speak_text_thread(self, text: str, lang: str):
        """Launches a TTS task running on a background thread."""
        if not text.strip():
            self.update_status("Nothing to say.", "warning")
            return

        # Resolve code
        lang_code = self.translator_service.get_lang_code(lang)

        # Stop existing playback if active
        if self.speech_service.is_playing_tts:
            self.speech_service.stop_speaking()
            self.update_status("Speech playback stopped.")
            return

        t = threading.Thread(
            target=self.speech_service.speak_text,
            args=(text, lang_code, self.handle_speech_status),
            daemon=True
        )
        t.start()

    def handle_speech_status(self, status: str):
        """Callback task to route speech engine statuses to UI."""
        state = "info"
        if "error" in status.lower() or "failed" in status.lower():
            state = "danger"
        elif "speaking" in status.lower():
            state = "warning"
        
        self.root.after(0, lambda: self.update_status(status, state))

    def start_voice_input(self):
        """Starts mic capture and SpeechRecognition in background."""
        src_lang = self.src_lang_combo.get()
        # Resolve lang code (default to 'en' if auto, google needs a region tag like en-US, es-ES)
        lang_code = self.translator_service.get_lang_code(src_lang)
        
        # Mapping clean generic language codes to recognition codes
        code_mapping = {
            "en": "en-US", "es": "es-ES", "fr": "fr-FR", "de": "de-DE", 
            "it": "it-IT", "zh": "zh-CN", "ja": "ja-JP", "ru": "ru-RU", 
            "pt": "pt-BR", "hi": "hi-IN", "ar": "ar-SA"
        }
        rec_code = code_mapping.get(lang_code, lang_code)

        t = threading.Thread(
            target=self.speech_service.recognize_speech,
            args=(rec_code, self.handle_voice_status, self.handle_voice_success),
            daemon=True
        )
        t.start()

    def handle_voice_status(self, status: str):
        """Callback to display voice processing state to the user."""
        state = "info"
        if "error" in status.lower():
            state = "danger"
        elif "listening" in status.lower() or "speak" in status.lower():
            state = "warning"
            
        self.root.after(0, lambda: self.update_status(status, state))

    def handle_voice_success(self, text: str):
        """Inserts transcribed speech into the input field."""
        self.root.after(0, lambda: self._insert_voice_text(text))

    def _insert_voice_text(self, text: str):
        self.src_text.set_text(text)
        self.char_count_label.configure(text=f"{len(text)} characters")
        self.trigger_translation()

    def copy_translation(self):
        """Copies translated output to the system clipboard."""
        text = self.dest_text.get_clean_text()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.update_status("Copied translation to clipboard!", "success")
        else:
            self.update_status("No text available to copy.", "warning")

    def clear_all(self):
        """Resets both text frames to empty."""
        self.src_text.set_text("")
        self.dest_text.set_text("")
        self.detected_lang_label.configure(text="")
        self.char_count_label.configure(text="0 characters")
        self.update_status("Cleared text fields.")

    def save_translation_to_file(self):
        """Prompts user and saves the output to a text file."""
        text = self.dest_text.get_clean_text()
        if not text:
            self.update_status("Nothing to save.", "warning")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Markdown Files", "*.md"), ("All Files", "*.*")],
            title="Save Translation"
        )
        
        if file_path:
            try:
                src_lang = self.src_lang_combo.get()
                dest_lang = self.dest_lang_combo.get()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"=== LingoFlux Translation Export ===\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"From ({src_lang}):\n{self.src_text.get_clean_text()}\n\n")
                    f.write(f"To ({dest_lang}):\n{text}\n")
                self.update_status(f"Translation successfully saved to file!", "success")
            except Exception as e:
                logger.error(f"Failed to write file: {e}")
                self.update_status(f"Failed to save file: {str(e)}", "danger")

    def show_history_modal(self):
        """Displays a clean modal listing previous translations."""
        history_window = tk.Toplevel(self.root)
        history_window.title("Translation History")
        history_window.geometry("600x450")
        history_window.transient(self.root)
        history_window.grab_set()

        colors = THEMES[self.current_theme]
        history_window.configure(background=colors["card_bg"])

        # Title Label
        title = tk.Label(
            history_window,
            text="Translation History Log",
            font=(FONT_FAMILY, 14, "bold"),
            background=colors["card_bg"],
            foreground=colors["text"]
        )
        title.pack(anchor="w", padx=15, pady=15)

        # Container Frame
        log_frame = tk.Frame(history_window, background=colors["card_bg"])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Scrollbar and Canvas for scrolling elements
        canvas = tk.Canvas(log_frame, borderwidth=0, highlightthickness=0, background=colors["card_bg"])
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, background=colors["card_bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not self.history:
            no_history = tk.Label(
                scrollable_frame,
                text="No translations recorded yet.",
                font=(FONT_FAMILY, 10, "italic"),
                background=colors["card_bg"],
                foreground=colors["text_secondary"]
            )
            no_history.pack(pady=20, fill=tk.X)
        else:
            # Build list of history panels
            for idx, entry in enumerate(self.history):
                item_frame = tk.Frame(
                    scrollable_frame, 
                    background=colors["input_bg"], 
                    padx=10, pady=8,
                    highlightbackground=colors["border"],
                    highlightthickness=1
                )
                item_frame.pack(fill=tk.X, pady=(0, 10), padx=2)
                item_frame.columnconfigure(0, weight=1)

                meta_txt = f"{entry['timestamp']}  •  {entry['source_lang']} ➔ {entry['dest_lang']}"
                meta_label = tk.Label(
                    item_frame, 
                    text=meta_txt, 
                    font=(FONT_FAMILY, 8, "bold"),
                    background=colors["input_bg"],
                    foreground=colors["accent"],
                    anchor="w"
                )
                meta_label.grid(row=0, column=0, sticky="ew")

                src_lbl = tk.Label(
                    item_frame,
                    text=f"In: {entry['source_text'][:60] + '...' if len(entry['source_text']) > 60 else entry['source_text']}",
                    font=(FONT_FAMILY, 9),
                    background=colors["input_bg"],
                    foreground=colors["text"],
                    anchor="w"
                )
                src_lbl.grid(row=1, column=0, sticky="ew", pady=(4, 0))

                dest_lbl = tk.Label(
                    item_frame,
                    text=f"Out: {entry['translated_text'][:60] + '...' if len(entry['translated_text']) > 60 else entry['translated_text']}",
                    font=(FONT_FAMILY, 9, "bold"),
                    background=colors["input_bg"],
                    foreground=colors["text_secondary"],
                    anchor="w"
                )
                dest_lbl.grid(row=2, column=0, sticky="ew")

                # Restore action button
                def load_restore(text=entry['source_text'], src=entry['source_lang'].split(' ')[0], dest=entry['dest_lang']):
                    self.src_text.set_text(text)
                    self.src_lang_combo.set(src if "Auto" not in src else "Auto Detect")
                    self.dest_lang_combo.set(dest)
                    self.trigger_translation()
                    history_window.destroy()

                restore_btn = HoverButton(
                    item_frame,
                    active_background=colors["accent_hover"],
                    active_foreground=colors["accent_text"],
                    text="Restore",
                    background=colors["secondary_btn"],
                    foreground=colors["text"],
                    font=(FONT_FAMILY, 8, "bold"),
                    padx=6, pady=3,
                    command=load_restore
                )
                restore_btn.grid(row=0, column=1, rowspan=3, padx=(10, 0), sticky="ns")

        # Bottom clear history button
        def clear_history():
            if messagebox.askyesno("Clear History", "Are you sure you want to delete all translation logs?", parent=history_window):
                self.history = []
                if os.path.exists(HISTORY_FILE):
                    try:
                        os.remove(HISTORY_FILE)
                    except Exception:
                        pass
                history_window.destroy()
                self.update_status("History cleared.")

        footer = tk.Frame(history_window, background=colors["card_bg"], pady=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        clear_btn = HoverButton(
            footer,
            active_background=colors["danger"],
            active_foreground="#ffffff",
            text="🗑️ Clear All Logs",
            background=colors["secondary_btn"],
            foreground=colors["text"],
            font=(FONT_FAMILY, 9, "bold"),
            padx=12, pady=5,
            command=clear_history
        )
        clear_btn.pack(side=tk.LEFT, padx=15)

        close_btn = HoverButton(
            footer,
            active_background=colors["secondary_btn_hover"],
            active_foreground=colors["text"],
            text="Close",
            background=colors["secondary_btn"],
            foreground=colors["text"],
            font=(FONT_FAMILY, 9, "bold"),
            padx=12, pady=5,
            command=history_window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=15)

    def on_close(self):
        """Cleans up system resources (TTS active locks and audio files) and quits."""
        self.speech_service.stop_speaking()
        self.speech_service.clean_temp_files()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()
