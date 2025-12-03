"""Export Helper - Export results to files"""
import pandas as pd
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class ExportHelper:
    """Helper for exporting results"""

    @staticmethod
    def export_to_excel(df: pd.DataFrame, filepath: str, sheet_name: str = 'Sheet1'):
        """Export DataFrame to Excel"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    @staticmethod
    def export_to_csv(df: pd.DataFrame, filepath: str):
        """Export DataFrame to CSV"""
        df.to_csv(filepath, index=False)

    @staticmethod
    def export_to_txt(df: pd.DataFrame, filepath: str, include_header: bool = True):
        """
        Export DataFrame to TXT with quoted comma-delimited format

        Args:
            df: DataFrame to export
            filepath: Output file path
            include_header: Whether to include header row (default True)

        Format: "value1","value2","value3"
        - Field delimiter: Comma (,)
        - Text qualifier: Double quotes (")
        - All values are quoted
        """
        df.to_csv(
            filepath,
            index=False,
            header=include_header,
            quoting=1,  # QUOTE_ALL - quote all fields
            quotechar='"',
            sep=','
        )

    @staticmethod
    def export_multiple_sheets(dataframes: dict, filepath: str):
        """Export multiple DataFrames to Excel sheets"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    # ==================== BATCH EXPORT METHODS ====================

    @staticmethod
    def export_batch_as_zip(results: List[Dict], output_path: str,
                           file_format: str = 'xlsx',
                           include_removed: bool = False,
                           progress_callback: Optional[Callable] = None) -> bool:
        """
        Export multiple processed files as a ZIP archive

        Args:
            results: List of result dictionaries from batch processing
                    Each dict should have: 'name', 'result_df', 'removed_df' (optional)
            output_path: Path to output ZIP file
            file_format: Export format ('xlsx', 'csv', 'txt')
            include_removed: Whether to include removed rows files
            progress_callback: Function to call with progress (current, total, filename)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Creating ZIP archive: {output_path}")

            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                total_files = len(results) * (2 if include_removed else 1)
                current = 0

                for result in results:
                    # Get base filename without extension
                    base_name = Path(result['name']).stem

                    # Export main result file
                    temp_file = self._create_temp_export(
                        result['result_df'],
                        base_name,
                        file_format
                    )

                    # Add to ZIP
                    arcname = f"{base_name}_processed.{file_format}"
                    zipf.write(temp_file, arcname)
                    temp_file.unlink()  # Delete temp file

                    current += 1
                    if progress_callback:
                        progress_callback(current, total_files, arcname)

                    logger.info(f"  Added: {arcname}")

                    # Export removed rows if requested
                    if include_removed and result.get('removed_df') is not None:
                        removed_temp = self._create_temp_export(
                            result['removed_df'],
                            f"{base_name}_removed",
                            file_format
                        )

                        removed_arcname = f"{base_name}_removed.{file_format}"
                        zipf.write(removed_temp, removed_arcname)
                        removed_temp.unlink()

                        current += 1
                        if progress_callback:
                            progress_callback(current, total_files, removed_arcname)

                        logger.info(f"  Added: {removed_arcname}")

            logger.info(f"✓ ZIP archive created successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create ZIP archive: {e}")
            return False

    @staticmethod
    def export_batch_individual(results: List[Dict], output_dir: str,
                               file_format: str = 'xlsx',
                               include_removed: bool = False,
                               progress_callback: Optional[Callable] = None) -> int:
        """
        Export multiple processed files to individual files in a directory

        Args:
            results: List of result dictionaries from batch processing
            output_dir: Directory to save files
            file_format: Export format ('xlsx', 'csv', 'txt')
            include_removed: Whether to include removed rows files
            progress_callback: Function to call with progress

        Returns:
            Number of files successfully exported
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting {len(results)} files to: {output_dir}")

        exported_count = 0
        total_files = len(results) * (2 if include_removed else 1)
        current = 0

        for result in results:
            try:
                base_name = Path(result['name']).stem

                # Export main result file
                output_file = output_path / f"{base_name}_processed.{file_format}"
                ExportHelper._export_by_format(result['result_df'], str(output_file), file_format)

                current += 1
                exported_count += 1
                if progress_callback:
                    progress_callback(current, total_files, output_file.name)

                logger.info(f"  Exported: {output_file.name}")

                # Export removed rows if requested
                if include_removed and result.get('removed_df') is not None:
                    removed_file = output_path / f"{base_name}_removed.{file_format}"
                    ExportHelper._export_by_format(result['removed_df'], str(removed_file), file_format)

                    current += 1
                    exported_count += 1
                    if progress_callback:
                        progress_callback(current, total_files, removed_file.name)

                    logger.info(f"  Exported: {removed_file.name}")

            except Exception as e:
                logger.error(f"Failed to export {result['name']}: {e}")

        logger.info(f"✓ Exported {exported_count}/{total_files} files successfully")
        return exported_count

    @staticmethod
    def export_combined_file(combined_df: pd.DataFrame, output_path: str,
                            file_format: str = 'xlsx',
                            sheet_name: str = 'Combined Data') -> bool:
        """
        Export a single combined DataFrame

        Args:
            combined_df: Combined DataFrame to export
            output_path: Path to output file
            file_format: Export format ('xlsx', 'csv', 'txt')
            sheet_name: Sheet name for Excel files

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Exporting combined file: {output_path}")
            logger.info(f"  Rows: {len(combined_df)}, Columns: {len(combined_df.columns)}")

            if file_format == 'xlsx':
                ExportHelper.export_to_excel(combined_df, output_path, sheet_name)
            elif file_format == 'csv':
                ExportHelper.export_to_csv(combined_df, output_path)
            elif file_format == 'txt':
                ExportHelper.export_to_txt(combined_df, output_path)
            else:
                raise ValueError(f"Unsupported format: {file_format}")

            logger.info(f"✓ Combined file exported successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to export combined file: {e}")
            return False

    @staticmethod
    def export_grouped_files(groups: Dict[str, pd.DataFrame], output_dir: str,
                            file_format: str = 'xlsx',
                            progress_callback: Optional[Callable] = None) -> int:
        """
        Export grouped DataFrames to individual files

        Args:
            groups: Dictionary mapping group names to DataFrames
            output_dir: Directory to save files
            file_format: Export format ('xlsx', 'csv', 'txt')
            progress_callback: Function to call with progress

        Returns:
            Number of files successfully exported
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting {len(groups)} grouped files to: {output_dir}")

        exported_count = 0
        total = len(groups)

        for idx, (group_name, group_df) in enumerate(groups.items(), 1):
            try:
                output_file = output_path / f"{group_name}.{file_format}"
                ExportHelper._export_by_format(group_df, str(output_file), file_format)

                exported_count += 1
                if progress_callback:
                    progress_callback(idx, total, output_file.name)

                logger.info(f"  Exported: {output_file.name} ({len(group_df)} rows)")

            except Exception as e:
                logger.error(f"Failed to export group {group_name}: {e}")

        logger.info(f"✓ Exported {exported_count}/{total} grouped files successfully")
        return exported_count

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _export_by_format(df: pd.DataFrame, filepath: str, file_format: str):
        """Export DataFrame in specified format"""
        if file_format == 'xlsx':
            ExportHelper.export_to_excel(df, filepath)
        elif file_format == 'csv':
            ExportHelper.export_to_csv(df, filepath)
        elif file_format == 'txt':
            ExportHelper.export_to_txt(df, filepath)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    @staticmethod
    def _create_temp_export(df: pd.DataFrame, base_name: str, file_format: str) -> Path:
        """Create temporary export file and return path"""
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"{base_name}_temp.{file_format}"

        ExportHelper._export_by_format(df, str(temp_file), file_format)
        return temp_file
