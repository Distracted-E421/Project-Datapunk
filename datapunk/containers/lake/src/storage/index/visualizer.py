from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
from pathlib import Path
import json
import io
import base64

from .stats import (
    IndexStats,
    StatisticsStore,
    StatisticsManager
)

class StatisticsVisualizer:
    """Generates visualizations for index statistics."""
    
    def __init__(
        self,
        store: StatisticsStore,
        output_dir: Optional[str] = None
    ):
        self.store = store
        self.output_dir = Path(output_dir) if output_dir else None
        
        # Set style
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
    def plot_performance_trends(
        self,
        index_name: str,
        days: int = 30,
        save: bool = False
    ) -> Optional[str]:
        """Plot read/write performance trends."""
        history = self._get_history(index_name, days)
        if not history:
            return None
            
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        dates = [stats.created_at for stats in history]
        
        # Read performance
        read_times = [stats.usage.avg_read_time_ms for stats in history]
        ax1.plot(dates, read_times, marker='o', label='Average Read Time (ms)')
        ax1.fill_between(dates, read_times, alpha=0.3)
        ax1.set_title('Read Performance Trend')
        ax1.set_ylabel('Time (ms)')
        ax1.grid(True)
        
        # Write performance
        write_times = [stats.usage.avg_write_time_ms for stats in history]
        ax2.plot(dates, write_times, marker='o', color='green', 
                label='Average Write Time (ms)')
        ax2.fill_between(dates, write_times, color='green', alpha=0.3)
        ax2.set_title('Write Performance Trend')
        ax2.set_ylabel('Time (ms)')
        ax2.grid(True)
        
        # Format dates
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
        plt.tight_layout()
        
        if save and self.output_dir:
            path = self.output_dir / f"{index_name}_performance.png"
            plt.savefig(path)
            plt.close()
            return str(path)
        else:
            return self._fig_to_base64(fig)
            
    def plot_size_distribution(
        self,
        index_names: List[str],
        save: bool = False
    ) -> Optional[str]:
        """Plot size comparison across indexes."""
        data = []
        for name in index_names:
            stats = self.store.get_latest_stats(name)
            if stats:
                data.append({
                    'name': name,
                    'entries': stats.size.total_entries,
                    'bytes': stats.size.size_bytes / 1024  # Convert to KB
                })
                
        if not data:
            return None
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Entries comparison
        entries = [d['entries'] for d in data]
        names = [d['name'] for d in data]
        ax1.bar(names, entries)
        ax1.set_title('Total Entries by Index')
        ax1.set_ylabel('Number of Entries')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Size comparison
        sizes = [d['bytes'] for d in data]
        ax2.bar(names, sizes, color='green')
        ax2.set_title('Index Sizes')
        ax2.set_ylabel('Size (KB)')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save and self.output_dir:
            path = self.output_dir / "index_size_comparison.png"
            plt.savefig(path)
            plt.close()
            return str(path)
        else:
            return self._fig_to_base64(fig)
            
    def plot_cache_performance(
        self,
        index_name: str,
        days: int = 30,
        save: bool = False
    ) -> Optional[str]:
        """Plot cache hit ratio trend."""
        history = self._get_history(index_name, days)
        if not history:
            return None
            
        fig, ax = plt.subplots(figsize=(12, 6))
        dates = [stats.created_at for stats in history]
        
        # Calculate hit ratios
        hit_ratios = []
        for stats in history:
            total = stats.usage.cache_hits + stats.usage.cache_misses
            ratio = (
                stats.usage.cache_hits / total if total > 0 else 0
            )
            hit_ratios.append(ratio * 100)  # Convert to percentage
            
        ax.plot(dates, hit_ratios, marker='o', color='purple')
        ax.fill_between(dates, hit_ratios, color='purple', alpha=0.3)
        ax.set_title('Cache Hit Ratio Trend')
        ax.set_ylabel('Hit Ratio (%)')
        ax.grid(True)
        ax.set_ylim(0, 100)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save and self.output_dir:
            path = self.output_dir / f"{index_name}_cache.png"
            plt.savefig(path)
            plt.close()
            return str(path)
        else:
            return self._fig_to_base64(fig)
            
    def plot_condition_analysis(
        self,
        index_name: str,
        days: int = 30,
        save: bool = False
    ) -> Optional[str]:
        """Plot condition performance metrics."""
        history = self._get_history(index_name, days)
        if not history or not all(h.condition for h in history):
            return None
            
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        dates = [stats.created_at for stats in history]
        
        # Selectivity and false positives
        selectivity = [stats.condition.selectivity * 100 for stats in history]
        false_positives = [
            stats.condition.false_positive_rate * 100 for stats in history
        ]
        
        ax1.plot(dates, selectivity, marker='o', label='Selectivity (%)')
        ax1.plot(dates, false_positives, marker='o', label='False Positives (%)')
        ax1.set_title('Condition Effectiveness')
        ax1.set_ylabel('Percentage')
        ax1.legend()
        ax1.grid(True)
        
        # Evaluation time
        eval_times = [
            stats.condition.evaluation_time_ms for stats in history
        ]
        ax2.plot(dates, eval_times, marker='o', color='red')
        ax2.set_title('Condition Evaluation Time')
        ax2.set_ylabel('Time (ms)')
        ax2.grid(True)
        
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
        plt.tight_layout()
        
        if save and self.output_dir:
            path = self.output_dir / f"{index_name}_condition.png"
            plt.savefig(path)
            plt.close()
            return str(path)
        else:
            return self._fig_to_base64(fig)
            
    def create_dashboard(
        self,
        index_name: str,
        days: int = 30,
        save: bool = False
    ) -> Optional[str]:
        """Create a comprehensive dashboard of all metrics."""
        history = self._get_history(index_name, days)
        if not history:
            return None
            
        fig = plt.figure(figsize=(15, 12))
        gs = fig.add_gridspec(3, 2)
        
        # Performance plot
        ax1 = fig.add_subplot(gs[0, :])
        dates = [stats.created_at for stats in history]
        read_times = [stats.usage.avg_read_time_ms for stats in history]
        write_times = [stats.usage.avg_write_time_ms for stats in history]
        
        ax1.plot(dates, read_times, marker='o', label='Read Time')
        ax1.plot(dates, write_times, marker='o', label='Write Time')
        ax1.set_title('Performance Metrics')
        ax1.set_ylabel('Time (ms)')
        ax1.legend()
        ax1.grid(True)
        
        # Size metrics
        ax2 = fig.add_subplot(gs[1, 0])
        entries = [stats.size.total_entries for stats in history]
        ax2.plot(dates, entries, color='green', marker='o')
        ax2.set_title('Total Entries')
        ax2.grid(True)
        
        # Cache performance
        ax3 = fig.add_subplot(gs[1, 1])
        hit_ratios = []
        for stats in history:
            total = stats.usage.cache_hits + stats.usage.cache_misses
            ratio = stats.usage.cache_hits / total if total > 0 else 0
            hit_ratios.append(ratio * 100)
            
        ax3.plot(dates, hit_ratios, color='purple', marker='o')
        ax3.set_title('Cache Hit Ratio (%)')
        ax3.grid(True)
        
        # Condition metrics (if available)
        if all(h.condition for h in history):
            ax4 = fig.add_subplot(gs[2, :])
            selectivity = [stats.condition.selectivity * 100 for stats in history]
            false_positives = [
                stats.condition.false_positive_rate * 100 for stats in history
            ]
            
            ax4.plot(dates, selectivity, marker='o', label='Selectivity (%)')
            ax4.plot(
                dates,
                false_positives,
                marker='o',
                label='False Positives (%)'
            )
            ax4.set_title('Condition Metrics')
            ax4.legend()
            ax4.grid(True)
            
        # Format all date axes
        for ax in fig.get_axes():
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
        plt.tight_layout()
        
        if save and self.output_dir:
            path = self.output_dir / f"{index_name}_dashboard.png"
            plt.savefig(path)
            plt.close()
            return str(path)
        else:
            return self._fig_to_base64(fig)
            
    def _get_history(
        self,
        index_name: str,
        days: int
    ) -> List[IndexStats]:
        """Get historical statistics for the specified period."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        return self.store.get_stats_history(index_name, start_time, end_time)
        
    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8') 