import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from demisto_sdk.commands.common.tools import get_json, get_current_repo
from demisto_sdk.commands.content_graph.constants import REPO_PATH, ContentTypes, Relationship, PACK_METADATA_FILENAME
from demisto_sdk.commands.content_graph.parsers.parser_factory import ParserFactory
import demisto_sdk.commands.content_graph.parsers.base_content as base_content


class PackParser(base_content.BaseContentParser):
    def __init__(self, path: Path) -> None:
        self.pack_id: str = path.parts[-1]
        print(f'Parsing {self.content_type} {self.pack_id}')
        self.path: Path = path
        self.metadata: Dict[str, Any] = get_json(path / PACK_METADATA_FILENAME)
        self.nodes: Dict[ContentTypes, List[Dict[str, Any]]] = {}
        self.relationships: Dict[Tuple[ContentTypes, Relationship, ContentTypes], List[Dict[str, Any]]] = {}

    @property
    def node_id(self) -> str:
        return f'{self.content_type}:{self.pack_id}'

    @property
    def content_type(self) -> ContentTypes:
        return ContentTypes.PACK

    @property
    def deprecated(self) -> bool:
        return self.metadata.get('deprecated', False)

    @property
    def marketplaces(self) -> List[str]:
        return self.metadata.get('marketplaces', [])

    def add_pack_node(self) -> Dict[str, Any]:
        self.nodes[ContentTypes.PACK] = [self.get_data()]

    def add_content_item_node(self, parser: Any) -> Dict[str, Any]:
        self.nodes.setdefault(parser.content_type, []).append(parser.get_data())

    def add_content_item_relationships(self, parser: Any) -> None:
        parser.add_relationship(
            Relationship.IN_PACK,
            target=self.node_id,
        )
        for k, v in parser.relationships.items():
            self.relationships.setdefault(k, []).extend(v)

    def get_data(self) -> Dict[str, Any]:
        base_content_data: Dict[str, Any] = super().get_data()
        pack_data: Dict[str, Any] = {
            'node_id': self.node_id,
            'id': self.pack_id,
            'name': self.metadata.get('name'),
            'file_path': self.path.relative_to(REPO_PATH).as_posix(),
            'current_version': self.metadata.get('currentVersion'),
            'author': self.metadata.get('author'),
            'certification': 'certified' if self.metadata.get('support', '').lower() in ['xsoar', 'partner'] else '',
            'tags': self.metadata.get('tags', []),
            'use_cases': self.metadata.get('useCases', []),
            'categories': self.metadata.get('categories', []),
            'content_type': self.content_type,
        }
        return pack_data | base_content_data

    def parse_pack(self) -> None:
        self.add_pack_node()
        for folder in ContentTypes.pack_folders(self.path):
            self.parse_pack_folder(folder)

    def parse_pack_folder(self, folder_path: Path) -> None:
        for content_item_path in folder_path.iterdir():  # todo: consider multiprocessing
            if content_item := ParserFactory.from_path(content_item_path, self.marketplaces):
                self.add_content_item_node(content_item)
                self.add_content_item_relationships(content_item)


class PackSubGraphCreator:
    """ Creates a graph representation of a pack in content repository.

    Attributes:
        nodes:         Holds all parsed nodes of a pack.
        relationships: Holds all parsed relationships of a pack.
    """
    @staticmethod
    def from_path(path: Path) -> Tuple[
        Dict[ContentTypes, List[Dict[str, Any]]],
        Dict[Relationship, List[Dict[str, Any]]]
    ]:
        """ Given a pack path, parses it into nodes and relationships. """
        try:
            pack_parser = PackParser(path)
            pack_parser.parse_pack()
        except Exception:
            print(traceback.format_exc())
            raise Exception(traceback.format_exc())
        return pack_parser.nodes, pack_parser.relationships
