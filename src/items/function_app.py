import azure.functions as func
from .app.main import bp


app = func.FunctionApp()
app.register_functions(bp)
