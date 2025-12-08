"""
DrugBank SQLite Database Manager

Creates and manages a SQLite database from DrugBank data for efficient
querying of drug interactions, food interactions, and drug properties.
"""

import sqlite3
from typing import List, Dict, Optional
from pathlib import Path
import sys
from .drugbank_loader import DrugBankLoader


class DrugBankDatabase:
    """Manages DrugBank data in SQLite database."""
    
    def __init__(self, db_file_path: str, xml_file_path: str = None):
        """
        Initialize database manager.
        
        Args:
            db_file_path: Path to SQLite database file
            xml_file_path: Path to DrugBank XML file (for initialization)
        """
        self.db_file_path = Path(db_file_path)
        self.xml_file_path = xml_file_path
        self.conn = None
    
    def initialize(self) -> bool:
        """
        Initialize database from XML file.
        Creates tables and loads data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load from XML
            if not self.xml_file_path:
                print("[ERROR] XML file path not provided", file=sys.stderr)
                return False
            
            print(f"[INFO] Initializing DrugBank database from XML", file=sys.stderr)
            loader = DrugBankLoader(self.xml_file_path)
            
            if not loader.load():
                return False
            
            # Create database and tables
            self._create_tables()
            
            # Load data from loader
            self._load_drugs(loader)
            
            print("[INFO] DrugBank database initialization complete", file=sys.stderr)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {str(e)}", file=sys.stderr)
            return False
    
    def connect(self) -> bool:
        """
        Connect to existing database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.db_file_path.exists():
                print(f"[WARNING] Database file not found: {self.db_file_path}", file=sys.stderr)
                return False
            
            self.conn = sqlite3.connect(str(self.db_file_path))
            self.conn.row_factory = sqlite3.Row
            print(f"[INFO] Connected to DrugBank database", file=sys.stderr)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to connect to database: {str(e)}", file=sys.stderr)
            return False
    
    def _create_tables(self):
        """Create database schema."""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_file_path))
            self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Drugs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drugs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                indication TEXT,
                mechanism_of_action TEXT,
                toxicity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Drug interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drug_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT NOT NULL,
                interacting_drug_id TEXT NOT NULL,
                interacting_drug_name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_drug_interactions_drug_id 
            ON drug_interactions(drug_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_drugs_name 
            ON drugs(name COLLATE NOCASE)
        """)
        
        # Food interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (drug_id) REFERENCES drugs(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_food_interactions_drug_id 
            ON food_interactions(drug_id)
        """)
        
        self.conn.commit()
        print("[INFO] Database tables created", file=sys.stderr)
    
    def _load_drugs(self, loader: DrugBankLoader):
        """
        Load drug data from loader into database.
        
        Args:
            loader: DrugBankLoader instance with loaded data
        """
        cursor = self.conn.cursor()
        
        drugs = loader.get_all_drugs()
        print(f"[INFO] Loading {len(drugs)} drugs into database...", file=sys.stderr)
        
        for i, drug in enumerate(drugs):
            try:
                # Insert drug
                cursor.execute("""
                    INSERT OR REPLACE INTO drugs 
                    (id, name, description, indication, mechanism_of_action, toxicity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    drug["primary_id"],
                    drug.get("name", ""),
                    drug.get("description", ""),
                    drug.get("indication", ""),
                    drug.get("mechanism_of_action", ""),
                    drug.get("toxicity", ""),
                ))
                
                # Insert drug interactions
                for interaction in drug.get("drug_interactions", []):
                    cursor.execute("""
                        INSERT INTO drug_interactions 
                        (drug_id, interacting_drug_id, interacting_drug_name, description)
                        VALUES (?, ?, ?, ?)
                    """, (
                        drug["primary_id"],
                        interaction.get("drugbank_id", ""),
                        interaction.get("name", ""),
                        interaction.get("description", ""),
                    ))
                
                # Insert food interactions
                for food_interaction in drug.get("food_interactions", []):
                    cursor.execute("""
                        INSERT INTO food_interactions (drug_id, description)
                        VALUES (?, ?)
                    """, (drug["primary_id"], food_interaction))
                
                if (i + 1) % 5000 == 0:
                    self.conn.commit()
                    print(f"[INFO] Loaded {i + 1} drugs ({int((i+1)/len(drugs)*100)}%)...", file=sys.stderr)
                    
            except Exception as e:
                print(f"[WARNING] Failed to load drug {drug.get('primary_id')}: {str(e)}", 
                      file=sys.stderr)
        
        self.conn.commit()
        print(f"[INFO] All drugs loaded into database", file=sys.stderr)
    
    def get_drug_by_id(self, drug_id: str) -> Optional[Dict]:
        """
        Get drug by DrugBank ID.
        
        Args:
            drug_id: DrugBank ID
            
        Returns:
            Drug data dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM drugs WHERE id = ?", (drug_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_drug_by_name(self, drug_name: str) -> Optional[Dict]:
        """
        Get drug by name (exact match, case-insensitive).
        
        Args:
            drug_name: Drug name
            
        Returns:
            Drug data dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM drugs WHERE LOWER(name) = LOWER(?)", (drug_name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def search_drugs(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search drugs by name (partial match).
        
        Args:
            search_term: Partial drug name
            limit: Maximum number of results
            
        Returns:
            List of matching drug dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM drugs WHERE LOWER(name) LIKE LOWER(?) LIMIT ?",
            (f"%{search_term}%", limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_drug_by_name_fuzzy(self, drug_name: str) -> Optional[Dict]:
        """
        Get drug by name with fuzzy matching fallback.
        First tries exact match, then tries smart partial match if no exact match found.
        Prefers matches where the search term is a complete word in the drug name.
        
        Args:
            drug_name: Drug name to search for
            
        Returns:
            Drug data dictionary or None
        """
        # Try exact match first
        drug = self.get_drug_by_name(drug_name)
        if drug:
            return drug
        
        # Try partial match, but prioritize matches where search term is a word boundary
        cursor = self.conn.cursor()
        
        # First try: search term at start of name (e.g., "aspirin" matches "Aspirin..." but not "Nitroaspirin")
        cursor.execute(
            "SELECT * FROM drugs WHERE LOWER(name) LIKE LOWER(?) LIMIT 1",
            (f"{drug_name}%",)
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        
        # Second try: search term after space (word boundary)
        cursor.execute(
            "SELECT * FROM drugs WHERE LOWER(name) LIKE LOWER(?) LIMIT 1",
            (f"% {drug_name}%",)
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        
        # Third try: generic/chemical name lookups (aspirin -> acetylsalicylic, ibuprofen -> isobutylphenyl)
        common_synonyms = {
            "aspirin": "acetylsalicylic",
            "ibuprofen": "isobutylphenylpropionic",
            "tylenol": "acetaminophen",
            "paracetamol": "acetaminophen",
        }
        
        if drug_name.lower() in common_synonyms:
            synonym = common_synonyms[drug_name.lower()]
            cursor.execute(
                "SELECT * FROM drugs WHERE LOWER(name) LIKE LOWER(?) LIMIT 1",
                (f"{synonym}%",)
            )
            result = cursor.fetchone()
            if result:
                return dict(result)
        
        # Finally: last resort - any partial match
        cursor.execute(
            "SELECT * FROM drugs WHERE LOWER(name) LIKE LOWER(?) LIMIT 1",
            (f"%{drug_name}%",)
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        
        return None
    
    def get_drug_interactions(self, drug_id: str) -> List[Dict]:
        """
        Get all drug-drug interactions for a drug.
        
        Args:
            drug_id: DrugBank ID of drug
            
        Returns:
            List of interaction dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM drug_interactions 
            WHERE drug_id = ?
            ORDER BY interacting_drug_name
        """, (drug_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_drug_interactions_by_name(self, drug_name: str) -> List[Dict]:
        """
        Get all drug-drug interactions for a drug by name.
        
        Args:
            drug_name: Drug name
            
        Returns:
            List of interaction dictionaries
        """
        drug = self.get_drug_by_name(drug_name)
        if not drug:
            return []
        return self.get_drug_interactions(drug["id"])
    
    def get_food_interactions(self, drug_id: str) -> List[str]:
        """
        Get all food interactions for a drug.
        
        Args:
            drug_id: DrugBank ID of drug
            
        Returns:
            List of food interaction descriptions
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT description FROM food_interactions 
            WHERE drug_id = ?
            ORDER BY id
        """, (drug_id,))
        return [row["description"] for row in cursor.fetchall()]
    
    def get_food_interactions_by_name(self, drug_name: str) -> List[str]:
        """
        Get all food interactions for a drug by name.
        
        Args:
            drug_name: Drug name
            
        Returns:
            List of food interaction descriptions
        """
        drug = self.get_drug_by_name(drug_name)
        if not drug:
            return []
        return self.get_food_interactions(drug["id"])
    
    def get_interaction_matrix(self, drug_ids: List[str]) -> List[Dict]:
        """
        Get all interactions between multiple drugs.
        
        Args:
            drug_ids: List of DrugBank IDs
            
        Returns:
            List of interaction dictionaries between any pair
        """
        cursor = self.conn.cursor()
        
        interactions = []
        for i, drug_id in enumerate(drug_ids):
            for other_id in drug_ids[i+1:]:
                # Check if drug_id has interaction with other_id
                cursor.execute("""
                    SELECT * FROM drug_interactions 
                    WHERE drug_id = ? AND interacting_drug_id = ?
                """, (drug_id, other_id))
                
                result = cursor.fetchone()
                if result:
                    interactions.append(dict(result))
                else:
                    # Check reverse direction
                    cursor.execute("""
                        SELECT * FROM drug_interactions 
                        WHERE drug_id = ? AND interacting_drug_id = ?
                    """, (other_id, drug_id))
                    result = cursor.fetchone()
                    if result:
                        interactions.append(dict(result))
        
        return interactions
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
