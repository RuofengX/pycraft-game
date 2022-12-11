from typing import Optional

import typer
import uvicorn

from server import create_app


def main(
    save_file_path: Optional[str],
    host: str = '127.0.0.0',
    port: int = 8000,

):
    uvicorn.run(
        create_app(save_file_path),
        host=host,
        port=port,
    )


if __name__ == '__main__':
    typer.run(main)
