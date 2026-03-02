from functools import lru_cache
from api.ml import MLPipeline

# Define as a Singleton so the 100MB+ model loads exactly once into RAM 
# when the FastAPI container starts, and NOT per-request.

@lru_cache()
def get_ml_pipeline() -> MLPipeline:
    """
    Returns the loaded ML Pipeline singleton.
    """
    return MLPipeline()
