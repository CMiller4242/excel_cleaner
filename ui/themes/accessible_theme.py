"""
Accessible Theme for Universal Excel Tool
High contrast, large fonts, simple design

FIXED: Button text now visible with proper colors
"""

import tkinter as tk
from tkinter import ttk


class AccessibleTheme:
    """Theme optimized for accessibility and older users"""
    
    # High contrast color palette
    COLORS = {
        'bg': '#FFFFFF',           # Pure white background
        'fg': '#000000',           # Pure black text
        'primary': '#0052CC',      # Strong blue
        'primary_hover': '#0747A6', # Darker blue on hover
        'success': '#00875A',      # Strong green
        'warning': '#FF8B00',      # Strong orange
        'danger': '#DE350B',       # Strong red
        'border': '#CCCCCC',       # Light gray border
        'card_bg': '#F4F5F7',      # Very light gray for cards
        'button_bg': '#0052CC',    # Blue button background
        'button_fg': '#FFFFFF',    # White button text
        'button_hover': '#0747A6'  # Darker blue on hover
    }
    
    # Large, readable fonts
    FONTS = {
        'title': ('Arial', 18, 'bold'),
        'heading': ('Arial', 14, 'bold'),
        'body': ('Arial', 12),
        'button': ('Arial', 13, 'bold'),
        'input': ('Arial', 13)
    }
    
    @classmethod
    def apply_theme(cls, root):
        """Apply accessible theme to root window"""
        
        # Configure root
        root.configure(bg=cls.COLORS['bg'])
        
        # Create style
        style = ttk.Style(root)
        
        # Use 'clam' theme as base (works well for customization)
        style.theme_use('clam')
        
        # Configure TFrame
        style.configure('TFrame',
                       background=cls.COLORS['bg'])
        
        style.configure('Card.TFrame',
                       background=cls.COLORS['card_bg'],
                       relief='flat',
                       borderwidth=0)
        
        # Configure TLabel
        style.configure('TLabel',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       font=cls.FONTS['body'])
        
        style.configure('Title.TLabel',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['primary'],
                       font=cls.FONTS['title'])
        
        style.configure('Heading.TLabel',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       font=cls.FONTS['heading'])
        
        # FIXED: Configure TButton with proper colors
        style.configure('TButton',
                       background=cls.COLORS['button_bg'],
                       foreground=cls.COLORS['button_fg'],
                       font=cls.FONTS['button'],
                       borderwidth=1,
                       relief='raised',
                       padding=(10, 5))
        
        # Button hover effect
        style.map('TButton',
                 background=[('active', cls.COLORS['button_hover']),
                           ('pressed', cls.COLORS['button_hover'])],
                 foreground=[('active', cls.COLORS['button_fg']),
                           ('pressed', cls.COLORS['button_fg'])])
        
        # FIXED: Primary Button (explicitly set colors)
        style.configure('Primary.TButton',
                       background=cls.COLORS['button_bg'],
                       foreground=cls.COLORS['button_fg'],
                       font=cls.FONTS['button'],
                       borderwidth=2,
                       relief='raised',
                       padding=(12, 6))
        
        style.map('Primary.TButton',
                 background=[('active', cls.COLORS['button_hover']),
                           ('pressed', cls.COLORS['button_hover'])],
                 foreground=[('active', cls.COLORS['button_fg']),
                           ('pressed', cls.COLORS['button_fg']),
                           ('disabled', '#999999')])
        
        # FIXED: Success Button (green)
        style.configure('Success.TButton',
                       background=cls.COLORS['success'],
                       foreground=cls.COLORS['button_fg'],
                       font=cls.FONTS['button'],
                       borderwidth=2,
                       relief='raised',
                       padding=(12, 6))
        
        style.map('Success.TButton',
                 background=[('active', '#006644'),
                           ('pressed', '#006644')],
                 foreground=[('active', cls.COLORS['button_fg']),
                           ('pressed', cls.COLORS['button_fg'])])
        
        # Warning Button
        style.configure('Warning.TButton',
                       background=cls.COLORS['warning'],
                       foreground=cls.COLORS['button_fg'],
                       font=cls.FONTS['button'],
                       borderwidth=2,
                       relief='raised',
                       padding=(12, 6))
        
        style.map('Warning.TButton',
                 background=[('active', '#CC7000'),
                           ('pressed', '#CC7000')],
                 foreground=[('active', cls.COLORS['button_fg']),
                           ('pressed', cls.COLORS['button_fg'])])
        
        # Danger Button
        style.configure('Danger.TButton',
                       background=cls.COLORS['danger'],
                       foreground=cls.COLORS['button_fg'],
                       font=cls.FONTS['button'],
                       borderwidth=2,
                       relief='raised',
                       padding=(12, 6))
        
        style.map('Danger.TButton',
                 background=[('active', '#B12A09'),
                           ('pressed', '#B12A09')],
                 foreground=[('active', cls.COLORS['button_fg']),
                           ('pressed', cls.COLORS['button_fg'])])
        
        # Accent Button (for Analyze Data Quality)
        style.configure('Accent.TButton',
                       background='#6554C0',  # Purple
                       foreground=cls.COLORS['button_fg'],
                       font=cls.FONTS['button'],
                       borderwidth=2,
                       relief='raised',
                       padding=(12, 6))
        
        style.map('Accent.TButton',
                 background=[('active', '#5243AA'),
                           ('pressed', '#5243AA')],
                 foreground=[('active', cls.COLORS['button_fg']),
                           ('pressed', cls.COLORS['button_fg'])])
        
        # Configure TEntry
        style.configure('TEntry',
                       fieldbackground=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       font=cls.FONTS['input'],
                       borderwidth=2,
                       relief='solid')
        
        # Configure TCombobox
        style.configure('TCombobox',
                       fieldbackground=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       font=cls.FONTS['input'],
                       borderwidth=2)
        
        # Configure Treeview
        style.configure('Treeview',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       fieldbackground=cls.COLORS['bg'],
                       font=cls.FONTS['body'],
                       rowheight=30)
        
        style.configure('Treeview.Heading',
                       background=cls.COLORS['primary'],
                       foreground=cls.COLORS['button_fg'],
                       font=cls.FONTS['heading'],
                       relief='raised',
                       borderwidth=1)
        
        style.map('Treeview.Heading',
                 background=[('active', cls.COLORS['primary_hover'])])
        
        # Configure TNotebook
        style.configure('TNotebook',
                       background=cls.COLORS['bg'],
                       borderwidth=0)
        
        style.configure('TNotebook.Tab',
                       background=cls.COLORS['card_bg'],
                       foreground=cls.COLORS['fg'],
                       font=cls.FONTS['button'],
                       padding=(15, 8))
        
        style.map('TNotebook.Tab',
                 background=[('selected', cls.COLORS['primary'])],
                 foreground=[('selected', cls.COLORS['button_fg'])])
        
        # Configure TCheckbutton
        style.configure('TCheckbutton',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       font=cls.FONTS['body'])
        
        # Configure TRadiobutton
        style.configure('TRadiobutton',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       font=cls.FONTS['body'])
        
        # Configure TScrollbar
        style.configure('TScrollbar',
                       background=cls.COLORS['card_bg'],
                       troughcolor=cls.COLORS['bg'],
                       borderwidth=1,
                       relief='flat',
                       width=16)
        
        # Configure TPanedwindow
        style.configure('TPanedwindow',
                       background=cls.COLORS['bg'])
        
        # Configure Listbox (using tk widget directly)
        root.option_add('*Listbox.font', cls.FONTS['body'])
        root.option_add('*Listbox.background', cls.COLORS['bg'])
        root.option_add('*Listbox.foreground', cls.COLORS['fg'])
        root.option_add('*Listbox.selectBackground', cls.COLORS['primary'])
        root.option_add('*Listbox.selectForeground', cls.COLORS['button_fg'])
        
        # Configure Text widget
        root.option_add('*Text.font', cls.FONTS['body'])
        root.option_add('*Text.background', cls.COLORS['bg'])
        root.option_add('*Text.foreground', cls.COLORS['fg'])
        
        return style