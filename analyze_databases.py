#!/usr/bin/env python3
"""
Database Analysis Script for Multi-Language Vocabulary Trainer
Analyzes existing vocabulary databases and prepares migration data
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any

def analyze_database(db_path: str, language_a: str, language_b: str) -> Dict[str, Any]:
    """Analyze a vocabulary database and return its structure and sample data"""
    
    print(f"\n🔍 Analyzing {db_path}")
    print(f"Language Pair: {language_a} → {language_b}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vocabulary'")
    schema = cursor.fetchone()[0]
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total_count = cursor.fetchone()[0]
    
    # Get sample data
    cursor.execute("SELECT * FROM vocabulary LIMIT 3")
    sample_data = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(vocabulary)")
    columns = [col[1] for col in cursor.fetchall()]
    
    conn.close()
    
    return {
        "db_path": db_path,
        "language_a": language_a,
        "language_b": language_b,
        "schema": schema,
        "total_count": total_count,
        "columns": columns,
        "sample_data": sample_data
    }

def create_migration_plan(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a migration plan based on the analyzed databases"""
    
    print("\n📋 Creating Migration Plan")
    
    migration_plan = {
        "databases": [],
        "total_vocabulary": 0,
        "language_pairs": set(),
        "recommendations": []
    }
    
    for analysis in analyses:
        db_info = {
            "source_path": analysis["db_path"],
            "language_a": analysis["language_a"],
            "language_b": analysis["language_b"],
            "total_words": analysis["total_count"],
            "columns": analysis["columns"]
        }
        
        migration_plan["databases"].append(db_info)
        migration_plan["total_vocabulary"] += analysis["total_count"]
        migration_plan["language_pairs"].add(f"{analysis['language_a']}→{analysis['language_b']}")
        
        print(f"  ✅ {analysis['language_a']} → {analysis['language_b']}: {analysis['total_count']} words")
    
    # Add recommendations
    migration_plan["recommendations"] = [
        "Create Supabase tables with language_a_word, language_b_translation structure",
        "Map existing columns to new schema",
        "Create deck metadata for each language pair",
        "Set up proper language codes for pronunciation",
        "Consider difficulty levels based on word frequency"
    ]
    
    return migration_plan

def main():
    """Main analysis function"""
    
    print("🌐 Multi-Language Vocabulary Database Analysis")
    print("=" * 50)
    
    # Define databases to analyze
    databases = [
        {
            "path": "/Users/ding/Desktop/Coding/Chinese App/vocab database/financial_vocab_batch_1.db",
            "language_a": "Chinese",
            "language_b": "French"
        },
        {
            "path": "/Users/ding/Desktop/Coding/Vocabulary Learning App/vocab bank/french_vocab_batch_4.db",
            "language_a": "French",
            "language_b": "English"
        }
    ]
    
    # Analyze each database
    analyses = []
    for db_info in databases:
        try:
            analysis = analyze_database(db_info["path"], db_info["language_a"], db_info["language_b"])
            analyses.append(analysis)
        except Exception as e:
            print(f"❌ Error analyzing {db_info['path']}: {e}")
    
    # Create migration plan
    migration_plan = create_migration_plan(analyses)
    
    # Print detailed analysis
    print("\n📊 Detailed Analysis")
    print("=" * 30)
    
    for analysis in analyses:
        print(f"\n🗂️ {analysis['language_a']} → {analysis['language_b']}")
        print(f"   Database: {Path(analysis['db_path']).name}")
        print(f"   Total Words: {analysis['total_count']}")
        print(f"   Columns: {', '.join(analysis['columns'])}")
        
        print("\n   Sample Data:")
        for i, row in enumerate(analysis['sample_data'], 1):
            print(f"   {i}. ID: {row[0]}, Word: {row[2][:30]}..., Translation: {row[3][:30]}...")
    
    # Save migration plan
    with open("migration_plan.json", "w", encoding="utf-8") as f:
        json.dump(migration_plan, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Migration plan saved to migration_plan.json")
    print(f"\n📈 Summary:")
    print(f"   Total Databases: {len(analyses)}")
    print(f"   Total Vocabulary: {migration_plan['total_vocabulary']}")
    print(f"   Language Pairs: {', '.join(migration_plan['language_pairs'])}")
    
    print(f"\n🎯 Next Steps:")
    for i, rec in enumerate(migration_plan["recommendations"], 1):
        print(f"   {i}. {rec}")

if __name__ == "__main__":
    main()
