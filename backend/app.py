"""TermHub backend
https://github.com/tiangolo/fastapi"""
from typing import Dict, List

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from enclave_wrangler.config import config


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)


@app.get("/")
def read_root():
    """Root route"""
    return {"Hello": "World"}
    # return ontocall('objectTypes')


@app.get("/ontocall")
def ontocall(path) -> [{}]:
    """API documentation at
    https://www.palantir.com/docs/foundry/api/ontology-resources/objects/list-objects/
    https://www.palantir.com/docs/foundry/api/ontology-resources/object-types/list-object-types/
    """
    headers = {
        "authorization": f"Bearer {config['PALANTIR_ENCLAVE_AUTHENTICATION_BEARER_TOKEN']}",
        # 'content-type': 'application/json'
    }
    # return {'path': path}
    print(f'ontocall param: {path}\n')
    ontology_rid = config['ONTOLOGY_RID']
    api_path = f'/api/v1/ontologies/{ontology_rid}/{path}'
    url = f'https://{config["HOSTNAME"]}{api_path}'
    print(f'ontocall: {api_path}\n{url}')

    response: List[Dict] = requests.get(url, headers=headers).json()
    # noinspection PyTypeChecker
    if path == 'objectTypes':
        response = response['data']
        api_names = sorted([
            t['apiName'] for t in response if t['apiName'].startswith('OMOP')])
        return api_names
    if path.startswith('objectTypes/'):
        return response

    return {'unrecognized path': path, 'response': response}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
