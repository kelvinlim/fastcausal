"""
fastcausal - Fast, easy-to-use causal discovery analysis tools.

A unified Python package for causal discovery that combines:
- tetrad-port (C++ causal algorithms, no Java required)
- dgraph_flex (graph visualization)
- Interactive Jupyter notebook support
- Config-driven batch processing pipeline

Usage::

    from fastcausal import FastCausal

    fc = FastCausal()
    df = fc.load_sample("boston")
    results, graph = fc.run_search(df, algorithm="gfci")
    fc.show_graph(graph)
"""

from fastcausal.core import FastCausal

__version_info__ = ('0', '1', '2')
__version__ = '.'.join(__version_info__)

__all__ = ["FastCausal"]
