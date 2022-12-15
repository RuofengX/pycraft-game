import typer
import uvicorn

from server import create_app


def main(
    save_file_path: str,
    host: str = "127.0.0.1",
    port: int = 8000,
):
    if save_file_path is None:
        save_file_path = 'tmp_save_file.bin'
    uvicorn.run(
        create_app(save_file_path),
        host=host,
        port=port,
    )


if __name__ == "__main__":
    typer.run(main)
