#!/usr/bin/env python
"""Tests for common/llm.py"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.llm import llm_query
from common.models import Article


class TestLlmQuery:
    """Test suite for llm_query function"""

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing"""
        from datetime import date

        return [
            Article(
                title="Test Article 1",
                url="https://example.com/article1",
                journal_name="Test Journal",
                date=date(2024, 1, 1),
                access_date=date(2024, 1, 15),
                raw_contents="Content 1",
            ),
            Article(
                title="Test Article 2",
                url="https://example.com/article2",
                journal_name="Test Journal",
                date=date(2024, 1, 2),
                access_date=date(2024, 1, 15),
                raw_contents="Content 2",
            ),
        ]

    @pytest.fixture
    def mock_system_prompt(self, tmp_path):
        """Create a mock system prompt file without examples"""
        prompt_file = tmp_path / "prompt.md"
        prompt_content = """System prompt for testing

# Examples

```json
[
  {
    "query": [{"url": "https://example.com", "title": "Test Article"}],
    "response": [{"doi": "10.1234/test", "decision": true}]
  }
]
```"""
        prompt_file.write_text(prompt_content)
        return str(prompt_file)

    @pytest.fixture
    def mock_system_prompt_no_examples(self, tmp_path):
        """Create a mock system prompt file without examples section"""
        prompt_file = tmp_path / "prompt_no_examples.md"
        prompt_file.write_text("System prompt for testing")
        return str(prompt_file)

    @pytest.fixture
    def mock_research_interests(self, tmp_path):
        """Create a mock research interests file"""
        interests_file = tmp_path / "interests.md"
        interests_file.write_text("AI and machine learning")
        return str(interests_file)

    def test_llm_query_raises_error_without_api_key(
        self, sample_articles, mock_system_prompt
    ):
        """Test that llm_query raises ValueError when API key is missing"""
        with pytest.raises(
            ValueError, match="GOOGLE_API_KEY environment variable not found"
        ):
            llm_query(
                articles=sample_articles,
                system_prompt_path=mock_system_prompt,
                model="gemini-1.5-flash",
                api_key="",
                research_interests_path=None,
                tools=[],
            )

    def test_llm_query_raises_error_with_none_api_key(
        self, sample_articles, mock_system_prompt
    ):
        """Test that llm_query raises ValueError when API key is None"""
        with pytest.raises(
            ValueError, match="GOOGLE_API_KEY environment variable not found"
        ):
            llm_query(
                articles=sample_articles,
                system_prompt_path=mock_system_prompt,
                model="gemini-1.5-flash",
                api_key=None,
                research_interests_path=None,
                tools=[],
            )

    @patch("common.llm.genai.Client")
    def test_llm_query_basic_success(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test successful basic LLM query without research interests"""
        # Setup mock client and response
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = '{"articles": []}'
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        result = llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify
        assert result == '{"articles": []}'
        mock_client_class.assert_called_once_with(
            api_key="test-api-key"  # noqa: S106  # pragma: allowlist secret
        )
        mock_client.models.generate_content.assert_called_once()

        # Check that the call included the correct model
        call_kwargs = mock_client.models.generate_content.call_args[1]
        assert call_kwargs["model"] == "gemini-1.5-flash"

    @patch("common.llm.genai.Client")
    def test_llm_query_with_research_interests(
        self,
        mock_client_class,
        sample_articles,
        mock_system_prompt,
        mock_research_interests,
    ):
        """Test LLM query with research interests file"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = '{"articles": []}'
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        result = llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-2.5-flash-lite",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=mock_research_interests,
            tools=[],
        )

        # Verify
        assert result == '{"articles": []}'
        mock_client.models.generate_content.assert_called_once()

    @patch("common.llm.genai.Client")
    def test_llm_query_with_tools(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test LLM query with tools"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "LLM response with tool usage"
        mock_client.models.generate_content.return_value = mock_response

        # Create mock tools
        def mock_tool_1():
            pass

        def mock_tool_2():
            pass

        tools = [mock_tool_1, mock_tool_2]

        # Execute
        result = llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=tools,
        )

        # Verify
        assert result == "LLM response with tool usage"

        # Check that tools were passed in the config
        call_kwargs = mock_client.models.generate_content.call_args[1]
        assert call_kwargs["config"].tools == tools

    @patch("common.llm.genai.Client")
    def test_llm_query_different_models(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test LLM query with different model names"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        models = ["gemini-1.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]

        for model in models:
            # Execute
            llm_query(
                articles=sample_articles,
                system_prompt_path=mock_system_prompt,
                model=model,
                api_key="test-api-key",  # pragma: allowlist secret
                research_interests_path=None,
                tools=[],
            )

            # Verify correct model was used
            call_kwargs = mock_client.models.generate_content.call_args[1]
            assert call_kwargs["model"] == model

    @patch("common.llm.genai.Client")
    def test_llm_query_strips_response_text(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test that LLM response text is stripped of whitespace"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "  \n  Response with whitespace  \n  "
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        result = llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify whitespace was stripped
        assert result == "Response with whitespace"

    @patch("common.llm.genai.Client")
    def test_llm_query_builds_correct_context(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test that the context is built correctly for the LLM"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify context structure
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]

        # Should have 3 parts: user prompt, model acknowledgment, user articles
        assert len(contents) == 3
        assert contents[0].role == "user"
        assert contents[1].role == "model"
        assert contents[2].role == "user"

    @patch("common.llm.genai.Client")
    def test_llm_query_thinking_config_disabled(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test that thinking is disabled in the config"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify thinking is disabled
        call_kwargs = mock_client.models.generate_content.call_args[1]
        assert call_kwargs["config"].thinking_config.include_thoughts is False

    @patch("common.llm.genai.Client")
    def test_llm_query_with_empty_articles_list(
        self, mock_client_class, mock_system_prompt
    ):
        """Test LLM query with empty articles list"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = '{"articles": []}'
        mock_client.models.generate_content.return_value = mock_response

        # Execute with empty list
        result = llm_query(
            articles=[],
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify it completes successfully
        assert result == '{"articles": []}'
        mock_client.models.generate_content.assert_called_once()

    @patch("common.llm.genai.Client")
    def test_llm_query_reads_system_prompt_file(
        self, mock_client_class, sample_articles, tmp_path
    ):
        """Test that system prompt is correctly read from file"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Create prompt file with specific content
        prompt_file = tmp_path / "custom_prompt.md"
        custom_prompt = """Custom system instruction for testing

# Examples

```json
[
  {
    "query": [{"url": "https://example.com"}],
    "response": [{"doi": "10.1234/test"}]
  }
]
```"""
        prompt_file.write_text(custom_prompt)

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=str(prompt_file),
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify system prompt was included in context
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]
        assert "Custom system instruction for testing" in contents[0].parts[0].text

    @patch("common.llm.genai.Client")
    def test_llm_query_formats_research_interests_into_prompt(
        self, mock_client_class, sample_articles, tmp_path
    ):
        """Test that research interests are formatted into system prompt"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Create prompt with placeholder
        prompt_file = tmp_path / "prompt.md"
        prompt_content = """Research interests: {research_interests}

# Examples

```json
[
  {
    "query": [{"url": "https://example.com"}],
    "response": [{"doi": "10.1234/test"}]
  }
]
```"""
        prompt_file.write_text(prompt_content)

        # Create research interests file
        interests_file = tmp_path / "interests.md"
        interests_file.write_text("AI and machine learning")

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=str(prompt_file),
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=str(interests_file),
            tools=[],
        )

        # Verify research interests were inserted
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]
        assert "AI and machine learning" in contents[0].parts[0].text

    @patch("common.llm.genai.Client")
    def test_llm_query_includes_articles_in_prompt(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test that articles are included in the user prompt"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify articles are in the prompt
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]
        articles_prompt = contents[2].parts[0].text

        assert "Here are the articles:" in articles_prompt
        assert "Test Article 1" in articles_prompt
        assert "Test Article 2" in articles_prompt

    @patch("common.llm.genai.Client")
    def test_llm_query_with_whitespace_in_prompt_file(
        self, mock_client_class, sample_articles, tmp_path
    ):
        """Test that whitespace is stripped from prompt file"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Create prompt file with whitespace
        prompt_file = tmp_path / "prompt.md"
        prompt_content = """
  System prompt

# Examples

```json
[
  {
    "query": [{"url": "https://example.com"}],
    "response": [{"doi": "10.1234/test"}]
  }
]
```
"""
        prompt_file.write_text(prompt_content)

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=str(prompt_file),
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify prompt is processed correctly despite whitespace
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]
        # Should still contain the system prompt part (before examples)
        assert "System prompt" in contents[0].parts[0].text

    @patch("common.llm.genai.Client")
    def test_llm_query_with_whitespace_in_research_interests(
        self, mock_client_class, sample_articles, tmp_path
    ):
        """Test that whitespace is stripped from research interests file"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Create files
        prompt_file = tmp_path / "prompt.md"
        prompt_content = """Interests: {research_interests}

# Examples

```json
[
  {
    "query": [{"url": "https://example.com"}],
    "response": [{"doi": "10.1234/test"}]
  }
]
```"""
        prompt_file.write_text(prompt_content)

        interests_file = tmp_path / "interests.md"
        interests_file.write_text("  \n  AI research  \n  ")

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=str(prompt_file),
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=str(interests_file),
            tools=[],
        )

        # Verify whitespace was stripped
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]
        assert "AI research" in contents[0].parts[0].text
        assert "  \n  " not in contents[0].parts[0].text

    @patch("common.llm.genai.Client")
    def test_llm_query_model_acknowledgment_contains_examples(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test that the model acknowledgment message contains example responses"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify model acknowledgment contains example responses
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]
        acknowledgment = contents[1].parts[0].text

        # Should contain the example response from the mock prompt
        assert "10.1234/test" in acknowledgment
        assert "decision" in acknowledgment

    @patch("common.llm.genai.Client")
    def test_llm_query_system_prompt_contains_example_queries(
        self, mock_client_class, sample_articles, mock_system_prompt
    ):
        """Test that the system prompt contains example queries"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=mock_system_prompt,
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify system prompt contains example queries
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]
        system_instruction = contents[0].parts[0].text

        # Should contain "Example of a user query:" and the query from mock prompt
        assert "Example of a user query:" in system_instruction
        assert "https://example.com" in system_instruction

    @patch("common.llm.genai.Client")
    def test_llm_query_parses_examples_correctly(
        self, mock_client_class, sample_articles, tmp_path
    ):
        """Test that examples are parsed correctly from the prompt file"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Create prompt with multiple examples
        prompt_file = tmp_path / "prompt_multi_example.md"
        prompt_content = """System prompt for testing

# Examples

```json
[
  {
    "query": [{"url": "https://example1.com", "title": "Article 1"}],
    "response": [{"doi": "10.1234/ex1", "decision": true}]
  },
  {
    "query": [{"url": "https://example2.com", "title": "Article 2"}],
    "response": [{"doi": "10.1234/ex2", "decision": false, "reasoning": "Not relevant"}]
  }
]
```"""
        prompt_file.write_text(prompt_content)

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=str(prompt_file),
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify both examples are included
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]

        # Check system instruction has both query examples
        system_instruction = contents[0].parts[0].text
        assert "https://example1.com" in system_instruction
        assert "https://example2.com" in system_instruction

        # Check model response has both response examples
        model_response = contents[1].parts[0].text
        assert "10.1234/ex1" in model_response
        assert "10.1234/ex2" in model_response
        assert "Not relevant" in model_response

    @patch("common.llm.genai.Client")
    def test_llm_query_handles_complex_example_structure(
        self, mock_client_class, sample_articles, tmp_path
    ):
        """Test handling of complex example structures with multiple queries/responses per example"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Create prompt with complex examples
        prompt_file = tmp_path / "prompt_complex.md"
        prompt_content = """System prompt for testing

# Examples

```json
[
  {
    "query": [
      {"url": "https://example1.com", "title": "Article 1"},
      {"url": "https://example2.com", "title": "Article 2"}
    ],
    "response": [
      {"doi": "10.1234/ex1", "decision": true},
      {"doi": "10.1234/ex2", "decision": false}
    ]
  }
]
```"""
        prompt_file.write_text(prompt_content)

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=str(prompt_file),
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=None,
            tools=[],
        )

        # Verify complex structure is preserved
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]

        system_instruction = contents[0].parts[0].text
        assert "Article 1" in system_instruction
        assert "Article 2" in system_instruction

        model_response = contents[1].parts[0].text
        assert "10.1234/ex1" in model_response
        assert "10.1234/ex2" in model_response

    def test_llm_query_raises_error_on_malformed_examples(
        self, sample_articles, tmp_path
    ):
        """Test that malformed examples in prompt file raise appropriate errors"""
        # Create prompt with invalid JSON in examples section
        prompt_file = tmp_path / "prompt_invalid.md"
        prompt_content = """System prompt for testing

# Examples

```json
[
  {
    "query": [{"url": "https://example.com"}]
    # Missing comma and response field - invalid JSON
  }
]
```"""
        prompt_file.write_text(prompt_content)

        # Execute and expect JSON decode error
        with pytest.raises(Exception):  # Could be JSONDecodeError or similar
            llm_query(
                articles=sample_articles,
                system_prompt_path=str(prompt_file),
                model="gemini-1.5-flash",
                api_key="test-api-key",  # pragma: allowlist secret
                research_interests_path=None,
                tools=[],
            )

    def test_llm_query_raises_error_on_missing_examples_section(
        self, sample_articles, mock_system_prompt_no_examples
    ):
        """Test that prompt without Examples section raises an error"""
        # Execute and expect ValueError due to split failing
        with pytest.raises(ValueError):
            llm_query(
                articles=sample_articles,
                system_prompt_path=mock_system_prompt_no_examples,
                model="gemini-1.5-flash",
                api_key="test-api-key",  # pragma: allowlist secret
                research_interests_path=None,
                tools=[],
            )

    @patch("common.llm.genai.Client")
    def test_llm_query_examples_with_research_interests_placeholder(
        self, mock_client_class, sample_articles, tmp_path
    ):
        """Test that examples are parsed correctly when prompt has research interests placeholder"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        # Create prompt with research interests placeholder
        prompt_file = tmp_path / "prompt_with_placeholder.md"
        prompt_content = """System prompt with research interests: {research_interests}

# Examples

```json
[
  {
    "query": [{"url": "https://example.com", "title": "Test"}],
    "response": [{"doi": "10.1234/test", "decision": true}]
  }
]
```"""
        prompt_file.write_text(prompt_content)

        # Create research interests file
        interests_file = tmp_path / "interests.md"
        interests_file.write_text("AI and ML")

        # Execute
        llm_query(
            articles=sample_articles,
            system_prompt_path=str(prompt_file),
            model="gemini-1.5-flash",
            api_key="test-api-key",  # pragma: allowlist secret
            research_interests_path=str(interests_file),
            tools=[],
        )

        # Verify both research interests insertion and examples parsing work
        call_kwargs = mock_client.models.generate_content.call_args[1]
        contents = call_kwargs["contents"]

        system_instruction = contents[0].parts[0].text
        assert "AI and ML" in system_instruction  # Research interests inserted
        assert "Example of a user query:" in system_instruction  # Examples parsed
        assert "https://example.com" in system_instruction  # Query example present
