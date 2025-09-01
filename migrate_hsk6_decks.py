#!/usr/bin/env python3
"""
HSK6 Vocabulary Migration Script
Migrates 5 merged HSK6 vocabulary databases to Supabase
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
print("Loading environment variables...")
load_dotenv('.env.local')

# Initialize Supabase client
supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

print(f"Supabase URL: {supabase_url}")
print(f"Supabase Key: {supabase_key[:20]}..." if supabase_key else "None")

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase environment variables")

print("Creating Supabase client...")
supabase: Client = create_client(supabase_url, supabase_key)

# HSK6 vocabulary database path
HSK6_VOCAB_PATH = "/Users/ding/Desktop/Coding/Chinese App"

# Traditional to Simplified Chinese mapping (common HSK6 terms)
TRADITIONAL_TO_SIMPLIFIED = {
    # Common HSK6 vocabulary that might contain traditional characters
    '學習': '学习',
    '學校': '学校',
    '學生': '学生',
    '老師': '老师',
    '課程': '课程',
    '考試': '考试',
    '成績': '成绩',
    '畢業': '毕业',
    '大學': '大学',
    '中學': '中学',
    '小學': '小学',
    '圖書館': '图书馆',
    '實驗室': '实验室',
    '辦公室': '办公室',
    '會議室': '会议室',
    '餐廳': '餐厅',
    '醫院': '医院',
    '銀行': '银行',
    '郵局': '邮局',
    '警察局': '警察局',
    '火車站': '火车站',
    '飛機場': '飞机场',
    '地鐵站': '地铁站',
    '公共汽車': '公共汽车',
    '計程車': '计程车',
    '自行車': '自行车',
    '摩托車': '摩托车',
    '電梯': '电梯',
    '樓梯': '楼梯',
    '電燈': '电灯',
    '電視': '电视',
    '電腦': '电脑',
    '電話': '电话',
    '手機': '手机',
    '相機': '相机',
    '收音機': '收音机',
    '錄音機': '录音机',
    '照相機': '照相机',
    '電影院': '电影院',
    '劇院': '剧院',
    '博物館': '博物馆',
    '美術館': '美术馆',
    '公園': '公园',
    '動物園': '动物园',
    '植物園': '植物园',
    '遊樂園': '游乐园',
    '游泳池': '游泳池',
    '健身房': '健身房',
    '體育館': '体育馆',
    '足球場': '足球场',
    '籃球場': '篮球场',
    '網球場': '网球场',
    '高爾夫球場': '高尔夫球场',
    '滑雪場': '滑雪场',
    '海灘': '海滩',
    '山脈': '山脉',
    '河流': '河流',
    '湖泊': '湖泊',
    '海洋': '海洋',
    '島嶼': '岛屿',
    '森林': '森林',
    '沙漠': '沙漠',
    '草原': '草原',
    '農田': '农田',
    '果園': '果园',
    '花園': '花园',
    '菜園': '菜园',
    '溫室': '温室',
    '農場': '农场',
    '牧場': '牧场',
    '漁場': '渔场',
    '礦場': '矿场',
    '工廠': '工厂',
    '車間': '车间',
    '倉庫': '仓库',
    '商店': '商店',
    '超市': '超市',
    '市場': '市场',
    '商場': '商场',
    '百貨公司': '百货公司',
    '專賣店': '专卖店',
    '便利店': '便利店',
    '書店': '书店',
    '文具店': '文具店',
    '服裝店': '服装店',
    '鞋店': '鞋店',
    '珠寶店': '珠宝店',
    '化妝品店': '化妆品店',
    '藥店': '药店',
    '眼鏡店': '眼镜店',
    '理髮店': '理发店',
    '美容院': '美容院',
    '按摩院': '按摩院',
    '瑜伽館': '瑜伽馆',
    '武術館': '武术馆',
    '舞蹈學校': '舞蹈学校',
    '音樂學校': '音乐学校',
    '美術學校': '美术学校',
    '語言學校': '语言学校',
    '駕駛學校': '驾驶学校',
    '烹飪學校': '烹饪学校',
    '電腦學校': '电脑学校',
    '會計師事務所': '会计师事务所',
    '律師事務所': '律师事务所',
    '建築師事務所': '建筑师事务所',
    '工程師事務所': '工程师事务所',
    '設計師事務所': '设计师事务所',
    '翻譯公司': '翻译公司',
    '廣告公司': '广告公司',
    '公關公司': '公关公司',
    '諮詢公司': '咨询公司',
    '投資公司': '投资公司',
    '保險公司': '保险公司',
    '房地產公司': '房地产公司',
    '旅遊公司': '旅游公司',
    '運輸公司': '运输公司',
    '物流公司': '物流公司',
    '快遞公司': '快递公司',
    '清潔公司': '清洁公司',
    '保安公司': '保安公司',
    '維修公司': '维修公司',
    '安裝公司': '安装公司',
    '裝修公司': '装修公司',
    '建築公司': '建筑公司',
    '開發公司': '开发公司',
    '製造公司': '制造公司',
    '貿易公司': '贸易公司',
    '進出口公司': '进出口公司',
    '批發公司': '批发公司',
    '零售公司': '零售公司',
    '連鎖店': '连锁店',
    '加盟店': '加盟店',
    '直營店': '直营店',
    '網店': '网店',
    '實體店': '实体店',
    '旗艦店': '旗舰店',
    '概念店': '概念店',
    '體驗店': '体验店',
    '展示廳': '展示厅',
    '展覽館': '展览馆',
    '會議中心': '会议中心',
    '展覽中心': '展览中心',
    '商務中心': '商务中心',
    '金融中心': '金融中心',
    '文化中心': '文化中心',
    '藝術中心': '艺术中心',
    '科技中心': '科技中心',
    '教育中心': '教育中心',
    '培訓中心': '培训中心',
    '研究中心': '研究中心',
    '開發中心': '开发中心',
    '創新中心': '创新中心',
    '創業中心': '创业中心',
    '孵化器': '孵化器',
    '加速器': '加速器',
    '科技園': '科技园',
    '工業園': '工业园',
    '經濟開發區': '经济开发区',
    '自由貿易區': '自由贸易区',
    '保稅區': '保税区',
    '出口加工區': '出口加工区',
    '高新技術開發區': '高新技术开发区',
    '經濟特區': '经济特区',
    '沿海開放城市': '沿海开放城市',
    '內陸開放城市': '内陆开放城市',
    '邊境開放城市': '边境开放城市',
    '一帶一路': '一带一路',
    '絲綢之路': '丝绸之路',
    '海上絲綢之路': '海上丝绸之路',
    '陸上絲綢之路': '陆上丝绸之路',
    '數字絲綢之路': '数字丝绸之路',
    '健康絲綢之路': '健康丝绸之路',
    '綠色絲綢之路': '绿色丝绸之路',
    '創新絲綢之路': '创新丝绸之路',
    '文明絲綢之路': '文明丝绸之路',
    '和平絲綢之路': '和平丝绸之路',
    '繁榮絲綢之路': '繁荣丝绸之路',
    '開放絲綢之路': '开放丝绸之路',
    '包容絲綢之路': '包容丝绸之路',
    '平衡絲綢之路': '平衡丝绸之路',
    '普惠絲綢之路': '普惠丝绸之路',
    '可持續絲綢之路': '可持续丝绸之路',
    '高質量絲綢之路': '高质量丝绸之路',
    '現代化絲綢之路': '现代化丝绸之路',
    '國際化絲綢之路': '国际化丝绸之路',
    '全球化絲綢之路': '全球化丝绸之路',
    '區域化絲綢之路': '区域化丝绸之路',
    '一體化絲綢之路': '一体化丝绸之路',
    '多元化絲綢之路': '多元化丝绸之路',
    '立體化絲綢之路': '立体化丝绸之路',
    '網絡化絲綢之路': '网络化丝绸之路',
    '智能化絲綢之路': '智能化丝绸之路',
    '數字化絲綢之路': '数字化丝绸之路',
    '信息化絲綢之路': '信息化丝绸之路'
}

def convert_to_simplified_chinese(text: str) -> str:
    """Convert traditional Chinese characters to simplified Chinese"""
    if not text:
        return text
    
    result = text
    for traditional, simplified in TRADITIONAL_TO_SIMPLIFIED.items():
        result = result.replace(traditional, simplified)
    
    return result

def create_hsk6_decks() -> List[Dict[str, Any]]:
    """Create the 5 HSK6 vocabulary decks"""
    decks = [
        {
            "name": "HSK6 Level 1",
            "description": "HSK6 vocabulary - Part 1 (Advanced Chinese)",
            "difficulty_level": "advanced",
            "language_a_name": "Chinese",
            "language_b_name": "French",
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 1003,
            "is_active": True
        },
        {
            "name": "HSK6 Level 2", 
            "description": "HSK6 vocabulary - Part 2 (Advanced Chinese)",
            "difficulty_level": "advanced",
            "language_a_name": "Chinese",
            "language_b_name": "French", 
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 1003,
            "is_active": True
        },
        {
            "name": "HSK6 Level 3",
            "description": "HSK6 vocabulary - Part 3 (Advanced Chinese)", 
            "difficulty_level": "advanced",
            "language_a_name": "Chinese",
            "language_b_name": "French",
            "language_a_code": "zh", 
            "language_b_code": "fr",
            "total_words": 1003,
            "is_active": True
        },
        {
            "name": "HSK6 Level 4",
            "description": "HSK6 vocabulary - Part 4 (Advanced Chinese)",
            "difficulty_level": "advanced", 
            "language_a_name": "Chinese",
            "language_b_name": "French",
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 1002,
            "is_active": True
        },
        {
            "name": "HSK6 Level 5",
            "description": "HSK6 vocabulary - Part 5 (Advanced Chinese)",
            "difficulty_level": "advanced",
            "language_a_name": "Chinese", 
            "language_b_name": "French",
            "language_a_code": "zh",
            "language_b_code": "fr",
            "total_words": 1002,
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

def migrate_hsk6_decks():
    """Main migration function"""
    print("🚀 Starting HSK6 Vocabulary Migration")
    print("=" * 60)
    
    # Create decks
    decks = create_hsk6_decks()
    deck_ids = []
    
    for i, deck in enumerate(decks, 1):
        print(f"\n📚 Processing Deck {i}: {deck['name']}")
        print("-" * 40)
        
        # Create deck in Supabase
        deck_id = insert_deck_to_supabase(deck)
        deck_ids.append(deck_id)
        
        # Load vocabulary from SQLite
        db_path = f"{HSK6_VOCAB_PATH}/hsk6_vocab_batch_merged_{i}.db"
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
    print("🎉 HSK6 Vocabulary Migration Complete!")
    print(f"📊 Created {len(deck_ids)} decks with total vocabulary items")
    
    return deck_ids

if __name__ == "__main__":
    try:
        deck_ids = migrate_hsk6_decks()
        print(f"\n🎯 Deck IDs created: {deck_ids}")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
