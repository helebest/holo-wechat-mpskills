from pydantic import BaseModel, Field


class CharacterProfile(BaseModel):
    """Visual profile for a character or entity in the story."""

    id: str = Field(description="Unique ID of the character/subject")
    description: str = Field(
        description="Visual description of the character (appearance, clothing, signature features)"
    )


class SceneDescription(BaseModel):
    """Description of a scene to be illustrated."""

    index: int = Field(description="Scene index (1-based)")
    scene_description: str = Field(
        description="Detailed visual description of the scene action and environment"
    )
    characters: list[str] = Field(
        description="List of character IDs present in this scene"
    )
    insert_after: str = Field(
        description="Anchor ID (e.g., 'P3') indicating where to insert the illustration"
    )
    final_prompt: str | None = Field(
        default=None, description="Generated prompt for image generation"
    )
    image_path: str | None = Field(
        default=None, description="Path to the generated image file"
    )


class StoryAnalysis(BaseModel):
    """Complete analysis of a story for illustration generation."""

    global_style: str = Field(description="Consistent artistic style for all illustrations")
    aspect_ratio: str = Field(
        default="16:9", description="Aspect ratio for all images (e.g., 16:9, 4:3, 1:1)"
    )
    negative_prompt: str = Field(
        default="", description="Global negative prompt to avoid artifacts"
    )
    characters: list[CharacterProfile] = Field(
        description="List of all key characters appearing in the story"
    )
    scenes: list[SceneDescription] = Field(
        description="List of scenes to illustrate, distributed throughout the story"
    )


class ArticleIllustratorOutput(BaseModel):
    """Output of the article illustration pipeline."""

    original_markdown: str
    illustrated_markdown: str
    output_path: str
    analysis: StoryAnalysis
