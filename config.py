from dataclasses import dataclass

@dataclass
class Config:
    region: str
    stage_name: str
    table_name: str
    log_level: str

    @property
    def lambda_env_vars(self):
        return {
            "TABLE_NAME": self.table_name,
            "LOG_LEVEL": self.log_level
        }
    
ENVIRONMENTS = {
    "dev": Config(
        region="ap-southeast-1",
        stage_name="dev",
        table_name="ItemsTable",
        log_level="DEBUG"
    ),
    "prod": Config(
        region="ap-southeast-1",
        stage_name="prod",
        table_name="ItemsTable",
        log_level="ERROR"
    )
}

def get_config(stage: str) -> Config:
    return ENVIRONMENTS.get(stage, ENVIRONMENTS["dev"])