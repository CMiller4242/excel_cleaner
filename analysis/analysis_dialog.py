"""
Data Quality Analysis Dialog
Interactive GUI for displaying analysis results and selecting fixes

Shows:
- Quality score
- Issues by severity
- Suggested operations with checkboxes
- AI insights (if available)
- Apply/Cancel buttons
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Dict, Callable, Optional


class AnalysisDialog:
    """Dialog window for displaying data quality analysis results"""
    
    def __init__(self, parent, analysis_report, ai_enhancement: Optional[Dict] = None):
        """
        Initialize the analysis dialog
        
        Args:
            parent: Parent tkinter window
            analysis_report: AnalysisReport object
            ai_enhancement: Optional AI enhancement dict
        """
        self.parent = parent
        self.report = analysis_report
        self.ai_enhancement = ai_enhancement
        self.selected_operations = []
        self.result = None  # "apply", "cancel", or None
        self.canvas = None  # Store reference for cleanup
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📊 Data Quality Analysis")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"900x700+{x}+{y}")
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create all dialog widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with quality score
        self.create_header(main_frame)
        
        # AI Insights section (if available)
        if self.ai_enhancement and self.ai_enhancement.get("success"):
            self.create_ai_insights(main_frame)
        
        # Scrollable content area
        self.create_scrollable_content(main_frame)
        
        # Button bar at bottom
        self.create_button_bar(main_frame)
        
    def create_header(self, parent):
        """Create header with quality score and summary"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="Data Quality Analysis Report",
            font=('Arial', 18, 'bold')
        )
        title_label.pack(anchor=tk.W)
        
        # Quality score with color coding
        score = self.report.quality_score
        score_color = self.get_score_color(score)
        
        score_frame = ttk.Frame(header_frame)
        score_frame.pack(anchor=tk.W, pady=(10, 5))
        
        ttk.Label(
            score_frame,
            text=f"Quality Score: ",
            font=('Arial', 14)
        ).pack(side=tk.LEFT)
        
        score_label = tk.Label(
            score_frame,
            text=f"{score}/100",
            font=('Arial', 14, 'bold'),
            fg=score_color
        )
        score_label.pack(side=tk.LEFT)
        
        # Summary stats
        summary_text = f"📁 {self.report.total_rows:,} rows  •  {self.report.total_columns} columns  •  {self.report.total_issues} issues found"
        if self.report.total_suggested_operations > 0:
            summary_text += f"  •  {self.report.total_suggested_operations} operations suggested"
        
        ttk.Label(
            header_frame,
            text=summary_text,
            font=('Arial', 11),
            foreground='#666666'
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Separator
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
    def create_ai_insights(self, parent):
        """Create AI insights section"""
        ai_frame = ttk.LabelFrame(parent, text="🤖 AI Insights", padding="10")
        ai_frame.pack(fill=tk.X, pady=(0, 10))
        
        enhanced = self.ai_enhancement.get("enhanced_analysis", {})
        
        # Show top priorities if available
        if "priority_assessment" in enhanced and enhanced["priority_assessment"].strip():
            insights_text = scrolledtext.ScrolledText(
                ai_frame,
                height=4,
                wrap=tk.WORD,
                font=('Arial', 10),
                relief=tk.FLAT,
                background='#f8f9fa',
                borderwidth=0
            )
            insights_text.pack(fill=tk.X)
            insights_text.insert('1.0', enhanced["priority_assessment"].strip())
            insights_text.configure(state='disabled')
        else:
            ttk.Label(
                ai_frame,
                text="AI analysis provides intelligent prioritization and context for the issues found.",
                font=('Arial', 10),
                foreground='#666666'
            ).pack(anchor=tk.W)
    
    def create_scrollable_content(self, parent):
        """Create scrollable area for issues and operations"""
        # Canvas and scrollbar for scrolling
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with issues
        self.populate_issues()
        
        # Mouse wheel scrolling - bind to canvas and its children only
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        try:
            if self.canvas and self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except tk.TclError:
            # Canvas was destroyed, ignore
            pass
    
    def _bind_mousewheel(self, event):
        """Bind mousewheel when mouse enters canvas"""
        try:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        except tk.TclError:
            pass
    
    def _unbind_mousewheel(self, event):
        """Unbind mousewheel when mouse leaves canvas"""
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        
    def populate_issues(self):
        """Populate the scrollable frame with issues"""
        # CRITICAL Issues
        if self.report.critical_issues:
            self.create_issue_section(
                "🔴 CRITICAL Issues (Fix First)",
                self.report.critical_issues,
                "#dc3545",
                True  # Checked by default
            )
        
        # RECOMMENDED Fixes
        if self.report.recommended_fixes:
            self.create_issue_section(
                "🟡 RECOMMENDED Fixes",
                self.report.recommended_fixes,
                "#ffc107",
                True  # Checked by default
            )
        
        # OPTIONAL Improvements
        if self.report.optional_improvements:
            self.create_issue_section(
                "🔵 OPTIONAL Improvements",
                self.report.optional_improvements,
                "#17a2b8",
                False  # Not checked by default
            )
        
        # No issues found
        if not self.report.get_all_issues():
            no_issues_frame = ttk.Frame(self.scrollable_frame)
            no_issues_frame.pack(fill=tk.X, pady=20)
            
            ttk.Label(
                no_issues_frame,
                text="✅ No Issues Found!",
                font=('Arial', 16, 'bold'),
                foreground='#28a745'
            ).pack()
            
            ttk.Label(
                no_issues_frame,
                text="Your data looks clean and ready to use.",
                font=('Arial', 12),
                foreground='#666666'
            ).pack(pady=(5, 0))
    
    def create_issue_section(self, title: str, issues: List, color: str, default_checked: bool):
        """Create a section for a group of issues"""
        # Section frame
        section_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=title,
            padding="10"
        )
        section_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Each issue
        for issue in issues:
            self.create_issue_card(section_frame, issue, color, default_checked)
    
    def create_issue_card(self, parent, issue, color: str, default_checked: bool):
        """Create a card for a single issue"""
        card_frame = ttk.Frame(parent, relief=tk.SOLID, borderwidth=1)
        card_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        # Inner padding
        inner_frame = ttk.Frame(card_frame, padding="10")
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Issue header with checkbox
        header_frame = ttk.Frame(inner_frame)
        header_frame.pack(fill=tk.X)
        
        # Checkbox variable for this issue
        var = tk.BooleanVar(value=default_checked)
        
        # Checkbox
        checkbox = ttk.Checkbutton(
            header_frame,
            variable=var,
            command=lambda: self.on_issue_toggled(issue, var.get())
        )
        checkbox.pack(side=tk.LEFT, padx=(0, 5))
        
        # Issue title
        title_label = tk.Label(
            header_frame,
            text=issue.title,
            font=('Arial', 12, 'bold'),
            anchor=tk.W,
            fg=color
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Issue description
        if issue.description:
            desc_label = ttk.Label(
                inner_frame,
                text=issue.description,
                font=('Arial', 10),
                foreground='#666666',
                wraplength=800,
                justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W, pady=(5, 5))
        
        # Reasoning (why it matters)
        if issue.reasoning:
            reason_label = ttk.Label(
                inner_frame,
                text=f"💡 Why: {issue.reasoning}",
                font=('Arial', 9, 'italic'),
                foreground='#888888',
                wraplength=800,
                justify=tk.LEFT
            )
            reason_label.pack(anchor=tk.W, pady=(5, 5))
        
        # Suggested operations
        if issue.suggested_operations:
            ops_frame = ttk.Frame(inner_frame)
            ops_frame.pack(anchor=tk.W, pady=(5, 0))
            
            ttk.Label(
                ops_frame,
                text="→ Suggested Operation: ",
                font=('Arial', 9, 'bold')
            ).pack(side=tk.LEFT)
            
            # Show operation names
            op_names = []
            for op_config in issue.suggested_operations:
                op_id = op_config.get('operation_id', 'Unknown')
                # Convert ID to readable name
                op_name = op_id.replace('_', ' ').title()
                op_names.append(op_name)
            
            ttk.Label(
                ops_frame,
                text=", ".join(op_names),
                font=('Arial', 9),
                foreground='#0066cc'
            ).pack(side=tk.LEFT)
        
        # Store the checkbox state for this issue
        if default_checked and issue.suggested_operations:
            for op in issue.suggested_operations:
                if op not in self.selected_operations:
                    self.selected_operations.append(op)
    
    def on_issue_toggled(self, issue, is_checked: bool):
        """Handle issue checkbox toggle"""
        if is_checked:
            # Add operations to selected list
            for op in issue.suggested_operations:
                if op not in self.selected_operations:
                    self.selected_operations.append(op)
        else:
            # Remove operations from selected list
            for op in issue.suggested_operations:
                if op in self.selected_operations:
                    self.selected_operations.remove(op)
    
    def create_button_bar(self, parent):
        """Create button bar with actions"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Left side - operation count
        left_frame = ttk.Frame(button_frame)
        left_frame.pack(side=tk.LEFT)
        
        self.op_count_label = ttk.Label(
            left_frame,
            text=f"{len(self.selected_operations)} operations selected",
            font=('Arial', 11),
            foreground='#666666'
        )
        self.op_count_label.pack(side=tk.LEFT)
        
        # Right side - action buttons
        right_frame = ttk.Frame(button_frame)
        right_frame.pack(side=tk.RIGHT)
        
        # Cancel button
        cancel_btn = ttk.Button(
            right_frame,
            text="Cancel",
            command=self.on_cancel,
            width=12
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Apply button
        apply_btn = ttk.Button(
            right_frame,
            text="Add to Queue",
            command=self.on_apply,
            width=15
        )
        apply_btn.pack(side=tk.LEFT)
        
        # Style the apply button
        apply_btn.configure(style='Accent.TButton')
    
    def on_apply(self):
        """Handle Apply button click"""
        self.result = "apply"
        self._cleanup_and_close()
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = "cancel"
        self._cleanup_and_close()
    
    def _cleanup_and_close(self):
        """Clean up bindings and close dialog"""
        try:
            # Unbind global mousewheel event
            self.canvas.unbind_all("<MouseWheel>")
        except (tk.TclError, AttributeError):
            pass
        
        try:
            self.dialog.destroy()
        except tk.TclError:
            pass
    
    def show(self) -> str:
        """Show the dialog and wait for result"""
        self.dialog.wait_window()
        return self.result
    
    def get_selected_operations(self) -> List[Dict]:
        """Get the list of selected operations"""
        return self.selected_operations
    
    @staticmethod
    def get_score_color(score: int) -> str:
        """Get color based on quality score"""
        if score >= 80:
            return '#28a745'  # Green
        elif score >= 60:
            return '#ffc107'  # Yellow
        elif score >= 40:
            return '#fd7e14'  # Orange
        else:
            return '#dc3545'  # Red


class ProgressDialog:
    """Simple progress dialog for analysis"""
    
    def __init__(self, parent, title="Analyzing Data..."):
        self.parent = parent
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center it
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 200
        y = (self.dialog.winfo_screenheight() // 2) - 75
        self.dialog.geometry(f"400x150+{x}+{y}")
        
        # Disable close button
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Content
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(
            frame,
            text="Analyzing your data...",
            font=('Arial', 12)
        )
        self.status_label.pack(pady=(10, 20))
        
        self.progress = ttk.Progressbar(
            frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack()
        self.progress.start(10)
        
        self.detail_label = ttk.Label(
            frame,
            text="This may take a few moments...",
            font=('Arial', 9),
            foreground='#666666'
        )
        self.detail_label.pack(pady=(10, 0))
    
    def update_status(self, message: str):
        """Update status message"""
        self.status_label.config(text=message)
        self.dialog.update()
    
    def close(self):
        """Close the dialog"""
        self.progress.stop()
        self.dialog.destroy()