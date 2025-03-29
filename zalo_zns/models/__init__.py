# models/__init__.py
from . import zns_config  # Import base models first
from . import zns_template
from . import zns_history
from . import sale_order
from . import purchase_order
from . import account_move
from . import zns_debug  # Debug model should be imported LAST