
import logging
from rich.logging import RichHandler



logging.basicConfig(
    level="INFO",
    
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

log = logging.getLogger("rich")