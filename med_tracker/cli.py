"""
Conversational Interface for Medication Interaction Tracker

Main CLI application that orchestrates the complete workflow:
1. Accept natural language queries
2. Parse them using LLM
3. Query medication databases
4. Check interactions
5. Summarize results
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

from .parser import QueryParser
from .checker import InteractionChecker
from .summarizer import ResultSummarizer


class MedicationTracker:
    """Main application class for the Medication Interaction Tracker."""
    
    def __init__(self, openai_api_key: Optional[str] = None, drugbank_api_key: Optional[str] = None):
        """
        Initialize the medication tracker.
        
        Args:
            openai_api_key: Optional OpenAI API key
            drugbank_api_key: Optional DrugBank API key
        """
        self.parser = QueryParser(api_key=openai_api_key)
        self.checker = InteractionChecker(api_key=drugbank_api_key)
        self.summarizer = ResultSummarizer(api_key=openai_api_key)
    
    def process_query(self, user_query: str, use_llm_summary: bool = True) -> str:
        """
        Process a user's natural language query end-to-end.
        
        Args:
            user_query: User's question about medication interactions
            use_llm_summary: Whether to use LLM for summarization
            
        Returns:
            Human-readable response string
        """
        # Step 1: Parse the query
        print("🔍 Parsing your question...")
        parsed = self.parser.parse_query(user_query)
        
        medications = parsed.get("medications", [])
        supplements = parsed.get("supplements", [])
        foods = parsed.get("foods", [])
        
        if not medications and not supplements and not foods:
            return ("I couldn't identify any specific medications, supplements, or foods in your question. "
                   "Could you please rephrase and mention specific items you'd like to check?")
        
        print(f"📋 Found: {len(medications)} medication(s), {len(supplements)} supplement(s), {len(foods)} food(s)")
        
        # Step 2: Check for interactions
        print("🔬 Checking interaction databases...")
        interaction_data = self.checker.check_interactions(
            medications=medications,
            supplements=supplements,
            foods=foods
        )
        
        # Step 3: Summarize results
        print("📝 Generating summary...\n")
        if use_llm_summary and self.summarizer.client:
            summary = self.summarizer.summarize(interaction_data, user_query)
        else:
            summary = self.summarizer._basic_summary(interaction_data, user_query)
        
        return summary
    
    def interactive_mode(self):
        """Run the tracker in interactive conversational mode."""
        print("=" * 70)
        print("💊 Medication Interaction Tracker - Interactive Mode")
        print("=" * 70)
        print("\nAsk questions about medication, supplement, and food interactions.")
        print("Examples:")
        print("  - 'Can I take aspirin with ibuprofen?'")
        print("  - 'Is it safe to eat grapefruit while on statins?'")
        print("  - 'What supplements interact with warfarin?'")
        print("\nType 'quit' or 'exit' to end the session.\n")
        
        while True:
            try:
                user_input = input("🗣️  Your question: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thank you for using Medication Interaction Tracker!")
                    break
                
                print()  # Blank line for readability
                response = self.process_query(user_input)
                print("\n" + response)
                print("\n" + "=" * 70 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again with a different question.\n")


def main():
    """Main entry point for the CLI application."""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    drugbank_key = os.getenv("DRUGBANK_API_KEY")
    
    if not openai_key:
        print("⚠️  Warning: OPENAI_API_KEY not found in environment.")
        print("   LLM features will be limited. Set OPENAI_API_KEY for full functionality.\n")
    
    # Initialize the tracker
    tracker = MedicationTracker(
        openai_api_key=openai_key,
        drugbank_api_key=drugbank_key
    )
    
    # Check if there's a command-line argument (single query mode)
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Processing query: {query}\n")
        response = tracker.process_query(query)
        print(response)
    else:
        # Interactive mode
        tracker.interactive_mode()


if __name__ == "__main__":
    main()
