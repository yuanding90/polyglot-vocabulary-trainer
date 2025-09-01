'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BookOpen, Globe, Brain, Target, Users, Zap } from 'lucide-react';

interface Deck {
  id: string;
  name: string;
  description: string;
  language_a_name: string;
  language_b_name: string;
  total_words: number;
  difficulty_level: string;
}

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);
  // const supabase = createClient();

  useEffect(() => {
    // Skip authentication for now - go directly to deck selection
    fetchDecks();
  }, []);

  const checkUser = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    setUser(user);
  };

  const fetchDecks = async () => {
    try {
      const { data, error } = await supabase
        .from('vocabulary_decks')
        .select('*')
        .order('created_at', { ascending: true });

      if (error) {
        console.error('Error fetching decks:', error);
      } else {
        setDecks(data || []);
      }
    } catch (error) {
      console.error('Error fetching decks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    });
    if (error) console.error('Error signing in:', error);
  };

  const handleSignOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) console.error('Error signing out:', error);
    setUser(null);
  };

  const handleDeckSelect = (deck: Deck) => {
    setSelectedDeck(deck);
    // Store selected deck in localStorage for the app to use
    localStorage.setItem('selectedDeck', JSON.stringify(deck));
    // Redirect to the main app
    window.location.href = '/dashboard';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Globe className="h-8 w-8 text-indigo-600" />
              <h1 className="text-2xl font-bold text-gray-900">Polyglot Vocabulary Trainer</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Polyglot Vocabulary Trainer</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Deck selection for all users (skip authentication) */}
        <div>
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Choose Your Language Deck
            </h2>
            <p className="text-lg text-gray-600">
              Select a vocabulary deck to start your learning journey
            </p>
          </div>

          {decks.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Decks Available</h3>
              <p className="text-gray-600 mb-6">
                Vocabulary decks will appear here once they're added to the system.
              </p>
              <div className="text-sm text-gray-500">
                <p>Example decks that will be available:</p>
                <ul className="mt-2 space-y-1">
                  <li>• Chinese → French (Financial Vocabulary)</li>
                  <li>• French → English (General Vocabulary)</li>
                  <li>• Spanish → English (Business Terms)</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {decks.map((deck) => (
                <Card 
                  key={deck.id} 
                  className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
                  onClick={() => handleDeckSelect(deck)}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Globe className="h-5 w-5 text-indigo-600" />
                        <CardTitle className="text-lg">{deck.name}</CardTitle>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        deck.difficulty_level === 'beginner' ? 'bg-green-100 text-green-800' :
                        deck.difficulty_level === 'elementary' ? 'bg-blue-100 text-blue-800' :
                        deck.difficulty_level === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {deck.difficulty_level}
                      </span>
                    </div>
                    <CardDescription>
                      {deck.language_a_name} → {deck.language_b_name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-4">{deck.description}</p>
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>{deck.total_words} words</span>
                      <Button size="sm" className="text-xs">
                        Start Learning
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
