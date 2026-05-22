import typer

from app.commands.documents import document_cli
from app.commands.literals import literal_cli
from app.commands.people import people_cli
from app.commands.structures import structure_cli
from app.commands.source_journals import source_journal_cli
from app.commands.source_records import source_record_cli

cli = typer.Typer()

cli.add_typer(people_cli, name="people")
cli.add_typer(structure_cli, name="structures")
cli.add_typer(document_cli, name="documents")
cli.add_typer(source_record_cli, name="source_records")
cli.add_typer(source_journal_cli, name="source_journals")
cli.add_typer(literal_cli, name="literals")

if __name__ == "__main__":
    cli()
