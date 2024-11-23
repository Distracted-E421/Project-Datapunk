from datapunk_shared.config.loader import ConfigLoader
from datapunk_shared.config.schemas import GlobalConfig
import structlog

logger = structlog.get_logger(__name__)

class LakeConfigManager:
    """Configuration manager for Lake service"""
    
    def __init__(self):
        self.loader = ConfigLoader(
            config_dir="/app/config",
            env_prefix="DATAPUNK_"
        )
        
    def load_configurations(self) -> None:
        """Load all service configurations"""
        try:
            # Load global config
            self.global_config = self.loader.load_config(
                "global",
                model=GlobalConfig
            )
            
            # Load service-specific configs
            self.storage_config = self.loader.load_config("storage")
            self.mesh_config = self.loader.load_config("mesh")
            
            logger.info(
                "Configurations loaded successfully",
                environment=self.global_config.environment
            )
            
        except Exception as e:
            logger.error(
                "Failed to load configurations",
                error=str(e)
            )
            raise 