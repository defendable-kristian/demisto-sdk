from __future__ import annotations

from typing import Iterable, List

from demisto_sdk.commands.content_graph.objects.pack import Pack
from demisto_sdk.commands.content_graph.parsers.related_files import RelatedFileType
from demisto_sdk.commands.validate.validators.base_validator import (
    BaseValidator,
    FixResult,
    ValidationResult,
)

ContentTypes = Pack


class ReleaseNotesBreakingChangesValidator(BaseValidator[ContentTypes]):
    error_code = "RN112"
    description = (
        "Makes sure breaking changes are accompanied with a suitable json file."
    )
    rationale = "Breaking changes should be highly visible  to users."
    error_message = "Breaking changes require a release note configuration file, see xsoar.pan.dev/TODO for more information"  # TODO
    fix_message = "Created a {} changelog file"
    related_field = ""  # TODO
    is_auto_fixable = True  # TODO
    related_file_type = [RelatedFileType.RELEASE_NOTE]

    def obtain_invalid_content_items(
        self, content_items: Iterable[ContentTypes]
    ) -> List[ValidationResult]:
        return [
            ValidationResult(
                validator=self,
                message=self.error_message,
                content_object=content_item,
            )
            for content_item in content_items
            if (
                "breaking change" in content_item.release_note.file_content_str.lower()
                and (content_item.pack_version)
                and (
                    (str(content_item.pack_version).replace(".", "_") + ".json")
                    not in content_item.release_note.rn_config_file_names
                )
            )
        ]

    def fix(self, content_item: ContentTypes) -> FixResult:
        # Add your fix right here
        return FixResult(
            validator=self,
            message=self.fix_message,
            content_object=content_item,
        )
