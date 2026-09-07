import uuid

import pytest
from app.contracts import SessionPayload


@pytest.fixture
def payload():
    rows, columns = [uuid.uuid4() for _ in range(2)], [uuid.uuid4() for _ in range(2)]
    return SessionPayload(
        session_id=uuid.uuid4(),
        revision=1,
        major="CS",
        universities=[
            dict(id=rows[0], name="Example", country="Canada"),
            dict(id=rows[1], name="Example", country="France", major="Math"),
        ],
        questions=[
            dict(id=columns[0], label="Fees"),
            dict(id=columns[1], label="Courses"),
        ],
        targets=[
            dict(row_id=row, column_id=column) for row in rows for column in columns
        ],
    )
