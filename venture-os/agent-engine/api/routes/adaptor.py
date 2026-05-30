from fastapi import Request


def get_orchastrator(request: Request):
    return request.app.state.orchestrator
