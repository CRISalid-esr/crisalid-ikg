import typer

from app.commands.documents import document_cli
from app.commands.people import people_cli
from app.commands.research_structures import research_structure_cli
from app.commands.source_journals import source_journal_cli
from app.commands.source_records import source_record_cli

cli = typer.Typer()

cli.add_typer(people_cli, name="people")
cli.add_typer(research_structure_cli, name="research_structures")
cli.add_typer(document_cli, name="documents")
cli.add_typer(source_record_cli, name="source_records")
cli.add_typer(source_journal_cli, name="source_journals")

if __name__ == "__main__":
    cli()
