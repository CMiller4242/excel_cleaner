"""
Data Quality Analysis Module for Universal Excel Tool V2.1

This module provides intelligent data quality analysis with optional AI enhancement.

Components:
- DataQualityAnalyzer: Deterministic rules engine for issue detection
- AIAnalysisEnhancer: Optional Claude AI integration for intelligent insights
- AnalysisDialog: Interactive GUI for reviewing and selecting fixes
- DataQualityIntegration: Integration layer for main application

Features:
- Automatic issue detection (duplicates, formatting, validation)
- Intelligent column type detection
- Mail list specific rules (PO boxes, excluded states)
- Quality scoring (0-100)
- AI-powered prioritization and insights
- Interactive fix selection
- One-click operation queuing

Usage:
    from analysis.data_quality_integration import DataQualityIntegration
    
    # In your main GUI:
    self.dq_integration = DataQualityIntegration(self)
    self.dq_integration.analyze_data()
"""

__version__ = "2.1.0"
__author__ = "Universal Excel Tool Team"

from .data_quality_analyzer import (
    DataQualityAnalyzer,
    AnalysisReport,
    Issue,
    ColumnInfo,
    IssueSeverity,
    IssueCategory,
    ColumnTypeDetector
)

from .ai_enhancement import (
    AIAnalysisEnhancer,
    AIEnhancementCache
)

from .analysis_dialog import (
    AnalysisDialog,
    ProgressDialog
)

from .data_quality_integration import (
    DataQualityIntegration,
    add_analyze_button_to_gui
)

__all__ = [
    # Main classes
    'DataQualityAnalyzer',
    'AIAnalysisEnhancer',
    'AnalysisDialog',
    'DataQualityIntegration',
    
    # Data classes
    'AnalysisReport',
    'Issue',
    'ColumnInfo',
    
    # Enums
    'IssueSeverity',
    'IssueCategory',
    
    # Utilities
    'ColumnTypeDetector',
    'ProgressDialog',
    'AIEnhancementCache',
    'add_analyze_button_to_gui',
    
    # Metadata
    '__version__',
    '__author__'
]

# Module-level convenience function
def quick_analyze(df, use_ai=False, api_key=None):
    """
    Quick analysis function for standalone use
    
    Args:
        df: pandas DataFrame to analyze
        use_ai: Whether to use AI enhancement
        api_key: Anthropic API key (required if use_ai=True)
        
    Returns:
        AnalysisReport object
        
    Example:
        import pandas as pd
        from analysis import quick_analyze
        
        df = pd.read_csv('data.csv')
        report = quick_analyze(df, use_ai=True, api_key='your_key')
        print(f"Quality Score: {report.quality_score}/100")
        print(f"Issues Found: {report.total_issues}")
    """
    analyzer = DataQualityAnalyzer()
    report = analyzer.analyze(df)
    
    if use_ai and api_key:
        enhancer = AIAnalysisEnhancer(api_key)
        df_summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        }
        enhancement = enhancer.enhance_analysis(report, df_summary)
        report.ai_enhancement = enhancement
    
    return report


# Print info when module is imported
import sys
if '--verbose' in sys.argv or '-v' in sys.argv:
    print(f"[Analysis Module v{__version__}] Loaded successfully")
    print(f"[Analysis Module] Components: {len(__all__)} exports")
    print(f"[Analysis Module] AI Enhancement: Available")
    print(f"[Analysis Module] Ready for integration")