
import config

if config.debug:
    from db.local import DB
else:
    raise NotImplementedError("Have to implement access to AWS")
