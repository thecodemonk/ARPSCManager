from flask import Blueprint

members_bp = Blueprint('members', __name__, url_prefix='/member')

from . import routes  # noqa: E402, F401
from . import auth  # noqa: E402, F401
