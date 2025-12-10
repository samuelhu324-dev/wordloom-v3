"""
Tag Application Layer - Use Cases & Ports

Application layer (hexagonal middle ring) orchestrates domain logic.

Structure:
  application/
  ├── ports/
  │   ├── input.py       - UseCase interfaces (input ports)
  │   └── output.py      - Repository interfaces (output ports)
  ├── use_cases/
  │   ├── create_tag.py
  │   ├── list_tags.py
  │   ├── search_tags.py
  │   ├── update_tag.py
  │   ├── delete_tag.py
  │   ├── restore_tag.py
  │   ├── associate_tag.py
  │   └── disassociate_tag.py
  └── __init__.py

Dependency flow:
  UseCase ← Repository (output port)
  Router → UseCase (input port)
"""
