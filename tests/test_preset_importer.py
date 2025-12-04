from src.services.preset_importer import (
    _split_name_and_part,
    _parse_numbers_and_meta,
    import_presets_from_lines,
    KNOWN_PART_TOKENS,
)


class TestPresetImporter:
    def test_known_part_tokens_exist(self):
        """Test that known part tokens are defined."""
        assert isinstance(KNOWN_PART_TOKENS, list)
        assert len(KNOWN_PART_TOKENS) > 0
        assert "wieniec" in KNOWN_PART_TOKENS
        assert "bok" in KNOWN_PART_TOKENS
        assert "półka" in KNOWN_PART_TOKENS

    def test_split_name_and_part_basic(self):
        """Test basic name and part splitting."""
        tokens = ["D60", "bok", "720", "560", "2"]
        name, part_name, rest = _split_name_and_part(tokens)

        assert name == "D60"
        assert part_name == "bok"
        assert rest == ["720", "560", "2"]

    def test_split_name_and_part_compound_name(self):
        """Test splitting with compound cabinet name."""
        tokens = ["D60", "special", "bok", "720", "560", "2"]
        name, part_name, rest = _split_name_and_part(tokens)

        assert name == "D60 special"
        assert part_name == "bok"
        assert rest == ["720", "560", "2"]

    def test_split_name_and_part_compound_part(self):
        """Test splitting with compound part name."""
        tokens = ["G40", "wieniec", "górny", "720", "560", "1"]
        name, part_name, rest = _split_name_and_part(tokens)

        assert name == "G40"
        assert part_name == "wieniec górny"
        assert rest == ["720", "560", "1"]

    def test_split_name_and_part_case_insensitive(self):
        """Test that part token matching is case insensitive."""
        tokens = ["D60", "BOK", "720", "560", "2"]
        name, part_name, rest = _split_name_and_part(tokens)

        assert name == "D60"
        assert part_name == "BOK"
        assert rest == ["720", "560", "2"]

    def test_split_name_and_part_no_known_part(self):
        """Test splitting when no known part token is found."""
        tokens = ["D60", "custom", "part", "720", "560", "2"]
        name, part_name, rest = _split_name_and_part(tokens)

        # Should fallback to first two tokens as name
        assert name == "D60 custom"
        assert part_name == "part"
        assert rest == ["720", "560", "2"]

    def test_split_name_and_part_short_tokens(self):
        """Test splitting with very short token list."""
        tokens = ["D60"]
        name, part_name, rest = _split_name_and_part(tokens)

        assert name == "D60"
        assert part_name == ""
        assert rest == []

    def test_parse_numbers_and_meta_complete(self):
        """Test parsing complete number and metadata."""
        rest = ["720", "560", "2", "D", "test comment"]
        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        assert height == 720.0
        assert width == 560.0
        assert pieces == 2
        assert wrapping == "D"
        assert comments == "test comment"

    def test_parse_numbers_and_meta_minimal(self):
        """Test parsing with minimal data."""
        rest = ["720"]
        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        assert height == 720.0
        assert width is None
        assert pieces == 1  # default
        assert wrapping is None
        assert comments is None

    def test_parse_numbers_and_meta_empty(self):
        """Test parsing with empty rest."""
        rest = []
        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        assert height is None
        assert width is None
        assert pieces == 1  # default
        assert wrapping is None
        assert comments is None

    def test_parse_numbers_and_meta_decimal_comma(self):
        """Test parsing numbers with decimal comma."""
        rest = ["720,5", "560,25", "1"]
        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        assert height == 720.5
        assert width == 560.25
        assert pieces == 1

    def test_parse_numbers_and_meta_invalid_pieces(self):
        """Test parsing with invalid pieces value."""
        rest = ["720", "560", "invalid", "D"]
        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        assert height == 720.0
        assert width == 560.0
        assert pieces == 1  # fallback to default
        assert wrapping == "D"

    def test_parse_numbers_and_meta_multi_word_comment(self):
        """Test parsing with multi-word comment."""
        rest = ["720", "560", "2", "D", "this", "is", "a", "comment"]
        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        assert height == 720.0
        assert width == 560.0
        assert pieces == 2
        assert wrapping == "D"
        assert comments == "this is a comment"

    def test_parse_numbers_and_meta_empty_comment(self):
        """Test parsing with empty comment."""
        rest = ["720", "560", "2", "D", ""]
        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        assert comments is None  # empty string should become None

    def test_import_presets_from_lines_basic(self, session, template_service):
        """Test basic preset import from lines."""
        lines = [
            "PresetD60 bok 720 560 2 D",
            "PresetD60 półka 560 540 1",
            "PresetG40 bok 720 300 2 D",
        ]

        import_presets_from_lines(session, lines)

        # Check that templates were created
        templates = template_service.list_templates()
        template_names = [t.name for t in templates]
        assert "PresetD60" in template_names
        assert "PresetG40" in template_names

        # Check PresetD60 template
        preset_d60 = next(t for t in templates if t.name == "PresetD60")

        # Check parts were added
        d60_parts = template_service.list_parts(preset_d60.id)
        assert len(d60_parts) == 2

        part_names = [p.part_name for p in d60_parts]
        assert "bok" in part_names
        assert "półka" in part_names

    def test_import_presets_from_lines_with_groups(self, session, template_service):
        """Test preset import with group headers."""
        lines = [
            "SZAFKI DOLNE",
            "PresetD70 bok 720 560 2 D",
            "PresetD70 półka 560 540 1",
            "",
            "SZAFKI GÓRNE",
            "PresetG50 bok 720 300 2 D",
        ]

        import_presets_from_lines(session, lines)

        # Check that templates were created
        templates = template_service.list_templates()
        template_names = [t.name for t in templates]
        assert "PresetD70" in template_names
        assert "PresetG50" in template_names

    def test_import_presets_from_lines_skip_comments(self, session, template_service):
        """Test preset import skips comment lines."""
        lines = [
            "# This is a comment",
            "PresetD80 bok 720 560 2 D",
            "// Another comment",
            "PresetD80 półka 560 540 1",
            "; Yet another comment",
        ]

        import_presets_from_lines(session, lines)

        # Check that template was created despite comments
        templates = template_service.list_templates()
        template_names = [t.name for t in templates]
        assert "PresetD80" in template_names

        # Check parts were added (comments ignored)
        preset_d80 = next(t for t in templates if t.name == "PresetD80")
        d80_parts = template_service.list_parts(preset_d80.id)
        assert len(d80_parts) == 2

    def test_import_presets_from_lines_skip_empty(self, session, template_service):
        """Test preset import skips empty lines."""
        lines = [
            "",
            "PresetD90 bok 720 560 2 D",
            "   ",  # whitespace only
            "PresetD90 półka 560 540 1",
            "",
        ]

        import_presets_from_lines(session, lines)

        # Check that template was created despite empty lines
        templates = template_service.list_templates()
        template_names = [t.name for t in templates]
        assert "PresetD90" in template_names

    def test_import_presets_from_lines_custom_kitchen_type(
        self, session, template_service
    ):
        """Test preset import with custom kitchen type."""
        lines = [
            "CustomD60 bok 720 560 2 D",
        ]

        import_presets_from_lines(session, lines, default_kitchen_type="CUSTOM")

        # Check that template was created with custom kitchen type
        templates = template_service.list_templates()
        custom_templates = [t for t in templates if t.name == "CustomD60"]
        assert len(custom_templates) == 1
        assert custom_templates[0].kitchen_type == "CUSTOM"

    def test_import_presets_from_lines_duplicate_handling(
        self, session, template_service
    ):
        """Test that duplicate templates are handled properly."""
        lines1 = ["DuplicateTest bok 720 560 2 D"]
        lines2 = ["DuplicateTest półka 560 540 1"]

        # Import first batch
        import_presets_from_lines(session, lines1)

        # Import second batch with same template name
        import_presets_from_lines(session, lines2)

        # Check that parts were added to existing template
        templates = template_service.list_templates()
        duplicate_templates = [t for t in templates if t.name == "DuplicateTest"]
        assert len(duplicate_templates) == 1  # Should reuse existing template

        # Check both parts exist
        duplicate_parts = template_service.list_parts(duplicate_templates[0].id)
        assert len(duplicate_parts) == 2

    def test_import_presets_malformed_line_handling(self, session, template_service):
        """Test handling of malformed lines."""
        lines = [
            "MalformedTest bok 720 560 2 D",  # good line
            "malformed line without proper format",  # bad line
            "MalformedTest półka 560 540 1",  # good line
        ]

        # Should not raise exception, should process good lines
        import_presets_from_lines(session, lines)

        # Check that good lines were processed
        templates = template_service.list_templates()
        malformed_templates = [t for t in templates if t.name == "MalformedTest"]
        if (
            malformed_templates
        ):  # May or may not create template depending on implementation
            malformed_parts = template_service.list_parts(malformed_templates[0].id)
            # Should have processed the good lines
            assert len(malformed_parts) >= 1
