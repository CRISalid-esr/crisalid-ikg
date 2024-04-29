""" Main application and routing logic for API """

import uvicorn

from app.crisalid_ikg import CrisalidIKG

app = CrisalidIKG()

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("app.crisalid_ikg:CrisalidIKG", host="0.0.0.0", port=8001, workers=1)
