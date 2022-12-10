from typing import Optional

import uvicorn
import typer

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
