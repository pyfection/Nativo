import os

from app import NativoApp


os.environ['NATIVO_DB'] = 'sqlite:///./client.db'

app = NativoApp()
app.run()
