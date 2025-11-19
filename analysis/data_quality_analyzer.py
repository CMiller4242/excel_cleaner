"""
Data Quality Analyzer for Universal Excel Tool V2.1
Automatically detects data quality issues and suggests cleaning operations

Focus: Mail list cleaning for promotional products industry
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
import pandas as pd
import re


class IssueSeverity(Enum):
    """Severity levels for data quality issues"""
    CRITICAL = "critical"      # Must fix (duplicates, PO boxes)
    RECOMMENDED = "recommended"  # Should fix (formatting)
    OPTIONAL = "optional"       # Nice to have (validation)


class IssueCategory(Enum):
    """Categories of data quality issues"""
    DUPLICATES = "Duplicates"
    MISSING_DATA = "Missing Data"
    FORMATTING = "Formatting"
    INVALID_DATA = "Invalid Data"
    MAIL_LIST_SPECIFIC = "Mail List Issues"
    DATA_QUALITY = "Data Quality"


@dataclass
class ColumnInfo:
    """Information about a detected column type"""
    name: str
    detected_type: str  # email, phone, address, company, name, zip, state, etc.
    confidence: float   # 0.0 to 1.0
    sample_values: List[str] = field(default_factory=list)
    issues_found: List[str] = field(default_factory=list)


@dataclass
class Issue:
    """Represents a data quality issue"""
    category: IssueCategory
    severity: IssueSeverity
    title: str
    description: str
    affected_rows: int
    affected_columns: List[str]
    suggested_operations: List[Dict]  # List of operation configs
    reasoning: str  # Why this matters


@dataclass
class AnalysisReport:
    """Complete data quality analysis report"""
    total_rows: int
    total_columns: int
    quality_score: int  # 0-100
    
    # Detected column types
    column_intelligence: Dict[str, ColumnInfo]
    
    # Issues by severity
    critical_issues: List[Issue] = field(default_factory=list)
    recommended_fixes: List[Issue] = field(default_factory=list)
    optional_improvements: List[Issue] = field(default_factory=list)
    
    # Summary stats
    total_issues: int = 0
    total_suggested_operations: int = 0
    estimated_time_seconds: int = 0
    
    def get_all_issues(self) -> List[Issue]:
        """Get all issues sorted by severity"""
        return self.critical_issues + self.recommended_fixes + self.optional_improvements
    
    def get_all_suggested_operations(self) -> List[Dict]:
        """Get all suggested operations from all issues"""
        operations = []
        for issue in self.get_all_issues():
            operations.extend(issue.suggested_operations)
        return operations


class ColumnTypeDetector:
    """Detects the type/purpose of columns intelligently"""
    
    # Common column name patterns for mail lists
    PATTERNS = {
        'customer_id': [r'customer.*id', r'cust.*id', r'account.*id', r'^id$', r'customer.*#', r'cust.*#'],
        'company': [r'company', r'business', r'organization', r'firm'],
        'contact_name': [r'^name$', r'contact.*name', r'full.*name', r'person'],
        'first_name': [r'first.*name', r'fname', r'^first$'],
        'last_name': [r'last.*name', r'lname', r'surname', r'^last$'],
        'email': [r'email', r'e-mail', r'mail'],
        'phone': [r'phone', r'telephone', r'tel', r'mobile', r'cell'],
        'address1': [r'address.*1', r'^address$', r'street', r'addr1'],
        'address2': [r'address.*2', r'addr2', r'suite', r'apt'],
        'city': [r'city', r'town'],
        'state': [r'state', r'province', r'^st$'],
        'zip': [r'zip', r'postal', r'postcode'],
        'country': [r'country', r'nation'],
    }
    
    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> Dict[str, ColumnInfo]:
        """Detect the type of each column"""
        column_info = {}
        
        for col in df.columns:
            col_lower = col.lower().strip()
            detected_type = "unknown"
            confidence = 0.0
            issues = []
            
            # Get sample non-null values
            sample_values = df[col].dropna().head(5).astype(str).tolist()
            
            # Try to match column name patterns
            for col_type, patterns in ColumnTypeDetector.PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, col_lower, re.IGNORECASE):
                        detected_type = col_type
                        confidence = 0.9
                        break
                if detected_type != "unknown":
                    break
            
            # If no name match, analyze content
            if detected_type == "unknown" and len(sample_values) > 0:
                detected_type, confidence = ColumnTypeDetector._analyze_content(
                    df[col], sample_values
                )
            
            # Detect column-specific issues
            if detected_type != "unknown":
                issues = ColumnTypeDetector._detect_column_issues(df[col], detected_type)
            
            column_info[col] = ColumnInfo(
                name=col,
                detected_type=detected_type,
                confidence=confidence,
                sample_values=sample_values,
                issues_found=issues
            )
        
        return column_info
    
    @staticmethod
    def _analyze_content(series: pd.Series, sample_values: List[str]) -> Tuple[str, float]:
        """Analyze column content to determine type"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return "unknown", 0.0
        
        # Check for email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = non_null.astype(str).str.match(email_pattern).sum()
        if email_matches / len(non_null) > 0.7:
            return "email", 0.8
        
        # Check for phone pattern (10 digits, various formats)
        phone_pattern = r'.*\d{3}.*\d{3}.*\d{4}.*'
        phone_matches = non_null.astype(str).str.match(phone_pattern).sum()
        if phone_matches / len(non_null) > 0.7:
            return "phone", 0.8
        
        # Check for zip code (5 digits)
        zip_pattern = r'^\d{5}(-\d{4})?$'
        zip_matches = non_null.astype(str).str.match(zip_pattern).sum()
        if zip_matches / len(non_null) > 0.7:
            return "zip", 0.8
        
        # Check for state code (2 letters)
        state_pattern = r'^[A-Z]{2}$'
        state_matches = non_null.astype(str).str.match(state_pattern).sum()
        if state_matches / len(non_null) > 0.7:
            return "state", 0.8
        
        # Check for address (contains numbers and street keywords)
        address_keywords = ['street', 'st', 'ave', 'avenue', 'road', 'rd', 'blvd', 'drive', 'dr', 'lane', 'ln']
        has_numbers = non_null.astype(str).str.contains(r'\d+', regex=True).sum()
        has_street_keywords = non_null.astype(str).str.lower().str.contains('|'.join(address_keywords), regex=True).sum()
        if (has_numbers / len(non_null) > 0.5) and (has_street_keywords / len(non_null) > 0.3):
            return "address1", 0.7
        
        return "unknown", 0.0
    
    @staticmethod
    def _detect_column_issues(series: pd.Series, col_type: str) -> List[str]:
        """Detect issues specific to column type"""
        issues = []
        non_null = series.dropna()
        
        if col_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid = non_null[~non_null.astype(str).str.match(email_pattern)]
            if len(invalid) > 0:
                issues.append(f"{len(invalid)} invalid email formats")
        
        elif col_type == "phone":
            # Check for consistent length
            lengths = non_null.astype(str).str.replace(r'\D', '', regex=True).str.len()
            not_10_digits = lengths[lengths != 10]
            if len(not_10_digits) > 0:
                issues.append(f"{len(not_10_digits)} phones not 10 digits")
        
        elif col_type == "zip":
            zip_pattern = r'^\d{5}(-\d{4})?$'
            invalid = non_null[~non_null.astype(str).str.match(zip_pattern)]
            if len(invalid) > 0:
                issues.append(f"{len(invalid)} invalid zip formats")
        
        elif col_type == "state":
            # Check for excluded states
            excluded = ['AK', 'HI', 'PR', 'GU', 'VI', 'AS', 'MP']
            has_excluded = non_null.astype(str).str.upper().isin(excluded).sum()
            if has_excluded > 0:
                issues.append(f"{has_excluded} excluded states (AK, HI, PR, territories)")
        
        elif col_type in ["company", "contact_name", "first_name", "last_name"]:
            # Check for case inconsistency
            all_upper = non_null.astype(str).str.isupper().sum()
            all_lower = non_null.astype(str).str.islower().sum()
            mixed = len(non_null) - all_upper - all_lower
            if mixed > len(non_null) * 0.3:
                issues.append(f"Mixed case formatting (not standardized)")
        
        elif col_type in ["address1", "address2"]:
            # Check for PO boxes
            po_box_pattern = r'(?i)\b(p\.?\s*o\.?\s*box|post\s*office\s*box|po\s*box)\b'
            po_boxes = non_null.astype(str).str.contains(po_box_pattern, regex=True).sum()
            if po_boxes > 0:
                issues.append(f"{po_boxes} PO Box addresses detected")
        
        return issues


class DataQualityAnalyzer:
    """Main analyzer that detects data quality issues"""
    
    def __init__(self):
        self.detector = ColumnTypeDetector()
    
    def analyze(self, df: pd.DataFrame) -> AnalysisReport:
        """
        Perform complete analysis of the dataframe
        Returns detailed report with issues and suggestions
        """
        # Initialize report
        report = AnalysisReport(
            total_rows=len(df),
            total_columns=len(df.columns),
            quality_score=100,  # Start at 100, deduct for issues
            column_intelligence={}
        )
        
        # Step 1: Detect column types
        report.column_intelligence = self.detector.detect_column_types(df)
        
        # Step 2: Detect issues by category
        self._detect_duplicate_issues(df, report)
        self._detect_missing_data_issues(df, report)
        self._detect_formatting_issues(df, report)
        self._detect_mail_list_issues(df, report)
        self._detect_validation_issues(df, report)
        
        # Step 3: Calculate quality score
        report.quality_score = self._calculate_quality_score(report)
        
        # Step 4: Count totals
        report.total_issues = len(report.get_all_issues())
        report.total_suggested_operations = len(report.get_all_suggested_operations())
        report.estimated_time_seconds = self._estimate_processing_time(report)
        
        return report
    
    def _detect_duplicate_issues(self, df: pd.DataFrame, report: AnalysisReport):
        """Detect duplicate rows"""
        # Find customer ID column
        customer_id_col = None
        for col_name, col_info in report.column_intelligence.items():
            if col_info.detected_type == "customer_id":
                customer_id_col = col_name
                break
        
        if customer_id_col:
            duplicates = df[df.duplicated(subset=[customer_id_col], keep=False)]
            num_duplicates = len(duplicates)
            
            if num_duplicates > 0:
                issue = Issue(
                    category=IssueCategory.DUPLICATES,
                    severity=IssueSeverity.CRITICAL,
                    title=f"Found {num_duplicates} duplicate rows",
                    description=f"Duplicate entries based on {customer_id_col}. These should be removed to avoid sending multiple mailings to the same customer.",
                    affected_rows=num_duplicates,
                    affected_columns=[customer_id_col],
                    suggested_operations=[{
                        'operation_id': 'data_remove_duplicates',
                        'params': {'columns': [customer_id_col], 'keep': 'first'}
                    }],
                    reasoning="Duplicates waste resources and may annoy customers with multiple mailings."
                )
                report.critical_issues.append(issue)
        else:
            # Check for complete duplicate rows
            duplicates = df[df.duplicated(keep=False)]
            num_duplicates = len(duplicates)
            
            if num_duplicates > 0:
                issue = Issue(
                    category=IssueCategory.DUPLICATES,
                    severity=IssueSeverity.CRITICAL,
                    title=f"Found {num_duplicates} duplicate rows",
                    description="Exact duplicate rows detected. These should be removed.",
                    affected_rows=num_duplicates,
                    affected_columns=list(df.columns),
                    suggested_operations=[{
                        'operation_id': 'data_remove_duplicates',
                        'params': {'columns': [], 'keep': 'first'}
                    }],
                    reasoning="Complete duplicates waste resources and processing time."
                )
                report.critical_issues.append(issue)
    
    def _detect_missing_data_issues(self, df: pd.DataFrame, report: AnalysisReport):
        """Detect missing/blank data"""
        # Find rows with too many blanks
        blank_threshold = len(df.columns) * 0.5  # 50% or more columns blank
        rows_with_many_blanks = df[df.isnull().sum(axis=1) >= blank_threshold]
        
        if len(rows_with_many_blanks) > 0:
            issue = Issue(
                category=IssueCategory.MISSING_DATA,
                severity=IssueSeverity.RECOMMENDED,
                title=f"Found {len(rows_with_many_blanks)} rows with excessive blank data",
                description=f"Rows with {int(blank_threshold)} or more empty columns. These may be incomplete records.",
                affected_rows=len(rows_with_many_blanks),
                affected_columns=[],
                suggested_operations=[{
                    'operation_id': 'clean_remove_blank_rows',
                    'params': {}
                }],
                reasoning="Incomplete records may cause mailing errors or waste resources."
            )
            report.recommended_fixes.append(issue)
    
    def _detect_formatting_issues(self, df: pd.DataFrame, report: AnalysisReport):
        """Detect formatting inconsistencies"""
        # Check for whitespace issues
        columns_with_whitespace = []
        for col in df.columns:
            if df[col].dtype == 'object':
                has_leading = df[col].astype(str).str.startswith(' ').any()
                has_trailing = df[col].astype(str).str.endswith(' ').any()
                if has_leading or has_trailing:
                    columns_with_whitespace.append(col)
        
        if columns_with_whitespace:
            issue = Issue(
                category=IssueCategory.FORMATTING,
                severity=IssueSeverity.RECOMMENDED,
                title=f"Found whitespace issues in {len(columns_with_whitespace)} columns",
                description=f"Columns with leading/trailing spaces: {', '.join(columns_with_whitespace[:3])}{'...' if len(columns_with_whitespace) > 3 else ''}",
                affected_rows=len(df),
                affected_columns=columns_with_whitespace,
                suggested_operations=[{
                    'operation_id': 'text_trim',
                    'params': {'columns': columns_with_whitespace}
                }],
                reasoning="Extra spaces cause matching errors and look unprofessional on labels."
            )
            report.recommended_fixes.append(issue)
        
        # Check for case inconsistency in name/company columns
        columns_needing_uppercase = []
        for col_name, col_info in report.column_intelligence.items():
            if col_info.detected_type in ['company', 'contact_name', 'address1', 'city']:
                # Check if data is mixed case
                non_null = df[col_name].dropna().astype(str)
                if len(non_null) > 0:
                    all_upper = non_null.str.isupper().sum()
                    if all_upper < len(non_null) * 0.9:  # Less than 90% uppercase
                        columns_needing_uppercase.append(col_name)
        
        if columns_needing_uppercase:
            issue = Issue(
                category=IssueCategory.FORMATTING,
                severity=IssueSeverity.RECOMMENDED,
                title=f"Inconsistent capitalization in {len(columns_needing_uppercase)} columns",
                description=f"For mailing labels, these should be UPPERCASE: {', '.join(columns_needing_uppercase)}",
                affected_rows=len(df),
                affected_columns=columns_needing_uppercase,
                suggested_operations=[{
                    'operation_id': 'text_uppercase',
                    'params': {'columns': columns_needing_uppercase}
                }],
                reasoning="Mailing labels look more professional and are easier to read when standardized to UPPERCASE."
            )
            report.recommended_fixes.append(issue)
    
    def _detect_mail_list_issues(self, df: pd.DataFrame, report: AnalysisReport):
        """Detect mail list specific issues"""
        # PO Box detection
        address_columns = []
        for col_name, col_info in report.column_intelligence.items():
            if col_info.detected_type in ['address1', 'address2']:
                address_columns.append(col_name)
        
        if address_columns:
            po_box_pattern = r'(?i)\b(p\.?\s*o\.?\s*box|post\s*office\s*box|po\s*box)\b'
            po_box_rows = 0
            for col in address_columns:
                po_box_rows += df[col].astype(str).str.contains(po_box_pattern, regex=True, na=False).sum()
            
            if po_box_rows > 0:
                issue = Issue(
                    category=IssueCategory.MAIL_LIST_SPECIFIC,
                    severity=IssueSeverity.CRITICAL,
                    title=f"Found {po_box_rows} PO Box addresses",
                    description="PO Box addresses detected. These may need special handling or flagging.",
                    affected_rows=po_box_rows,
                    affected_columns=address_columns,
                    suggested_operations=[{
                        'operation_id': 'conditional_flag_contains',
                        'params': {
                            'column': address_columns[0],
                            'text': 'PO BOX',
                            'flag_column': 'PO_Box_Flag'
                        }
                    }],
                    reasoning="PO Boxes may have different shipping costs or restrictions for sample mailings."
                )
                report.critical_issues.append(issue)
        
        # Excluded states detection
        state_column = None
        for col_name, col_info in report.column_intelligence.items():
            if col_info.detected_type == 'state':
                state_column = col_name
                break
        
        if state_column:
            excluded_states = ['AK', 'HI', 'PR', 'GU', 'VI', 'AS', 'MP']
            excluded_count = df[state_column].astype(str).str.upper().isin(excluded_states).sum()
            
            if excluded_count > 0:
                issue = Issue(
                    category=IssueCategory.MAIL_LIST_SPECIFIC,
                    severity=IssueSeverity.CRITICAL,
                    title=f"Found {excluded_count} addresses in excluded states/territories",
                    description=f"States/territories: AK, HI, PR, and US territories. These typically have higher shipping costs.",
                    affected_rows=excluded_count,
                    affected_columns=[state_column],
                    suggested_operations=[{
                        'operation_id': 'conditional_flag_contains',
                        'params': {
                            'column': state_column,
                            'text': 'AK|HI|PR|GU|VI|AS|MP',
                            'flag_column': 'Excluded_State_Flag'
                        }
                    }],
                    reasoning="Alaska, Hawaii, and territories have significantly higher shipping costs for sample boxes."
                )
                report.critical_issues.append(issue)
        
        # Generic contacts detection
        contact_columns = []
        for col_name, col_info in report.column_intelligence.items():
            if col_info.detected_type in ['contact_name', 'first_name', 'last_name']:
                contact_columns.append(col_name)
        
        if contact_columns:
            generic_patterns = ['ACCOUNTS PAYABLE', 'A/P', 'ACCOUNTING', 'OFFICE', 'MANAGER']
            generic_count = 0
            for col in contact_columns:
                for pattern in generic_patterns:
                    generic_count += df[col].astype(str).str.upper().str.contains(pattern, regex=False, na=False).sum()
            
            if generic_count > 0:
                issue = Issue(
                    category=IssueCategory.MAIL_LIST_SPECIFIC,
                    severity=IssueSeverity.RECOMMENDED,
                    title=f"Found {generic_count} generic contact names",
                    description="Generic contacts like 'ACCOUNTS PAYABLE' or 'A/P' detected. These may need review.",
                    affected_rows=generic_count,
                    affected_columns=contact_columns,
                    suggested_operations=[],  # Manual review recommended
                    reasoning="Generic contacts may indicate businesses rather than individuals, affecting targeting."
                )
                report.recommended_fixes.append(issue)
    
    def _detect_validation_issues(self, df: pd.DataFrame, report: AnalysisReport):
        """Detect validation issues"""
        # Email validation
        email_column = None
        for col_name, col_info in report.column_intelligence.items():
            if col_info.detected_type == 'email':
                email_column = col_name
                break
        
        if email_column:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid_emails = df[email_column].dropna()
            invalid_count = len(invalid_emails[~invalid_emails.astype(str).str.match(email_pattern)])
            
            if invalid_count > 0:
                issue = Issue(
                    category=IssueCategory.INVALID_DATA,
                    severity=IssueSeverity.OPTIONAL,
                    title=f"Found {invalid_count} potentially invalid email addresses",
                    description="Email addresses that don't match standard format.",
                    affected_rows=invalid_count,
                    affected_columns=[email_column],
                    suggested_operations=[{
                        'operation_id': 'validate_email',
                        'params': {'column': email_column, 'flag_invalid': True}
                    }],
                    reasoning="Invalid emails will bounce and waste follow-up efforts."
                )
                report.optional_improvements.append(issue)
        
        # Phone validation
        phone_column = None
        for col_name, col_info in report.column_intelligence.items():
            if col_info.detected_type == 'phone':
                phone_column = col_name
                break
        
        if phone_column:
            # Count phones that aren't 10 digits (after removing non-digits)
            phone_lengths = df[phone_column].dropna().astype(str).str.replace(r'\D', '', regex=True).str.len()
            invalid_count = len(phone_lengths[phone_lengths != 10])
            
            if invalid_count > 0:
                issue = Issue(
                    category=IssueCategory.INVALID_DATA,
                    severity=IssueSeverity.OPTIONAL,
                    title=f"Found {invalid_count} phone numbers not 10 digits",
                    description="Phone numbers should be exactly 10 digits (area code + number).",
                    affected_rows=invalid_count,
                    affected_columns=[phone_column],
                    suggested_operations=[],  # Could add phone formatting operation
                    reasoning="Invalid phone numbers prevent follow-up contact with customers."
                )
                report.optional_improvements.append(issue)
    
    def _calculate_quality_score(self, report: AnalysisReport) -> int:
        """Calculate overall quality score (0-100)"""
        score = 100
        
        # Deduct for critical issues
        score -= len(report.critical_issues) * 15
        
        # Deduct for recommended fixes
        score -= len(report.recommended_fixes) * 5
        
        # Deduct for optional improvements
        score -= len(report.optional_improvements) * 2
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def _estimate_processing_time(self, report: AnalysisReport) -> int:
        """Estimate processing time in seconds"""
        # Rough estimate based on operation count and row count
        base_time = 2  # Base overhead
        op_time = len(report.get_all_suggested_operations()) * 3  # 3 seconds per operation
        row_time = (report.total_rows / 1000) * 2  # 2 seconds per 1000 rows
        
        return int(base_time + op_time + row_time)