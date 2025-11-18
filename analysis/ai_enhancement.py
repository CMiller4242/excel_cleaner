"""
AI Enhancement Layer for Data Quality Analyzer
Uses Claude API to provide intelligent analysis and suggestions

Enhances deterministic analysis with:
- Contextual understanding
- Priority suggestions
- Reasoning explanations
- Unusual pattern detection
"""

from typing import Dict, List, Optional
import json
from anthropic import Anthropic
from dataclasses import asdict


class AIAnalysisEnhancer:
    """Enhances data quality analysis using Claude AI"""
    
    SYSTEM_PROMPT = """You are an expert data quality analyst specializing in mail list cleaning for the promotional products industry.

Your role is to review data quality analysis reports and provide:
1. Intelligent prioritization of issues
2. Clear explanations of why issues matter
3. Detection of unusual patterns the rules might miss
4. Suggestions for optimal operation sequencing
5. Business context and reasoning

Focus on:
- Mail list cleaning (sample box distribution)
- Practical business impact
- Time/cost savings
- Professional mailing standards
- Avoiding shipping errors

Keep suggestions concise and actionable. Use promotional products industry terminology."""
    
    def __init__(self, api_key: str):
        """Initialize with Anthropic API key"""
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def enhance_analysis(self, 
                        analysis_report,  # AnalysisReport object
                        df_summary: Dict,
                        conversation_history: List[Dict] = None) -> Dict:
        """
        Enhance the deterministic analysis with AI insights
        
        Args:
            analysis_report: The deterministic AnalysisReport
            df_summary: Summary statistics about the dataframe
            conversation_history: Optional previous AI conversations for context
            
        Returns:
            Enhanced analysis with AI suggestions
        """
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(analysis_report, df_summary)
        
        # Prepare messages
        messages = conversation_history or []
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,  # Lower temperature for more consistent analysis
                system=self.SYSTEM_PROMPT,
                messages=messages
            )
            
            # Parse response
            ai_content = response.content[0].text
            
            # Try to extract JSON if present, otherwise use text
            enhanced_analysis = self._parse_ai_response(ai_content)
            
            return {
                "success": True,
                "enhanced_analysis": enhanced_analysis,
                "raw_response": ai_content,
                "conversation_history": messages + [{
                    "role": "assistant",
                    "content": ai_content
                }]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "enhanced_analysis": None
            }
    
    def _build_analysis_prompt(self, analysis_report, df_summary: Dict) -> str:
        """Build the prompt for AI analysis"""
        
        # Convert report to a structured format
        report_summary = {
            "total_rows": analysis_report.total_rows,
            "total_columns": analysis_report.total_columns,
            "quality_score": analysis_report.quality_score,
            "total_issues": analysis_report.total_issues,
            "critical_issues": [
                {
                    "title": issue.title,
                    "description": issue.description,
                    "affected_rows": issue.affected_rows,
                    "affected_columns": issue.affected_columns,
                    "category": issue.category.value
                }
                for issue in analysis_report.critical_issues
            ],
            "recommended_fixes": [
                {
                    "title": issue.title,
                    "description": issue.description,
                    "affected_rows": issue.affected_rows,
                    "category": issue.category.value
                }
                for issue in analysis_report.recommended_fixes
            ],
            "optional_improvements": [
                {
                    "title": issue.title,
                    "description": issue.description,
                    "affected_rows": issue.affected_rows
                }
                for issue in analysis_report.optional_improvements
            ],
            "detected_columns": {
                col_name: {
                    "type": col_info.detected_type,
                    "confidence": col_info.confidence,
                    "issues": col_info.issues_found
                }
                for col_name, col_info in analysis_report.column_intelligence.items()
                if col_info.detected_type != "unknown"
            }
        }
        
        prompt = f"""I've analyzed a mail list CSV file and detected the following issues. Please review and provide insights.

## Dataset Overview
- Total Rows: {analysis_report.total_rows}
- Total Columns: {analysis_report.total_columns}
- Quality Score: {analysis_report.quality_score}/100

## Detected Column Types
{json.dumps(report_summary['detected_columns'], indent=2)}

## Issues Detected

### CRITICAL Issues ({len(analysis_report.critical_issues)}):
{json.dumps(report_summary['critical_issues'], indent=2)}

### RECOMMENDED Fixes ({len(analysis_report.recommended_fixes)}):
{json.dumps(report_summary['recommended_fixes'], indent=2)}

### OPTIONAL Improvements ({len(analysis_report.optional_improvements)}):
{json.dumps(report_summary['optional_improvements'], indent=2)}

## Your Task

Please provide:

1. **Priority Assessment**: Should we adjust the severity of any issues based on the business context?

2. **Operation Sequence**: What's the optimal order to apply fixes? (e.g., remove duplicates before formatting)

3. **Business Impact**: Explain the real-world impact of each critical issue in terms of:
   - Cost (wasted samples/shipping)
   - Customer experience
   - Professional appearance

4. **Hidden Patterns**: Are there any patterns or issues the automated rules might have missed?

5. **Recommendations**: Any additional suggestions specific to this dataset?

Please provide your response in a structured format that includes:
- Top 3 priorities (in order)
- Recommended operation sequence
- Key insights about this specific dataset
- Estimated impact of applying all fixes

Keep it concise and actionable."""

        return prompt
    
    def _parse_ai_response(self, ai_content: str) -> Dict:
        """Parse AI response into structured format"""
        # Try to extract structured information from the response
        # For now, return as text with sections identified
        
        sections = {
            "priority_assessment": "",
            "operation_sequence": "",
            "business_impact": "",
            "hidden_patterns": "",
            "recommendations": "",
            "top_priorities": [],
            "key_insights": [],
            "raw_response": ai_content
        }
        
        # Simple section extraction
        current_section = None
        for line in ai_content.split('\n'):
            line_lower = line.lower().strip()
            
            if 'priority' in line_lower and ('assessment' in line_lower or 'priorities' in line_lower):
                current_section = "priority_assessment"
            elif 'operation' in line_lower and 'sequence' in line_lower:
                current_section = "operation_sequence"
            elif 'business' in line_lower and 'impact' in line_lower:
                current_section = "business_impact"
            elif 'hidden' in line_lower or 'pattern' in line_lower:
                current_section = "hidden_patterns"
            elif 'recommendation' in line_lower:
                current_section = "recommendations"
            elif current_section:
                sections[current_section] += line + "\n"
        
        return sections
    
    def get_quick_suggestion(self, user_question: str, context: Dict) -> str:
        """
        Get a quick AI suggestion for a specific question
        
        Args:
            user_question: User's specific question
            context: Context about the data
            
        Returns:
            AI's response
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"""Context: {json.dumps(context, indent=2)}

User Question: {user_question}

Provide a brief, actionable answer (2-3 sentences max)."""
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Unable to get AI suggestion: {str(e)}"
    
    def explain_operation_suggestion(self, 
                                    operation_id: str,
                                    issue_description: str,
                                    data_context: Dict) -> str:
        """
        Explain why a specific operation is suggested
        
        Args:
            operation_id: The operation being suggested
            issue_description: Description of the issue
            data_context: Context about the data
            
        Returns:
            Explanation of why this operation helps
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=0.3,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"""Issue: {issue_description}

Suggested Operation: {operation_id}

Data Context: {json.dumps(data_context, indent=2)}

Explain in 2-3 sentences why this operation is recommended and what business impact it has for mail list cleaning."""
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"This operation helps address the detected issue."


class AIEnhancementCache:
    """Simple cache for AI enhancements to avoid redundant API calls"""
    
    def __init__(self):
        self.cache = {}
    
    def get_cache_key(self, analysis_report) -> str:
        """Generate cache key based on issues detected"""
        key_parts = [
            str(analysis_report.total_rows),
            str(analysis_report.total_columns),
            str(len(analysis_report.critical_issues)),
            str(len(analysis_report.recommended_fixes)),
            str(len(analysis_report.optional_improvements))
        ]
        return "|".join(key_parts)
    
    def get(self, cache_key: str) -> Optional[Dict]:
        """Get cached enhancement"""
        return self.cache.get(cache_key)
    
    def set(self, cache_key: str, enhancement: Dict):
        """Cache an enhancement"""
        self.cache[cache_key] = enhancement
    
    def clear(self):
        """Clear the cache"""
        self.cache.clear()