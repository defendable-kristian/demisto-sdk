import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Set

from pydantic import Field

from demisto_sdk.commands.common.constants import MarketplaceVersions
from demisto_sdk.commands.content_graph.common import ContentType
from demisto_sdk.commands.content_graph.objects.content_item import ContentItem

logger = logging.getLogger("demisto-sdk")


class Job(ContentItem, content_type=ContentType.JOB):  # type: ignore[call-arg]
    description: str = Field(alias="details")

    def metadata_fields(self) -> Set[str]:
        return {"name", "description"}

    def _upload(self, client, marketplace: MarketplaceVersions):
        with TemporaryDirectory("w") as f:
            dir_path = Path(f)
            self.dump(dir_path, marketplace=marketplace)

            return client.generic_request(
                method="POST",
                path="jobs/import",
                files={"file": str(self.path)},
                content_type="multipart/form-data",
            )
