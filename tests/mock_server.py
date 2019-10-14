from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

app = Starlette()


@app.route("/")
async def source_redirect(req):
    return PlainTextResponse('ok')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=9090)
