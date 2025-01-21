import typer
from app.commands.documents import document_cli

cli = typer.Typer()

cli.add_typer(document_cli, name="documents")

if __name__ == "__main__":
    cli()
