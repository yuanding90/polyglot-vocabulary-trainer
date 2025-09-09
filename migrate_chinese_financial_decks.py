#!/usr/bin/env python3
"""
Chinese Financial Vocabulary Migration Script
Migrates 5 merged Chinese financial vocabulary databases to Supabase
Converts traditional Chinese to simplified Chinese
"""

import sqlite3
import json
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from typing import List, Dict, Any
import re

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Chinese vocabulary database path
CHINESE_VOCAB_PATH = "/Users/ding/Desktop/Coding/Chinese App/vocab database"

# Traditional to Simplified Chinese mapping (common financial terms)
TRADITIONAL_TO_SIMPLIFIED = {
    '帳單': '账单',
    '帳戶': '账户',
    '帳目': '账目',
    '帳務': '账务',
    '帳款': '账款',
    '帳面': '账面',
    '帳冊': '账册',
    '帳簿': '账簿',
    '帳號': '账号',
    '銀行': '银行',
    '貸款': '贷款',
    '還款': '还款',
    '付款': '付款',
    '收款': '收款',
    '轉帳': '转账',
    '匯款': '汇款',
    '匯率': '汇率',
    '匯兌': '汇兑',
    '匯票': '汇票',
    '保險': '保险',
    '保單': '保单',
    '保費': '保费',
    '理賠': '理赔',
    '投資': '投资',
    '股票': '股票',
    '債券': '债券',
    '基金': '基金',
    '期貨': '期货',
    '期權': '期权',
    '證券': '证券',
    '交易': '交易',
    '市場': '市场',
    '價格': '价格',
    '價值': '价值',
    '收益': '收益',
    '利潤': '利润',
    '虧損': '亏损',
    '風險': '风险',
    '管理': '管理',
    '服務': '服务',
    '業務': '业务',
    '公司': '公司',
    '企業': '企业',
    '機構': '机构',
    '部門': '部门',
    '職員': '职员',
    '客戶': '客户',
    '合同': '合同',
    '協議': '协议',
    '條款': '条款',
    '條件': '条件',
    '規定': '规定',
    '規則': '规则',
    '政策': '政策',
    '制度': '制度',
    '系統': '系统',
    '程序': '程序',
    '流程': '流程',
    '標準': '标准',
    '要求': '要求',
    '審核': '审核',
    '批准': '批准',
    '授權': '授权',
    '確認': '确认',
    '驗證': '验证',
    '檢查': '检查',
    '監督': '监督',
    '控制': '控制',
    '監管': '监管',
    '報告': '报告',
    '記錄': '记录',
    '檔案': '档案',
    '資料': '资料',
    '信息': '信息',
    '數據': '数据',
    '統計': '统计',
    '分析': '分析',
    '研究': '研究',
    '調查': '调查',
    '評估': '评估',
    '計算': '计算',
    '預算': '预算',
    '計劃': '计划',
    '策略': '策略',
    '目標': '目标',
    '結果': '结果',
    '效果': '效果',
    '影響': '影响',
    '關係': '关系',
    '聯繫': '联系',
    '溝通': '沟通',
    '協調': '协调',
    '合作': '合作',
    '支持': '支持',
    '幫助': '帮助',
    '建議': '建议',
    '意見': '意见',
    '問題': '问题',
    '困難': '困难',
    '挑戰': '挑战',
    '機會': '机会',
    '優勢': '优势',
    '劣勢': '劣势',
    '競爭': '竞争',
    '需求': '需求',
    '供應': '供应',
    '成本': '成本',
    '費用': '费用',
    '收入': '收入',
    '支出': '支出',
    '資產': '资产',
    '負債': '负债',
    '權益': '权益',
    '資本': '资本',
    '資金': '资金',
    '現金': '现金',
    '存款': '存款',
    '儲蓄': '储蓄',
    '利息': '利息',
    '利率': '利率'
}

def convert_to_simplified_chinese(text: str) -> str:
    """Convert traditional Chinese characters to simplified Chinese"""
    if not text:
        return text
    
    result = text
    for traditional, simplified in TRADITIONAL_TO_SIMPLIFIED.items():
        result = result.replace(traditional, simplified)
    
    return result

def create_chinese_decks() -> List[Dict[str, Any]]:
    """Create the 5 Chinese financial vocabulary decks"""
    decks = [
        {
            "name": "Chinese Finance 1",
            "description": "Essential Chinese financial vocabulary - Part 1",
            "difficulty_level": "intermediate",
            "language_a_name": "Chinese",
            "language_b_name": "French",
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 516,
            "is_active": True
        },
        {
            "name": "Chinese Finance 2", 
            "description": "Essential Chinese financial vocabulary - Part 2",
            "difficulty_level": "intermediate",
            "language_a_name": "Chinese",
            "language_b_name": "French", 
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 516,
            "is_active": True
        },
        {
            "name": "Chinese Finance 3",
            "description": "Essential Chinese financial vocabulary - Part 3", 
            "difficulty_level": "intermediate",
            "language_a_name": "Chinese",
            "language_b_name": "French",
            "language_a_code": "zh", 
            "language_b_code": "fr",
            "total_words": 515,
            "is_active": True
        },
        {
            "name": "Chinese Finance 4",
            "description": "Essential Chinese financial vocabulary - Part 4",
            "difficulty_level": "intermediate", 
            "language_a_name": "Chinese",
            "language_b_name": "French",
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 515,
            "is_active": True
        },
        {
            "name": "Chinese Finance 5",
            "description": "Essential Chinese financial vocabulary - Part 5",
            "difficulty_level": "intermediate",
            "language_a_name": "Chinese", 
            "language_b_name": "French",
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 515,
            "is_active": True
        }
    ]
    return decks

def load_vocabulary_from_db(db_path: str) -> List[Dict[str, Any]]:
    """Load vocabulary from SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT word_number, chinese_word, french_translation, 
               example_sentence, sentence_translation
        FROM vocabulary
        ORDER BY word_number
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    vocabulary = []
    for row in rows:
        word_number, chinese_word, french_translation, example_sentence, sentence_translation = row
        
        # Convert traditional Chinese to simplified
        chinese_word_simplified = convert_to_simplified_chinese(chinese_word)
        example_sentence_simplified = convert_to_simplified_chinese(example_sentence)
        
        vocabulary.append({
            "word_number": word_number,
            "language_a_word": chinese_word_simplified,
            "language_b_translation": french_translation,
            "language_a_sentence": example_sentence_simplified,
            "language_b_sentence": sentence_translation
        })
    
    return vocabulary

def insert_deck_to_supabase(deck: Dict[str, Any]) -> str:
    """Insert deck into Supabase and return deck ID"""
    try:
        result = supabase.table('vocabulary_decks').insert(deck).execute()
        deck_id = result.data[0]['id']
        print(f"✅ Created deck: {deck['name']} (ID: {deck_id})")
        return deck_id
    except Exception as e:
        print(f"❌ Error creating deck {deck['name']}: {e}")
        raise

def insert_vocabulary_to_supabase(vocabulary: List[Dict[str, Any]]) -> List[str]:
    """Insert vocabulary into Supabase and return vocabulary IDs"""
    vocab_ids = []
    
    # Insert in batches of 100
    batch_size = 100
    for i in range(0, len(vocabulary), batch_size):
        batch = vocabulary[i:i + batch_size]
        
        # Prepare batch data
        batch_data = []
        for item in batch:
            batch_data.append({
                "language_a_word": item["language_a_word"],
                "language_b_translation": item["language_b_translation"],
                "language_a_sentence": item["language_a_sentence"],
                "language_b_sentence": item["language_b_sentence"]
            })
        
        try:
            result = supabase.table('vocabulary').insert(batch_data).execute()
            batch_ids = [item['id'] for item in result.data]
            vocab_ids.extend(batch_ids)
            print(f"✅ Inserted batch {i//batch_size + 1}: {len(batch_ids)} words")
        except Exception as e:
            print(f"❌ Error inserting vocabulary batch {i//batch_size + 1}: {e}")
            raise
    
    return vocab_ids

def link_vocabulary_to_deck(deck_id: str, vocabulary_ids: List[str]):
    """Link vocabulary to deck in deck_vocabulary table"""
    deck_vocab_data = []
    for i, vocab_id in enumerate(vocabulary_ids):
        deck_vocab_data.append({
            "deck_id": deck_id,
            "vocabulary_id": vocab_id,
            "word_order": i + 1
        })
    
    # Insert in batches
    batch_size = 100
    for i in range(0, len(deck_vocab_data), batch_size):
        batch = deck_vocab_data[i:i + batch_size]
        
        try:
            supabase.table('deck_vocabulary').insert(batch).execute()
            print(f"✅ Linked batch {i//batch_size + 1}: {len(batch)} words to deck")
        except Exception as e:
            print(f"❌ Error linking vocabulary batch {i//batch_size + 1}: {e}")
            raise

def migrate_chinese_decks():
    """Main migration function"""
    print("🚀 Starting Chinese Financial Vocabulary Migration")
    print("=" * 60)
    
    # Create decks
    decks = create_chinese_decks()
    deck_ids = []
    
    for i, deck in enumerate(decks, 1):
        print(f"\n📚 Processing Deck {i}: {deck['name']}")
        print("-" * 40)
        
        # Create deck in Supabase
        deck_id = insert_deck_to_supabase(deck)
        deck_ids.append(deck_id)
        
        # Load vocabulary from SQLite
        db_path = f"{CHINESE_VOCAB_PATH}/financial_vocab_batch_merged_{i}.db"
        print(f"📖 Loading vocabulary from: {db_path}")
        
        vocabulary = load_vocabulary_from_db(db_path)
        print(f"📝 Loaded {len(vocabulary)} vocabulary items")
        
        # Show sample of converted text
        if vocabulary:
            sample = vocabulary[0]
            print(f"🔍 Sample conversion:")
            print(f"   Chinese: {sample['language_a_word']}")
            print(f"   French: {sample['language_b_translation']}")
            print(f"   Example: {sample['language_a_sentence'][:50]}...")
        
        # Insert vocabulary to Supabase
        print(f"💾 Inserting vocabulary to Supabase...")
        vocabulary_ids = insert_vocabulary_to_supabase(vocabulary)
        
        # Link vocabulary to deck
        print(f"🔗 Linking vocabulary to deck...")
        link_vocabulary_to_deck(deck_id, vocabulary_ids)
        
        print(f"✅ Completed Deck {i}: {deck['name']}")
        
        # Small delay between decks
        if i < len(decks):
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎉 Chinese Financial Vocabulary Migration Complete!")
    print(f"📊 Created {len(deck_ids)} decks with total vocabulary items")
    
    return deck_ids

if __name__ == "__main__":
    try:
        deck_ids = migrate_chinese_decks()
        print(f"\n🎯 Deck IDs created: {deck_ids}")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

