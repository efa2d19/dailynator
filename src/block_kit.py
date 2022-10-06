from typing import Sequence, Optional

from slack_sdk.models.blocks import Block
from slack_sdk.models.blocks import SectionBlock
from slack_sdk.models.blocks import ContextBlock

from slack_sdk.models.attachments import BlockAttachment
from slack_sdk.models.blocks import MarkdownTextObject
from slack_sdk.models.blocks import DividerBlock
from slack_sdk.models.blocks import HeaderBlock


def report_attachment_block(
        header_text: str,
        body_text: str,
        color: str,
) -> BlockAttachment:
    """
    Attachment unit to be sent as a report in the channel

    :param header_text: Question text (no markdown)
    :param body_text: Answer text (has markdown)
    :param color: Color of the strip on the left side of the block
    :return: Report block unit
    """

    return BlockAttachment(
        blocks=[
            HeaderBlock(
                text=header_text,
            ),
            SectionBlock(
                text=MarkdownTextObject(
                    text=body_text,
                )
            )
        ],
        color=color,
    )


def start_daily_block(
        header_text: str,
        body_text: str,
        first_question: str,
) -> Sequence[Block]:
    """
    Set of blocks to be sent to users on daily start

    :param header_text: Greetings above divider
    :param body_text: Something inspirational (yup, daily is hard, cheer 'em up)
    :param first_question: First question from question list
    :return: Blocks to be sent on daily start
    """

    return [
        ContextBlock(
            elements=[
                MarkdownTextObject(
                    text=header_text,
                ),
            ]
        ),
        DividerBlock(),
        SectionBlock(
            text=MarkdownTextObject(
                text=body_text,
            )
        ),
        SectionBlock(
            text=MarkdownTextObject(
                text=">" + first_question,
            )
        ),
    ]


def end_daily_block(
        start_body_text: str,
        end_body_text: str,
        footer_text: str,
) -> Sequence[Block]:
    """
    Set of blocks to be sent on daily end (all questions ended)

    :param start_body_text: Show 'em your gratitude here and tag 'em
    :param end_body_text: Something inspirational again (they have all day ahead)
    :param footer_text: Where to find a report (add chanel link here)
    :return: Blocks to be sent on daily end
    """

    return [
        SectionBlock(
            text=MarkdownTextObject(
                text=start_body_text,
            )
        ),
        SectionBlock(
            text=MarkdownTextObject(
                text=end_body_text,
            )
        ),
        DividerBlock(),
        ContextBlock(
            elements=[
                MarkdownTextObject(
                    text=footer_text,
                ),
            ]
        ),
    ]


def question_list_block(
        question_list: list[str, str],
) -> Sequence[Block]:
    """
    Blocks constructor for get questions command

    :param question_list: List of all question for the channel
    :return: List of blocks w/ questions
    """

    field_list = list()

    # Add indexes (for pop command)
    for idx, question in enumerate(question_list, start=1):
        field_list.append(
            MarkdownTextObject(
                text=f"{idx}.\t{question}",
            )
        )

    return [
        HeaderBlock(
            text="Question list",
        ),
        DividerBlock(),
        SectionBlock(
            fields=field_list,
        ),
    ]


def error_block(
        header_text: str,
        body_text: Optional[str] = None,
) -> Sequence[Block]:
    """
    Make it look beautiful at least when error occurs

    :param header_text: Error summary
    :param body_text: Error main message (Optional)
    :return: Error block
    """

    blocks = [
        HeaderBlock(
            text=":x:\t" + header_text,
        ),
        DividerBlock(),
    ]

    if body_text is not None:
        blocks.append(
            SectionBlock(
                fields=[
                    MarkdownTextObject(
                        text=body_text,
                    )
                ],
            ),
        )

    return blocks


def success_block(
        header_text: str,
        body_text: Optional[str] = None,
) -> Sequence[Block]:
    """
    Block to be shown on success execution

    :param header_text: Success summary
    :param body_text: Success main message (optional)
    :return: Success block
    """

    blocks = [
        HeaderBlock(
            text=":white_check_mark:\t" + header_text,
        ),
        DividerBlock(),
    ]

    if body_text is not None:
        blocks.insert(
            1,
            SectionBlock(
                text=MarkdownTextObject(
                    text=body_text,
                )
            ),
        )

    return blocks
