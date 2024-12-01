from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
import json

class FormatStyle(Enum):
    """Query formatting styles."""
    COMPACT = "compact"
    READABLE = "readable"
    INDENTED = "indented"

@dataclass
class FormatOptions:
    """Query formatting options."""
    style: FormatStyle = FormatStyle.READABLE
    indent_size: int = 4
    uppercase_keywords: bool = True
    max_line_length: int = 80
    align_columns: bool = True
    align_conditions: bool = True
    split_conditions: bool = True
    one_statement_per_line: bool = True

class QueryFormatter:
    """Base class for query formatters."""
    
    def __init__(self, options: Optional[FormatOptions] = None):
        self.options = options or FormatOptions()
        self.logger = logging.getLogger(__name__)
    
    def format(self, query: Any) -> str:
        """Format the query."""
        raise NotImplementedError

class ResultFormatter:
    """Formats query results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_table(self,
                    data: List[Dict[str, Any]],
                    headers: Optional[List[str]] = None,
                    format_type: str = "text") -> str:
        """Format results as a table."""
        try:
            if not data:
                return "No results"
            
            # Get headers if not provided
            if not headers:
                headers = list(data[0].keys())
            
            if format_type == "text":
                return self._format_text_table(data, headers)
            elif format_type == "csv":
                return self._format_csv(data, headers)
            elif format_type == "json":
                return self._format_json(data)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
        except Exception as e:
            self.logger.error(f"Error formatting table: {e}")
            return str(e)
    
    def format_scalar(self, value: Any, format_type: str = "text") -> str:
        """Format a scalar result."""
        try:
            if format_type == "text":
                return str(value)
            elif format_type == "json":
                return json.dumps(value)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
        except Exception as e:
            self.logger.error(f"Error formatting scalar: {e}")
            return str(e)
    
    def format_error(self, error: Exception) -> str:
        """Format an error result."""
        try:
            return f"Error: {str(error)}"
        except Exception as e:
            self.logger.error(f"Error formatting error: {e}")
            return str(e)
    
    def _format_text_table(self,
                          data: List[Dict[str, Any]],
                          headers: List[str]) -> str:
        """Format data as text table."""
        try:
            # Calculate column widths
            widths = {
                header: max(
                    len(str(header)),
                    max(len(str(row.get(header, ''))) for row in data)
                )
                for header in headers
            }
            
            # Create separator line
            separator = '+' + '+'.join(
                '-' * (widths[header] + 2)
                for header in headers
            ) + '+'
            
            # Create header row
            header_row = '|' + '|'.join(
                f" {header:{widths[header]}} "
                for header in headers
            ) + '|'
            
            # Create data rows
            data_rows = []
            for row in data:
                data_rows.append('|' + '|'.join(
                    f" {str(row.get(header, '')):{widths[header]}} "
                    for header in headers
                ) + '|')
            
            # Combine all parts
            return '\n'.join([
                separator,
                header_row,
                separator,
                *data_rows,
                separator
            ])
        except Exception as e:
            self.logger.error(f"Error formatting text table: {e}")
            return str(e)
    
    def _format_csv(self,
                   data: List[Dict[str, Any]],
                   headers: List[str]) -> str:
        """Format data as CSV."""
        try:
            # Create header row
            rows = [','.join(headers)]
            
            # Create data rows
            for row in data:
                rows.append(','.join(
                    str(row.get(header, ''))
                    for header in headers
                ))
            
            return '\n'.join(rows)
        except Exception as e:
            self.logger.error(f"Error formatting CSV: {e}")
            return str(e)
    
    def _format_json(self, data: List[Dict[str, Any]]) -> str:
        """Format data as JSON."""
        try:
            return json.dumps(data, indent=2)
        except Exception as e:
            self.logger.error(f"Error formatting JSON: {e}")
            return str(e)

class StreamingResultFormatter(ResultFormatter):
    """Formats streaming query results."""
    
    def __init__(self,
                 batch_size: int = 1000,
                 max_buffer_size: int = 10000):
        super().__init__()
        self.batch_size = batch_size
        self.max_buffer_size = max_buffer_size
        self._buffer: List[Dict[str, Any]] = []
        self._headers: Optional[List[str]] = None
    
    async def start_batch(self,
                         headers: Optional[List[str]] = None) -> None:
        """Start a new batch of results."""
        self._buffer = []
        self._headers = headers
    
    async def add_row(self, row: Dict[str, Any]) -> Optional[str]:
        """Add a row to the current batch."""
        try:
            self._buffer.append(row)
            
            # Update headers if not set
            if not self._headers:
                self._headers = list(row.keys())
            
            # Format and return batch if buffer is full
            if len(self._buffer) >= self.batch_size:
                return await self.end_batch()
            
            return None
        except Exception as e:
            self.logger.error(f"Error adding row: {e}")
            return str(e)
    
    async def end_batch(self) -> str:
        """End and format current batch."""
        try:
            if not self._buffer:
                return ""
            
            result = self.format_table(
                self._buffer,
                self._headers,
                format_type="text"
            )
            self._buffer = []
            return result
        except Exception as e:
            self.logger.error(f"Error ending batch: {e}")
            return str(e)

class ProgressFormatter:
    """Formats query execution progress."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_progress(self,
                       current: int,
                       total: int,
                       width: int = 50) -> str:
        """Format progress bar."""
        try:
            if total <= 0:
                return "[Error: Invalid total]"
            
            percentage = min(100, int((current / total) * 100))
            filled = int((width * current) / total)
            bar = '=' * filled + '-' * (width - filled)
            
            return f"[{bar}] {percentage}% ({current}/{total})"
        except Exception as e:
            self.logger.error(f"Error formatting progress: {e}")
            return str(e)
    
    def format_stage_progress(self,
                            stages: List[Dict[str, Any]]) -> str:
        """Format multi-stage progress."""
        try:
            lines = []
            total_progress = 0
            
            for stage in stages:
                name = stage.get('name', 'Unknown')
                current = stage.get('current', 0)
                total = stage.get('total', 0)
                
                if total > 0:
                    progress = self.format_progress(current, total)
                    lines.append(f"{name}: {progress}")
                    total_progress += (current / total)
            
            overall = int((total_progress / len(stages)) * 100)
            lines.insert(0, f"Overall Progress: {overall}%")
            
            return '\n'.join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting stage progress: {e}")
            return str(e)
    
    def format_timing(self, timing: Dict[str, float]) -> str:
        """Format execution timing information."""
        try:
            lines = []
            total_time = sum(timing.values())
            
            for stage, time in timing.items():
                percentage = int((time / total_time) * 100)
                lines.append(
                    f"{stage}: {time:.2f}s ({percentage}%)"
                )
            
            lines.append(f"Total Time: {total_time:.2f}s")
            return '\n'.join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting timing: {e}")
            return str(e) 