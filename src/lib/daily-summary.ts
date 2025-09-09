import { supabase } from './supabase'

export interface DailySummary {
  date: string
  reviews_done: number
  new_words_learned: number
}

export class DailySummaryManager {
  /**
   * Log daily summary for a user
   */
  static async logDailySummary(
    userId: string, 
    reviewsDone: number, 
    newWordsLearned: number
  ): Promise<void> {
    try {
      const dateString = new Date().toISOString().split('T')[0]
      
      // Get existing summary for today
      const { data: existingSummary } = await supabase
        .from('daily_summary')
        .select('*')
        .eq('user_id', userId)
        .eq('date', dateString)
        .single()

      let totalReviews = reviewsDone
      let totalNewWords = newWordsLearned

      if (existingSummary) {
        // Add to existing counts
        totalReviews = existingSummary.reviews_done + reviewsDone
        totalNewWords = existingSummary.new_words_learned + newWordsLearned
      }

      // Insert or update daily summary
      const { error } = await supabase
        .from('daily_summary')
        .upsert({
          user_id: userId,
          date: dateString,
          reviews_done: totalReviews,
          new_words_learned: totalNewWords
        })

      if (error) {
        console.error('Error logging daily summary:', error)
      } else {
        console.log(`Daily summary logged: ${totalReviews} reviews, ${totalNewWords} new words`)
      }
    } catch (error) {
      console.error('Error in logDailySummary:', error)
    }
  }

  /**
   * Get recent activity stats for a user
   */
  static async getRecentActivityStats(userId: string): Promise<{
    reviewsToday: number
    reviews7Days: number
    reviews30Days: number
    currentStreak: number
  }> {
    try {
      const today = new Date()
      const sevenDaysAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
      const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)

      // Get daily summaries for the last 30 days
      const { data: summaries, error } = await supabase
        .from('daily_summary')
        .select('*')
        .eq('user_id', userId)
        .gte('date', thirtyDaysAgo.toISOString().split('T')[0])
        .order('date', { ascending: false })

      if (error) {
        console.error('Error fetching daily summaries:', error)
        return { reviewsToday: 0, reviews7Days: 0, reviews30Days: 0, currentStreak: 0 }
      }

      let reviewsToday = 0
      let reviews7Days = 0
      let reviews30Days = 0

      summaries?.forEach(summary => {
        const summaryDate = new Date(summary.date)
        const dayDiff = Math.floor((today.getTime() - summaryDate.getTime()) / (1000 * 60 * 60 * 24))

        if (dayDiff < 1) {
          reviewsToday = summary.reviews_done
        }
        if (dayDiff < 7) {
          reviews7Days += summary.reviews_done
        }
        if (dayDiff < 30) {
          reviews30Days += summary.reviews_done
        }
      })

      // Calculate current streak
      const currentStreak = this.calculateCurrentStreak(summaries || [])

      return {
        reviewsToday,
        reviews7Days,
        reviews30Days,
        currentStreak
      }
    } catch (error) {
      console.error('Error in getRecentActivityStats:', error)
      return { reviewsToday: 0, reviews7Days: 0, reviews30Days: 0, currentStreak: 0 }
    }
  }

  /**
   * Calculate current streak from daily summaries
   */
  private static calculateCurrentStreak(summaries: DailySummary[]): number {
    const dateSet = new Set(summaries.map(s => s.date))
    let streak = 0
    let checkDay = new Date()

    // If no activity today, start from yesterday
    if (!dateSet.has(checkDay.toISOString().split('T')[0])) {
      checkDay.setDate(checkDay.getDate() - 1)
    }

    // Count consecutive days with activity
    while (dateSet.has(checkDay.toISOString().split('T')[0])) {
      streak++
      checkDay.setDate(checkDay.getDate() - 1)
    }

    return streak
  }
}
