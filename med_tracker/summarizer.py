"""
Result Summarizer

Uses LLM to summarize interaction data in plain language while avoiding medical advice.
"""

import os
import json
from typing import Dict, Optional
from openai import OpenAI


class ResultSummarizer:
    """Summarizes medication interaction results in natural language."""
    
    DISCLAIMER = "\n\n⚠️  IMPORTANT: This information is for educational purposes only and is not medical advice. Always consult your healthcare provider before starting, stopping, or changing any medications or supplements."
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the summarizer.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def summarize(self, interaction_data: Dict, original_query: str = "") -> str:
        """
        Generate a plain-language summary of interaction findings.
        
        Args:
            interaction_data: Structured interaction data from InteractionChecker
            original_query: The user's original question
            
        Returns:
            Human-readable summary string
        """
        if not self.client:
            return self._basic_summary(interaction_data, original_query)
        
        # Prepare data for LLM
        data_summary = self._prepare_data_for_llm(interaction_data)
        
        system_prompt = """You are a medication information assistant. Your role is to explain drug interactions in clear, understandable language.

IMPORTANT RULES:
1. DO NOT provide medical advice or recommendations
2. DO NOT tell users what they should or shouldn't do
3. DO use educational language like "research shows", "studies indicate"
4. DO present facts about known interactions
5. DO remind users to consult healthcare providers
6. Keep responses concise and organized
7. Use a concerned but neutral tone"""
        
        user_prompt = f"""The user asked: "{original_query}"

Here is the interaction data found:

{data_summary}

Please provide a clear, factual summary of these findings. Focus on what the data shows, not on what the user should do. End with a reminder to consult a healthcare provider."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            summary = response.choices[0].message.content
            return summary + self.DISCLAIMER
            
        except Exception as e:
            print(f"Error generating summary with LLM: {e}")
            return self._basic_summary(interaction_data, original_query)
    
    def _prepare_data_for_llm(self, data: Dict) -> str:
        """
        Convert interaction data into a readable format for the LLM.
        
        Args:
            data: Interaction data dictionary
            
        Returns:
            Formatted string
        """
        sections = []
        
        # Summary statistics
        summary = data.get("summary", {})
        sections.append(f"Total interactions found: {summary.get('total_interactions', 0)}")
        sections.append(f"- High severity: {summary.get('high_severity_count', 0)}")
        sections.append(f"- Moderate severity: {summary.get('moderate_severity_count', 0)}")
        sections.append(f"- Low severity: {summary.get('low_severity_count', 0)}")
        sections.append("")
        
        # Drug-drug interactions
        drug_interactions = data.get("drug_drug_interactions", [])
        if drug_interactions:
            sections.append("DRUG-DRUG INTERACTIONS:")
            for interaction in drug_interactions[:5]:  # Limit to top 5
                sections.append(f"- {interaction.get('drug1')} + {interaction.get('drug2')}")
                sections.append(f"  Severity: {interaction.get('severity')}")
                sections.append(f"  Details: {interaction.get('description', 'N/A')}")
            sections.append("")
        
        # Drug-food interactions
        food_interactions = data.get("drug_food_interactions", [])
        if food_interactions:
            sections.append("DRUG-FOOD INTERACTIONS:")
            for interaction in food_interactions:
                sections.append(f"- {interaction.get('medication')} + {interaction.get('food')}")
                sections.append(f"  Severity: {interaction.get('severity')}")
                sections.append(f"  Details: {interaction.get('interaction')}")
                sections.append(f"  Recommendation: {interaction.get('recommendation')}")
            sections.append("")
        
        # Drug-supplement interactions
        supp_interactions = data.get("drug_supplement_interactions", [])
        if supp_interactions:
            sections.append("DRUG-SUPPLEMENT INTERACTIONS:")
            for interaction in supp_interactions:
                sections.append(f"- {interaction.get('medication')} + {interaction.get('supplement')}")
                sections.append(f"  Severity: {interaction.get('severity')}")
                sections.append(f"  Details: {interaction.get('interaction')}")
                sections.append(f"  Recommendation: {interaction.get('recommendation')}")
            sections.append("")
        
        return "\n".join(sections)
    
    def _basic_summary(self, interaction_data: Dict, original_query: str = "") -> str:
        """
        Generate a basic summary without LLM (fallback).
        
        Args:
            interaction_data: Structured interaction data
            original_query: User's question
            
        Returns:
            Basic formatted summary
        """
        lines = []
        
        if original_query:
            lines.append(f"Query: {original_query}\n")
        
        summary = interaction_data.get("summary", {})
        total = summary.get("total_interactions", 0)
        
        lines.append(f"🔍 Interaction Analysis Results")
        lines.append(f"=" * 50)
        lines.append(f"\nTotal interactions found: {total}\n")
        
        if total == 0:
            lines.append("✅ No known interactions found in our database.")
            lines.append("\nNote: This doesn't guarantee safety. New interactions may exist.")
        else:
            # Show severity breakdown
            high = summary.get("high_severity_count", 0)
            moderate = summary.get("moderate_severity_count", 0)
            low = summary.get("low_severity_count", 0)
            
            if high > 0:
                lines.append(f"⚠️  HIGH SEVERITY: {high}")
            if moderate > 0:
                lines.append(f"⚡ MODERATE SEVERITY: {moderate}")
            if low > 0:
                lines.append(f"ℹ️  LOW SEVERITY: {low}")
            
            # Drug-drug interactions
            drug_interactions = interaction_data.get("drug_drug_interactions", [])
            if drug_interactions:
                lines.append(f"\n📊 Drug-Drug Interactions ({len(drug_interactions)}):")
                for i, interaction in enumerate(drug_interactions[:5], 1):
                    lines.append(f"\n{i}. {interaction.get('drug1')} ↔ {interaction.get('drug2')}")
                    lines.append(f"   Severity: {interaction.get('severity')}")
                    desc = interaction.get('description', 'No details available')
                    lines.append(f"   {desc[:100]}...")
            
            # Drug-food interactions
            food_interactions = interaction_data.get("drug_food_interactions", [])
            if food_interactions:
                lines.append(f"\n🍽️  Drug-Food Interactions ({len(food_interactions)}):")
                for i, interaction in enumerate(food_interactions, 1):
                    lines.append(f"\n{i}. {interaction.get('medication')} + {interaction.get('food')}")
                    lines.append(f"   Severity: {interaction.get('severity')}")
                    lines.append(f"   {interaction.get('interaction')}")
                    lines.append(f"   Recommendation: {interaction.get('recommendation')}")
            
            # Drug-supplement interactions
            supp_interactions = interaction_data.get("drug_supplement_interactions", [])
            if supp_interactions:
                lines.append(f"\n💊 Drug-Supplement Interactions ({len(supp_interactions)}):")
                for i, interaction in enumerate(supp_interactions, 1):
                    lines.append(f"\n{i}. {interaction.get('medication')} + {interaction.get('supplement')}")
                    lines.append(f"   Severity: {interaction.get('severity')}")
                    lines.append(f"   {interaction.get('interaction')}")
                    lines.append(f"   Recommendation: {interaction.get('recommendation')}")
        
        result = "\n".join(lines)
        return result + self.DISCLAIMER
