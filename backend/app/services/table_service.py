"""Keeps the college x column grid consistent as rows and columns change."""

from sqlalchemy.orm import Session

from app.models import Cell, Chat, CollegeRow, ColumnDef
from app.services.defaults import DEFAULT_COLUMNS, unique_column_key


def create_default_columns(db: Session, chat: Chat) -> list[ColumnDef]:
    columns = [
        ColumnDef(
            chat_id=chat.id, key=key, label=label, is_default=True, sort_order=index
        )
        for index, (key, label) in enumerate(DEFAULT_COLUMNS)
    ]
    db.add_all(columns)
    db.flush()
    return columns


def add_empty_cells_for_college(
    db: Session, college: CollegeRow, columns: list[ColumnDef]
) -> None:
    db.add_all(
        Cell(college_row_id=college.id, column_id=column.id, value="", status="empty")
        for column in columns
    )


def add_empty_cells_for_column(
    db: Session, column: ColumnDef, colleges: list[CollegeRow]
) -> None:
    db.add_all(
        Cell(college_row_id=college.id, column_id=column.id, value="", status="empty")
        for college in colleges
    )


def add_college(
    db: Session,
    chat: Chat,
    *,
    name: str,
    country: str | None,
    major_override: str | None = None,
) -> CollegeRow:
    college = CollegeRow(
        chat_id=chat.id,
        name=name.strip(),
        country=country,
        major_override=major_override.strip() if major_override else None,
    )
    db.add(college)
    db.flush()
    add_empty_cells_for_college(db, college, chat.columns)
    return college


def add_column(db: Session, chat: Chat, label: str) -> ColumnDef:
    column = ColumnDef(
        chat_id=chat.id,
        key=unique_column_key(label, {c.key for c in chat.columns}),
        label=label,
        is_default=False,
        sort_order=max((column.sort_order for column in chat.columns), default=-1) + 1,
    )
    db.add(column)
    db.flush()
    add_empty_cells_for_column(db, column, chat.colleges)
    return column
