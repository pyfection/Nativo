import os

from app import NativoApp


os.environ["NATIVO_LANG"] = "bav"

app = NativoApp()
app.run()
