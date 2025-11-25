"""
Theme Manager for Light/Dark Mode
Handles theme switching and persistence
"""
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import Config


class ThemeManager:
    """Manages application themes (light/dark mode)"""

    THEMES = {
        'light': {
            'name': 'Light Mode',
            'bg_primary': '#FFFFFF',
            'bg_secondary': '#F3F2F1',
            'bg_header': '#FAFAFA',
            'text_primary': '#323130',
            'text_secondary': '#666666',
            'border': '#E1DFDD',
            'accent_blue': '#0078D4',
            'accent_green': '#107C10',
            'card_bg': '#FFFFFF',
            'hover': '#F3F2F1',
            'selection_bg': '#CCE4F7',
            'selection_fg': '#000000'
        },
        'dark': {
            'name': 'Dark Mode',
            # Primary backgrounds
            'bg_primary': '#1E1E1E',           # Main background (softer than pure black)
            'bg_secondary': '#252526',         # Secondary panels
            'bg_header': '#2D2D30',            # Header/ribbon area
            'card_bg': '#252526',              # Card backgrounds
            'hover': '#2A2D2E',                # Hover states

            # Text colors
            'text_primary': '#CCCCCC',         # Primary text (easy on eyes)
            'text_secondary': '#858585',       # Secondary text (not too dim)
            'text_muted': '#6A6A6A',           # Very muted text

            # Borders and separators
            'border': '#3E3E42',               # Border color
            'separator': '#454545',            # Separator lines

            # Accent colors (slightly muted for dark mode)
            'accent_blue': '#4FC3F7',          # Softer blue (not harsh)
            'accent_green': '#66BB6A',         # Softer green
            'accent_orange': '#FFA726',        # Warning/info color

            # Button states
            'button_bg': '#2D2D30',
            'button_hover': '#3E3E42',
            'button_active': '#4A4A4A',

            # Data grid colors
            'grid_bg': '#1E1E1E',
            'grid_alt_row': '#252526',         # Alternating row color
            'grid_header': '#2D2D30',
            'grid_border': '#3E3E42',
            'grid_selected': '#264F78',        # Selected row (VS Code blue)
            'grid_text': '#CCCCCC',

            # Input fields
            'input_bg': '#2D2D30',
            'input_border': '#3E3E42',
            'input_focus': '#4FC3F7',

            # Status colors
            'success': '#66BB6A',
            'error': '#F44336',
            'warning': '#FFA726',

            # Selection
            'selection_bg': '#264F78',
            'selection_fg': '#FFFFFF'
        }
    }

    def __init__(self):
        self.current_theme = self.load_saved_theme()
        self.theme_callbacks = []  # Callbacks to notify when theme changes

    def load_saved_theme(self):
        """Load saved theme preference"""
        try:
            settings_file = Config.get_app_data_dir() / 'settings.json'
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('theme', 'light')
        except Exception as e:
            print(f"Failed to load theme: {e}")

        return 'light'  # Default to light mode

    def save_theme(self, theme_name):
        """Save theme preference"""
        try:
            settings_file = Config.get_app_data_dir() / 'settings.json'
            settings = {}

            if settings_file.exists():
                try:
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                except:
                    settings = {}

            settings['theme'] = theme_name

            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

        except Exception as e:
            print(f"Failed to save theme: {e}")

    def get_theme_colors(self, theme_name=None):
        """Get color scheme for theme"""
        theme = theme_name or self.current_theme
        return self.THEMES.get(theme, self.THEMES['light']).copy()

    def apply_theme(self, root, theme_name):
        """Apply theme to tkinter root window and all ttk styles"""
        self.current_theme = theme_name
        self.save_theme(theme_name)

        colors = self.get_theme_colors(theme_name)
        style = ttk.Style()

        # ==================== FRAMES ====================
        style.configure('TFrame', background=colors['bg_primary'])
        style.configure('Card.TFrame', background=colors['card_bg'], relief='raised')
        style.configure('Header.TFrame', background=colors['bg_header'])
        style.configure('Ribbon.TFrame', background=colors['bg_secondary'])
        style.configure('WorkflowCompact.TFrame', background=colors.get('bg_secondary', colors['bg_header']))
        style.configure('QueueCard.TFrame',
                       background=colors['card_bg'],
                       relief='raised',
                       borderwidth=1)

        # ==================== LABELS ====================
        style.configure('TLabel',
                       background=colors['bg_primary'],
                       foreground=colors['text_primary'])

        style.configure('HeaderTitle.TLabel',
                       font=('Segoe UI', 11, 'bold'),
                       foreground=colors['accent_blue'],
                       background=colors['bg_header'])

        style.configure('HeaderText.TLabel',
                       font=('Segoe UI', 11),
                       foreground=colors['text_secondary'],
                       background=colors['bg_header'])

        style.configure('UserInfo.TLabel',
                       font=('Segoe UI', 9),
                       foreground=colors['text_secondary'],
                       background=colors['bg_header'])

        # ==================== BUTTONS ====================
        style.configure('TButton',
                       background=colors.get('button_bg', colors['bg_secondary']),
                       foreground=colors['text_primary'],
                       borderwidth=1,
                       relief='flat',
                       padding=(8, 4))

        style.map('TButton',
                 background=[('active', colors.get('button_hover', colors['hover'])),
                            ('pressed', colors.get('button_active', colors['bg_secondary']))],
                 foreground=[('active', colors['text_primary'])])

        # Header buttons
        style.configure('HeaderButton.TButton',
                       font=('Segoe UI', 9),
                       padding=(8, 4))

        # Ribbon buttons
        style.configure('RibbonButton.TButton',
                       font=('Segoe UI', 10),
                       padding=(10, 5))

        style.configure('RibbonButtonSuccess.TButton',
                       background=colors.get('accent_green', '#66BB6A'),
                       foreground='#FFFFFF',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(10, 5))

        style.map('RibbonButtonSuccess.TButton',
                 background=[('active', '#81C784' if theme_name == 'dark' else '#0F9D0F')])

        # Accent buttons
        style.configure('Accent.TButton',
                       background=colors['accent_blue'],
                       foreground='#FFFFFF',
                       font=('Segoe UI', 10, 'bold'))

        style.configure('Success.TButton',
                       background=colors.get('accent_green', '#66BB6A'),
                       foreground='#FFFFFF')

        style.configure('ThemeToggle.TButton',
                       font=('Segoe UI', 9),
                       padding=(8, 4))

        style.configure('Logout.TButton',
                       font=('Segoe UI', 9),
                       padding=(8, 4))

        # ==================== ENTRIES ====================
        style.configure('TEntry',
                       fieldbackground=colors.get('input_bg', colors['bg_primary']),
                       foreground=colors['text_primary'],
                       bordercolor=colors.get('input_border', colors['border']))

        # ==================== COMBOBOX ====================
        style.configure('TCombobox',
                       fieldbackground=colors.get('input_bg', colors['bg_primary']),
                       foreground=colors['text_primary'],
                       background=colors['bg_secondary'],
                       bordercolor=colors['border'])

        # ==================== NOTEBOOK (TABS) ====================
        style.configure('TNotebook',
                       background=colors['bg_primary'],
                       bordercolor=colors['border'])

        style.configure('TNotebook.Tab',
                       background=colors['bg_secondary'],
                       foreground=colors['text_primary'],
                       padding=[10, 5],
                       borderwidth=0)

        style.map('TNotebook.Tab',
                 background=[('selected', colors['bg_primary'])],
                 foreground=[('selected', colors['text_primary'])],
                 expand=[('selected', [1, 1, 1, 0])])

        # ==================== TREEVIEW ====================
        style.configure('Treeview',
                       background=colors['bg_primary'],
                       foreground=colors['text_primary'],
                       fieldbackground=colors['bg_primary'],
                       bordercolor=colors['border'])

        style.map('Treeview',
                 background=[('selected', colors['selection_bg'])],
                 foreground=[('selected', colors['selection_fg'])])

        # ==================== CHECKBUTTON ====================
        style.configure('TCheckbutton',
                       background=colors['card_bg'],
                       foreground=colors['text_primary'])

        # ==================== SCROLLBAR ====================
        style.configure('Vertical.TScrollbar',
                       background=colors['bg_secondary'],
                       troughcolor=colors['bg_primary'],
                       bordercolor=colors['border'])

        # Configure root window
        root.configure(bg=colors['bg_primary'])

        # Notify all registered callbacks
        for callback in self.theme_callbacks:
            try:
                callback(colors)
            except Exception as e:
                print(f"Error in theme callback: {e}")

        return colors

    def register_callback(self, callback):
        """Register a callback to be notified when theme changes"""
        self.theme_callbacks.append(callback)

    def toggle_theme(self):
        """Toggle between light and dark mode"""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        return new_theme

    def get_theme_icon_text(self):
        """Get the icon and text for theme toggle button"""
        if self.current_theme == 'light':
            return "🌙 Dark Mode"
        else:
            return "☀️ Light Mode"


# Test/demo code
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Theme Manager Test")
    root.geometry("600x400")

    theme_mgr = ThemeManager()

    # Apply initial theme
    colors = theme_mgr.apply_theme(root, theme_mgr.current_theme)

    # Create test UI
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Theme Manager Test", style='HeaderTitle.TLabel').pack(pady=10)
    ttk.Label(frame, text=f"Current theme: {theme_mgr.current_theme}").pack(pady=5)

    def toggle():
        new_theme = theme_mgr.toggle_theme()
        theme_mgr.apply_theme(root, new_theme)
        label.config(text=f"Current theme: {new_theme}")
        btn.config(text=theme_mgr.get_theme_icon_text())

    label = ttk.Label(frame, text=f"Current theme: {theme_mgr.current_theme}")
    label.pack(pady=10)

    btn = ttk.Button(frame, text=theme_mgr.get_theme_icon_text(), command=toggle)
    btn.pack(pady=10)

    ttk.Label(frame, text="This is a test label").pack(pady=5)
    ttk.Entry(frame).pack(pady=5)
    ttk.Button(frame, text="Test Button").pack(pady=5)

    root.mainloop()
