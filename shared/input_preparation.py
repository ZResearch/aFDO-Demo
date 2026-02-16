"""
Schema-Driven Input Preparation

Prepares inputs based on delegee's self-described schema.
NO HARDCODING!

Principle: Delegees declare requirements, LLM transforms accordingly.

Following FAIR/FDO principles for machine-actionable metadata.
"""

from typing import Dict, Any
from openai import AsyncOpenAI
import json
import logging
import os


class SchemaBasedInputPreparator:
    """
    Prepares inputs based on discovered schemas.

    Flow:
    1. Get delegee's input schema
    2. Use LLM to transform user query based on schema
    3. No hardcoded transformation rules!

    This is the key to extensibility - any agent can declare its own
    input requirements and this class will transform accordingly.
    """

    def __init__(self, has_llm: bool = True):
        self.has_llm = has_llm
        if has_llm:
            # Use Ollama LLM (configured in .env)
            api_key = os.getenv("OPENAI_API_KEY", "not-needed")
            api_base = os.getenv("OPENAI_API_BASE", "https://ollama.fit.fraunhofer.de/api")
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=api_base
            )
            self.model = os.getenv("LLM_MODEL", "mistral:7b")
        self.logger = logging.getLogger(self.__class__.__name__)

    async def prepare_input(
        self,
        user_query: str,
        input_schema: Dict[str, Any],
        operation_name: str,
        delegee_name: str
    ) -> Dict[str, Any]:
        """
        Prepare input based on delegee's schema.

        Args:
            user_query: Original user query
            input_schema: Delegee's input schema (from get_self_description)
            operation_name: Operation being called
            delegee_name: Name of delegee (for logging)

        Returns:
            Prepared parameters matching delegee's requirements
        """

        self.logger.info(f"🔧 Preparing input for {delegee_name}.{operation_name}")
        self.logger.info(f"   User query: {user_query[:100]}...")

        if not self.has_llm:
            # Fallback: basic extraction
            return self._basic_preparation(user_query, input_schema)

        # Use LLM to transform based on schema
        return await self._llm_transform_from_schema(
            user_query=user_query,
            input_schema=input_schema,
            operation_name=operation_name,
            delegee_name=delegee_name
        )

    async def _llm_transform_from_schema(
        self,
        user_query: str,
        input_schema: Dict[str, Any],
        operation_name: str,
        delegee_name: str
    ) -> Dict[str, Any]:
        """
        Use LLM to transform query based on schema.

        This is the KEY method - fully schema-driven!
        No hardcoded transformation rules.
        """

        # Extract format requirements from schema
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        # Build comprehensive prompt from schema
        prompt = self._build_transformation_prompt(
            user_query=user_query,
            properties=properties,
            required=required,
            operation_name=operation_name,
            delegee_name=delegee_name
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Low for consistent transformations
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            self.logger.info(f"   ✅ Prepared: {result}")

            return result

        except Exception as e:
            self.logger.error(f"❌ LLM transformation failed: {e}")
            return self._basic_preparation(user_query, input_schema)

    def _build_transformation_prompt(
        self,
        user_query: str,
        properties: Dict[str, Any],
        required: list,
        operation_name: str,
        delegee_name: str
    ) -> str:
        """
        Build LLM prompt from delegee's schema.

        This dynamically constructs the prompt - NO hardcoding!
        The schema tells us how to transform.
        """

        prompt = f"""Transform user query to match the required input format for {delegee_name}.

User query: {user_query}

Operation: {operation_name}

Required parameters: {required}

Input format requirements:
"""

        # Add each parameter's requirements
        for param_name, param_schema in properties.items():
            prompt += f"\n\n**Parameter: {param_name}**\n"
            prompt += f"Type: {param_schema.get('type', 'string')}\n"
            prompt += f"Description: {param_schema.get('description', 'N/A')}\n"

            # Add format requirements if present
            format_reqs = param_schema.get("format_requirements")
            if format_reqs:
                prompt += "\nFormat requirements:\n"

                # Add rules
                rules = format_reqs.get("rules", [])
                for rule in rules:
                    prompt += f"  - {rule}\n"

                # Add transformation examples
                examples = format_reqs.get("transformation_examples", [])
                if examples:
                    prompt += "\nExamples:\n"
                    for ex in examples:
                        prompt += f"  User: '{ex.get('user_query')}'\n"
                        # Handle different field names
                        correct_value = (
                            ex.get(f'correct_{param_name}') or
                            ex.get('correct_query') or
                            ex.get('correct_topic') or
                            ""
                        )
                        prompt += f"  → {param_name}: '{correct_value}'\n"
                        prompt += f"  Reasoning: {ex.get('reasoning')}\n\n"

                # Add common mistakes
                mistakes = format_reqs.get("common_mistakes", [])
                if mistakes:
                    prompt += "\nCommon mistakes to avoid:\n"
                    for mistake in mistakes:
                        prompt += f"  ❌ Wrong: '{mistake.get('wrong')}'\n"
                        prompt += f"  ✅ Correct: '{mistake.get('correct')}'\n"
                        prompt += f"  Issue: {mistake.get('issue')}\n\n"

        prompt += f"""

Your task:
1. Read the format requirements carefully
2. Transform the user query to match those requirements
3. Extract/transform each required parameter
4. Return JSON with the required parameters

Return JSON matching this structure:
{{
"""

        for param in required:
            param_type = properties.get(param, {}).get("type", "string")
            if param_type == "integer":
                prompt += f'  "{param}": 5,\n'
            elif param_type == "boolean":
                prompt += f'  "{param}": true,\n'
            else:
                prompt += f'  "{param}": "extracted_value",\n'

        prompt += "}\n"

        return prompt

    def _basic_preparation(
        self,
        user_query: str,
        input_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Basic fallback preparation (no LLM).

        Just extracts based on required parameters.
        """

        required = input_schema.get("required", [])

        result = {}
        for param in required:
            if param in ["topic", "query"]:
                # Basic extraction
                result[param] = self._basic_extract(user_query)
            elif param in ["limit", "max_results"]:
                result[param] = 5
            else:
                result[param] = user_query

        self.logger.info(f"   ⚠️ Basic preparation: {result}")

        return result

    def _basic_extract(self, query: str) -> str:
        """Basic stopword removal."""
        stopwords = ["what", "is", "who", "where", "when", "the", "a", "an", "latest", "current"]
        words = query.lower().split()
        return " ".join(w for w in words if w not in stopwords) or query
