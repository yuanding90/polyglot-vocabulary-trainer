# Multi-Language Vocabulary Trainer

A modern, intelligent vocabulary learning application that supports any language pair with advanced spaced repetition algorithms.

## 🌟 Features

- **Multi-Language Support**: Learn vocabulary in any language pair (A → B)
- **Smart SRS Algorithm**: Advanced spaced repetition system for optimal learning
- **Progress Tracking**: Detailed analytics and learning statistics
- **Multiple Study Modes**: Review, Discovery, and Deep Dive sessions
- **Pronunciation Support**: Text-to-speech for multiple languages
- **Modern UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- Python 3.8+ (for data migration)
- Supabase account

### Installation

1. **Clone and install dependencies**
   ```bash
   cd multi-language-vocabulary-trainer
   npm install
   ```

2. **Set up environment variables**
   ```bash
   cp .env.local.example .env.local
   ```
   
   Add your Supabase credentials:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

3. **Set up database**
   ```bash
   # Run the database schema
   # Copy the contents of database_schema.sql to your Supabase SQL Editor
   ```

4. **Migrate existing data** (optional)
   ```bash
   python migrate_databases.py
   ```

5. **Start development server**
   ```bash
   npm run dev
   ```

## 📊 Database Schema

### Core Tables

- **`vocabulary`**: Language-agnostic vocabulary storage
- **`vocabulary_decks`**: Deck metadata with language pair information
- **`deck_vocabulary`**: Relationship between decks and vocabulary
- **`user_progress`**: Individual user learning progress
- **`study_sessions`**: Session tracking and analytics
- **`rating_history`**: SRS algorithm data

### Language Support

The system supports any language pair through:
- Language codes (e.g., 'zh', 'fr', 'en')
- Language names (e.g., 'Chinese', 'French', 'English')
- Dynamic pronunciation based on language codes

## 🔧 Development

### Project Structure

```
src/
├── app/                 # Next.js app router
├── components/          # React components
│   ├── ui/             # Reusable UI components
│   └── ...             # Feature components
├── lib/                # Utilities and configurations
├── store/              # Zustand state management
└── types/              # TypeScript type definitions
```

### Key Technologies

- **Frontend**: Next.js 15, React 19, TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Icons**: Lucide React

## 📈 Data Migration

### Supported Formats

The migration script supports SQLite databases with the following structure:
```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY,
    word_number INTEGER,
    [language_a]_word TEXT,
    [language_b]_translation TEXT,
    example_sentence TEXT,
    sentence_translation TEXT,
    created_at TIMESTAMP
);
```

### Migration Process

1. **Analyze databases**: `python analyze_databases.py`
2. **Set up Supabase**: Run the database schema
3. **Migrate data**: `python migrate_databases.py`

## 🎯 Study Modes

### Review Mode
- Spaced repetition algorithm
- Due word prioritization
- Progress tracking

### Discovery Mode
- New word introduction
- Contextual learning
- Example sentences

### Deep Dive Mode
- Focused practice on specific categories
- Leech management
- Advanced analytics

## 🌐 Language Support

### Currently Supported Languages
- Chinese (zh)
- French (fr)
- English (en)
- Spanish (es)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Japanese (ja)
- Korean (ko)

### Adding New Languages
1. Add language code to `LANGUAGE_CODES` in utils
2. Update pronunciation settings
3. Add language-specific text processing if needed

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🤝 Support

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for language learners worldwide**
