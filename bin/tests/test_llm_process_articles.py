"""
Tests for llm_process_articles.py
"""

from datetime import date
from unittest.mock import patch

import pytest

from common.models import Article, ArticleList
from llm_process_articles import llm_process_articles


class TestLLMProcessArticles:
    """Test suite for llm_process_articles function"""

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing"""
        return [
            Article(
                title="Test Article 1",
                url="https://example.com/article1",
                journal="Test Journal",
                date=date(2024, 1, 1),
                access_date=date(2024, 1, 15),
                raw_contents="Content 1",
            ),
            Article(
                title="Test Article 2",
                url="https://example.com/article2",
                journal="Test Journal",
                date=date(2024, 1, 2),
                access_date=date(2024, 1, 15),
                raw_contents="Content 2",
            ),
        ]

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables"""
        with patch("llm_process_articles.get_env_variable") as mock_get_env:
            mock_get_env.return_value = "test-api-key"  # pragma: allowlist secret
            yield mock_get_env

    def test_metadata_stage_success(self, sample_articles, mock_env, tmp_path):
        """Test successful metadata stage processing"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        mock_response = '{"articles": []}'

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses") as mock_save,
            patch("llm_process_articles.pathlib.Path.write_text") as mock_write,
        ):
            mock_llm.return_value = mock_response
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify
            assert mock_llm.call_count == 1
            call_kwargs = mock_llm.call_args[1]
            assert len(call_kwargs["articles"]) == 2
            assert call_kwargs["system_prompt_path"] == str(system_prompt)
            assert call_kwargs["model"] == "gemini-1.5-flash"
            assert call_kwargs["api_key"] == "test-api-key"  # pragma: allowlist secret
            assert call_kwargs["research_interests_path"] is None
            assert len(call_kwargs["tools"]) == 3

            mock_validate.assert_called_once()
            assert mock_validate.call_args[1]["stage"] == "metadata"
            assert mock_validate.call_args[1]["merge_key"] == "url"

            mock_save.assert_called_once()
            mock_write.assert_called_once_with(mock_response)

    def test_tagging_stage_with_research_interests(
        self, sample_articles, mock_env, tmp_path
    ):
        """Test tagging stage with research interests"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        research_interests = tmp_path / "interests.md"
        research_interests.write_text("AI and machine learning")

        mock_response = '{"articles": []}'

        try:
            with (
                patch("llm_process_articles.chat") as mock_llm,
                patch("llm_process_articles.validate_llm_response") as mock_validate,
                patch("llm_process_articles.pathlib.Path.write_text"),
            ):
                mock_llm.return_value = mock_response
                mock_validate.return_value = {}

                # Execute
                llm_process_articles(
                    stage="tagging",
                    articles_json=str(articles_json),
                    system_prompt_path=str(system_prompt),
                    research_interests_path=str(research_interests),
                    model="gemini-2.5-flash-lite",
                    allow_qc_errors=True,
                    debug=True,
                )

                # Verify
                call_kwargs = mock_llm.call_args[1]
                assert call_kwargs["research_interests_path"] == str(research_interests)
                assert call_kwargs["model"] == "gemini-2.5-flash-lite"

                assert mock_validate.call_args[1]["stage"] == "tagging"
                assert mock_validate.call_args[1]["merge_key"] == "doi"
                assert mock_validate.call_args[1]["allow_qc_errors"] is True
        finally:
            # Cleanup: Remove generated JSON files
            from pathlib import Path

            for pattern in ["tagging_pass.json", "tagging_fail.json"]:
                file_path = Path(pattern)
                if file_path.exists():
                    file_path.unlink()

    def test_saves_raw_response_to_file(self, sample_articles, mock_env, tmp_path):
        """Test that raw LLM response is saved to file"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        mock_response = '{"articles": [{"title": "test"}]}'

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses"),
            patch("llm_process_articles.pathlib.Path.write_text") as mock_write,
        ):
            mock_llm.return_value = mock_response
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify - should save raw response
            mock_write.assert_called_once_with(mock_response)

    def test_loads_articles_from_json(self, sample_articles, mock_env, tmp_path):
        """Test that articles are loaded from JSON file"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses"),
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = '{"articles": []}'
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify articles were loaded and passed to chat
            call_kwargs = mock_llm.call_args[1]
            loaded_articles = call_kwargs["articles"]
            assert len(loaded_articles) == 2
            assert loaded_articles[0].title == "Test Article 1"
            assert loaded_articles[1].title == "Test Article 2"

    def test_passes_tools_to_chat(self, sample_articles, mock_env, tmp_path):
        """Test that metadata tools are passed to chat"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses"),
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = '{"articles": []}'
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify tools were passed
            call_kwargs = mock_llm.call_args[1]
            tools = call_kwargs["tools"]
            assert len(tools) == 3
            # Check function names
            assert tools[0].__name__ == "get_abstract_from_doi"
            assert tools[1].__name__ == "springer_get_abstract_from_doi"
            assert tools[2].__name__ == "get_doi_for_arxiv_url"

    def test_validation_failure_propagates(self, sample_articles, mock_env, tmp_path):
        """Test that validation failure is handled properly"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses") as mock_save,
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = '{"articles": []}'
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify validation was called and save was still called
            mock_validate.assert_called_once()
            mock_save.assert_called_once()
            # Check that response_pass={} (empty dict) was passed to save
            assert mock_save.call_args[1]["response_pass"] == {}

    def test_allow_qc_errors_propagates(self, sample_articles, mock_env, tmp_path):
        """Test that allow_qc_errors flag is passed through"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses") as mock_save,
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = '{"articles": []}'
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=True,
                debug=False,
            )

            # Verify flag was passed to both validate and save
            assert mock_validate.call_args[1]["allow_qc_errors"] is True
            assert mock_save.call_args[1]["allow_qc_errors"] is True

    def test_empty_articles_list(self, mock_env, tmp_path):
        """Test processing with empty articles list"""
        # Setup
        empty_articles = []
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(empty_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses"),
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = '{"articles": []}'
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify - should still call LLM with empty list
            call_kwargs = mock_llm.call_args[1]
            assert len(call_kwargs["articles"]) == 0

    def test_passes_correct_stage_to_validate(
        self, sample_articles, mock_env, tmp_path
    ):
        """Test that stage is correctly passed to validate function"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        research_interests = tmp_path / "interests.md"
        research_interests.write_text("Test")

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses"),
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = '{"articles": []}'
            mock_validate.return_value = {}

            # Test each stage
            for stage in ["metadata", "tagging"]:
                # Execute
                llm_process_articles(
                    stage=stage,
                    articles_json=str(articles_json),
                    system_prompt_path=str(system_prompt),
                    research_interests_path=str(research_interests)
                    if stage != "metadata"
                    else None,
                    model="gemini-1.5-flash",
                    allow_qc_errors=False,
                    debug=False,
                )

                # Verify stage was passed correctly
                assert mock_validate.call_args[1]["stage"] == stage

    def test_passes_response_text_to_validate(
        self, sample_articles, mock_env, tmp_path
    ):
        """Test that LLM response text is passed to validate function"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        mock_response = '{"articles": [{"title": "validated"}]}'

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses"),
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = mock_response
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify response text was passed
            assert mock_validate.call_args[1]["response_text"] == mock_response

    def test_passes_articles_to_save(self, sample_articles, mock_env, tmp_path):
        """Test that articles are passed to save function"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        with (
            patch("llm_process_articles.chat") as mock_llm,
            patch("llm_process_articles.validate_llm_response") as mock_validate,
            patch("llm_process_articles.save_validated_responses") as mock_save,
            patch("llm_process_articles.pathlib.Path.write_text"),
        ):
            mock_llm.return_value = '{"articles": []}'
            mock_validate.return_value = {}

            # Execute
            llm_process_articles(
                stage="metadata",
                articles_json=str(articles_json),
                system_prompt_path=str(system_prompt),
                research_interests_path=None,
                model="gemini-1.5-flash",
                allow_qc_errors=False,
                debug=False,
            )

            # Verify articles were passed to save
            saved_articles = mock_save.call_args[1]["articles"]
            assert len(saved_articles) == 2
            assert saved_articles[0].title == "Test Article 1"

    def test_different_models_passed_correctly(
        self, sample_articles, mock_env, tmp_path
    ):
        """Test that different model names are passed correctly"""
        # Setup
        articles_json = tmp_path / "articles.json"
        articles_json.write_text(ArticleList.dump_json(sample_articles).decode())

        system_prompt = tmp_path / "prompt.md"
        system_prompt.write_text("Test prompt")

        models = [
            "gemini-1.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
        ]

        for model in models:
            with (
                patch("llm_process_articles.chat") as mock_llm,
                patch("llm_process_articles.validate_llm_response") as mock_validate,
                patch("llm_process_articles.save_validated_responses"),
                patch("llm_process_articles.pathlib.Path.write_text"),
            ):
                mock_llm.return_value = '{"articles": []}'
                mock_validate.return_value = {}

                # Execute
                llm_process_articles(
                    stage="metadata",
                    articles_json=str(articles_json),
                    system_prompt_path=str(system_prompt),
                    research_interests_path=None,
                    model=model,
                    allow_qc_errors=False,
                    debug=False,
                )

                # Verify correct model was passed
                assert mock_llm.call_args[1]["model"] == model


class TestLLMProcessArticlesCLI:
    """Test suite for llm_process_articles CLI interface"""

    def test_cli_argument_parsing_metadata(self, tmp_path, monkeypatch):
        """Test that CLI arguments are parsed correctly for metadata command"""
        import sys
        import argparse

        # Create dummy files
        articles_json = tmp_path / "articles.json"
        articles_json.write_text("[]")
        prompt = tmp_path / "prompt.md"
        prompt.write_text("test")

        test_args = [
            "llm_process_articles.py",
            "--articles_json",
            str(articles_json),
            "metadata",
            "--system_prompt_path",
            str(prompt),
            "--model",
            "gemini-2.5-flash-lite",
            "--allow_qc_errors",
            "False",  # Note: This will be cast to bool, "False" string becomes True
        ]

        monkeypatch.setattr(sys, "argv", test_args)

        # Parse arguments using the same logic as the script
        from common.parsers import (
            add_input_articles_json_argument,
            add_debug_argument,
            add_llm_arguments,
        )

        parser = argparse.ArgumentParser()
        parser = add_input_articles_json_argument(parser)
        parser = add_debug_argument(parser)
        subparsers = parser.add_subparsers(dest="command", required=True)

        metadata_parser = subparsers.add_parser("metadata")
        metadata_parser = add_llm_arguments(
            metadata_parser, include_research_interests=False
        )

        args = parser.parse_args()

        assert args.command == "metadata"
        assert str(articles_json) in args.articles_json
        assert str(prompt) in args.system_prompt_path
        assert args.model == "gemini-2.5-flash-lite"
        # When type=bool in argparse, any non-empty string becomes True
        assert args.allow_qc_errors is True
        assert args.debug is False

    def test_cli_argument_parsing_tagging(self, tmp_path, monkeypatch):
        """Test that CLI arguments are parsed correctly for tagging command"""
        import sys
        import argparse

        # Create dummy files
        articles_json = tmp_path / "articles.json"
        articles_json.write_text("[]")
        prompt = tmp_path / "prompt.md"
        prompt.write_text("test")
        interests = tmp_path / "interests.md"
        interests.write_text("interests")

        test_args = [
            "llm_process_articles.py",
            "--articles_json",
            str(articles_json),
            "tagging",
            "--system_prompt_path",
            str(prompt),
            "--research_interests_path",
            str(interests),
            "--model",
            "gemini-1.5-flash",
            "--allow_qc_errors",
            "true",
        ]

        monkeypatch.setattr(sys, "argv", test_args)

        from common.parsers import (
            add_input_articles_json_argument,
            add_debug_argument,
            add_llm_arguments,
        )

        parser = argparse.ArgumentParser()
        parser = add_input_articles_json_argument(parser)
        parser = add_debug_argument(parser)
        subparsers = parser.add_subparsers(dest="command", required=True)

        tagging_parser = subparsers.add_parser("tagging")
        tagging_parser = add_llm_arguments(
            tagging_parser, include_research_interests=True
        )

        args = parser.parse_args()

        assert args.command == "tagging"
        assert hasattr(args, "research_interests_path")
        assert str(interests) in args.research_interests_path
        assert args.model == "gemini-1.5-flash"
        assert args.allow_qc_errors is True  # Parsed as boolean, not string

    def test_cli_debug_flag_parsing(self, tmp_path, monkeypatch):
        """Test that debug flag is parsed correctly"""
        import sys
        import argparse

        articles_json = tmp_path / "articles.json"
        articles_json.write_text("[]")
        prompt = tmp_path / "prompt.md"
        prompt.write_text("test")

        test_args = [
            "llm_process_articles.py",
            "--articles_json",
            str(articles_json),
            "--debug",
            "metadata",
            "--system_prompt_path",
            str(prompt),
            "--model",
            "gemini-2.5-flash-lite",
            "--allow_qc_errors",
            "false",
        ]

        monkeypatch.setattr(sys, "argv", test_args)

        from common.parsers import (
            add_input_articles_json_argument,
            add_debug_argument,
            add_llm_arguments,
        )

        parser = argparse.ArgumentParser()
        parser = add_input_articles_json_argument(parser)
        parser = add_debug_argument(parser)
        subparsers = parser.add_subparsers(dest="command", required=True)

        metadata_parser = subparsers.add_parser("metadata")
        metadata_parser = add_llm_arguments(
            metadata_parser, include_research_interests=False
        )

        args = parser.parse_args()

        assert args.debug is True

    def test_cli_missing_required_args(self, monkeypatch):
        """Test CLI with missing required arguments"""
        import sys
        import argparse

        test_args = ["llm_process_articles.py"]  # Missing all required arguments
        monkeypatch.setattr(sys, "argv", test_args)

        from common.parsers import add_input_articles_json_argument, add_debug_argument

        parser = argparse.ArgumentParser()
        parser = add_input_articles_json_argument(parser)
        parser = add_debug_argument(parser)
        _ = parser.add_subparsers(dest="command", required=True)

        with pytest.raises(SystemExit):
            _ = parser.parse_args()
