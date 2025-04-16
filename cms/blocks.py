from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.contrib.table_block.blocks import TableBlock

class LessonContentBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(
        form_classname="full title",
        icon="title",
        template="cms/blocks/heading.html"
    )
    paragraph = blocks.RichTextBlock(
        features=['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul', 'image'],
        icon="pilcrow"
    )
    image = ImageChooserBlock(icon="image")
    video = blocks.URLBlock(
        help_text="Incolla URL video (YouTube/Vimeo)",
        icon="media"
    )
    exercise = blocks.StructBlock([
        ('question', blocks.RichTextBlock()),
        ('solution', blocks.RichTextBlock(required=False)),
        ('points', blocks.IntegerBlock(min_value=1, default=10))
    ], icon="form")

    class Meta:
        template = "cms/blocks/lesson_content.html"

class QuizBlock(blocks.StructBlock):
    question = blocks.RichTextBlock(features=['bold', 'italic', 'link'])
    answers = blocks.ListBlock(
        blocks.StructBlock([
            ('text', blocks.CharBlock(required=True)),
            ('correct', blocks.BooleanBlock(default=False)),
        ])
    )
    explanation = blocks.RichTextBlock(features=['bold', 'italic', 'link'], required=False)

    class Meta:
        icon = 'form'
        template = 'cms/blocks/quiz_block.html'

class FileUploadBlock(blocks.StructBlock):
    prompt = blocks.CharBlock(help_text="Istruzioni per l'upload")
    allowed_extensions = blocks.ListBlock(
        blocks.ChoiceBlock(choices=[
            ('pdf', 'PDF'),
            ('jpg', 'JPG'),
            ('png', 'PNG'),
        ])
    )
    max_size = blocks.IntegerBlock(
        help_text="Dimensione massima in KB",
        default=2048
    )

    class Meta:
        icon = 'download'
        template = 'cms/blocks/file_upload_block.html'

class EvaluationBlock(blocks.StructBlock):
    rubric = blocks.ListBlock(
        blocks.StructBlock([
            ('criteria', blocks.CharBlock()),
            ('points', blocks.IntegerBlock(min_value=1, max_value=10)),
        ])
    )
    teacher_notes = blocks.RichTextBlock(features=['bold', 'italic', 'link'])

    class Meta:
        icon = 'edit'
        template = 'cms/blocks/evaluation_block.html'