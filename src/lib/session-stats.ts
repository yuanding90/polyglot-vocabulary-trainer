import { supabase } from './supabase'

export interface SessionStats {
  reviewsToday: number
  reviews7Days: number
  reviews30Days: number
  currentStreak: number
}

export async function calculateSessionStats(userId: string): Promise<SessionStats> {
  try {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const sevenDaysAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)

    // Calculate reviews today (from rating_history)
    const { count: reviewsToday, error: todayError } = await supabase
      .from('rating_history')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId)
      .gte('timestamp', today.toISOString())

    if (todayError) {
      console.error('Error calculating reviews today:', todayError)
    }

    // Calculate reviews in last 7 days
    const { count: reviews7Days, error: weekError } = await supabase
      .from('rating_history')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId)
      .gte('timestamp', sevenDaysAgo.toISOString())

    if (weekError) {
      console.error('Error calculating reviews 7 days:', weekError)
    }

    // Calculate reviews in last 30 days
    const { count: reviews30Days, error: monthError } = await supabase
      .from('rating_history')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId)
      .gte('timestamp', thirtyDaysAgo.toISOString())

    if (monthError) {
      console.error('Error calculating reviews 30 days:', monthError)
    }

    // Calculate current streak
    const currentStreak = await calculateCurrentStreak(userId)

    return {
      reviewsToday: reviewsToday || 0,
      reviews7Days: reviews7Days || 0,
      reviews30Days: reviews30Days || 0,
      currentStreak
    }
  } catch (error) {
    console.error('Error calculating session stats:', error)
    return {
      reviewsToday: 0,
      reviews7Days: 0,
      reviews30Days: 0,
      currentStreak: 0
    }
  }
}

async function calculateCurrentStreak(userId: string): Promise<number> {
  try {
    // Get all study days for the user
    const { data: ratingHistory, error } = await supabase
      .from('rating_history')
      .select('timestamp')
      .eq('user_id', userId)
      .order('timestamp', { ascending: false })

    if (error || !ratingHistory) {
      return 0
    }

    // Group by date and check for consecutive days
    const studyDates = new Set<string>()
    ratingHistory.forEach(rating => {
      const date = new Date(rating.timestamp).toDateString()
      studyDates.add(date)
    })

    const sortedDates = Array.from(studyDates).sort().reverse()
    let streak = 0
    const today = new Date().toDateString()
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toDateString()

    // Check if user studied today or yesterday to start counting
    if (sortedDates.includes(today)) {
      streak = 1
      let currentDate = new Date(Date.now() - 24 * 60 * 60 * 1000)
      
      for (let i = 1; i < 365; i++) { // Check up to a year
        const checkDate = currentDate.toDateString()
        if (sortedDates.includes(checkDate)) {
          streak++
          currentDate = new Date(currentDate.getTime() - 24 * 60 * 60 * 1000)
        } else {
          break
        }
      }
    } else if (sortedDates.includes(yesterday)) {
      // If no study today but studied yesterday, start from yesterday
      streak = 1
      let currentDate = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
      
      for (let i = 1; i < 365; i++) {
        const checkDate = currentDate.toDateString()
        if (sortedDates.includes(checkDate)) {
          streak++
          currentDate = new Date(currentDate.getTime() - 24 * 60 * 60 * 1000)
        } else {
          break
        }
      }
    }

    return streak
  } catch (error) {
    console.error('Error calculating streak:', error)
    return 0
  }
}

